"""Personal voice profiles and isolated, persistent local TTS workers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid

import soundfile as sf

from .core import ROOT, CREATE_FLAGS, binary, digest, read_json, run, write_json

BASE = ROOT / '.models/voice-cloning'
STORE = ROOT / '.private/cloned-voices'
ENGINES = {'chatterbox': ('Chatterbox · original V3', 'chatterbox-multilingual')}
MAX_BYTES = 30 * 1024 * 1024
LOCK = threading.RLock()
_worker = None


def python_path(engine):
    if engine not in ENGINES:
        raise ValueError('Escolha o Chatterbox para clonar a voz.')
    return BASE / 'envs' / engine / 'Scripts/python.exe'


def engines():
    manifest = read_json(BASE / 'installed-models.json', {}).get('models', [])
    installed = {Path(m['path']).name for m in manifest if m.get('complete')}
    return [{'id': key, 'nome': name, 'instalado': folder in installed and python_path(key).is_file()}
            for key, (name, folder) in ENGINES.items()]


def profile(voice):
    if not re.fullmatch(r'clone_[0-9a-f]{12}', voice):
        raise ValueError('Identificador de voz inválido.')
    value = read_json(STORE / voice / 'profile.json')
    if not value:
        raise ValueError('A voz salva não está disponível. Escolha outra voz ou cadastre a amostra novamente.')
    return value


def listing():
    # Profile JSON is replaced atomically. Catalog reads must remain responsive
    # while the synthesis worker holds LOCK, sometimes for several minutes.
    values=[value for p in STORE.glob('clone_*/profile.json') if (value:=read_json(p))]
    return sorted(values,key=lambda p:p['criado'])


def catalog():
    ready = {e['id']: e['instalado'] for e in engines()}
    return [{'id': p['id'], 'nome': p['nome'], 'motor': ENGINES.get(p['motor'], ('Motor removido',))[0],
             'descricao': p.get('preparo_erro') or 'Sua voz salva · timbre preservado',
             'instalada': ready.get(p['motor'], False) and not p.get('preparo_erro')}
            for p in listing()]


def identity(voice):
    from .clone_performance import VERSION
    p = profile(voice)
    variant = read_json(BASE / 'runtime.json', {}).get('variant', 'multilingual-v3')
    return digest('cloned-voice-v4', VERSION, p['hash'], p['motor'], 'original-reference',
                  p['expressividade'], p.get('fidelidade', 0.), p.get('variacao', .8),
                  p.get('interpretacao', 'natural'), variant)


def configure(voice, expression, fidelity, variation, interpretation=None):
    from .clone_performance import MODES
    if not .25 <= expression <= 1 or not 0 <= fidelity <= .8 or not .4 <= variation <= 1:
        raise ValueError('Os ajustes de voz estão fora dos limites.')
    if interpretation is not None and interpretation not in MODES:
        raise ValueError('Escolha uma interpretação de voz válida.')
    with LOCK:
        value = profile(voice)
        value.update(expressividade=expression, fidelidade=fidelity, variacao=variation)
        if interpretation is not None:
            value['interpretacao'] = interpretation
        write_json(STORE / voice / 'profile.json', value)
        return {'ok': True, 'id': voice}


def upgrade_profiles():
    """Restore the initial synthesis once; retain future user adjustments."""
    from .voice_reference import prepare, VERSION
    with LOCK:
        for value in listing():
            if value['motor'] == 'chatterbox' and value.get('perfil_sintese') == 'original-v1':
                continue
            folder = STORE / value['id']
            if not (folder / 'profile-original.json').exists():
                write_json(folder / 'profile-original.json', value)
            if not (folder / 'profile-before-original.json').exists():
                write_json(folder / 'profile-before-original.json', value)
            value.update(motor='chatterbox', expressividade=.5, fidelidade=0., variacao=.8,
                         perfil_sintese='original-v1')
            try:
                if value.get('preparo', {}).get('versao') != VERSION:
                    value['preparo'] = prepare(folder / 'reference.wav', folder / 'reference-prepared.wav')
                value.pop('preparo_erro', None)
            except (ValueError, OSError, RuntimeError) as exc:
                value['preparo_erro'] = str(exc)
            write_json(folder / 'profile.json', value)


def _owned_directory(base, name):
    base = Path(base)
    target = base / name
    if not base.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('A pasta da voz está fora desta instalação.')
    if base.is_symlink() or base.is_junction() or target.is_symlink() or target.is_junction():
        raise ValueError('A pasta da voz não pode ser um atalho.')
    if target.resolve().parent != base.resolve():
        raise ValueError('A pasta da voz está fora do local esperado.')
    # Check all descendants before any recursive deletion, including junctions
    # that Windows would otherwise follow outside the voice's own directory.
    pending = [target] if target.is_dir() else []
    while pending:
        for item in pending.pop().iterdir():
            if item.is_symlink() or item.is_junction() or not item.resolve().is_relative_to(target.resolve()):
                raise ValueError('A pasta da voz contém um atalho. Nenhum arquivo foi apagado.')
            if item.is_dir():
                pending.append(item)
    return target


def remove_previews(voice):
    """Discard preview audio and its synthesis cache, keeping the voice intact."""
    with LOCK:
        value = profile(voice)
        if value.get('id') != voice:
            raise ValueError('A identificação da voz salva é inconsistente.')
        folder = _owned_directory(ROOT / 'output/amostras/clonadas', voice)
        try:
            if folder.is_dir():
                shutil.rmtree(folder)
        except OSError as exc:
            raise ValueError('Não foi possível apagar a prévia. Feche o áudio aberto e tente novamente.') from exc
        return {'ok': True, 'id': voice}


def remove(voice):
    with LOCK:
        if not re.fullmatch(r'clone_[0-9a-f]{12}', voice):
            raise ValueError('Identificador de voz inválido.')
        folder = _owned_directory(STORE, voice)
        value = profile(voice)
        if value.get('id') != voice:
            raise ValueError('A identificação da voz salva é inconsistente.')
        previews = _owned_directory(ROOT / 'output/amostras/clonadas', voice)
        from .voices import DELIVERIES
        samples = [ROOT / 'output/amostras' / (voice + ('-' + style if style != 'natural' else '') + '.wav')
                   for style in DELIVERIES]
        for sample in samples:
            if sample.is_symlink() or sample.is_junction() or sample.resolve().parent != (ROOT / 'output/amostras').resolve():
                raise ValueError('A amostra da voz está fora do local esperado.')
        release()
        try:
            if previews.is_dir():
                shutil.rmtree(previews)
            for sample in samples:
                sample.unlink(missing_ok=True)
            shutil.rmtree(folder)
        except OSError as exc:
            # A locked file must not make a partially deleted profile disappear
            # from the list: retain its marker so removal can be retried.
            if folder.is_dir() and not (folder / 'profile.json').exists():
                write_json(folder / 'profile.json', value)
            raise ValueError('Não foi possível apagar todos os arquivos da voz. Feche as amostras abertas e tente novamente.') from exc
        return {'ok': True, 'id': voice}


def save(name, engine, transcript, expression, audio, fidelity=0., variation=.8, interpretation='natural'):
    from .clone_performance import MODES
    if not name.strip() or len(name.strip()) > 80:
        raise ValueError('Dê à voz um nome de até 80 caracteres.')
    if engine not in ENGINES or not any(e['id'] == engine and e['instalado'] for e in engines()):
        raise ValueError('O motor escolhido ainda não está instalado.')
    if len(transcript) > 2000:
        raise ValueError('A transcrição deve ter até 2000 caracteres.')
    if not .25 <= expression <= 1:
        raise ValueError('Expressividade inválida.')
    if not 0 <= fidelity <= .8 or not .4 <= variation <= 1:
        raise ValueError('Os ajustes de fidelidade ou variação estão fora dos limites.')
    if interpretation not in MODES:
        raise ValueError('Escolha uma interpretação de voz válida.')
    if not audio or len(audio) > MAX_BYTES:
        raise ValueError('Envie uma amostra de até 30 MB.')
    voice = 'clone_' + uuid.uuid4().hex[:12]
    folder = STORE / voice
    folder.mkdir(parents=True)
    source, reference = folder / 'upload.audio', folder / 'reference.wav'
    try:
        source.write_bytes(audio)
        # Bounded decode accepts browser recordings too; reject clips over 60s.
        run([binary('ffmpeg'), '-v', 'error', '-y', '-nostdin',
             '-protocol_whitelist', 'file,pipe',
             '-format_whitelist', 'wav,mp3,flac,ogg,mov,matroska,webm,aac', '-i', source, '-t', '61',
             '-vn', '-ar', '24000', '-ac', '1', reference], timeout=60)
        info = sf.info(reference)
        if not 5 <= info.duration <= 60:
            raise ValueError('Use uma gravação entre 5 e 60 segundos, com voz limpa e sem música.')
        import numpy as np
        data, _ = sf.read(reference, dtype='float32')
        if not np.isfinite(data).all() or np.max(np.abs(data)) < .005:
            raise ValueError('A amostra está vazia ou muito baixa. Grave novamente.')
        value = {'id': voice, 'nome': name.strip(), 'motor': engine,
                 'transcricao': transcript.strip(), 'expressividade': expression,
                 'fidelidade': fidelity, 'variacao': variation, 'perfil_sintese': 'original-v1',
                 'interpretacao': interpretation,
                 'duracao': info.duration, 'criado': time.time(),
                 'hash': hashlib.sha256(reference.read_bytes()).hexdigest()}
        from .voice_reference import prepare
        value['preparo'] = prepare(reference, folder / 'reference-prepared.wav')
        write_json(folder / 'profile.json', value)
        return value
    finally:
        source.unlink(missing_ok=True)
        if not (folder / 'profile.json').is_file():
            reference.unlink(missing_ok=True)
            (folder / 'reference-prepared.wav').unlink(missing_ok=True)
            folder.rmdir()


class Worker:
    def __init__(self, engine):
        self.engine = engine
        log = ROOT / 'logs/voice-cloning.log'
        log.parent.mkdir(exist_ok=True)
        self.log = log.open('a', encoding='utf-8')
        self.results = queue.Queue()
        environment = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1'}
        # No dependency on VoiceStudio, its service, or its environment variables.
        environment.pop('PYTHONPATH', None)
        self.process = subprocess.Popen(
            [str(python_path(engine)), str(ROOT / 'tools/voice_cloning_worker.py'), '--engine', engine],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
            encoding='utf-8', errors='replace', bufsize=1, cwd=ROOT, env=environment,
            creationflags=CREATE_FLAGS)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    value = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(value, dict) and 'ok' in value:
                    self.results.put(value)
        finally:
            self.results.put({'ok': False, 'error': 'O motor de voz foi encerrado. Veja logs/voice-cloning.log.'})

    def request(self, body):
        self.process.stdin.write(json.dumps(body, ensure_ascii=False) + '\n')
        self.process.stdin.flush()
        try:
            result = self.results.get(timeout=600)
        except queue.Empty:
            self.close()
            raise RuntimeError('A voz demorou mais que o esperado. Teste um trecho menor.')
        if not result['ok']:
            raise RuntimeError('Não foi possível gerar com esta voz: ' + result.get('error', '')[:500])
        return result

    def close(self):
        if self.process.poll() is None:
            # Windows venv launchers can have a child interpreter. EOF lets
            # both exit normally; terminate the owned tree if GPU teardown hangs.
            import psutil
            try:
                descendants = psutil.Process(self.process.pid).children(recursive=True)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                descendants = []
            try:
                self.process.stdin.close()
            except (OSError, ValueError):
                pass
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                for child in reversed(descendants):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                self.process.kill()
                self.process.wait(timeout=5)
        self.log.close()


def release():
    global _worker
    with LOCK:
        if _worker:
            try:
                _worker.close()
            finally:
                _worker = None


def synthesize(text, voice, cache, delivery='natural', *, seed=42):
    from .clone_performance import direction
    global _worker
    p = profile(voice)
    if p.get('preparo_erro'):
        raise ValueError('A gravação precisa ser refeita: ' + p['preparo_erro'])
    if not python_path(p['motor']).is_file():
        raise RuntimeError('O motor desta voz não está instalado.')
    performance = direction(p, text, delivery)
    target = Path(cache) / (digest(text, identity(voice), performance) + '.wav')
    if seed != 42:
        target = target.with_name(digest(text, identity(voice), performance, seed)+'.wav')
    with LOCK:
        if not target.is_file():
            if _worker and (_worker.engine != p['motor'] or _worker.process.poll() is not None):
                release()
            if not _worker:
                _worker = Worker(p['motor'])
            try:
                # Match the first Chatterbox version: the full original recording
                # supplies speaker identity; the model selects its own prompts.
                reference = STORE / voice / 'reference.wav'
                _worker.request({'text': text, 'reference': str(reference),
                                 'transcript': p['transcricao'], 'seed': seed, **performance,
                                 'output': str(target.resolve())})
            except Exception:
                release()
                raise
    return target
