from __future__ import annotations

import time
import uuid

from .core import PROJECTS, Scene, Settings, read_json, set_status, write_json,digest
from .ingest import ingest
from .llm import make_script, unload
from .runtime import using_settings,model_runtime
from .project_trash import synchronized


@synchronized
def trash(path):
    from .core import worker_active
    root=PROJECTS.resolve();path=path.resolve()
    if path.parent!=root or worker_active(path):raise ValueError('Pause e aguarde o projeto antes de excluí-lo.')
    target=root/'.trash'/path.name
    if target.parent.resolve()!=root/'.trash':raise ValueError('Destino de lixeira inválido')
    target.parent.mkdir(exist_ok=True)
    if target.exists():raise ValueError('Já existe uma cópia deste projeto na lixeira.')
    write_json(path/'deleted.json',{'excluido_em':time.time()})
    path.rename(target)


@synchronized
def restore(pid):
    from .core import project_dir
    if not pid or any(c not in '0123456789abcdef-' for c in pid):raise ValueError('Identificador inválido')
    root=PROJECTS.resolve();source=(root/'.trash'/pid).resolve();target=root/pid
    if source.parent!=root/'.trash' or not (source/'project.json').is_file():raise FileNotFoundError('Projeto não está na lixeira')
    if (source/'purge-incomplete.json').is_file():raise ValueError('Parte dos arquivos já foi apagada. Esvazie a lixeira novamente para concluir a remoção.')
    if target.exists():raise ValueError('Já existe um projeto com esse identificador.')
    source.rename(target)
    (target/'deleted.json').unlink(missing_ok=True)
    return project_dir(pid)


@using_settings
def create(title, settings, files=(), text="", urls=(), *, topic='', favorite=None):
    from .reels_media import VIDEO_EXT,import_files
    videos=[f for f in files if f.suffix.lower() in VIDEO_EXT]
    files=[f for f in files if f.suffix.lower() not in VIDEO_EXT]
    if videos and (settings.tipo_video!='shorts' or settings.modo_shorts!='clipes'):
        raise ValueError('Para adicionar clipes, escolha Reels / Shorts e Fotos e clipes com narração.')
    if videos and not files and not text.strip() and not any(u.strip() for u in urls) and not topic.strip():
        raise ValueError('Descreva o assunto ou cole a narração. Os clipes são mídia visual; seu áudio original não vira fonte de roteiro.')
    if settings.roteiro_pronto and (settings.tipo_video!='shorts' or len(text.strip())<5):
        raise ValueError('Para usar narração pronta, escolha Reels / Shorts e cole o texto completo na aba Texto.')
    pid=str(uuid.uuid4())
    path=PROJECTS/pid
    path.mkdir(parents=True)
    info={"id":pid,"titulo":title.strip() or topic.strip()[:100] or "Novo vídeo", "criado":time.time(),"config":settings.model_dump(),
          'titulo_automatico':not bool(title.strip()),'titulo_manual':bool(title.strip())}
    if favorite:
        write_json(path/'favorite.json',favorite)
        info['favorito']={'id':favorite['id'],'nome':favorite['nome']}
    if topic.strip():write_json(path/'topic.json',{'assunto':topic.strip(),'pesquisa_pendente':False})
    write_json(path/"project.json",info)
    if settings.roteiro_pronto:write_json(path/'narracao-pronta.json',{'texto':text.strip()})
    set_status(path,"importando","Lendo fontes")
    try:
        if not files and not text.strip() and not any(u.strip() for u in urls) and topic.strip():
            (path/'assets').mkdir(exist_ok=True)
            write_json(path/'sources.json',{'fontes':[],'imagens':[],'imagens_meta':{}})
            write_json(path/'topic.json',{'assunto':topic.strip(),'pesquisa_pendente':True})
        else:ingest(path,files,text,urls)
        if videos:import_files(path,videos)
        set_status(path,"fontes_prontas","Fontes importadas. Gere o roteiro.")
    except Exception as exc:
        set_status(path,"erro",str(exc))
        raise
    return path


def generate(path, only=None):
    settings=Settings.model_validate(read_json(path/'project.json')['config'])
    started=time.monotonic()
    from .production_time import begin_script
    begin_script(path,only)
    with model_runtime(settings):
        scenes=_generate(path,only)
        from .runtime import local_model
        previous=read_json(path/'script-timing.json',{}) if only is not None else {}
        write_json(path/'script-timing.json',{'tempo_s':round(time.monotonic()-started+previous.get('tempo_s',0),2),
            'completo':only is None or previous.get('completo',False),'roteiro_hash':digest(scenes),
            'modelo':'Texto enviado' if settings.roteiro_pronto else local_model(settings) if settings.roteiro_provedor=='local' else settings.roteiro_modelo,
            'provedor':'manual' if settings.roteiro_pronto else settings.roteiro_provedor,'gerado_em':time.time()})
        return scenes


def _generate(path, only=None):
    info=read_json(path/"project.json")
    settings=Settings.model_validate(info["config"])
    def update(message,progress):
        if (path/"pause.request").exists():
            from .render import Paused
            raise Paused()
        set_status(path,"roteirizando",message,progress)
    try:
        if settings.roteiro_pronto:
            return _ready_script(path,info,only,update)
        sources=read_json(path/'sources.json',{}).get('fontes',[])
        topic=read_json(path/'topic.json',{}).get('assunto','')
        substantive=[s for s in sources if s['origem']!='Imagens das fontes' and s.get('texto','').strip()]
        if settings.tipo_roteiro=='motivacional':
            if topic and not substantive and settings.fonte_ia_automatica:
                from .source_ai import attach
                sources=attach(path,topic,settings,update)
        elif topic and not substantive:
            if settings.fonte_ia_automatica:
                from .source_ai import attach
                from .topics import collect_media,subject
                sources=attach(path,topic,settings,update)
                collect_media(path,subject(topic),update)
            else:
                from .topics import discover
                sources=discover(path,topic,update)
        elif topic and all(s.get('pesquisada') or s.get('gerada_por_ia') for s in substantive):
            from .topics import collect_media,subject
            collect_media(path,subject(topic),update)
        if only is None:
            scenes=make_script(path,sources,settings,update)
        else:
            scenes=read_json(path/"script.json")
            old=Scene.model_validate(scenes[only])
            sources=[s for s in sources if s["id"] in old.fontes] or sources
            generated=make_script(path,sources,settings,update,old.model_dump_json())[0]
            generated["apresentador"]=old.apresentador
            scenes[only]=generated
        from .favorites import apply_scene_styles
        if only is None:apply_scene_styles(path,scenes)
        else:apply_scene_styles(path,[scenes[only]],index=only)
        from .topic_media import assign
        assign(path,scenes if only is None else [scenes[only]])
        write_json(path/"script.json",scenes)
        from .research import sync_script
        sync_script(path,scenes)
        scheduled=read_json(path/'task.json',{}).get('tipo')=='render_youtube'
        if not scheduled and (info.get('titulo_automatico') or info.get('titulo_manual')):
            from .youtube import metadata
            copy=metadata(path,regenerate=True,use_ai=True,auto_title=info.get('titulo_automatico',False),
                          title=info['titulo'][:100] if info.get('titulo_manual') else '')
            if info.get('titulo_automatico'):
                info['titulo']=copy['titulo'];write_json(path/'project.json',info)
        teaching=read_json(path/('plano-motivacional.json' if settings.tipo_roteiro=='motivacional' else 'plano-didatico.json'),{})
        warning=bool(teaching.get('pendencias_para_revisao_humana') or teaching.get('aviso_tempo'))
        set_status(path,"revisao","Roteiro pronto. Confira os pontos da revisão didática." if warning else
                   "Roteiro motivacional planejado e pronto para sua avaliação." if settings.tipo_roteiro=='motivacional' else "Roteiro estudado, revisado e pronto para sua avaliação.",1)
        return scenes
    except Exception as exc:
        from .render import Paused
        set_status(path,"pausado" if isinstance(exc,Paused) else "erro",str(exc) or "Tarefa pausada")
        raise
    finally:
        if not settings.roteiro_pronto:unload()


def _ready_script(path,info,only,update):
    """Keep the user's words; splitting into scenes never asks an LLM to rewrite."""
    import re
    if only is not None:
        raise ValueError('Esta narração foi enviada pronta. Edite o texto da cena diretamente para preservar suas palavras.')
    raw=read_json(path/'narracao-pronta.json',{}).get('texto','').strip()
    if len(raw)<5:raise ValueError('Não há texto de narração pronta neste projeto. Cole o texto ao criar um novo Shorts.')
    update('Organizando a narração enviada, sem reescrever o texto',.25)
    pieces=[]
    # Split on complete paragraphs/sentences where possible, without dropping
    # punctuation or inserting narration. The scene model permits 3,000 chars.
    for paragraph in re.split(r'\n\s*\n',raw):
        remaining=paragraph.strip()
        while len(remaining)>2800:
            chunk=remaining[:2800]
            ends=list(re.finditer(r'[.!?]\s+',chunk))
            cut=ends[-1].end() if ends else chunk.rfind(' ')
            if cut<1:raise ValueError('Há uma palavra longa demais na narração. Confira o texto enviado.')
            pieces.append(remaining[:cut].strip());remaining=remaining[cut:].strip()
        if remaining:pieces.append(remaining)
    for index in range(len(pieces)-1,0,-1):
        if len(pieces[index])<5 or len(pieces[index-1])<5:
            pieces[index-1]+='\n\n'+pieces.pop(index)
    sources=read_json(path/'sources.json',{}).get('fontes',[])
    ids=[s['id'] for s in sources if s.get('origem')=='Texto enviado']
    scenes=[Scene(titulo=info['titulo'][:100] if len(pieces)==1 else f'Trecho {i+1}',narracao_ptbr=text,
                  texto_na_tela=[info['titulo'][:80]],fontes=ids,etapa='aula_curta',
                  duracao_estimada=max(1,len(text.split())/2.3)).model_dump()
            for i,text in enumerate(pieces)]
    write_json(path/'script.json',scenes)
    from .youtube import metadata
    metadata(path,regenerate=True,use_ai=False,title=info['titulo'][:100])
    set_status(path,'revisao','Narração pronta organizada. Suas palavras foram preservadas; revise antes de renderizar.',1)
    return scenes
