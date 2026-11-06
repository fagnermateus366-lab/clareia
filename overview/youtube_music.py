"""Music-only discovery and explicit, bounded imports into the local library.

Community clients, separate from Clareia's Google/YouTube publishing credentials.
No browser cookies, account login, private content or DRM-enabled formats.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

from . import music
from .core import CREATE_FLAGS,ROOT,digest,read_json,write_json

LOCK=threading.RLock()
MAX_SECONDS=1800
MAX_JOB_SECONDS=300
RUNNING={'aguardando','baixando','convertendo'}


def storage():return music.LIBRARY/'youtube'


def token(value,length=24):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{'+str(length)+'}',value):raise ValueError('Identificador de mídia inválido.')
    return value


def saved_track(video_id):
    return next((t for t in music.catalog() if t.get('youtube_id')==video_id and music.track_path(t).is_file()),None)


def normalize(item):
    vid=item.get('videoId','')
    if item.get('resultType')!='song' or not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid) or item.get('isAvailable') is False:return None
    try:seconds=float(item.get('duration_seconds',0))
    except (ValueError,TypeError):return None
    if not math.isfinite(seconds) or not 1<=seconds<=MAX_SECONDS:return None
    return {'id':digest('youtube-music',vid),'youtube_id':vid,'nome':str(item.get('title') or 'Música')[:180],
        'autor':', '.join(str(a.get('name','')) for a in item.get('artists',[]) if isinstance(a,dict))[:250] or 'Artista não informado',
        'album':str((item.get('album') or {}).get('name',''))[:180],
        'duracao_s':seconds,'miniatura':f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
        'fonte':f'https://music.youtube.com/watch?v={vid}','licenca':'Permissão de reutilização não verificada'}


def search(query):
    query=query.strip()
    if not 2<=len(query)<=200:raise ValueError('Digite de 2 a 200 caracteres, com o nome da música ou do artista.')
    from ytmusicapi import YTMusic
    import requests
    class Session(requests.Session):
        def request(self,*args,**kwargs):
            kwargs.setdefault('timeout',20)
            return super().request(*args,**kwargs)
    try:
        with Session() as session:
            results=YTMusic(language='en',location='BR',requests_session=session).search(query,filter='songs',limit=20)
    except Exception as exc:
        raise ValueError('Não foi possível consultar o YouTube Music agora. Confira a internet e tente novamente.') from exc
    tracks=[];seen=set()
    for item in results:
        record=normalize(item)
        if record is None or record['id'] in seen:continue
        seen.add(record['id'])
        write_json(storage()/'results'/(record['id']+'.json'),{**record,'consultado_em':time.time()})
        saved=saved_track(record['youtube_id'])
        tracks.append(record|{'salva_id':saved['id'] if saved else None})
        if len(tracks)>=20:break
    return {'faixas':tracks,'busca':query,'origem':'YouTube Music','filtro':'songs'}


def result(record_id):
    data=read_json(storage()/'results'/(token(record_id)+'.json'))
    if not data or time.time()-data.get('consultado_em',0)>7*86400:
        raise ValueError('Faça a busca novamente antes de baixar esta música.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',data.get('youtube_id','')) or not 1<=data.get('duracao_s',0)<=MAX_SECONDS:
        raise ValueError('Música inválida. Faça a busca novamente.')
    return data


def job_path(job_id):return storage()/'jobs'/(token(job_id,32)+'.json')


def update(job_id,**values):
    data=read_json(job_path(job_id),{})
    write_json(job_path(job_id),data|values|{'atualizado':time.time()})


def public_job(data):
    return {k:v for k,v in data.items() if k in ('id','estado','mensagem','progresso','baixados_bytes','total_bytes','musica','faixa','criado','atualizado')}


def alive(data):
    import psutil
    try:return abs(psutil.Process(data['processo']).create_time()-data['processo_criado'])<.1
    except (psutil.Error,KeyError):return False


def active_job():
    with LOCK:
        for path in (storage()/'jobs').glob('*.json'):
            data=read_json(path,{})
            if data.get('estado') not in RUNNING:continue
            if alive(data):return public_job(data)
            # A small launch window is allowed before the child PID is written.
            if time.time()-data.get('atualizado',0)<5:return public_job(data)
            update(data['id'],estado='erro',mensagem='A importação anterior foi interrompida. Você pode tentar novamente.')
    return None


def get_job(job_id):
    data=read_json(job_path(job_id))
    if not data:raise FileNotFoundError('Importação não encontrada.')
    if data.get('estado') in RUNNING:active_job();data=read_json(job_path(job_id))
    return public_job(data)


def start(record_id,credits=''):
    record=result(record_id)
    with LOCK:
        saved=saved_track(record['youtube_id'])
        if saved:return {'estado':'concluido','faixa':saved,'mensagem':'Esta música já está na sua biblioteca.','progresso':1}
        previous=active_job()
        if previous:
            if previous['musica']['id']==record_id:return previous
            raise ValueError('Já há uma música sendo importada. Aguarde ou cancele a importação atual.')
        job_id=uuid.uuid4().hex
        data={'id':job_id,'estado':'aguardando','mensagem':'Preparando a importação do áudio…','progresso':0,
              'musica':{k:v for k,v in record.items() if k!='consultado_em'},'creditos':credits.strip()[:2000],
              'criado':time.time(),'atualizado':time.time()}
        write_json(job_path(job_id),data)
        threading.Thread(target=coordinate,args=(job_id,),daemon=True,name='clareia-music-import').start()
        return public_job(data)


def cancel(job_id):
    data=read_json(job_path(job_id))
    if not data:raise FileNotFoundError('Importação não encontrada.')
    if data.get('estado') in RUNNING:job_path(job_id).with_suffix('.cancel').touch()
    return public_job(data)


def kill_tree(proc):
    import psutil
    try:
        parent=psutil.Process(proc.pid)
        children=parent.children(recursive=True)
        for child in children:
            try:child.kill()
            except psutil.Error:pass
        parent.kill()
    except psutil.Error:pass
    proc.wait()


def coordinate(job_id):
    proc=None
    try:
        proc=subprocess.Popen([sys.executable,'-m','overview.youtube_music','--worker',job_id],cwd=ROOT,
             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=CREATE_FLAGS)
        started=time.monotonic();cancelled=job_path(job_id).with_suffix('.cancel')
        while proc.poll() is None:
            if cancelled.exists() or time.monotonic()-started>MAX_JOB_SECONDS:
                kill_tree(proc)
                current=read_json(job_path(job_id),{})
                if current.get('estado')!='concluido':update(job_id,estado='cancelado' if cancelled.exists() else 'erro',
                    mensagem='Importação cancelada.' if cancelled.exists() else 'A importação demorou demais. Tente novamente mais tarde.')
                return
            time.sleep(.2)
        if read_json(job_path(job_id),{}).get('estado') in RUNNING:
            update(job_id,estado='erro',mensagem='Não foi possível concluir a importação. Tente novamente.')
    except Exception:
        if proc and proc.poll() is None:kill_tree(proc)
        update(job_id,estado='erro',mensagem='Não foi possível iniciar a importação da música.')
    finally:
        # Only this job's staging files; library tracks are never removed here.
        temp=storage()/'incoming'/job_id
        if temp.resolve().parent==(storage()/'incoming').resolve():shutil.rmtree(temp,ignore_errors=True)


def download_options(folder,hook):
    node=shutil.which('node');deno=shutil.which('deno')
    if not node and not deno:raise ValueError('O importador precisa do Node.js 22 ou mais recente, ou do Deno 2.3 ou mais recente.')
    return {'format':'bestaudio','noplaylist':True,'outtmpl':str(folder/'audio.%(ext)s'),
        'max_filesize':music.MAX_BYTES,'socket_timeout':20,'retries':1,'fragment_retries':1,
        'concurrent_fragment_downloads':1,'overwrites':False,'continuedl':False,'quiet':True,'no_warnings':True,
        'progress_hooks':[hook],'js_runtimes':{'node':{'path':node}} if node else {'deno':{'path':deno}},
        'cachedir':False,'allow_unplayable_formats':False,'restrictfilenames':True,
        'writethumbnail':False,'writesubtitles':False,'writeinfojson':False,'extract_flat':False}


def worker(job_id):
    import psutil
    from yt_dlp import YoutubeDL
    data=read_json(job_path(job_id));record=result(data['musica']['id'])
    proc=psutil.Process()
    update(job_id,processo=proc.pid,processo_criado=proc.create_time(),estado='baixando',mensagem='Conectando ao YouTube…')
    folder=storage()/'incoming'/job_id;folder.mkdir(parents=True,exist_ok=True)
    last=0.
    def hook(event):
        nonlocal last
        if job_path(job_id).with_suffix('.cancel').exists():raise ValueError('Importação cancelada.')
        downloaded=int(event.get('downloaded_bytes') or 0);total=int(event.get('total_bytes') or event.get('total_bytes_estimate') or 0)
        if max(downloaded,total)>music.MAX_BYTES:raise ValueError('O áudio ultrapassa o limite de 120 MB.')
        now=time.monotonic()
        if now-last>.4 or event.get('status')=='finished':
            last=now;update(job_id,estado='baixando',mensagem='Baixando somente o áudio…',baixados_bytes=downloaded,
                           total_bytes=total,progresso=min(.85,.85*downloaded/total) if total else .05)
    try:
        with YoutubeDL(download_options(folder,hook)) as ydl:
            url='https://www.youtube.com/watch?v='+record['youtube_id']
            info=ydl.extract_info(url,download=False)
            duration=float(info.get('duration') or 0)
            if info.get('is_live') or not 1<=duration<=MAX_SECONDS:raise ValueError('Escolha uma música de até 30 minutos; transmissões ao vivo não são importadas.')
            if info.get('availability') in ('private','premium_only','subscriber_only','needs_auth'):
                raise ValueError('Esta música exige acesso restrito e não pode ser importada por esta conexão pública.')
            if info.get('acodec') in (None,'none') or info.get('vcodec') not in (None,'none'):
                raise ValueError('O YouTube não disponibilizou um arquivo somente de áudio para esta faixa.')
            # Use the already extracted public format, rather than requesting a playlist or another item.
            ydl.process_info(info)
            source=Path(ydl.prepare_filename(info))
        if not source.is_file() or not 0<source.stat().st_size<=music.MAX_BYTES:raise ValueError('O download do áudio não foi concluído.')
        if job_path(job_id).with_suffix('.cancel').exists():raise ValueError('Importação cancelada.')
        update(job_id,estado='convertendo',mensagem='Preparando a música para a biblioteca…',progresso=.9)
        credit=data.get('creditos') or f"{record['nome']} — {record['autor']}\nFonte: {record['fonte']}\nPermissão de reutilização não verificada."
        metadata=dict(categoria='YouTube · minhas músicas',autor=record['autor'],fonte=record['fonte'],
            uso='Áudio importado do YouTube Music. Confira sua permissão antes de publicar.',
            licenca='Conforme a licença ou autorização que você possui',youtube_id=record['youtube_id'],
            origem='youtube_music',licenca_origem=str(info.get('license') or 'Não informada')[:500])
        track=music.import_track(source,record['nome'],credit,key='user-'+digest('youtube-music',record['youtube_id']),
                                 metadata=metadata,staging=folder/'converted.wav')
        update(job_id,estado='concluido',mensagem='Música salva na biblioteca e pronta para seus vídeos.',progresso=1,faixa=track)
    except ValueError as exc:
        update(job_id,estado='cancelado' if job_path(job_id).with_suffix('.cancel').exists() else 'erro',mensagem=str(exc)[:500])
    except Exception:
        update(job_id,estado='erro',mensagem='O YouTube não disponibilizou o áudio para esta conexão. A faixa pode estar restrita ou o serviço pode ter mudado. Tente outra versão ou importe seu arquivo local.')
    finally:
        if folder.resolve().parent==(storage()/'incoming').resolve():shutil.rmtree(folder,ignore_errors=True)


if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='--worker':raise SystemExit(2)
    worker(token(sys.argv[2],32))
