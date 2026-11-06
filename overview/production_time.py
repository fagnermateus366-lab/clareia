"""Wall-clock boundaries for the user's script → render → finished timeline."""
import time

from .core import read_json,write_json


def requested(path,at,job_id):
    write_json(path/'script-request.json',{'solicitado_em':at,'job_id':job_id})


def begin_script(path,only=None,now=None):
    if only is not None:return
    now=time.time() if now is None else now
    task=read_json(path/'task.json',{})
    request=read_json(path/'script-request.json',{})
    previous=read_json(path/'production-clock.json',{})
    # Resuming the same job preserves its original boundary.
    if previous.get('job_id') and previous['job_id']==task.get('job_id') and not previous.get('concluido_em'):return
    start=request.get('solicitado_em') if task.get('tipo')=='roteiro' and request.get('job_id')==task.get('job_id') else now
    if not isinstance(start,(float,int)) or start>now:start=now
    write_json(path/'production-clock.json',{'roteiro_solicitado_em':start,'estudo_iniciado_em':now,'job_id':task.get('job_id')})


def begin_render(path,now=None):
    now=time.time() if now is None else now
    clock=read_json(path/'production-clock.json',{})
    if not clock.get('render_iniciado_em'):
        clock['render_iniciado_em']=now
    clock.pop('concluido_em',None)
    write_json(path/'production-clock.json',clock)


def finish_render(path,now=None):
    now=time.time() if now is None else now
    clock=read_json(path/'production-clock.json',{})
    render=clock.get('render_iniciado_em');script=clock.get('roteiro_solicitado_em')
    render_time=round(now-render,2) if isinstance(render,(float,int)) and 0<=render<=now else None
    script_time=round(render-script,2) if isinstance(script,(float,int)) and isinstance(render,(float,int)) and 0<=script<=render else None
    clock['concluido_em']=now;write_json(path/'production-clock.json',clock)
    return {'roteiro_s':script_time,'renderizacao_s':render_time,
            'total_s':round(script_time+render_time,2) if script_time is not None and render_time is not None else None,
            'origem':'registrado','roteiro_inicio':script,'render_inicio':render,'fim':now}
