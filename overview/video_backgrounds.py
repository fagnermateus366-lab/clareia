"""Project-color stages can inherit or override their background per scene."""
from PIL import Image,ImageOps
from .core import digest,read_json

STYLES={'ilustracoes','recortes','tipografia','infografico'}

def style_for(scene,settings):
    chosen=scene.get('animacao','herdar')
    return settings.animacao if chosen=='herdar' else chosen

def supported(scene,settings):
    return style_for(scene,settings) in STYLES and not (settings.tipo_video=='shorts' and settings.modo_shorts in ('fotos','clipes'))

def selection(scene,settings):
    if not supported(scene,settings):return settings.estilo,None,settings.intensidade_fundo
    mode=scene.get('fundo_cena','herdar')
    color=scene.get('estilo_cena','herdar') if mode!='herdar' else 'herdar'
    color=settings.estilo if color=='herdar' else color
    photo=settings.imagem_fundo if mode=='herdar' else scene.get('imagem_fundo') if mode=='imagem' else None
    strength=scene.get('intensidade_fundo')
    return color,photo,settings.intensidade_fundo if strength is None or mode=='herdar' else strength

def resolve(path,name):
    allowed=read_json(path/'sources.json',{}).get('imagens',[])
    target=(path/'assets'/name).resolve()
    if name not in allowed or target.parent!=(path/'assets').resolve() or not target.is_file():
        raise ValueError('A imagem de fundo precisa pertencer às imagens deste projeto.')
    return target

def identity(scene,settings,path):
    if not supported(scene,settings):return None
    color,photo,strength=selection(scene,settings)
    if not photo and color==settings.estilo:return None
    return {'cor':color,'imagem':photo,'conteudo':digest(resolve(path,photo).read_bytes().hex()) if photo else None,
            'intensidade':strength if photo else None}

def canvas(scene,settings,path,size,color):
    _,photo,strength=selection(scene,settings)
    base=Image.new('RGB',size,color)
    if photo:
        with Image.open(resolve(path,photo)) as source:
            picture=ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'),size,Image.Resampling.LANCZOS)
        base=Image.blend(base,picture,strength)
    return base

def validate(scenes,settings,path):
    # Reject unavailable selections before writing or starting a render, even
    # if a scene currently has a proprietary background and ignores the option.
    for name in [settings.imagem_fundo,*[s.get('imagem_fundo') for s in scenes]]:
        if name:resolve(path,name)
