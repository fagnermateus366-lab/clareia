"""Scene-specific art review notes, independent of the editable script and job status."""
import time

from .core import Scene,Settings,digest,read_json,write_json

FILE='scene-review-issues.json'


def signature(scene,settings):
    scene=Scene.model_validate(scene).model_dump()
    settings=Settings.model_validate(settings) if isinstance(settings,dict) else settings
    keys=('titulo','narracao_ptbr','texto_na_tela','etapa','prompt_visual','animacao','shotcraft_receita',
          'shotcraft_figuras','distribuicao_figuras','imagem','imagens_cena','usar_imagem','tipo_visual')
    config=settings.model_dump()
    return digest({k:scene[k] for k in keys},{k:v for k,v in config.items() if k.startswith('shotcraft_')},
                  settings.animacao,settings.tipo_video,settings.modo_shorts)


def issues(path,scenes=None,settings=None):
    scenes=read_json(path/'script.json',[]) if scenes is None else scenes
    settings=read_json(path/'project.json',{}).get('config',{}) if settings is None else settings
    result=[]
    for note in read_json(path/FILE,[]):
        index=note.get('indice')
        if isinstance(index,int) and 0<=index<len(scenes) and note.get('assinatura')==signature(scenes[index],settings):
            result.append({**note,'titulo':scenes[index]['titulo']})
    return result


def record(path,index,scene,settings,error):
    note={'indice':index,'cena':index+1,'titulo':scene['titulo'],'tipo':'direcao_arte',
          'mensagem':str(error),'detalhes':error.details,'assinatura':signature(scene,settings),'atualizado':time.time()}
    saved=[n for n in issues(path) if n['indice']!=index]
    write_json(path/FILE,[*saved,note])
    return note


def clear(path,indices):
    if not (path/FILE).exists():return
    saved=[n for n in issues(path) if n['indice'] not in indices]
    write_json(path/FILE,saved)


def sync_preview(parent,snapshot,*,validated=False):
    """An immutable preview may finish after editing; never mark a revised scene."""
    info=read_json(snapshot/'scene-preview.json',{})
    if info.get('parent_path')!=str(parent.resolve()):return
    scenes=read_json(snapshot/'script.json',[])
    cfg=read_json(snapshot/'project.json',{}).get('config',{})
    current=read_json(parent/'script.json',[])
    settings=read_json(parent/'project.json',{}).get('config',{})
    notes=issues(snapshot,scenes,cfg)
    relevant={*(n['indice'] for n in notes)}
    if validated:relevant.add(info['index'])
    matching={i for i in relevant if 0<=i<len(current) and i<len(scenes) and signature(current[i],settings)==signature(scenes[i],cfg)}
    saved=[n for n in issues(parent,current,settings) if n['indice'] not in matching]
    write_json(parent/FILE,[*saved,*(n for n in notes if n['indice'] in matching)])
