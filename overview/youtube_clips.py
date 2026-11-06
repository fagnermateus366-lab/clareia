"""Public YouTube clips, stored without source audio and reusable in Reels."""
import json
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.parse import urlsplit,parse_qs

from .core import ROOT,binary,digest,read_json,write_json,run
from .youtube_music import token,download_options
from .youtube_downloads import DownloadJobs

STORE=ROOT/'output/youtube-clips'
MAX_BYTES=200*1024*1024


def storage():return STORE
jobs=DownloadJobs(storage,'overview.youtube_clips')


def youtube_id(query):
    if not re.match(r'https?://',query,re.I):return None
    parsed=urlsplit(query);host=(parsed.hostname or '').lower()
    parts=parsed.path.strip('/').split('/')
    if host in ('youtu.be','www.youtu.be'):key=parts[0]
    elif host in ('youtube.com','www.youtube.com','m.youtube.com','music.youtube.com'):
        key=parts[1] if len(parts)>1 and parts[0] in ('shorts','embed','live') else parse_qs(parsed.query).get('v',[''])[0]
    else:raise ValueError('Use o nome do vídeo ou um link do YouTube.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',key):raise ValueError('Este link não identifica um vídeo do YouTube.')
    return key


def normalize(item):
    vid=item.get('id','')
    try:seconds=float(item.get('duration') or 0)
    except (TypeError,ValueError):return None
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid) or item.get('is_live') or item.get('live_status')=='is_live':return None
    if not math.isfinite(seconds) or not 1<=seconds<=1800:return None
    return {'id':digest('youtube-video',vid),'youtube_id':vid,'nome':str(item.get('title') or 'Clipe')[:180],
            'autor':str(item.get('channel') or item.get('uploader') or 'Canal não informado')[:180],
            'duracao_s':seconds,'fonte':'https://www.youtube.com/watch?v='+vid,
            'miniatura':f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'}


def catalog():
    return [r for p in (STORE/'library').glob('*.json') if (r:=read_json(p,{})) and
            re.fullmatch('[a-f0-9]{24}',r.get('id','')) and (STORE/'library'/(r['id']+'.mp4')).is_file()]


def search(query):
    query=query.strip()
    if not 2<=len(query)<=200:raise ValueError('Digite de 2 a 200 caracteres com o nome ou link do vídeo.')
    from yt_dlp import YoutubeDL
    key=youtube_id(query)
    options={'extract_flat':'in_playlist','quiet':True,'no_warnings':True,'skip_download':True,'socket_timeout':20,'retries':1,
             'noplaylist':True,'cachedir':False,'js_runtimes':{'node':{'path':shutil.which('node')}} if shutil.which('node') else {}}
    try:
        with YoutubeDL(options) as ydl:info=ydl.extract_info('https://www.youtube.com/watch?v='+key if key else 'ytsearch12:'+query,download=False)
    except Exception as exc:raise ValueError('Não foi possível pesquisar no YouTube agora. Confira a internet e tente novamente.') from exc
    found=[];seen=set();saved=catalog()
    for item in info.get('entries',[]) if not key else [info]:
        row=normalize(item or {})
        if not row or row['id'] in seen:continue
        seen.add(row['id']);write_json(STORE/'results'/(row['id']+'.json'),row|{'consultado_em':time.time()})
        available=[c for c in saved if c['youtube_id']==row['youtube_id']]
        found.append(row|{'salvos':[c['id'] for c in available]})
    return {'videos':found,'busca':query}


def result(key):
    row=read_json(STORE/'results'/(token(key)+'.json'))
    if not row or time.time()-row.get('consultado_em',0)>7*86400:raise ValueError('Faça a busca novamente antes de baixar o clipe.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',row.get('youtube_id','')):raise ValueError('Clipe inválido.')
    return row


def clip(key):
    token(key);row=read_json(STORE/'library'/(key+'.json'))
    if not row or not (STORE/'library'/(key+'.mp4')).is_file():raise FileNotFoundError('Clipe não encontrado na biblioteca.')
    return row


def start(key,quality=720):
    row=result(key)
    if quality not in (720,1080):raise ValueError('Escolha 720p ou 1080p.')
    saved=next((c for c in catalog() if c['youtube_id']==row['youtube_id'] and c['qualidade']==quality),None)
    if saved:return {'estado':'concluido','clipe':saved,'progresso':1,'mensagem':'Este clipe já está na biblioteca.'}
    return jobs.start(row,quality)


def attach(path,keys,guard=lambda:None):
    from .reels_media import import_files
    from .review_media import LOCK
    if not isinstance(keys,list) or len(keys)>12 or any(not isinstance(k,str) for k in keys):raise ValueError('Escolha até 12 clipes da biblioteca por vez.')
    keys=list(dict.fromkeys(keys));records=[clip(k) for k in keys]
    if not records:return {'adicionadas':[]}
    with LOCK:
        files=[STORE/'library'/(r['id']+'.mp4') for r in records]
        names=[]
        for source in files:
            with source.open('rb') as handle:names.append('clip-'+hashlib.file_digest(handle,'sha256').hexdigest()[:24]+'.mp4')
        added=import_files(path,files,guard)
        sources=read_json(path/'sources.json')
        for name,row in zip(names,records):
            sources['videos_meta'][name].update(nome_original=row['nome']+'.mp4',origem_youtube=row['fonte'])
        write_json(path/'sources.json',sources)
        return added|{'videos_meta':sources['videos_meta']}


def video_format(quality):
    def choose(context):
        choices=[f for f in context['formats'] if f.get('vcodec') not in (None,'none')
            and f.get('width') and f.get('height') and min(f['width'],f['height'])<=quality
            and max(f['width'],f['height'])<=round(quality*16/9)+2 and (f.get('fps') or 0)<=30]
        silent=[f for f in choices if f.get('acodec') in (None,'none')]
        choices=silent or choices
        compatible=[f for f in choices if f.get('ext')=='mp4' and str(f.get('vcodec','')).startswith('avc')]
        if compatible:choices=compatible
        if choices:yield choices[-1]
    return choose


def worker(key):
    from yt_dlp import YoutubeDL
    import psutil
    data=read_json(jobs.path(key));row=result(data['video']['id']);quality=data['qualidade']
    proc=psutil.Process();folder=STORE/'incoming'/key;folder.mkdir(parents=True,exist_ok=True)
    jobs.update(key,estado='baixando',processo=proc.pid,processo_criado=proc.create_time(),mensagem='Conectando ao YouTube…')
    last=0.
    def hook(event):
        nonlocal last
        if jobs.path(key).with_suffix('.cancel').exists():raise ValueError('Importação cancelada.')
        downloaded=int(event.get('downloaded_bytes') or 0);total=int(event.get('total_bytes') or event.get('total_bytes_estimate') or 0)
        if max(downloaded,total)>MAX_BYTES:raise ValueError('O clipe ultrapassa 200 MB. Escolha 720p ou um vídeo mais curto.')
        now=time.monotonic()
        if now-last>.4 or event.get('status')=='finished':
            last=now;jobs.update(key,estado='baixando',mensagem='Baixando o clipe…',baixados_bytes=downloaded,total_bytes=total,progresso=min(.85,.85*downloaded/total) if total else .05)
    options=download_options(folder,hook)
    options.update(max_filesize=MAX_BYTES,outtmpl=str(folder/'video.%(ext)s'),format=video_format(quality))
    try:
        with YoutubeDL(options) as ydl:
            info=ydl.extract_info('https://www.youtube.com/watch?v='+row['youtube_id'],download=False)
            duration=float(info.get('duration') or 0)
            if info.get('is_live') or not 1<=duration<=1800:raise ValueError('Escolha um vídeo de até 30 minutos; transmissões ao vivo não são importadas.')
            if info.get('availability') in ('private','premium_only','subscriber_only','needs_auth'):raise ValueError('Este vídeo exige acesso restrito e não pode ser importado por esta conexão pública.')
            ydl.process_info(info);source=Path(ydl.prepare_filename(info))
        if not source.is_file() or not 0<source.stat().st_size<=MAX_BYTES:raise ValueError('O download do clipe não foi concluído.')
        if jobs.path(key).with_suffix('.cancel').exists():raise ValueError('Importação cancelada.')
        jobs.update(key,estado='convertendo',mensagem='Preparando o vídeo sem o áudio original…',progresso=.9)
        target=folder/'muted.mp4'
        run([binary('ffmpeg'),'-y','-v','error','-i',source,'-map','0:v:0','-an','-sn','-dn','-c:v','copy','-movflags','+faststart',target],timeout=120)
        from .reels_media import probe
        details=probe(target)
        streams=json.loads(run([binary('ffprobe'),'-v','error','-show_entries','stream=codec_type','-of','json',target],timeout=20))['streams']
        if any(s['codec_type']=='audio' for s in streams):raise ValueError('Não foi possível remover o áudio original.')
        identity=digest('youtube-clip',row['youtube_id'],quality);library=STORE/'library';library.mkdir(parents=True,exist_ok=True)
        poster=folder/'poster.jpg'
        run([binary('ffmpeg'),'-y','-v','error','-i',target,'-frames:v','1','-vf','scale=320:320:force_original_aspect_ratio=decrease','-threads','1',poster],timeout=30)
        record={k:v for k,v in row.items() if k not in ('id','miniatura','consultado_em')}
        record.update(id=identity,qualidade=quality,**details,sem_audio=True,adicionado_em=time.time())
        if jobs.path(key).with_suffix('.cancel').exists():raise ValueError('Importação cancelada.')
        os.replace(target,library/(identity+'.mp4'));os.replace(poster,library/(identity+'.jpg'));write_json(library/(identity+'.json'),record)
        jobs.update(key,estado='concluido',mensagem='Clipe salvo sem áudio. Adicione ao projeto e escolha sua narração e música.',progresso=1,clipe=record)
    except ValueError as exc:jobs.update(key,estado='cancelado' if jobs.path(key).with_suffix('.cancel').exists() else 'erro',mensagem=str(exc)[:500])
    except Exception:jobs.update(key,estado='erro',mensagem='O YouTube não disponibilizou este clipe para a conexão. Tente outra versão, um vídeo mais curto ou envie seu arquivo local.')
    finally:
        if folder.resolve().parent==(STORE/'incoming').resolve():shutil.rmtree(folder,ignore_errors=True)


if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='--worker':raise SystemExit(2)
    worker(token(sys.argv[2],32))
