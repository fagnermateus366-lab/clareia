"""Media-only grading and measured, local ASS caption templates."""
from PIL import ImageEnhance,ImageOps

VERSION='reels-styles-v1'
PRESETS={
    'impacto':dict(font='Arial Black',file='ariblk.ttf',size=72,upper=True,outline=6,shadow=2),
    'faixa_branca':dict(font='Arial',file='arialbd.ttf',size=68,upper=False,outline=12,shadow=0,box=True,primary='101010',background='FFFFFF'),
    'caixa_escura':dict(font='Arial',file='arialbd.ttf',size=68,upper=False,outline=12,shadow=0,box=True,background='161616'),
    'minimalista':dict(font='Segoe UI',file='segoeuib.ttf',size=66,upper=False,outline=2,shadow=2),
    'documental':dict(font='Georgia',file='georgiab.ttf',size=64,upper=False,outline=3,shadow=2),
    'neon':dict(font='Arial Black',file='ariblk.ttf',size=70,upper=True,outline=4,shadow=3,neon=True),
    'editorial':dict(font='Georgia',file='georgiab.ttf',size=66,upper=False,outline=14,shadow=0,box=True,primary='101010',background='F7F2E7'),
    'compacta':dict(font='Impact',file='impact.ttf',size=80,upper=True,outline=5,shadow=2),
}


def filter_frame(image,name):
    # Captions are burned by FFmpeg after this step; their colors never enter it.
    if name=='original':return image
    if name=='pb':return ImageOps.grayscale(image).convert('RGB')
    if name=='pb_contraste':return ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(1.28).convert('RGB')
    if name=='sepia':return ImageOps.colorize(ImageOps.grayscale(image),'#241a12','#f5dfb3')
    if name=='suave':return ImageEnhance.Contrast(ImageEnhance.Color(image).enhance(.82)).enhance(.9)
    if name=='cinema':image=ImageEnhance.Contrast(ImageEnhance.Color(image).enhance(.72)).enhance(1.12)
    if name in ('quente','frio','cinema'):
        shift=(7,1,-6) if name=='quente' else (-5,2,7)
        return image.point([min(255,max(0,i+s)) for s in shift for i in range(256)])
    raise ValueError('Filtro de Reels desconhecido.')


def ass_color(rgb):
    return '&H'+rgb[4:6]+rgb[2:4]+rgb[0:2]+'&'


def caption_colors(style,accent):
    preset=PRESETS[style]
    colors={'amarelo':'FFE14A','ciano':'31E6F5','branca':'FFFFFF','vermelho':'FF4545','verde':'80F064','roxo':'CD9AFF'}
    if preset.get('primary')=='101010':
        # Keep the selected color family legible on a white/paper panel.
        colors.update(amarelo='806000',ciano='00676F',branca='101010',vermelho='C31919',verde='27630A',roxo='6830A2')
    return ass_color(preset.get('primary','FFFFFF')),ass_color(colors[accent])
