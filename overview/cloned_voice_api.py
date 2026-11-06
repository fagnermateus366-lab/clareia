"""Local API for the My Voices window; GPU work never blocks the request loop."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import cloned_voices as voices
from .core import ROOT, Settings
from .voices import Delivery


class Preview(BaseModel):
    texto: str = Field(default='Uma boa explicação começa com uma pergunta. Vamos descobrir novas ideias, passo a passo.', min_length=3, max_length=1000)
    estilo_locucao: Delivery = 'natural'
    como_narracao: bool = False


class VoiceTuning(BaseModel):
    expressividade: float = Field(default=.5, ge=.25, le=1)
    fidelidade: float = Field(default=0., ge=0, le=.8)
    variacao: float = Field(default=.8, ge=.4, le=1)
    interpretacao: Literal['natural', 'original'] | None = None


def make_router(active):
    router = APIRouter(prefix='/api/cloned-voices')
    previews = {}

    @router.get('')
    def listing():
        return {'motores': voices.engines(), 'vozes': [
            {k: p[k] for k in ('id', 'nome', 'motor', 'duracao', 'criado', 'preparo', 'preparo_erro', 'fidelidade', 'variacao', 'expressividade', 'interpretacao') if k in p}
            for p in voices.listing()]}

    @router.post('')
    async def save(nome: str = Form(...), motor: str = Form(...), transcricao: str = Form(''),
                   expressividade: float = Form(.5), audio: UploadFile = File(...),
                   fidelidade: float = Form(0.), variacao: float = Form(.8),
                   interpretacao: Literal['natural', 'original'] = Form('natural')):
        from starlette.concurrency import run_in_threadpool
        try:
            data = bytearray()
            while chunk := await audio.read(1024 * 1024):
                data.extend(chunk)
                if len(data) > voices.MAX_BYTES:
                    raise HTTPException(413, 'Envie uma amostra de até 30 MB.')
            try:
                return await run_in_threadpool(voices.save, nome, motor, transcricao, expressividade, bytes(data), fidelidade, variacao, interpretacao)
            except (RuntimeError, ValueError) as exc:
                raise HTTPException(400, str(exc)[:500]) from exc
        finally:
            await audio.close()

    @router.get('/{voice}/reference')
    def reference(voice: str, preparada: bool = False):
        voices.profile(voice)
        target = voices.STORE / voice / ('reference-prepared.wav' if preparada else 'reference.wav')
        if not target.is_file():
            raise HTTPException(404, 'A amostra não está disponível. Grave novamente.')
        return FileResponse(target, media_type='audio/wav')

    @router.put('/{voice}/settings')
    def configure(voice: str, body: VoiceTuning):
        from .speech import TTS_LOCK
        if not active.acquire(blocking=False):
            raise HTTPException(409, 'Aguarde o processamento terminar antes de ajustar a voz.')
        try:
            if not TTS_LOCK.acquire(blocking=False):
                raise HTTPException(409, 'Já existe uma voz em processamento. Aguarde.')
            try:
                return voices.configure(voice, body.expressividade, body.fidelidade, body.variacao, body.interpretacao)
            finally:
                TTS_LOCK.release()
        finally:
            active.release()

    @router.delete('/{voice}')
    def remove(voice: str):
        from .speech import TTS_LOCK
        if not active.acquire(blocking=False):
            raise HTTPException(409, 'Aguarde o processamento terminar antes de apagar uma voz.')
        try:
            if not TTS_LOCK.acquire(blocking=False):
                raise HTTPException(409, 'Já existe uma voz em processamento. Aguarde antes de apagar.')
            try:
                result = voices.remove(voice)
                for key, value in list(previews.items()):
                    if value.get('voz') == voice:
                        del previews[key]
                return result
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            finally:
                TTS_LOCK.release()
        finally:
            active.release()

    @router.delete('/{voice}/previews')
    def remove_previews(voice: str):
        from .speech import TTS_LOCK
        if not active.acquire(blocking=False):
            raise HTTPException(409, 'Aguarde o processamento terminar antes de apagar a prévia.')
        try:
            if not TTS_LOCK.acquire(blocking=False):
                raise HTTPException(409, 'Já existe uma voz em processamento. Aguarde antes de apagar a prévia.')
            try:
                result = voices.remove_previews(voice)
                for key, value in list(previews.items()):
                    if value.get('voz') == voice:
                        del previews[key]
                return result
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            finally:
                TTS_LOCK.release()
        finally:
            active.release()

    @router.post('/{voice}/preview')
    def preview(voice: str, body: Preview):
        from .speech import TTS_LOCK, synthesize, scene_audio, release
        voices.profile(voice)
        if not active.acquire(blocking=False):
            raise HTTPException(409, 'Aguarde o projeto em processamento antes de testar uma voz.')
        if not TTS_LOCK.acquire(blocking=False):
            active.release()
            raise HTTPException(409, 'Já existe uma voz em processamento. Aguarde.')
        job = uuid.uuid4().hex
        for key, value in list(previews.items()):
            if time.time() - value['criado'] > 86400:
                del previews[key]
        previews[job] = {'status': 'processando', 'criado': time.time(), 'voz': voice, 'mensagem': 'Preparando o modelo e gerando a prévia…'}

        def work():
            try:
                folder = ROOT / 'output/amostras/clonadas' / voice
                if body.como_narracao:
                    path, _ = scene_audio({'narracao_ptbr': body.texto, 'apresentador': 1},
                                          Settings(voz=voice, estilo_locucao=body.estilo_locucao), folder)
                else:
                    path, _ = synthesize(body.texto, voice, 1, folder, delivery=body.estilo_locucao)
                previews[job].update(status='concluido', arquivo=str(path),
                                     url=f'/api/cloned-voices/previews/{job}/audio', mensagem='Prévia pronta.')
            except Exception as exc:
                import logging
                logging.exception('Falha na prévia de voz clonada')
                previews[job].update(status='erro', mensagem=str(exc)[:600])
            finally:
                try:
                    release()
                except Exception:
                    import logging
                    logging.exception('Falha ao liberar o motor de voz')
                finally:
                    TTS_LOCK.release()
                    active.release()

        threading.Thread(target=work, daemon=True).start()
        return {'id': job, **previews[job]}

    @router.get('/previews/{job}')
    def preview_status(job: str):
        if job not in previews:
            raise HTTPException(404, 'Prévia não encontrada. Gere novamente.')
        return {k: v for k, v in previews[job].items() if k != 'arquivo'}

    @router.get('/previews/{job}/audio')
    def preview_audio(job: str):
        value = previews.get(job, {})
        if value.get('status') != 'concluido':
            raise HTTPException(404, 'A prévia ainda não está pronta.')
        return FileResponse(value['arquivo'], media_type='audio/wav')

    return router
