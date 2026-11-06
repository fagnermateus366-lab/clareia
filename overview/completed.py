"""Small, cached video posters and recorded completion metadata."""
from pathlib import Path
import json
import sqlite3
import threading
import uuid

from .core import MODEL,binary,digest,read_json,run
from .model_profiles import LOCAL_MODELS

LOCK=threading.Lock()


def positive(value):
    import math
    return float(value) if isinstance(value,(float,int)) and math.isfinite(value) and value>0 else None


def history(database,paths):
    result={}
    if not database or not Path(database).is_file() or not paths:return result
    try:
        with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True,timeout=1) as db:
            db.row_factory=sqlite3.Row
            rows=db.execute('SELECT path,kind,submitted,started,finished,status,options FROM jobs WHERE path IN ('+
                ','.join('?' for _ in paths)+') AND started IS NOT NULL ORDER BY id',[str(p.resolve()) for p in paths]).fetchall()
            for row in rows:result.setdefault(row['path'],[]).append(dict(row))
    except (sqlite3.Error,OSError):pass
    return result


def recorded_times(path,report,jobs):
    stored=report.get('tempos') or {}
    if stored.get('total_s') is not None:return stored
    render_time=positive(stored.get('renderizacao_s')) or positive(report.get('tempo_render_s'))
    result=stored or {'roteiro_s':None,'renderizacao_s':render_time,'total_s':None,'origem':'incompleto'}
    # Recover old boundaries only from the real queue journal and the final
    # render report timestamp, never from creation date or video length.
    video=path/'export/video.mp4';record=path/'render-report.json'
    if not render_time or not video.is_file() or not record.is_file():return result
    end=positive(stored.get('fim')) or positive(report.get('concluido_em')) or record.stat().st_mtime
    if abs(end-video.stat().st_mtime)>120:return result
    candidates=[j for j in jobs if j.get('started') and j['started']<end]
    scripts=[j for j in candidates if j['kind']=='roteiro' and j['status']=='revisao' and j.get('finished') and j['finished']<=end]
    if scripts:
        script=scripts[-1];start=script['submitted']
        renders=[j['started'] for j in candidates if j['kind']=='render' and j['started']>=script['finished']]
        if not renders:return result
        render_start=stored.get('render_inicio') or min(renders)
    else:
        checkpoint=read_json(path/'scheduled-publication.json',{})
        if not checkpoint.get('gerou_roteiro'):return result
        scheduled=[]
        for job in candidates:
            if job['kind']!='render_youtube':continue
            try:run_id=json.loads(job.get('options') or '{}').get('run_id')
            except ValueError:continue
            if run_id==checkpoint.get('run_id'):scheduled.append(job)
        # A single uninterrupted scheduled job has an unambiguous script start.
        if len(scheduled)!=1:return result
        start=scheduled[0]['started'];render_start=end-render_time
    if not 0<start<=render_start<=end:return result
    script_time=round(render_start-start,2);render_time=round(end-render_start,2)
    return {'roteiro_s':script_time,'renderizacao_s':render_time,'total_s':round(script_time+render_time,2),
            'origem':'historico','roteiro_inicio':start,'render_inicio':render_start,'fim':end}


def details(path,info,jobs=()):
    report=read_json(path/'render-report.json',{})
    plan=read_json(path/'plano-didatico.json',{}) or {}
    cfg=info.get('config',{})
    provider=report.get('provedor_roteiro') or plan.get('provedor') or cfg.get('roteiro_provedor','local')
    model=report.get('modelo_roteiro') or plan.get('modelo') or cfg.get('roteiro_modelo') or (MODEL if provider=='local' else '')
    name=LOCAL_MODELS[model][0] if model in LOCAL_MODELS else model
    video=path/'export/video.mp4'
    video_info=video.stat() if video.is_file() else None
    stamp=video_info.st_mtime_ns if video_info else None
    checkpoint=read_json(path/'scheduled-publication.json',{})
    scheduled=bool(video_info and checkpoint.get('stage')=='complete' and
                   checkpoint.get('file_hash')==digest(video_info.st_size,stamp))
    times=recorded_times(path,report,jobs)
    return {'modelo':model,'modelo_nome':name,'provedor':provider,
            'duracao_s':positive(report.get('musica',{}).get('duracao_s')) or positive(report.get('duracao_s')),
            'tempo_roteiro_s':times.get('roteiro_s'),
            'tempo_render_s':times.get('renderizacao_s'),
            'tempo_producao_s':times.get('total_s'),'tempos_origem':times.get('origem'),'fluxo_agendado':scheduled,
            'miniatura':f'/api/projects/{path.name}/thumbnail?v={stamp}' if stamp else None}


def thumbnail(path):
    video=path/'export/video.mp4'
    if not video.is_file() or not video.resolve().is_relative_to(path.resolve()):raise FileNotFoundError('Vídeo concluído não encontrado.')
    signature=digest(video.stat().st_mtime_ns,video.stat().st_size,'poster-v1')
    cache=path/'cache/thumbnails';target=cache/(signature+'.jpg')
    with LOCK:
        if target.is_file():return target
        cache.mkdir(parents=True,exist_ok=True)
        duration=positive(read_json(path/'render-report.json',{}).get('duracao_s')) or 1
        at=min(3,duration*.25)
        temporary=cache/(uuid.uuid4().hex+'.jpg')
        try:
            run([binary('ffmpeg'),'-y','-v','error','-threads','1','-ss',at,'-i',video,
                 '-frames:v','1','-vf','scale=480:-2','-threads','1','-q:v','4',temporary],timeout=25)
            if not temporary.is_file():raise ValueError('Não foi possível extrair a miniatura.')
            temporary.replace(target)
        finally:temporary.unlink(missing_ok=True)
    return target
