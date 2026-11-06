"""Immutable single-scene snapshots rendered by the existing serial worker."""
from pathlib import Path
import os
import shutil
import threading

from .core import ROOT,Settings,read_json,write_json,digest,set_status

LOCK=threading.RLock()
VERSION='scene-review-preview-v3-media-continuity'
STORE=ROOT/'output/scenes'


def cached_copy(source,target):
    try:os.link(source,target)
    except OSError:shutil.copy2(source,target)


def signature(path,index):
    info=read_json(path/'project.json');scenes=read_json(path/'script.json',[])
    if index<0 or index>=len(scenes):raise ValueError('Cena não encontrada. Gere ou salve o roteiro primeiro.')
    from .collage_assets import content_hash
    from .collage import VERSION as COLLAGE_VERSION
    from .diagram_layout import LAYOUT_VERSION
    sources=read_json(path/'sources.json',{})
    images=[]
    for name in sources.get('imagens',[])+sources.get('videos',[]):
        target=(path/'assets'/name).resolve()
        if target.parent!=(path/'assets').resolve() or not target.is_file():raise ValueError('Imagem não pertence ao projeto.')
        images.append((name,content_hash(target)))
    for person in (read_json(path/'pesquisa.json',{}) or {}).get('retratos',[]):
        name=person.get('arquivo','');target=(path/'assets'/name).resolve()
        if target.parent==(path/'assets').resolve() and target.is_file():images.append((name,content_hash(target)))
    start=0 if info['config'].get('modo_shorts') in ('fotos','clipes') and info['config'].get('continuar_clipes',True) else max(0,index-1)
    key=digest(VERSION,str(path.resolve()),COLLAGE_VERSION,LAYOUT_VERSION,index,len(scenes),scenes[start:index+1],info['config'],sources,images,read_json(path/'pronuncia.json',{}),read_json(path/'pesquisa.json'))
    if info['config'].get('animacao')=='shotcraft' or any(s.get('animacao')=='shotcraft' for s in scenes[start:index+1]):
        from .shotcraft import VERSION as SHOTCRAFT_VERSION
        from .shotcraft_remotion import fingerprint
        key=digest(key,SHOTCRAFT_VERSION,fingerprint())
    return key,info,scenes,sources


def directory(path,key):
    if len(key)!=24 or any(c not in '0123456789abcdef' for c in key):raise FileNotFoundError()
    target=STORE/key
    if read_json(target/'scene-preview.json',{}).get('parent_path')!=str(path.resolve()):raise FileNotFoundError()
    return target


def prepare(path,index):
    with LOCK:
        key,info,scenes,sources=signature(path,index)
        # Keep renderer cache filenames below Windows MAX_PATH even when the
        # user's project lives in a long OneDrive path.
        target=STORE/key
        if (target/'scene-preview.json').is_file():return key,target
        target.mkdir(parents=True,exist_ok=True)
        write_json(target/'project.json',info)
        write_json(target/'script.json',scenes)
        write_json(target/'sources.json',sources)
        write_json(target/'pronuncia.json',read_json(path/'pronuncia.json',{}))
        for filename in ('pesquisa.json','plano-didatico.json','plano-motivacional.json','fontes.md'):
            if (path/filename).is_file():shutil.copy2(path/filename,target/filename)
        assets=target/'assets';assets.mkdir(exist_ok=True)
        names=sources.get('imagens',[])+sources.get('videos',[])+[v['miniatura'] for v in sources.get('videos_meta',{}).values() if v.get('miniatura')]
        for name in names:
            source=(path/'assets'/name).resolve()
            if source.parent!=(path/'assets').resolve() or not source.is_file():raise ValueError('Mídia não pertence ao projeto.')
            cached_copy(source,assets/name)
        for person in (read_json(path/'pesquisa.json',{}) or {}).get('retratos',[]):
            name=person.get('arquivo','');original=(path/'assets'/name).resolve()
            if original.parent==(path/'assets').resolve() and original.is_file():shutil.copy2(original,assets/name)
        # Reuse planning/audio already prepared in this project; no scripts are regenerated.
        for folder in ('storyboard','audio'):
            if (path/'cache'/folder).is_dir():shutil.copytree(path/'cache'/folder,target/'cache'/folder,dirs_exist_ok=True,copy_function=cached_copy,ignore=shutil.ignore_patterns('*.partial*','*-raw.wav'))
        write_json(target/'scene-preview.json',{'index':index,'parent':path.name,'parent_path':str(path.resolve()),'parent_status':read_json(path/'status.json',{}),'parent_task':read_json(path/'task.json')})
        set_status(target,'revisao','Prévia pronta para gerar')
        return key,target


def run(path,key,renderer):
    target=directory(path,key);info=read_json(target/'scene-preview.json')
    settings=Settings.model_validate(read_json(target/'project.json')['config'])
    def update(message,progress):set_status(path,'renderizando',f"Prévia da cena {info['index']+1} · {message}",progress)
    from .scene_diagnostics import sync_preview
    from .shotcraft_figures import ArtDirectionError
    try:
        result=renderer(target,settings,callback=update,only_scene=info['index'],pause_file=path/'pause.request')
    except ArtDirectionError:
        sync_preview(path,target)
        raise
    if result.get('pausado'):
        set_status(path,'pausado','Prévia pausada. Use Retomar para continuar.');return
    sync_preview(path,target,validated=True)
    previous=info['parent_status'];state=previous.get('status')
    if state not in ('concluido','enviado_youtube','pausado'):state='revisao'
    set_status(path,state,f"Prévia da cena {info['index']+1} pronta. O vídeo completo foi preservado.",1)
    if info.get('parent_task'):write_json(path/'task.json',info['parent_task'])
    else:(path/'task.json').unlink(missing_ok=True)


def status(path,key):
    target=directory(path,key);info=read_json(target/'scene-preview.json');state=read_json(target/'status.json',{})
    ready=(target/'export/video.mp4').is_file()
    try:stale=signature(path,info['index'])[0]!=key
    except ValueError:stale=True
    return {'id':key,'cena':info['index'],'pronta':ready,'desatualizada':stale,'status':state.get('status','fila'),'mensagem':state.get('mensagem','Aguardando a vez'),'progresso':state.get('progresso',0),
            'url':f'/api/projects/{path.name}/scene-previews/{key}/video' if ready else None}
