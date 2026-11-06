"""Painted expression assets on an articulated rig, with narration-aware framing."""
from functools import lru_cache
import math,re
from PIL import Image,ImageDraw,ImageOps,ImageChops,ImageFilter
from .core import ROOT,digest
from .cartoon import cast_for,background

ASSETS=ROOT/'overview/assets/illustrated'
INK='#493e38'
VERSION='illustrated-v2'


def expression(actor):
    explicit=actor.get('expressao','auto')
    if explicit!='auto':return explicit
    return 'reflexiva' if actor.get('acao')=='pensar' else 'serena'


@lru_cache(maxsize=1)
def heads():
    result={}
    for row,role in enumerate(['pessoa','idoso','mulher','menina','lobo']):
        cells=[Image.open(ASSETS/f'{role}-{mood}.png').convert('RGBA') for mood in ['serena','reflexiva','surpresa']]
        width=max(c.width for c in cells);height=max(c.height for c in cells)
        result[row]=[]
        for cell in cells:
            aligned=Image.new('RGBA',(width,height));aligned.paste(cell,((width-cell.width)//2,height-cell.height))
            result[row].append(ImageOps.contain(aligned,(175,207),Image.Resampling.LANCZOS))
    return result


@lru_cache(maxsize=1)
def asset_fingerprint():
    return digest(VERSION,[(p.name,digest(p.read_bytes().hex())) for p in sorted(ASSETS.glob('*.png'))])


def head_row(kind,name):
    if kind=='idoso':return 1
    if kind=='menina':return 3
    if kind=='lobo':return 4
    if re.search(r'vizinha|mulher|professora|cientista mulher|senhora|\bana\b|\bmaria\b',name,re.I):return 2
    return 0


def smooth(value):
    value=max(0,min(1,value));return value*value*(3-2*value)


def camera_pose(previous,current,local,length,enabled=True):
    """A bounded push-in eased from the preceding shot; text stays outside the lens."""
    def zoom(actors):
        if not enabled:return 1.
        if any(expression(a)=='reflexiva' for a in actors):return 1.17
        if any(expression(a)=='surpresa' for a in actors):return 1.09
        return 1.025
    p=smooth(local/min(1.8,max(.35,length*.45)))
    return zoom(previous)+(zoom(current)-zoom(previous))*p


def puppet(actor,t,local):
    from .painted_rig import painted_body
    row=head_row(actor.get('tipo','pessoa'),actor['nome'])
    role=['pessoa','idoso','mulher','menina','lobo'][row]
    image,bob,front=painted_body(role,actor.get('acao','gesticular'),t,actor.get('_previous_action'),smooth(local/.85))
    emotion=expression(actor);column={'serena':0,'reflexiva':1,'surpresa':2}[emotion]
    previous_emotion=actor.get('_previous_expression','serena')
    neutral,target=heads()[row][{'serena':0,'reflexiva':1,'surpresa':2}[previous_emotion]],heads()[row][column]
    face=Image.new('RGBA',(195,225));base=Image.new('RGBA',face.size)
    base.paste(neutral,((195-neutral.width)//2,225-neutral.height),neutral)
    face.paste(target,((195-target.width)//2,225-target.height),target)
    change=smooth(local/.8);face=Image.blend(base,face,change)
    tilt=(-2.5 if previous_emotion=='reflexiva' else 0)*(1-change)+(-2.5 if emotion=='reflexiva' else 0)*change
    face=face.rotate(tilt+.7*math.sin(t*.7),Image.Resampling.BICUBIC)
    image.paste(face,(152,round(bob)),face)
    if actor.get('acao')=='pensar' or actor.get('_previous_action')=='pensar':image.alpha_composite(front)
    if actor.get('acao')=='ler':
        d=ImageDraw.Draw(image)
        d.polygon([(193,415),(250,428),(310,415),(306,487),(250,501),(195,486)],fill='#c1a77a',outline=INK,width=4)
        d.polygon([(202,422),(250,434),(301,422),(299,477),(250,491),(205,478)],fill='#eee7cf',outline='#8d8067',width=2)
        d.line((250,434,250,490),fill='#8d8067',width=3)
    return image


class IllustratedStage:
    def __init__(self,animator):
        self.a=animator;self.backgrounds={}
        self.units=[]
        from .speech import phrases
        self.units=phrases(animator.scene['narracao_ptbr'])

    def actors(self,beat):
        actors=[dict(x) for x in cast_for(self.a.scene,beat)]
        phrase=self.units[min(beat['frase'],len(self.units)-1)].lower()
        for actor in actors:
            if actor.get('expressao','auto')=='auto':
                actor['expressao']='reflexiva' if actor.get('acao')=='pensar' or re.search(r'reflet|pensando|pensamento',phrase) else 'surpresa' if re.search(r'surpres|espant|assombr',phrase) else 'serena'
        return actors

    def position(self,actor,j,t):
        distance=0
        for beat in self.a.beats:
            if beat['inicio']>t:break
            previous=next((c for c in cast_for(self.a.scene,beat) if c['nome']==actor['nome']),None)
            if previous and previous.get('acao') in ('andar','correr'):
                distance+=max(0,min(t,beat['fim'])-beat['inicio'])*(.052 if previous['acao']=='correr' else .025)
        # Identity has a stable anchor even when the ordering of the cast changes.
        names=list(dict.fromkeys(p['nome'] for b in self.a.beats for p in cast_for(self.a.scene,b)))
        index=names.index(actor['nome'])
        base=.59 if len(names)==1 else [.27,.69,.48][index%3]
        travel=(base+distance-.13)%1.48
        return .13+(travel if travel<.74 else 1.48-travel),travel<.74

    def frame(self,t,beat,local,length):
        a=self.a;environment=beat.get('ambiente') or ('rua' if re.search(r'rua|caminha|vizinh',a.scene['narracao_ptbr'],re.I) else 'sala')
        if environment not in self.backgrounds:
            name='rua.png' if environment=='rua' else 'estudio.png' if environment in ('sala','escola','laboratorio') else None
            self.backgrounds[environment]=ImageOps.fit(Image.open(ASSETS/name).convert('RGB'),(a.w,a.h),Image.Resampling.LANCZOS) if name else background((a.w,a.h),environment)
        canvas=self.backgrounds[environment].copy();d=ImageDraw.Draw(canvas)
        actors=self.actors(beat);floor=a.h-(110 if len(actors)==1 and not a.portrait else 195);focus=(a.w/2,a.h*.43)
        index=a.beats.index(beat);previous=self.actors(a.beats[index-1]) if index else []
        for j,actor in enumerate(actors):
            location,facing=self.position(actor,j,t)
            height=(900 if len(actors)==1 else 700) if not a.portrait else (1240 if len(actors)==1 else 1000)
            if a.mobile:height=min(a.h-440,(a.content_right-a.margin)/max(1,len(actors))*1.65)
            if len(actors)>2:height*=.86
            old_actor=next((p for p in previous if p['nome']==actor['nome']),actor)
            actor['_previous_action']=old_actor.get('acao','gesticular')
            actor['_previous_expression']=expression(old_actor)
            sprite=puppet(actor,t,local);sprite=ImageOps.contain(sprite,(round(height*.55),round(height)),Image.Resampling.LANCZOS)
            if not facing:sprite=sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            x=round(a.margin+(a.content_right-a.margin)*location-sprite.width/2);y=round(floor-sprite.height*1040/1060)
            if a.mobile:x=max(a.margin,min(a.content_right-sprite.width,x))
            shadow=Image.new('RGBA',(a.w,a.h));ImageDraw.Draw(shadow).ellipse((x+sprite.width*.14,floor-8,x+sprite.width*.94,floor+12),fill=(51,43,28,68))
            shadow=shadow.filter(ImageFilter.GaussianBlur(9));canvas.paste(shadow,(0,0),shadow)
            canvas.paste(sprite,(x,y),sprite)
            if j==0 or expression(actor)=='reflexiva':focus=(x+sprite.width*.5,y+sprite.height*.3)
        zoom=camera_pose(previous,actors,local,length,a.camera_dynamic)
        if zoom!=1:
            cw,ch=a.w/zoom,a.h/zoom
            x=max(0,min(a.w-cw,focus[0]-cw/2));y=max(0,min(a.h-ch,focus[1]-ch/2))
            canvas=canvas.resize((a.w,a.h),Image.Resampling.BICUBIC,box=(x,y,x+cw,y+ch))
        # Titles and captions are composited after the lens, preserving their size.
        text_width=min(a.content_right-a.margin,round(a.w*.46)) if len(actors)==1 and not a.portrait else a.content_right-a.margin
        overlay=Image.new('RGBA',(min(a.w,text_width+a.margin*2),205))
        od=ImageDraw.Draw(overlay)
        for y in range(205):od.line((0,y,a.w,y),fill=(250,246,234,round(230*(1-y/205)**.65)))
        feather=Image.new('L',overlay.size,255);fd=ImageDraw.Draw(feather)
        for x in range(max(0,overlay.width-180),overlay.width):fd.line((x,0,x,205),fill=round(255*(overlay.width-1-x)/180))
        overlay.putalpha(ImageChops.multiply(overlay.getchannel('A'),feather))
        canvas.paste(overlay,(0,0),overlay)
        title=a.text(a.scene['titulo'],text_width,39,'#253c36',True)
        canvas.paste(title,(a.margin,30),title)
        if a.highlights:a.large_words(canvas,beat,local,length,188,text_width)
        a.paint_portrait(canvas,t,beat,local)
        return canvas
