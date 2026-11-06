from __future__ import annotations

import json
from pathlib import Path
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, SecretStr,Field
from typing import Literal

from .core import PROJECTS, ROOT, Scene, Settings, StageAI, JobLock, worker_active, project_dir, read_json, set_status, write_json, digest
from . import projects
from .metrics import Metrics
from .render import render_project

@asynccontextmanager
async def lifespan(app):
    from .cloned_voices import upgrade_profiles
    upgrade_profiles()
    scheduler().start()
    try:
        yield
    finally:
        if SCHEDULER is not None:SCHEDULER.stop()
        from .cloned_voices import release
        release()


app=FastAPI(title="Clareia · Estúdio local",lifespan=lifespan)
app.mount("/static",StaticFiles(directory=ROOT/"overview/static"),name="static")
app.mount('/3d',StaticFiles(directory=ROOT/'overview/three_gallery/out',html=True,check_dir=False),name='three-gallery')
ACTIVE=threading.Lock()
SCHEDULER=None
SCHEDULER_INIT=threading.Lock()
from .cloned_voice_api import make_router as voice_router
app.include_router(voice_router(ACTIVE))


def execute_task(path,kind,lease):
    if kind.startswith('scene_preview:'):
        from .scene_preview import run
        with JobLock(path,processing_lock=lease):run(path,kind.split(':',1)[1],render_project)
        return
    if kind=='render_youtube':
        from .publication import run_scheduled
        settings=Settings.model_validate(read_json(path/'project.json')['config'])
        def render_scheduled_video():
            with Metrics(path/f'metrics-{int(time.time())}.json'):render_project(path,settings)
        with JobLock(path,processing_lock=lease):run_scheduled(path,render_scheduled_video)
        return
    if kind=='youtube':
        from .youtube_upload import upload
        with JobLock(path,processing_lock=lease):upload(path)
        return
    with JobLock(path,processing_lock=lease), Metrics(path/f"metrics-{int(time.time())}.json"):
        if kind in ('render','preview'):
            settings=Settings.model_validate(read_json(path/'project.json')['config'])
            render_project(path,settings)
            if kind=='render' and read_json(path/'status.json',{}).get('status')=='concluido':
                # Metadata failure must never turn a successfully rendered video into an error.
                try:
                    from .youtube import metadata
                    metadata(path,use_ai=not settings.roteiro_pronto)
                except Exception:
                    import logging
                    logging.exception('Não foi possível preparar os textos do YouTube')
        elif kind.startswith('cena:'):projects.generate(path,int(kind.split(':',1)[1]))
        else:projects.generate(path)


def scheduler():
    global SCHEDULER
    with SCHEDULER_INIT:
        if SCHEDULER is None:
            from .scheduler import Scheduler
            SCHEDULER=Scheduler(ROOT/'.private/queue.sqlite3',ACTIVE,execute_task)
            SCHEDULER.start()
    return SCHEDULER


@app.exception_handler(FileNotFoundError)
async def missing(request,exc):
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail":"Projeto ou arquivo não encontrado"},status_code=404)


@app.exception_handler(ValueError)
async def invalid(request,exc):
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail":str(exc)},status_code=400)


@app.middleware("http")
async def local_only(request:Request,call_next):
    # Rejeita DNS rebinding e chamadas de escrita feitas por sites externos.
    host=request.headers.get("host","").split(":")[0]
    if host not in ("127.0.0.1","localhost","testserver"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail":"Acesso somente por localhost"},status_code=403)
    if request.method in ("POST","PUT","DELETE"):
        origin=request.headers.get("origin")
        if origin and origin not in (f"http://{request.headers.get('host')}",f"https://{request.headers.get('host')}"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail":"Origem externa recusada"},status_code=403)
    response=await call_next(request)
    if request.url.path=='/api/youtube/oauth/callback':
        # Do not put Google's authorization code/state in Uvicorn access logs.
        request.scope['query_string']=b''
    return response


def launch(path,fn,kind='roteiro'):
    # Resolve kind from saved project data when it runs, including after a restart.
    try:return scheduler().submit(path,kind)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc


def editable(path):
    status=read_json(path/"status.json",{}).get("status")
    if SCHEDULER is not None and SCHEDULER.pending(path):
        raise HTTPException(409,'Cancele a espera na fila ou aguarde a tarefa antes de editar ou excluir.')
    if status in ("fila","roteirizando","renderizando","importando") and (ACTIVE.locked() or worker_active(path)):
        raise HTTPException(409,"Aguarde a tarefa atual antes de editar")


@app.get("/")
def index():
    return FileResponse(ROOT/"overview/static/index.html")


@app.get("/api/health")
def health():
    from .core import MODEL
    from .youtube_music import active_job
    from .youtube_clips import jobs as clip_jobs
    importing=active_job() is not None;clips=clip_jobs.active() is not None
    return {"ok":True,"local":True,"modelo":MODEL,"ocupado":ACTIVE.locked() or importing or clips,'musica_importando':importing,'clipe_importando':clips,'musica_youtube':True,'clipes_youtube':True,"fila_agendamentos":True,"youtube_upload":True,"agendamento_publica":True,'revisao_imagens':True,'cena_previa':True,'lixeira_esvaziar':True,'concluidos_miniaturas':True,'clonagem_voz':True}


@app.get('/api/queue')
def queue_status():
    return scheduler().snapshot()


@app.get('/api/dictation')
def dictation_status():
    from .dictation import status
    return status()


@app.post('/api/dictation/transcribe')
async def dictation_transcribe(audio:UploadFile=File(...)):
    from .dictation import MAX_BYTES, BusyError, NotReadyError, transcribe
    from starlette.concurrency import run_in_threadpool
    try:
        data=bytearray()
        while chunk:=await audio.read(1024*1024):
            data.extend(chunk)
            if len(data)>MAX_BYTES:
                raise HTTPException(413,'A gravação é muito grande. Grave um trecho menor.')
        return await run_in_threadpool(transcribe,bytes(data),audio.content_type or '')
    except BusyError as exc:
        raise HTTPException(409,str(exc)) from exc
    except NotReadyError as exc:
        raise HTTPException(503,str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logging.exception('Falha no ditado local')
        raise HTTPException(500,'Não foi possível transcrever agora. Tente gravar novamente.') from exc
    finally:
        await audio.close()


@app.delete('/api/queue/{job_id}')
def queue_cancel(job_id:int):
    scheduler().cancel(job_id)
    return {'ok':True}


@app.get('/api/notifications')
def notifications():
    return scheduler().notifications()


class ReadNotifications(BaseModel):
    ate:int=Field(ge=0)


@app.post('/api/notifications/read')
def notifications_read(body:ReadNotifications):
    scheduler().mark_read(body.ate)
    return {'ok':True}


class Credential(BaseModel):
    provedor: Literal['gemini','openrouter','groq']
    chave: SecretStr
    persistir: bool = False


@app.get('/api/roteiro/credenciais')
def credentials():
    from .providers import key_status
    return key_status()


@app.post('/api/roteiro/credenciais')
def credentials_save(body:Credential):
    if ACTIVE.locked():raise HTTPException(409,'Aguarde a tarefa atual antes de mudar as chaves.')
    from .providers import save_key, key_status
    save_key(body.provedor,body.chave.get_secret_value(),body.persistir)
    return key_status()


@app.delete('/api/roteiro/credenciais/{provider}')
def credentials_remove(provider:str):
    if ACTIVE.locked():raise HTTPException(409,'Aguarde a tarefa atual antes de mudar as chaves.')
    from .providers import remove_key, key_status
    remove_key(provider)
    return key_status()


@app.get('/api/roteiro/modelos/{provider}')
def models(provider:str):
    from .providers import catalog
    return {'modelos':catalog(provider)}


class GeminiProbe(BaseModel):
    modelo:str=Field(min_length=1,max_length=160,pattern=r'^[a-zA-Z0-9_.+-]+$')


@app.post('/api/roteiro/gemini/testar')
def test_gemini_model(body:GeminiProbe):
    if ACTIVE.locked():raise HTTPException(409,'Aguarde a tarefa atual antes de testar outra chamada do Gemini.')
    from .providers import probe_gemini
    return probe_gemini(body.modelo)


@app.get('/api/gemini/voz/modelos')
def gemini_voice_models():
    from .gemini_audio import available_models
    return {'modelos':available_models()}


@app.post('/api/gemini/voz/preview')
def gemini_voice_preview(settings:Settings):
    from .runtime import gemini_only
    from .speech import TTS_LOCK,synthesize_settings,release
    if not gemini_only(settings):raise ValueError('Ative o processamento completo com Gemini para testar a voz da API.')
    if ACTIVE.locked() or not TTS_LOCK.acquire(blocking=False):raise HTTPException(409,'Aguarde a voz em processamento para testar outra amostra.')
    try:
        wav,_=synthesize_settings('Uma boa explicação começa com uma pergunta. Vamos aprender passo a passo, com uma narração clara em português brasileiro.',settings,ROOT/'output/amostras/gemini')
        return {'url':'/api/gemini/voz/amostras/'+wav.stem}
    finally:release();TTS_LOCK.release()


@app.get('/api/gemini/voz/amostras/{key}')
def gemini_voice_sample(key:str):
    import re
    if not re.fullmatch('[a-f0-9]{24}',key):raise FileNotFoundError()
    path=ROOT/'output/amostras/gemini'/(key+'.wav')
    if not path.is_file():raise FileNotFoundError()
    return FileResponse(path,media_type='audio/wav')


@app.get("/api/projects")
def listing():
    items=[]
    pending={j['project']:j for j in SCHEDULER.snapshot()['tarefas']} if SCHEDULER is not None else {}
    if PROJECTS.exists():
        for path in PROJECTS.iterdir():
            info=read_json(path/"project.json")
            if info:
                state=read_json(path/'status.json',{});job=pending.get(path.name)
                draft=(path/'schedule-draft.json').is_file()
                scheduled=draft or bool(job and (job['scheduled'] is not None or job['kind']=='render_youtube'))
                running=bool(job and job['status']=='executando') or worker_active(path)
                complete=state.get('status') in ('concluido','enviado_youtube') and not job and not running
                progress=max(0,min(1,float(state.get('progresso') or 0)))
                if job and job['kind']=='render_youtube':
                    checkpoint=read_json(path/'scheduled-publication.json',{});stage=checkpoint.get('stage','render')
                    if stage=='script':progress=.15*progress
                    elif stage=='render':progress=.15+.70*progress if checkpoint.get('gerou_roteiro') else .85*progress
                    elif stage=='metadata':progress=.88
                    elif stage=='upload':progress=.9+.09*progress
                    else:progress=1
                items.append({**info,'status':state,'grupo':'agendamentos' if scheduled else 'concluidos' if complete else 'ativos',
                              'em_execucao':running,'progresso_total':progress,'tarefa_fila':job,
                              'agendamento':read_json(path/'agendamento.json',{}),'agendamento_em_edicao':draft})
    from .completed import details,history
    finished=[item for item in items if item['grupo']=='concluidos']
    records=history(SCHEDULER.database if SCHEDULER else ROOT/'.private/queue.sqlite3',[PROJECTS/item['id'] for item in finished])
    for item in finished:
        path=PROJECTS/item['id']
        item['conclusao']=details(path,item,records.get(str(path.resolve()),[]))
    return sorted(items,key=lambda x:x["criado"],reverse=True)


@app.get('/api/options')
def options():
    from .voices import catalog,DELIVERIES
    from .animation_styles import STYLES
    from .transitions import TRANSITIONS
    from .gemini_audio import VOICES,TTS_MODELS
    from .narration_styles import TONES,VOICE_PRESETS
    from .shotcraft import catalog as shotcraft_catalog
    from .video_palettes import catalog as palette_catalog
    voices=catalog();available={v['id'] for v in voices if v['instalada']}
    return {'vozes':voices,'locucoes':[{'id':k,**v} for k,v in DELIVERIES.items()],'tons':TONES,
            'vozes_motivacionais':[p for p in VOICE_PRESETS if p['voz'] in available],
            'animacoes':STYLES,'transicoes':[{'id':k,'nome':n,'descricao':d} for k,n,d in TRANSITIONS],
            'gemini_vozes':VOICES,'gemini_modelos_voz':TTS_MODELS,'shotcraft':shotcraft_catalog(),'paletas_video':palette_catalog()}


@app.get('/api/shotcraft/recipes/{recipe}/preview')
def shotcraft_recipe_preview(recipe:str,estilo:str='editorial',intensidade:str='equilibrada',vertical:bool=False,modelo:str='auto',acabamento:str='vidro_avancado'):
    from .shotcraft_previews import prepare
    cfg=Settings(shotcraft_estilo=estilo,shotcraft_intensidade=intensidade,shotcraft_modelo=modelo,shotcraft_acabamento=acabamento)
    return FileResponse(prepare(recipe,cfg.shotcraft_estilo,cfg.shotcraft_intensidade,vertical,cfg.shotcraft_modelo,cfg.shotcraft_acabamento),media_type='image/webp')


@app.get('/api/projects/{pid}/shotcraft')
def shotcraft_direction_report(pid:str):
    from .shotcraft import report
    return report(project_dir(pid))


@app.get('/api/shotcraft/recipes/{recipe}/poster')
def shotcraft_recipe_poster(recipe:str,estilo:str='editorial',vertical:bool=False,acabamento:str='vidro_avancado'):
    from .shotcraft_previews import poster
    return FileResponse(poster(recipe,estilo,vertical,acabamento),media_type='image/png')


@app.get('/api/shotcraft/figures/{figure}/preview')
def shotcraft_figure_preview(figure:str):
    from .shotcraft_figures import path_for
    return FileResponse(path_for(figure),media_type='image/svg+xml',headers={'Cache-Control':'public, max-age=86400'})


@app.get('/api/collage/figures')
def collage_figures():
    from .collage_assets import catalog
    from .collage_motion import motion_info
    return [{**{k:v for k,v in r.items() if k in ('id','name','category','tags')},'movimento':motion_info(r['id'])} for r in catalog()]


@app.get('/api/music')
def music_catalog():
    from .music import public_catalog
    return public_catalog()


@app.get('/api/music/youtube/search')
def search_youtube_music(q:str=''):
    from .youtube_music import search
    return search(q)


class YouTubeMusicImport(BaseModel):
    resultado: str = Field(pattern=r'^[a-f0-9]{24}$')
    creditos: str = Field(default='',max_length=2000)


@app.post('/api/music/youtube/imports')
def start_youtube_music_import(body:YouTubeMusicImport):
    from .youtube_music import start
    return start(body.resultado,body.creditos)


@app.get('/api/music/youtube/imports/active')
def active_youtube_music_import():
    from .youtube_music import active_job
    return {'importacao':active_job()}


@app.get('/api/music/youtube/imports/{job_id}')
def youtube_music_import_status(job_id:str):
    from .youtube_music import get_job
    return get_job(job_id)


@app.post('/api/music/youtube/imports/{job_id}/cancel')
def cancel_youtube_music_import(job_id:str):
    from .youtube_music import cancel
    return cancel(job_id)


@app.get('/api/youtube-clips/search')
def search_youtube_clips(q:str=''):
    from .youtube_clips import search
    return search(q)


@app.get('/api/youtube-clips/library')
def youtube_clip_library():
    from .youtube_clips import catalog
    return catalog()


class YouTubeClipImport(BaseModel):
    resultado: str = Field(pattern=r'^[a-f0-9]{24}$')
    qualidade: Literal[720,1080] = 720


@app.post('/api/youtube-clips/imports')
def start_youtube_clip_import(body:YouTubeClipImport):
    from .youtube_clips import start
    return start(body.resultado,body.qualidade)


@app.get('/api/youtube-clips/imports/active')
def active_youtube_clip_import():
    from .youtube_clips import jobs
    return {'importacao':jobs.active()}


@app.get('/api/youtube-clips/imports/{job_id}')
def youtube_clip_import_status(job_id:str):
    from .youtube_clips import jobs
    return jobs.get(job_id)


@app.post('/api/youtube-clips/imports/{job_id}/cancel')
def cancel_youtube_clip_import(job_id:str):
    from .youtube_clips import jobs
    return jobs.cancel(job_id)


@app.get('/api/youtube-clips/library/{key}/poster')
def youtube_clip_poster(key:str):
    from .youtube_clips import clip,STORE
    clip(key)
    return FileResponse(STORE/'library'/(key+'.jpg'),media_type='image/jpeg')


@app.get('/api/youtube-clips/library/{key}/video')
def youtube_clip_video(key:str):
    from .youtube_clips import clip,STORE
    clip(key)
    return FileResponse(STORE/'library'/(key+'.mp4'),media_type='video/mp4')


class AttachYouTubeClips(BaseModel):
    clipes:list[str] = Field(min_length=1,max_length=12)


@app.post('/api/projects/{pid}/reels/youtube-clips')
def attach_youtube_clips(pid:str,body:AttachYouTubeClips):
    from .youtube_clips import attach
    path=project_dir(pid);editable(path)
    return attach(path,body.clipes,lambda:editable(path))


@app.get('/api/music/tracks/{track_id}')
def music_audio(track_id:str):
    from .music import ensure_track
    return FileResponse(ensure_track(track_id),media_type='audio/wav' if track_id.startswith('user-') else 'audio/mpeg')


@app.post('/api/music/import')
async def music_import(file:UploadFile=File(...),titulo:str=Form(''),creditos:str=Form('')):
    from .music import LIBRARY,MAX_BYTES,import_track
    from starlette.concurrency import run_in_threadpool
    import uuid
    if len(titulo)>100 or len(creditos)>2000:raise ValueError('Título ou créditos da faixa muito longos.')
    if Path(file.filename or '').suffix.lower() not in ('.mp3','.wav','.flac','.ogg','.m4a','.aac'):
        raise ValueError('Use MP3, WAV, FLAC, OGG ou M4A.')
    staging=LIBRARY/'incoming';staging.mkdir(parents=True,exist_ok=True)
    target=staging/(uuid.uuid4().hex+Path(file.filename).suffix.lower())
    try:
        total=0
        with target.open('wb') as out:
            while chunk:=await file.read(256*1024):
                total+=len(chunk)
                if total>MAX_BYTES:raise ValueError('Música maior que 120 MB.')
                out.write(chunk)
        return await run_in_threadpool(import_track,target,titulo.strip() or Path(file.filename).stem,creditos)
    finally:target.unlink(missing_ok=True)


@app.post('/api/music/preview')
def music_preview(settings:Settings):
    from .music import LIBRARY,fingerprint,mix_audio,VERSION
    from .speech import TTS_LOCK,synthesize_settings,release
    from .core import binary,run
    if not settings.musica_fundo:raise ValueError('Escolha uma música para testar com a voz.')
    folder=LIBRARY/'previews';folder.mkdir(parents=True,exist_ok=True)
    key=digest(VERSION,fingerprint(settings.musica_fundo),settings.musica_fundo,settings.volume_musica_db,settings.reduzir_musica_na_fala,settings.voz,settings.velocidade,settings.estilo_locucao)
    from .runtime import gemini_only
    if gemini_only(settings):
        from .gemini_audio import identity
        key=digest(key,*identity(settings))
    target=folder/(key+'.wav')
    if not target.is_file():
        if ACTIVE.locked() or not TTS_LOCK.acquire(blocking=False):raise HTTPException(409,'Aguarde a voz em processamento para testar a música.')
        try:
            wav,_=synthesize_settings('Uma boa explicação começa com uma pergunta. A música acompanha o vídeo com suavidade, enquanto a narração continua clara. Vamos aprender, passo a passo.',settings,folder/'voice-cache')
            voice=folder/(key+'-voice.wav')
            run([binary('ffmpeg'),'-y','-v','error','-i',wav,'-ar',48000,'-ac',2,'-c:a','pcm_f32le',voice],timeout=60)
            partial=folder/(key+'.partial.wav')
            try:
                report=mix_audio(voice,settings,partial)
                partial.replace(target)
                write_json(folder/(key+'.json'),report)
            finally:partial.unlink(missing_ok=True);voice.unlink(missing_ok=True)
        finally:release();TTS_LOCK.release()
    return {'url':'/api/music/previews/'+key,'id':key}


@app.get('/api/music/previews/{key}')
def music_preview_audio(key:str):
    from .music import LIBRARY
    import re
    if not re.fullmatch('[a-f0-9]{24}',key):raise FileNotFoundError()
    path=LIBRARY/'previews'/(key+'.wav')
    if not path.is_file():raise FileNotFoundError()
    return FileResponse(path,media_type='audio/wav')


@app.get('/api/collage/figures/{figure}')
def collage_figure(figure:str):
    from .collage_assets import catalog,ASSETS
    record=next((r for r in catalog() if r['id']==figure),None)
    if not record:raise FileNotFoundError()
    return FileResponse(ASSETS/record['file'],media_type='image/png')


@app.post('/api/animation-previews')
def create_animation_preview(settings:Settings,projeto:str|None=None):
    from .preview import prepare
    key,path,cfg=prepare(settings,source_path=project_dir(projeto) if projeto else None)
    if not (path/'export/video.mp4').is_file():
        if worker_active(path) or (SCHEDULER and SCHEDULER.pending(path)):return {'id':key}
        launch(path,lambda:render_project(path,cfg),kind='preview')
    return {'id':key}


@app.get('/api/transitions/{style}/preview')
def transition_preview(style):
    from .transitions import preview
    return FileResponse(preview(style,ROOT),media_type='image/gif')


@app.get('/api/animation-previews/{key}')
def animation_preview_status(key):
    from .preview import preview_path
    path=preview_path(key)
    state=read_json(path/'status.json',{})
    ready=(path/'export/video.mp4').is_file()
    if not ready and state.get('status') in ('fila','renderizando') and not ACTIVE.locked() and not worker_active(path) and not (SCHEDULER and SCHEDULER.pending(path)):
        state={'status':'pausado','mensagem':'A preparação foi interrompida. Clique em Testar com esta voz para retomar.'}
    return {'id':key,'status':'concluido' if ready else state.get('status','fila'),'mensagem':state.get('mensagem','Preparando prévia'),
            'url':f'/api/animation-previews/{key}/video' if ready else None}


@app.get('/api/animation-previews/{key}/video')
def animation_preview_video(key):
    from .preview import preview_path
    target=preview_path(key)/'export/video.mp4'
    if not target.is_file():raise FileNotFoundError()
    return FileResponse(target,media_type='video/mp4')


@app.get('/api/trash')
def trash_listing():
    from .project_trash import listing
    return listing(PROJECTS)


class EmptyTrash(BaseModel):
    projetos:list[str]=Field(min_length=1,max_length=10000)


@app.delete('/api/trash')
def empty_trash(body:EmptyTrash):
    from .project_trash import empty
    return empty(PROJECTS,body.projetos)


@app.delete('/api/projects/{pid}')
def remove_project(pid):
    path=project_dir(pid);editable(path);projects.trash(path)
    return {'ok':True,'recuperavel':True}


@app.post('/api/trash/{pid}/restore')
def restore_project(pid):
    path=projects.restore(pid)
    return read_json(path/'project.json')


@app.get('/api/favorites')
def favorite_listing():
    from .favorites import listing
    return listing()


class FavoriteName(BaseModel):
    nome:str=Field(default='',max_length=150)


@app.post('/api/projects/{pid}/favorite')
def favorite_project(pid,body:FavoriteName|None=None):
    from .favorites import save
    path=project_dir(pid);editable(path)
    return save(path,body.nome if body else '')


@app.get('/api/favorites/{key}')
def favorite_detail(key):
    from .favorites import get
    return get(key)


@app.put('/api/favorites/{key}')
def favorite_rename(key,body:FavoriteName):
    from .favorites import rename
    rename(key,body.nome)
    return {'ok':True}


@app.delete('/api/favorites/{key}')
def favorite_remove(key):
    from .favorites import remove
    remove(key)
    return {'ok':True}


def cleanup_stale_uploads():
    if PROJECTS.exists():
        import shutil
        for folder in PROJECTS.glob("upload-*"):
            if folder.is_dir():
                shutil.rmtree(folder, ignore_errors=True)


cleanup_stale_uploads()


class AISource(BaseModel):
    assunto:str=Field(min_length=1,max_length=2000)
    config:Settings=Field(default_factory=Settings)


@app.post('/api/sources/ai')
def create_ai_source(body:AISource):
    from . import source_ai
    topic=body.assunto.strip()
    if not topic:raise ValueError('Informe o assunto antes de criar uma fonte com IA.')
    key,_,_=source_ai.identity(topic,body.config)
    queue=scheduler();lease=queue.lock_factory()
    with queue.mutex:
        if not ACTIVE.acquire(blocking=False):raise HTTPException(409,'Aguarde o processamento atual terminar antes de criar uma fonte com IA.')
    try:
        if not lease.acquire():raise HTTPException(409,'Há outro processamento em andamento. Aguarde antes de criar a fonte.')
        path=source_ai.STORE/key;path.mkdir(parents=True,exist_ok=True)
        with JobLock(path,processing_lock=lease):
            def update(message,progress):set_status(path,'roteirizando',message,progress)
            result=source_ai.generate(path,topic,body.config,update)
            set_status(path,'revisao','Fonte criada com IA. Revise o material antes de usar no roteiro.',1)
            return {'texto':result['texto'],'provedor':result['provedor'],'modelo':result['modelo'],'secoes':len(result['secoes'])}
    finally:lease.release();ACTIVE.release()


@app.post("/api/projects")
async def create(titulo:str=Form(""),config:str=Form("{}"),texto:str=Form(""),urls:str=Form(""),files:list[UploadFile]=File(default=[]),assunto:str=Form('',max_length=2000),favorito:str=Form(''),modelo_local:str=Form('',max_length=120),clipes_youtube:str=Form('[]')):
    upload=None
    try:
        cleanup_stale_uploads()
        favorite=None
        if favorito:
            from .favorites import get,settings_for
            favorite=get(favorito);raw=json.loads(config)
            settings=settings_for(favorite,raw.get('minutos',3),assunto.strip(),overrides=raw)
        else:settings=Settings.model_validate_json(config)
        clips=json.loads(clipes_youtube)
        if not isinstance(clips,list) or len(clips)>12:raise ValueError('Escolha até 12 clipes da biblioteca.')
        if clips:
            from .youtube_clips import clip
            if settings.tipo_video!='shorts' or settings.modo_shorts!='clipes':raise ValueError('Para usar clipes, escolha Reels / Shorts e Fotos e clipes com narração.')
            for key in clips:clip(key)
        if modelo_local:
            from .llm import installed_models
            if modelo_local not in {m['name'] for m in installed_models()}:
                raise ValueError('Escolha um modelo local instalado no Ollama.')
            settings=settings.model_copy(update={'roteiro_provedor':'local','roteiro_modelo':modelo_local})
        elif favorito and settings.roteiro_provedor=='local' and raw.get('roteiro_modelo'):
            from .llm import installed_models
            if settings.roteiro_modelo not in {m['name'] for m in installed_models()}:
                raise ValueError('Escolha um modelo local instalado no Ollama.')
        if settings.fonte_ia_automatica and assunto.strip() and not texto.strip() and not urls.strip() and not files:
            from .source_ai import settings_for
            settings_for(settings)
        import uuid
        upload=PROJECTS/("upload-"+str(uuid.uuid4()))
        upload.mkdir(parents=True)
        saved=[]
        for i,file in enumerate(files):
            name=Path(file.filename or "fonte.txt").name
            target=upload/f"{i+1}-{name}"
            size=0
            with open(target,"wb") as out:
                while chunk:=await file.read(1024*1024):
                    size+=len(chunk)
                    if size>200_000_000:
                        raise ValueError("Fonte maior que 200 MB")
                    out.write(chunk)
            saved.append(target)
        path=projects.create(titulo,settings,saved,texto,urls.splitlines(),topic=assunto,favorite=favorite)
        if clips:
            from .youtube_clips import attach
            attach(path,clips)
        import shutil
        shutil.move(str(upload),str(path/"originais"))
        upload=None
        return read_json(path/"project.json")
    except Exception as exc:
        raise HTTPException(400,str(exc)) from exc
    finally:
        if upload and upload.exists():
            import shutil
            shutil.rmtree(upload,ignore_errors=True)


@app.get("/api/projects/{pid}")
def get_project(pid):
    path=project_dir(pid)
    status=read_json(path/"status.json",{})
    if status.get("status") in ("renderizando","roteirizando","fila") and not ACTIVE.locked() and not worker_active(path) and not (SCHEDULER and SCHEDULER.pending(path)):
        set_status(path,"pausado","Processo anterior interrompido. Retome para aproveitar o cache.")
        status=read_json(path/"status.json")
    sources=read_json(path/"sources.json",{})
    research=read_json(path/'pesquisa.json')
    if research:
        from .research import public_report
        research=public_report(research)
        research['desatualizada']=research.get('roteiro_hash')!=digest([s['narracao_ptbr'] for s in read_json(path/'script.json',[])])
    extra_sources=[{'id':s['id'],'origem':s['url'],'caracteres':s.get('caracteres',0),'externa':True} for s in (research or {}).get('fontes',[])]
    from .speech import phrases
    from .scene_diagnostics import issues as scene_issues
    scenes=read_json(path/'script.json',[])
    info=read_json(path/'project.json')
    return {**info,"status":status,"cenas":scenes,'erros_cenas':scene_issues(path,scenes,info['config']),
            'frases_midias':[phrases(s['narracao_ptbr']) for s in scenes],
            'videos':sources.get('videos',[]),'videos_meta':sources.get('videos_meta',{}),
            "fontes":[{"id":s["id"],"origem":s["origem"],"caracteres":len(s["texto"])} for s in sources.get("fontes",[])]+extra_sources,
            "imagens":sources.get("imagens",[]),'imagens_meta':sources.get('imagens_meta',{}),"pronuncia":read_json(path/"pronuncia.json",{}),
            'pesquisa_imagens':{k:v for k,v in read_json(path/'topic-images.json',{}).items() if k in ('aviso','meta_imagens','entidade')},
            "didatica":read_json(path/('plano-motivacional.json' if read_json(path/'project.json').get('config',{}).get('tipo_roteiro')=='motivacional' else 'plano-didatico.json')),
            "checagem":research,
            "creditos_colagem":(path/'export/creditos-colagem.md').is_file(),
            "creditos_shotcraft":(path/'export/creditos-shotcraft.md').is_file(),
            "creditos_musica":(path/'export/creditos-musica.md').is_file(),
            "tarefa":read_json(path/'task.json',{}),
            'assunto':read_json(path/'topic.json',{}),
            "agendamento":read_json(path/'agendamento.json',{}),
            "agendamento_em_edicao":(path/'schedule-draft.json').is_file(),
            "processando":worker_active(path),
            "exportado":(path/"export/video.mp4").exists() and status.get("status") in ('concluido','enviando_youtube','enviado_youtube','erro_youtube','pausado_youtube')}


@app.get('/api/projects/{pid}/thumbnail')
def project_thumbnail(pid):
    from .completed import thumbnail
    return FileResponse(thumbnail(project_dir(pid)),media_type='image/jpeg',headers={'Cache-Control':'private, max-age=86400'})


class Edit(BaseModel):
    config:Settings
    cenas:list[Scene]
    pronuncia:dict[str,str]={}
    assunto:str|None=Field(default=None,max_length=2000)


@app.post('/api/projects/{pid}/images')
async def add_project_images(pid,files:list[UploadFile]=File(...),descricao:str=Form('',max_length=500)):
    from .review_media import append_images,MAX_BYTES,MAX_FILES
    from starlette.concurrency import run_in_threadpool
    path=project_dir(pid);editable(path)
    try:
        if not files or len(files)>MAX_FILES:raise ValueError('Envie de 1 a 12 imagens por vez.')
        uploads=[];total=0
        for file in files:
            data=bytearray()
            while chunk:=await file.read(1024*1024):
                data.extend(chunk);total+=len(chunk)
                if len(data)>MAX_BYTES or total>100*1024*1024:raise HTTPException(413,'Cada imagem pode ter até 20 MB; envie até 100 MB por vez.')
            uploads.append((file.filename or 'imagem.png',bytes(data)))
        return await run_in_threadpool(append_images,path,uploads,descricao,lambda:editable(path))
    finally:
        for file in files:await file.close()


@app.get('/api/projects/{pid}/images/{name}')
def project_image(pid,name):
    path=project_dir(pid)
    if name not in read_json(path/'sources.json',{}).get('imagens',[]):raise HTTPException(404)
    target=(path/'assets'/name).resolve()
    if target.parent!=(path/'assets').resolve() or not target.is_file():raise HTTPException(404)
    return FileResponse(target)


@app.post('/api/projects/{pid}/reels/media')
async def add_reels_media(pid,files:list[UploadFile]=File(...)):
    from .reels_media import import_files,MAX_BYTES,MAX_TOTAL
    from starlette.concurrency import run_in_threadpool
    import tempfile
    path=project_dir(pid);editable(path)
    try:
        if not files or len(files)>12:raise ValueError('Envie de 1 a 12 fotos ou clipes por vez.')
        folder=path/'cache';folder.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='reels-upload-',dir=folder) as temporary:
            uploads=[];total=0
            for i,file in enumerate(files):
                name=Path((file.filename or 'midia').replace('\\','/')).name
                target=Path(temporary)/(str(i+1)+'-'+name);size=0
                with target.open('wb') as out:
                    while chunk:=await file.read(1024*1024):
                        size+=len(chunk);total+=len(chunk)
                        if size>MAX_BYTES or total>MAX_TOTAL:raise HTTPException(413,'Até 200 MB por clipe e 500 MB por envio.')
                        out.write(chunk)
                uploads.append(target)
            return await run_in_threadpool(import_files,path,uploads,lambda:editable(path))
    except ValueError as exc:raise HTTPException(400,str(exc)) from exc
    finally:
        for file in files:await file.close()


@app.get('/api/projects/{pid}/media/{name}')
def reels_media_file(pid,name):
    path=project_dir(pid);sources=read_json(path/'sources.json',{})
    names=sources.get('videos',[])+[v.get('miniatura') for v in sources.get('videos_meta',{}).values()]
    target=(path/'assets'/name).resolve()
    if name not in names or target.parent!=(path/'assets').resolve() or not target.is_file():raise HTTPException(404)
    return FileResponse(target)


@app.post('/api/projects/{pid}/scenes/{index}/preview')
def create_scene_preview(pid,index:int):
    from .scene_preview import prepare,status
    path=project_dir(pid);editable(path)
    key,target=prepare(path,index)
    job=None
    if not (target/'export/video.mp4').is_file():
        job=launch(path,None,kind='scene_preview:'+key)
        if read_json(target/'status.json',{}).get('status')=='revisao':set_status(target,'fila','Prévia aguardando a vez na fila')
    return {**status(path,key),'tarefa':job}


@app.get('/api/projects/{pid}/scene-previews/{key}')
def scene_preview_status(pid,key):
    from .scene_preview import status
    path=project_dir(pid);result=status(path,key)
    job=next((j for j in SCHEDULER.snapshot()['tarefas'] if j['project']==pid and j['kind']=='scene_preview:'+key),None) if SCHEDULER else None
    matches=job is not None
    result['em_execucao']=bool(matches and job['status']=='executando')
    result['tarefa']=job if matches else None
    if not matches and not result['pronta'] and result['status'] in ('fila','renderizando'):
        result.update(status='pausado',mensagem='Prévia interrompida. Gere novamente para retomar o cache.')
    return result


@app.get('/api/projects/{pid}/scene-previews/{key}/video')
def scene_preview_video(pid,key):
    from .scene_preview import directory
    target=directory(project_dir(pid),key)/'export/video.mp4'
    if not target.is_file():raise HTTPException(404)
    return FileResponse(target,media_type='video/mp4')


@app.put("/api/projects/{pid}")
def save(pid,body:Edit):
    path=project_dir(pid)
    editable(path)
    was_paused=read_json(path/'status.json',{}).get('status')=='pausado'
    info=read_json(path/"project.json")
    old=Settings.model_validate(info['config'])
    from .video_backgrounds import validate as validate_backgrounds
    validate_backgrounds([s.model_dump() for s in body.cenas],body.config,path)
    if body.config.tipo_video=='video':
        allowed=read_json(path/'sources.json',{}).get('imagens',[])
        for scene in body.cenas:
            if len(scene.imagens_cena)!=len(set(scene.imagens_cena)):raise ValueError('Escolha imagens diferentes para a sequência da cena.')
            if any(name not in allowed for name in scene.imagens_cena):raise ValueError('Uma imagem da sequência não pertence ao projeto.')
    previous=read_json(path/'script.json',[])
    if body.assunto is not None and not previous:
        topic=read_json(path/'topic.json',{})
        requested=body.assunto.strip()
        body.config.objetivo_aprendizagem=requested[:250]
        if requested!=topic.get('assunto',''):
            sources=read_json(path/'sources.json',{}).get('fontes',[])
            supplied=any(not s.get('pesquisada') and not s.get('gerada_por_ia') and s.get('origem')!='Imagens das fontes' for s in sources)
            if not requested and not supplied:raise ValueError('Informe um assunto ou adicione uma fonte.')
            write_json(path/'topic.json',{'assunto':requested,'pesquisa_pendente':not supplied})
            if not supplied:
                source_data=read_json(path/'sources.json',{})
                write_json(path/'sources.json',{**source_data,'fontes':[]})
            if info.get('titulo_automatico'):info['titulo']=requested[:100] or 'Novo vídeo'
    updated=[x.model_dump() for x in body.cenas]
    teaching_file=path/('plano-motivacional.json' if old.tipo_roteiro=='motivacional' else 'plano-didatico.json')
    teaching=read_json(teaching_file)
    significant=('tom','voz','voz_secundaria','estilo_locucao','velocidade','minutos','publico','objetivo_aprendizagem','roteiro_provedor','apresentadores','pesquisa_externa','gemini_projeto_completo','gemini_modelo_voz','gemini_voz','gemini_voz_secundaria','planejamento_ia','tipo_roteiro','publico_motivacional','tipo_video')
    from .runtime import local_model
    model_changed=(local_model(old)!=local_model(body.config) if body.config.roteiro_provedor=='local' else old.roteiro_modelo!=body.config.roteiro_modelo)
    if teaching and (previous!=updated or model_changed or any(getattr(old,k)!=getattr(body.config,k) for k in significant)):
        teaching['desatualizado']=True
        write_json(teaching_file,teaching)
    info["config"]=body.config.model_dump()
    write_json(path/"project.json",info)
    write_json(path/"script.json",updated)
    from .research import sync_script
    sync_script(path,updated)
    write_json(path/"pronuncia.json",body.pronuncia)
    set_status(path,'pausado' if was_paused else 'revisao','Alterações salvas. Retome quando quiser.' if was_paused else 'Alterações salvas. Renderize para atualizar o vídeo.')
    return {"ok":True}


@app.post("/api/projects/{pid}/script")
def script(pid):
    path=project_dir(pid)
    job=launch(path,lambda:projects.generate(path))
    return {"ok":True,"tarefa":job}


@app.post("/api/projects/{pid}/scenes/{index}/regenerate")
def regenerate(pid,index:int):
    path=project_dir(pid)
    if index<0 or index>=len(read_json(path/"script.json",[])):
        raise HTTPException(404,"Cena não encontrada")
    # Ignora o cache desta única geração pelo conteúdo de uma instrução explícita.
    launch(path,lambda:projects.generate(path,index),kind=f'cena:{index}')
    return {"ok":True}


@app.post("/api/projects/{pid}/render")
def render(pid):
    path=project_dir(pid)
    if not read_json(path/"script.json"):
        raise HTTPException(400,"Gere um roteiro primeiro")
    settings=Settings.model_validate(read_json(path/"project.json")["config"])
    job=launch(path,lambda:render_project(path,settings),kind='render')
    return {"ok":True,"tarefa":job}


class ScheduleRender(BaseModel):
    youtube_ia:StageAI|None=None
    horario:str=Field(max_length=50)
    canal:str=Field(default='',max_length=24)
    titulo:str=Field(default='',max_length=100)
    orientacao:str=Field(default='',max_length=1000)
    privacidade:Literal['public','unlisted','private']='public'
    conteudo_infantil:bool=False
    incluir_fontes:bool=False
    incluir_creditos:bool=False
    gerar_roteiro:bool=False
    playlists:list[str]=Field(default_factory=list,max_length=100)


@app.post('/api/projects/{pid}/schedule')
def schedule_render(pid,body:ScheduleRender):
    from datetime import datetime
    path=project_dir(pid)
    if not read_json(path/'script.json'):
        if not body.gerar_roteiro:raise ValueError('Gere e revise o roteiro antes de agendar, ou escolha criar o roteiro automaticamente.')
        if not read_json(path/'sources.json',{}).get('fontes') and not read_json(path/'topic.json',{}).get('assunto'):
            raise ValueError('Informe um assunto ou fontes para criar o roteiro agendado.')
    try:
        moment=datetime.fromisoformat(body.horario.replace('Z','+00:00'))
    except ValueError as exc:raise ValueError('Data ou horário inválido.') from exc
    if moment.tzinfo is None:raise ValueError('O horário deve incluir o fuso do seu computador.')
    from .publication import settings_for_schedule
    config=settings_for_schedule(path,body.canal,body.titulo,body.orientacao,body.privacidade,body.conteudo_infantil,
                                 include_sources=body.incluir_fontes,include_credits=body.incluir_creditos,playlists=body.playlists,youtube_ia=body.youtube_ia)
    queue=scheduler()
    with queue.mutex:
        job=queue.submit(path,'render_youtube',moment.timestamp(),options=config)
        from .stage_ai import save_youtube_choice
        save_youtube_choice(path,config['youtube_ia'])
        write_json(path/'agendamento.json',{**config,'horario':moment.isoformat()})
        (path/'schedule-draft.json').unlink(missing_ok=True)
    return {**job,'publicacao':config}


@app.post('/api/projects/{pid}/schedule/edit')
def edit_scheduled_project(pid):
    path=project_dir(pid);queue=scheduler()
    with queue.mutex:
        with queue.transaction() as db:
            job=db.execute("SELECT * FROM jobs WHERE path=? AND status IN ('agendado','fila','executando')",(str(path.resolve()),)).fetchone()
        if not job:
            if (path/'schedule-draft.json').is_file():return {'ok':True,'agendamento':read_json(path/'agendamento.json',{})}
            raise HTTPException(409,'Este projeto não tem um agendamento aguardando execução.')
        if job['status']=='executando':raise HTTPException(409,'O fluxo já começou. Pause e aguarde antes de alterar o vídeo.')
        if job['kind']!='render_youtube':raise HTTPException(409,'Esta tarefa pertence à fila manual.')
        queue.cancel(job['id'])
        draft={'job_anterior':job['id'],'opcoes':json.loads(job['options']),'horario':job['scheduled']}
        write_json(path/'schedule-draft.json',draft)
        set_status(path,'revisao','Agendamento em edição e suspenso. Altere o vídeo e use Salvar e reagendar para ativá-lo novamente.')
        return {'ok':True,'agendamento':read_json(path/'agendamento.json',{})}


class YouTubeChannel(BaseModel):
    nome:str=Field(min_length=1,max_length=100)
    canal:str=Field(min_length=1,max_length=300)
    padrao:bool=False


@app.get('/api/youtube/channels')
def youtube_channels():
    from .youtube import channels
    from .youtube_upload import connected
    return [{**c,'conectado':connected(c['id'])} for c in channels()]


@app.get('/api/youtube/channels/{cid}/playlists')
def youtube_channel_playlists(cid:str):
    from .youtube_playlists import listing
    return listing(cid)


@app.get('/api/youtube/oauth/config')
def youtube_oauth_configuration():
    from .youtube_upload import configuration
    return configuration()


class YouTubeOAuthConfig(BaseModel):
    documento:SecretStr=Field(max_length=30000)


@app.post('/api/youtube/oauth/config')
def youtube_oauth_configure(body:YouTubeOAuthConfig):
    from .youtube_upload import configure
    if ACTIVE.locked() or any(j['kind']=='youtube' for j in scheduler().snapshot()['tarefas']):
        raise HTTPException(409,'Aguarde os processamentos e envios pendentes antes de mudar o cliente OAuth.')
    return configure(body.documento.get_secret_value())


class YouTubeOAuthStart(BaseModel):
    canal:str=Field(default='',max_length=24)


@app.post('/api/youtube/oauth/start')
def youtube_oauth_start(request:Request,body:YouTubeOAuthStart):
    from .youtube_upload import begin_connection
    if body.canal:
        from .youtube import channel_id
        channel_id(body.canal)
    return begin_connection(str(request.base_url).rstrip('/'),body.canal)


@app.get('/api/youtube/oauth/attempts/{attempt}')
def youtube_oauth_attempt(attempt:str):
    from .youtube_upload import connection_status
    return connection_status(attempt)


@app.get('/api/youtube/oauth/callback')
def youtube_oauth_callback(state:str='',code:str='',error:str=''):
    from html import escape
    from fastapi.responses import HTMLResponse
    from .youtube_upload import finish_connection
    try:
        result=finish_connection(state,code,error);message=result['message'];status=200
    except ValueError as exc:message=str(exc);status=400
    return HTMLResponse('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="referrer" content="no-referrer"><title>Clareia · YouTube</title><body><h1>Conexão com YouTube</h1><p>'+escape(message)+'</p><p>Você pode fechar esta aba e voltar ao estúdio.</p></body></html>',status_code=status,headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'"})


@app.delete('/api/youtube/channels/{cid}/connection')
def youtube_disconnect(cid:str):
    from .youtube_upload import disconnect
    if ACTIVE.locked() or any(j['kind']=='youtube' for j in scheduler().snapshot()['tarefas']):
        raise HTTPException(409,'Aguarde os processamentos e envios pendentes antes de desconectar o canal.')
    disconnect(cid)
    return {'ok':True}


@app.post('/api/youtube/channels')
def youtube_channel_save(body:YouTubeChannel):
    from .youtube import save_channel
    return save_channel(body.nome,body.canal,body.padrao)


@app.delete('/api/youtube/channels/{cid}')
def youtube_channel_remove(cid:str):
    from .youtube import remove_channel
    if ACTIVE.locked() or any(j['kind']=='youtube' for j in scheduler().snapshot()['tarefas']):
        raise HTTPException(409,'Aguarde os processamentos e envios pendentes antes de remover o canal.')
    remove_channel(cid)
    return {'ok':True}


@app.get('/api/projects/{pid}/youtube')
def youtube_metadata(pid):
    from .youtube import metadata
    return metadata(project_dir(pid))


class YouTubeGeneration(BaseModel):
    youtube_ia:StageAI|None=None
    incluir_fontes:bool=False
    incluir_creditos:bool=False


@app.post('/api/projects/{pid}/youtube/regenerate')
def youtube_metadata_regenerate(pid,body:YouTubeGeneration|None=None):
    from .youtube import metadata
    options=body or YouTubeGeneration()
    path=project_dir(pid);queue=scheduler();lease=queue.lock_factory()
    with queue.mutex:
        editable(path)
        if not ACTIVE.acquire(blocking=False):raise HTTPException(409,'Aguarde o processamento atual terminar antes de gerar os textos.')
    try:
        if not lease.acquire():raise HTTPException(409,'Há outro processamento em andamento. Aguarde antes de gerar os textos.')
        with JobLock(path,processing_lock=lease):
            if options.youtube_ia is not None:
                from .stage_ai import save_youtube_choice
                save_youtube_choice(path,options.youtube_ia)
            return metadata(path,regenerate=True,use_ai=True,auto_title=True,
                            include_sources=options.incluir_fontes,include_credits=options.incluir_creditos)
    finally:
        lease.release();ACTIVE.release()


class YouTubeMetadata(BaseModel):
    youtube_ia:StageAI|None=None
    titulo:str=Field(min_length=1,max_length=100)
    descricao:str=Field(max_length=5000)
    canal:str=Field(default='',max_length=24)
    playlists:list[str]|None=Field(default=None,max_length=100)


@app.put('/api/projects/{pid}/youtube')
def youtube_metadata_save(pid,body:YouTubeMetadata):
    from .youtube import save_metadata
    path=project_dir(pid)
    with scheduler().mutex:
        if body.youtube_ia is not None:
            editable(path)
            from .stage_ai import save_youtube_choice
            save_youtube_choice(path,body.youtube_ia)
        return save_metadata(path,body.titulo,body.descricao,body.canal,playlists=body.playlists)


class YouTubeUpload(BaseModel):
    canal:str=Field(min_length=24,max_length=24)
    privacidade:Literal['private','unlisted','public']='public'
    conteudo_infantil:bool=False
    nova_sessao:bool=False
    playlists:list[str]=Field(default_factory=list,max_length=100)


@app.get('/api/projects/{pid}/youtube/upload')
def youtube_upload_status(pid):
    from .youtube_upload import upload_status
    return upload_status(project_dir(pid))


@app.post('/api/projects/{pid}/youtube/upload')
def youtube_upload_start(pid,body:YouTubeUpload):
    from .youtube_upload import prepare_upload
    from .youtube import channel_id
    path=project_dir(pid);channel_id(body.canal)
    queue=scheduler()
    with queue.mutex:
        if queue.pending(path):raise HTTPException(409,'Este projeto já está na fila ou em execução. Aguarde ou cancele a espera.')
        status=prepare_upload(path,body.canal,body.privacidade,body.conteudo_infantil,restart=body.nova_sessao,playlists=body.playlists)
        if status.get('video_id') and status.get('playlists_concluidas'):return {'ok':True,'envio':status,'ja_enviado':True}
        try:job=queue.submit(path,'youtube')
        except Exception:
            from .youtube_upload import cancelled
            cancelled(path)
            raise
    return {'ok':True,'tarefa':job,'envio':status}


@app.post("/api/projects/{pid}/pause")
def pause(pid):
    path=project_dir(pid)
    if not worker_active(path):raise HTTPException(409,'Este projeto não está processando. Cancele a espera na fila, se necessário.')
    (path/"pause.request").touch()
    return {"ok":True,"mensagem":"Pausa solicitada; aguarde concluir a operação atual"}


@app.post('/api/projects/{pid}/resume')
def resume(pid):
    path=project_dir(pid)
    kind=read_json(path/'task.json',{}).get('tipo','render' if read_json(path/'script.json') else 'roteiro')
    if kind=='render_youtube':
        job=scheduler().submit(path,'render_youtube',options=read_json(path/'task.json',{}).get('opcoes') or read_json(path/'agendamento.json',{}))
        return {'ok':True,'tipo':kind,'tarefa':job}
    elif kind=='youtube':
        from .youtube_upload import upload
        launch(path,lambda:upload(path),kind='youtube')
    elif kind.startswith('scene_preview:'):
        from .scene_preview import directory
        directory(path,kind.split(':',1)[1])
        launch(path,None,kind=kind)
    elif kind=='render':
        settings=Settings.model_validate(read_json(path/'project.json')['config'])
        if not read_json(path/'script.json'):raise HTTPException(400,'Gere o roteiro primeiro.')
        launch(path,lambda:render_project(path,settings),kind='render')
    elif kind.startswith('cena:'):
        index=int(kind.split(':',1)[1])
        if index<0 or index>=len(read_json(path/'script.json',[])):raise HTTPException(400,'Cena não encontrada no roteiro atual.')
        launch(path,lambda:projects.generate(path,index),kind=kind)
    else:launch(path,lambda:projects.generate(path),kind='roteiro')
    return {'ok':True,'tipo':kind}


@app.get("/api/projects/{pid}/download/{name}")
def download(pid,name):
    if name not in ("video.mp4","legendas.srt","roteiro.md","legendas.ass","fontes-verificadas.md","checagem.json","creditos-imagens.md","creditos-imagens-pesquisadas.md","creditos-colagem.md","creditos-shotcraft.md","creditos-musica.md","youtube.txt"):
        raise HTTPException(404)
    path=project_dir(pid)/"export"/name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path,filename=name)


@app.get("/api/samples/{voice}")
def sample(voice,estilo:str='natural'):
    from .voices import catalog,DELIVERIES,SAMPLE_TEXTS
    if voice not in {v['id'] for v in catalog()} or estilo not in DELIVERIES:
        raise HTTPException(404)
    target=ROOT/"output/amostras"/(voice+('-'+estilo if estilo!='natural' else '')+".wav")
    if not target.exists():
        from .speech import TTS_LOCK,synthesize,release
        if ACTIVE.locked() or not TTS_LOCK.acquire(blocking=False):raise HTTPException(409,'Aguarde a voz em processamento para ouvir outra amostra.')
        try:
            import shutil
            text=SAMPLE_TEXTS.get(estilo,'Uma boa explicação começa com uma pergunta. Como transformar uma ideia difícil em algo que faz sentido? Vamos descobrir, passo a passo.')
            try:
                wav,_=synthesize(text,voice,1,ROOT/'output/amostras/cache',delivery=estilo)
            except (RuntimeError,ValueError) as exc:
                raise HTTPException(503,str(exc)[:500]) from exc
            shutil.copyfile(wav,target)
        finally:release();TTS_LOCK.release()
    return FileResponse(target,media_type="audio/wav")
