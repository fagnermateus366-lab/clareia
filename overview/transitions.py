"""Local presentation transitions; narration and caption timings stay unchanged."""
from typing import Literal
import math

from PIL import Image, ImageDraw

Transition = Literal['padrao','nenhuma','dissolver','escurecer','clarear','deslizar_esquerda',
    'deslizar_direita','deslizar_cima','deslizar_baixo','empurrar','revelar','revelar_cima',
    'circulo','diamante','persianas','xadrez','zoom','afastar','papel_amassado']

TRANSITIONS=[
    ('padrao','Padrão · entre cenas','Passagem suave somente na mudança de cena, sem efeito a cada frase ou figurinha.'),
    ('nenhuma','Sem transição · corte','Troca de cena direta.'),
    ('dissolver','Dissolver','Mistura gradual entre os dois contextos.'),
    ('escurecer','Passagem pelo preto','Escurece e revela o próximo contexto.'),
    ('clarear','Passagem pelo branco','Clareia e revela o próximo contexto.'),
    ('deslizar_esquerda','Deslizar para a esquerda','O próximo contexto entra pela direita.'),
    ('deslizar_direita','Deslizar para a direita','O próximo contexto entra pela esquerda.'),
    ('deslizar_cima','Deslizar para cima','O próximo contexto entra por baixo.'),
    ('deslizar_baixo','Deslizar para baixo','O próximo contexto entra por cima.'),
    ('empurrar','Empurrar','Os dois contextos se deslocam juntos.'),
    ('revelar','Revelação lateral','Uma faixa revela o próximo contexto.'),
    ('revelar_cima','Revelação vertical','Revela o próximo contexto de baixo para cima.'),
    ('circulo','Abertura circular','Um círculo se abre a partir do centro.'),
    ('diamante','Abertura em diamante','Uma forma geométrica revela o próximo contexto.'),
    ('persianas','Persianas','Faixas horizontais revelam o próximo contexto.'),
    ('xadrez','Mosaico','Blocos alternados formam o próximo contexto.'),
    ('zoom','Aproximar','O próximo contexto cresce suavemente.'),
    ('afastar','Afastar','O contexto anterior encolhe e desaparece.'),
    ('papel_amassado','Papel de caderno amassado','A folha se dobra e amassa, vira uma bola de papel e dá lugar a uma folha nova. Use 1,5 a 2 segundos para apreciar as dobras.'),
]


def transition_frame(old,new,style,progress):
    p=max(0.,min(1.,progress))
    if p>=1 or style in ('nenhuma','padrao'):return new.copy()
    if p<=0:return old.copy()
    if style=='papel_amassado':
        from .paper_transition import crumple
        return crumple(old,new,p)
    q=p*p*(3-2*p)
    w,h=new.size
    if style=='dissolver':return Image.blend(old,new,q)
    if style in ('escurecer','clarear'):
        color=Image.new('RGB',new.size,'black' if style=='escurecer' else 'white')
        return Image.blend(old,color,q*2) if q<.5 else Image.blend(color,new,q*2-1)
    out=old.copy()
    if style.startswith('deslizar_') or style=='empurrar':
        dx,dy=0,0
        if style in ('deslizar_esquerda','empurrar'):dx=round(w*(1-q))
        elif style=='deslizar_direita':dx=-round(w*(1-q))
        elif style=='deslizar_cima':dy=round(h*(1-q))
        else:dy=-round(h*(1-q))
        if style=='empurrar':out.paste(old,(-round(w*q),0))
        out.paste(new,(dx,dy));return out
    if style in ('zoom','afastar'):
        source=new if style=='zoom' else old
        scale=(.65+.35*q) if style=='zoom' else (1-.35*q)
        tile=source.resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.BICUBIC)
        layer=(old if style=='zoom' else new).copy()
        layer.paste(tile,((w-tile.width)//2,(h-tile.height)//2))
        return Image.blend(old,layer,q) if style=='zoom' else Image.blend(layer,new,q)
    mask=Image.new('L',new.size);d=ImageDraw.Draw(mask)
    if style=='revelar':d.rectangle((0,0,round(w*q),h),fill=255)
    elif style=='revelar_cima':d.rectangle((0,round(h*(1-q)),w,h),fill=255)
    elif style=='circulo':
        r=math.hypot(w,h)*q/2
        d.ellipse((w/2-r,h/2-r,w/2+r,h/2+r),fill=255)
    elif style=='diamante':
        r=(w+h)*q/2
        d.polygon([(w/2,h/2-r),(w/2+r,h/2),(w/2,h/2+r),(w/2-r,h/2)],fill=255)
    elif style=='persianas':
        for j in range(10):d.rectangle((0,round(j*h/10),w,round((j+q)*h/10)),fill=255)
    elif style=='xadrez':
        for row in range(6):
            for col in range(10):
                amount=max(0,min(1,q*2-((row+col)%2)))
                if amount:d.rectangle((round(col*w/10),round(row*h/6),round((col+amount)*w/10),round((row+1)*h/6)),fill=255)
    else:raise ValueError('Transição desconhecida: '+style)
    return Image.composite(new,old,mask)


def preview(style,root):
    if style not in {row[0] for row in TRANSITIONS}:raise ValueError('Transição desconhecida.')
    version='v1'
    if style=='papel_amassado':
        from .paper_transition import fingerprint
        version=fingerprint()[:12]
    path=root/'output/transition-previews'/(version+'-'+style+'.gif')
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        frames=[]
        from .visuals import font
        first=Image.new('RGB',(480,270),'#103b48');d=ImageDraw.Draw(first)
        d.rounded_rectangle((55,65,210,210),18,fill='#86e0bc')
        d.text((245,130),'Contexto A',font=font(24,True),fill='white')
        second=Image.new('RGB',(480,270),'#f6f2e9');d=ImageDraw.Draw(second)
        d.ellipse((275,65,420,210),fill='#087c69')
        d.text((65,130),'Contexto B',font=font(24,True),fill='#172c32')
        if style=='papel_amassado':
            from .paper_transition import material,printed
            first=Image.new('RGB',(480,270),'#f6f2e9');d=ImageDraw.Draw(first)
            d.text((80,40),'Primeiro assunto',font=font(27,True),fill='#172c32')
            d.ellipse((95,105,210,220),fill='#087c69')
            d.text((250,150),'Uma ideia',font=font(22,True),fill='#172c32')
            second=Image.new('RGB',first.size,'#f6f2e9');d=ImageDraw.Draw(second)
            d.text((80,40),'Um novo assunto',font=font(27,True),fill='#172c32')
            d.rounded_rectangle((95,105,210,220),14,fill='#087c69')
            d.text((250,150),'Outra ideia',font=font(22,True),fill='#172c32')
            first=printed(first,material(first.size)[0]);second=printed(second,material(second.size)[0])
        steps=36 if style=='papel_amassado' else 18
        for old,new in ((first,second),(second,first)):
            frames.extend([old]*8)
            frames.extend(transition_frame(old,new,style,j/steps) for j in range(steps+1))
            frames.extend([new]*8)
        from uuid import uuid4
        temporary=path.with_name(path.stem+'-'+uuid4().hex+'.partial.gif')
        try:
            frames[0].save(temporary,format='GIF',save_all=True,append_images=frames[1:],duration=50,loop=0)
            temporary.replace(path)
        finally:temporary.unlink(missing_ok=True)
    return path
