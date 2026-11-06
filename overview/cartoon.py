"""Original articulated 2D characters and layered settings for narrated stories."""
import math,re
from PIL import Image,ImageDraw
from .core import digest

INK='#353a38'


def cast_for(scene,beat):
    if beat.get('elenco'):return beat['elenco']
    text=scene['narracao_ptbr'].lower()
    cast=[]
    if 'chapeuzinho' in text:cast.append({'nome':'Chapeuzinho','tipo':'menina','acao':'andar'})
    if 'lobo' in text:cast.append({'nome':'Lobo','tipo':'lobo','acao':'observar'})
    if not cast:
        elder=bool(re.search(r'senhor|idoso|velho|avô|vizinho',text))
        scientist=bool(re.search(r'cientista|pesquisa|cern|berners',text))
        cast=[{'nome':'Personagem','tipo':'idoso' if elder else 'cientista' if scientist else 'pessoa','acao':'gesticular'}]
    return cast


def background(size,environment):
    w,h=size;im=Image.new('RGB',size,'#d5e6e9');d=ImageDraw.Draw(im);floor=h-240
    def poly(points,fill):d.polygon([(round(x*w),round(y*floor)) for x,y in points],fill=fill)
    if environment in ('sala','escola','laboratorio'):
        d.rectangle((0,0,w,floor),fill='#f1e9da');d.rectangle((0,floor,w,h),fill='#c6b496')
        for x in range(0,w,150):d.line((x,floor,x-120,h),fill='#b09d80',width=2)
        d.line((0,floor,w,floor),fill=INK,width=5)
        d.rounded_rectangle((w*.08,floor*.23,w*.36,floor*.65),15,fill='#c7e4e4',outline=INK,width=5)
        d.line((w*.22,floor*.23,w*.22,floor*.65),fill='#7c9c98',width=5)
        d.line((w*.08,floor*.44,w*.36,floor*.44),fill='#7c9c98',width=5)
        d.rounded_rectangle((w*.56,floor*.22,w*.94,floor*.64),12,fill='#285f54',outline=INK,width=6)
        for j in range(3):d.line((w*.61,floor*(.32+j*.09),w*(.87-j*.04),floor*(.32+j*.09)),fill='#c1d3bb',width=4)
        for x in [.05,.43,.93]:
            d.rectangle((w*x,floor*.8,w*(x+.04),floor),fill='#9d7860',outline=INK,width=3)
            d.ellipse((w*(x-.03),floor*.62,w*(x+.07),floor*.87),fill='#72956b',outline=INK,width=3)
        return im
    # Distant hills, then architectural/forest layers and the ground plane.
    poly([(0,.68),(.18,.53),(.4,.67),(.65,.5),(1,.65),(1,1),(0,1)],'#b5c9aa')
    if environment=='rua':
        for x,scale,color in [(-.08,.28,'#d9c99f'),(.27,.2,'#d5dcce'),(.57,.32,'#e9dbbc'),(.88,.27,'#cbd6ce')]:
            x1=w*x;x2=x1+w*scale;y1=floor*.4;y2=floor*.9
            d.rectangle((x1,y1,x2,y2),fill=color,outline=INK,width=4)
            d.polygon([(x1-20,y1),(x1+(x2-x1)*.5,y1-floor*.18),(x2+20,y1)],fill='#aa8d78',outline=INK,width=4)
            for part in [.18,.65]:
                wx=x1+(x2-x1)*part
                d.rectangle((wx,y1+floor*.09,wx+(x2-x1)*.17,y1+floor*.24),fill='#b4ced0',outline=INK,width=4)
                d.line((wx+(x2-x1)*.085,y1+floor*.09,wx+(x2-x1)*.085,y1+floor*.24),fill=INK,width=2)
            d.rectangle((x1+(x2-x1)*.42,y1+floor*.25,x1+(x2-x1)*.58,y2),fill='#9d8063',outline=INK,width=4)
        d.rectangle((0,floor*.88,w,floor),fill='#a4b68a')
        for x in range(0,w,55):
            y=floor*.8
            d.polygon([(x,y+15),(x+17,y),(x+34,y+15),(x+34,floor),(x,floor)],fill='#c4b08b',outline='#5b6250',width=3)
    else:
        for j,x in enumerate([.04,.23,.75,.94]):
            cx=w*x;cy=floor*(.48+.06*(j%2));r=min(w*.18,floor*.28)
            d.polygon([(cx-20,floor),(cx-12,cy),(cx+20,cy),(cx+35,floor)],fill='#957459',outline=INK,width=4)
            for dx,dy in [(-.5,0),(.45,-.1),(0,-.6),(.1,.3)]:
                d.ellipse((cx+dx*r-r*.65,cy+dy*r-r*.65,cx+dx*r+r*.65,cy+dy*r+r*.65),fill='#839d70' if j%2 else '#6f946b',outline='#4f6a52',width=3)
        poly([(0,.88),(.35,.88),(.5,.7),(.62,.7),(.6,1),(0,1)],'#c9bd99')
    d.rectangle((0,floor,w,h),fill='#d6d8cc' if environment=='rua' else '#a3b886')
    d.line((0,floor,w,floor),fill='#697367',width=4)
    if environment=='rua':
        for x in range(-100,w,250):d.line((x,floor,x-150,h),fill='#a0a99d',width=2)
        d.line((0,floor+130,w,floor+130),fill='#a0a99d',width=2)
    return im


def character(kind,action,phase,seed=0):
    """Jointed limbs, planted feet, expressive eyes and distinct costumes."""
    im=Image.new('RGBA',(420,640));d=ImageDraw.Draw(im)
    walking=action in ('andar','correr');cycle=phase*(6 if action=='correr' else 3.6)
    swing=math.sin(cycle) if walking else .12*math.sin(phase*1.7)
    bob=abs(math.sin(cycle))*5 if walking else math.sin(phase*1.5)*2
    skin='#e6ad8c' if kind!='lobo' else '#9aa8a2';shirt='#b57c55' if kind=='idoso' else '#e4ece7' if kind=='cientista' else '#c54b43' if kind=='menina' else ['#6c9e9d','#ab806a','#7f9469','#8997b2'][seed%4]
    pants='#b59a5c' if kind=='idoso' else '#43596c';head_y=157+bob
    def ellipse(box,fill,width=6):d.ellipse(box,fill=fill,outline=INK,width=width)
    def limb(points,color,width):
        d.line(points,fill=INK,width=width+8,joint='curve');d.line(points,fill=color,width=width,joint='curve')
        for x,y in points[1:-1]:d.ellipse((x-width/2,y-width/2,x+width/2,y+width/2),fill=color)
    # Rear leg/arm, then body, then the near leg and arm.
    for side in [-1,1]:
        hx=210+side*22;fx=210+side*swing*62;fy=578-max(0,side*math.cos(cycle))*18 if walking else 578
        limb([(hx,410+bob),(hx+side*swing*25,493),(fx,fy)],pants,43)
        d.rounded_rectangle((fx-28,fy-7,fx+55,fy+25),14,fill='#545a53',outline=INK,width=6)
    if kind=='menina':d.polygon([(156,244+bob),(267,244+bob),(310,460),(115,460)],fill='#b9383a',outline=INK,width=7)
    d.rounded_rectangle((150,263+bob,272,424+bob),24,fill=shirt,outline=INK,width=7)
    d.polygon([(153,271+bob),(191,303+bob),(211,267+bob),(230,303+bob),(267,273+bob)],fill='#d9d2b5',outline=INK,width=4)
    if kind=='cientista':
        d.line((211,302+bob,211,422+bob),fill='#657c78',width=4)
        d.rectangle((230,337+bob,258,373+bob),outline='#657c78',width=4)
    if kind=='idoso':
        for x in [162,250]:d.line((x,306+bob,x,414+bob),fill='#795a42',width=5)
        d.rectangle((234,355+bob,258,391+bob),outline='#795a42',width=3)
    for side in [-1,1]:
        shoulder=(210+side*61,286+bob);elbow=(210+side*(85+swing*15),352+bob)
        hand=(210+side*(79-swing*43),407+bob)
        if side==1 and action in ('gesticular','apontar','conversar'):
            elbow=(307,311+bob);hand=(333+8*math.sin(phase*2),231+18*math.sin(phase*2))
        if side==1 and action=='pensar':elbow=(303,338);hand=(264,217+bob)
        if action=='ler':elbow=(210+side*77,334);hand=(210+side*32,358)
        limb([shoulder,elbow,hand],shirt,31);ellipse((hand[0]-19,hand[1]-20,hand[0]+19,hand[1]+20),skin,5)
    d.rectangle((192,227+bob,231,280+bob),fill=skin,outline=INK,width=5)
    if kind=='lobo':
        d.polygon([(144,112+bob),(141,30+bob),(201,87+bob),(257,79+bob),(303,38+bob),(293,139+bob)],fill=skin,outline=INK,width=7)
    ellipse((126,71+bob,295,244+bob),skin)
    ellipse((111,144+bob,145,190+bob),skin,5)
    if kind=='menina':
        d.arc((111,48+bob,309,269+bob),178,352,fill='#a92f36',width=25)
        d.polygon([(135,100+bob),(160,55+bob),(255,51+bob),(285,108+bob),(234,89+bob)],fill='#b9383a',outline=INK,width=5)
    elif kind=='idoso':
        for x,y in [(142,90),(151,77),(162,70),(272,87),(285,111)]:ellipse((x-16,y+bob-10,x+15,y+bob+28),'#d5d1bd',3)
        d.arc((180,192+bob,237,224+bob),190,330,fill='#a06c58',width=2)
    elif kind!='lobo':d.pieslice((131,64+bob,288,162+bob),180,352,fill='#665047',outline=INK,width=5)
    blink=phase%4.1<.12
    for x in [184,247]:
        d.arc((x-17,122+bob,x+13,138+bob),180,345,fill=INK,width=4)
        if blink:d.line((x-7,159+bob,x+7,159+bob),fill=INK,width=4)
        else:ellipse((x-5,148+bob,x+6,164+bob),INK,1)
    d.arc((213,158+bob,232,186+bob),275,440,fill='#9d6b56' if kind!='lobo' else INK,width=3)
    if kind=='lobo':
        ellipse((220,177+bob,302,225+bob),'#c7d0c3',5);ellipse((278,177+bob,302,195+bob),INK,2)
    else:d.arc((194,192+bob,250,218+bob),5,170,fill=INK,width=4)
    if kind=='cientista':
        for x in [183,246]:d.rounded_rectangle((x-21,139+bob,x+20,170+bob),9,outline=INK,width=4)
        d.line((204,153+bob,224,153+bob),fill=INK,width=3)
    if action=='ler':
        d.polygon([(162,339),(210,350),(259,339),(254,392),(211,403),(167,391)],fill='#e5cf8e',outline=INK,width=5)
        d.line((210,350,211,401),fill=INK,width=3)
    return im


class StoryStage:
    def __init__(self,animator):self.a=animator;self.backgrounds={}
    def frame(self,t,beat,local,length):
        a=self.a;environment=beat.get('ambiente') or ('floresta' if re.search(r'floresta|lobo|chapeuzinho',a.scene['narracao_ptbr'],re.I) else 'rua' if re.search(r'rua|caminh|vizinho',a.scene['narracao_ptbr'],re.I) else 'sala')
        if environment not in self.backgrounds:self.backgrounds[environment]=background((a.w,a.h),environment)
        canvas=self.backgrounds[environment].copy();d=ImageDraw.Draw(canvas)
        floor=a.h-(150 if a.mobile else 240);cast=cast_for(a.scene,beat)
        lane_width=(a.content_right-a.margin)/max(1,len(cast))
        stage_top=310
        if a.highlights:
            header=a.text(beat['titulo'],a.content_right-a.margin-20,54 if a.portrait else 57,bold=True)
            stage_top=max(stage_top,170+20+header.height+24)
        for j,actor in enumerate(cast):
            action=actor.get('acao','gesticular');name=actor.get('nome','Personagem');kind=actor.get('tipo','pessoa')
            distance=0
            for b in a.beats:
                if b['inicio']>t:break
                active=next((c for c in cast_for(a.scene,b) if c['nome']==name),None)
                if active and active.get('acao') in ('andar','correr'):
                    distance+=max(0,min(t,b['fim'])-b['inicio'])*(.065 if active['acao']=='correr' else .035)
            base=.19+j*.34;travel=(base+distance) % 1.36;position=.12+(travel if travel<=.68 else 1.36-travel)
            facing=travel<=.68
            height=min(590 if not a.portrait else 720,floor-stage_top,(lane_width-30)*640/420)
            sprite=character(kind,action,t,int(digest(name)[:8],16));sprite=sprite.resize((round(sprite.width*height/640),round(height)),Image.Resampling.BICUBIC)
            if not facing:sprite=sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            x=round(a.margin+(a.content_right-a.margin)*position-sprite.width/2);y=round(floor-sprite.height+height*.058)
            if len(cast)>1:
                # Keep the existing walk/gesture phase inside a separate lane
                # for each actor, including the complete name below their feet.
                travel_fraction=(position-.12)/.68
                x=round(a.margin+j*lane_width+15+(lane_width-sprite.width-30)*travel_fraction)
            d.ellipse((x+sprite.width*.2,floor-9,x+sprite.width*.95,floor+16),fill='#899586')
            canvas.paste(sprite,(x,y),sprite)
            if name!='Personagem':
                label=a.text(name,min(360,sprite.width+60,lane_width-30),27,'#263b38',True)
                used=label.getbbox()[2]
                px=round(max(a.margin+j*lane_width+12,
                             min(x+(sprite.width-used)/2,a.margin+(j+1)*lane_width-used-12)))
                d.rounded_rectangle((px-10,floor+37,px+used+10,floor+37+label.height),8,fill='#f7f4e9')
                canvas.paste(label,(px,floor+37),label)
        title=a.text(a.scene['titulo'],a.content_right-a.margin,48,'#263b38',True)
        d.rectangle((0,0,a.w,145),fill='#f7f4e9');canvas.paste(title,(a.margin,55),title)
        if a.highlights:a.large_words(canvas,beat,local,length,270,a.content_right-a.margin)
        a.paint_portrait(canvas,t,beat,local)
        return canvas
