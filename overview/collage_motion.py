"""Reusable animation rigs for every documentary sticker; no frame-time I/O."""
from __future__ import annotations

import math
from PIL import Image,ImageDraw,ImageFilter,ImageChops

VERSION='sticker-motion-v1'

# Every shipped figure has an explicit motion, rather than silently falling back
# to the same sway. New user/online images retain the gentle sticker motion.
GROUPS={
    'flight':('Voo suave','aviao foguete astronauta'),
    'sail':('Balanço de navegação','navio veleiro'),
    'drive':('Deslocamento e vibração','carro onibus caminhao trem bicicleta trator cadeira-rodas'),
    'flutter':('Flutuação e batimento do recorte','borboleta abelha'),
    'swim':('Ondulação e nado','peixe onda'),
    'water':('Gota e ondulações','gota-agua torneira'),
    'wind':('Pás girando, torre fixa','turbina-eolica'),
    'rotate':('Rotação contínua','engrenagem terra bola'),
    'heartbeat':('Pulsação','coracao'),
    'breathe':('Respiração suave','pulmoes cerebro esqueleto'),
    'plant':('Balanço ao vento','arvore folha trigo'),
    'twist':('Torção suave','dna'),
    'glow':('Luz e brilho suave','lampada painel-solar'),
    'signal':('Sinais em expansão','antena globo telefone celular radio roteador servidores'),
    'scan':('Varredura de luz','computador televisao chip camera microscopio telescopio'),
    'steam':('Vapor em movimento','fabrica vulcao petroleo cafe'),
    'bubble':('Bolhas em movimento','tubos-ensaio remedios seringa'),
    'pages':('Ondulação de páginas','livros jornal quadro-escolar'),
    'pendulum':('Oscilação de equilíbrio','balanca balanca-moedas'),
    'clock':('Ponteiro em movimento','relogio'),
    'step':('Balanço de caminhada','executivo multidao telefonista jaleco'),
    'vibrate':('Vibração rítmica','guitarra piano fones controle-jogo estetoscopio'),
    'bounce':('Pequenos saltos','dinheiro encomenda carrinho formatura urna claquete'),
    'tilt':('Inclinação com relevo','governo casa predio ponte cidade banco conteiner montanha caixa-geometrica cilindro carteira-escolar grafico'),
    'gleam':('Reflexo em movimento','martelo-juiz distintivo picareta acordo cadeado oculos dente primeiros-socorros'),
    'nod':('Balanço orgânico','vaca robo pao'),
}
PROFILES={ident:kind for kind,(_,ids) in GROUPS.items() for ident in ids.split()}


def motion_info(ident):
    kind=PROFILES.get(ident,'sticker')
    return {'id':kind,'nome':GROUPS[kind][0] if kind in GROUPS else 'Balanço suave de adesivo'}


def pose(ident,mode,t,phase=0):
    if mode=='nenhum':return 0.,0.,0.
    q=t+phase*.7
    if mode!='tematico':return 3*math.sin(q*.85),4*math.sin(q*1.15),1.15*math.sin(q*.8)
    kind=PROFILES.get(ident,'sticker')
    if kind=='wind':return 0.,0.,0.
    if kind=='flight':return 19*math.sin(q*.85),-12*math.sin(q*1.05),-2.4*math.cos(q*.85)
    if kind=='sail':return 7*math.sin(q*.65),8*math.sin(q*1.65),2.7*math.sin(q*1.2)
    if kind=='drive':return 17*math.sin(q*.9),1.8*math.sin(q*8),.35*math.sin(q*4)
    if kind=='flutter':return 12*math.sin(q*1.6),8*math.cos(q*2.1),3.2*math.sin(q*2)
    if kind=='swim':return 9*math.sin(q*1.1),5*math.cos(q*1.8),1.5*math.sin(q*1.4)
    if kind=='water':return 0.,8*math.sin(q*1.6),.6*math.sin(q*1.1)
    if kind=='plant':return 2*math.sin(q*.9),0.,2.2*math.sin(q*1.15)
    if kind=='pendulum':return 0.,1.5*math.sin(q),3.7*math.sin(q*1.7)
    if kind=='step':return 9*math.sin(q*.85),-3*abs(math.sin(q*3)),1.1*math.sin(q*3)
    if kind=='vibrate':return 1.5*math.sin(q*18),1.2*math.cos(q*15),.65*math.sin(q*12)
    if kind=='bounce':return 3*math.sin(q),-7*abs(math.sin(q*1.65)),1.7*math.sin(q*1.2)
    if kind=='tilt':return 2*math.sin(q*.7),3*math.sin(q*.95),1.6*math.sin(q*.75)
    if kind=='nod':return 4*math.sin(q*.8),3*math.sin(q*1.6),1.8*math.sin(q*1.4)
    if kind=='rotate':return 0.,0.,0.
    return 2.5*math.sin(q*.85),3*math.sin(q*1.15),.8*math.sin(q*.8)


class StickerRig:
    def __init__(self,image,ident,pivot=None):
        self.base=image;self.ident=ident;self.kind=PROFILES.get(ident,'sticker')
        self.box=image.getbbox() or (0,0,image.width,image.height)
        x1,y1,x2,y2=self.box
        self.pivot=pivot or ((x1+x2)/2,(y1+y2)/2)
        self.mask=image.getchannel('A')
        self.glow=None
        if self.kind=='glow':
            self.glow=Image.new('RGBA',image.size,'#e1b95c')
            self.glow.putalpha(self.mask.filter(ImageFilter.GaussianBlur(max(4,int(image.width*.024)))).point(lambda a:round(a*.48)))

    def scale(self,image,sx,sy,anchor=None):
        # Fixed output bounds protect adjacent figures and captions.
        ax,ay=anchor or self.pivot
        return image.transform(image.size,Image.Transform.AFFINE,
            (1/sx,0,ax*(1-1/sx),0,1/sy,ay*(1-1/sy)),Image.Resampling.BICUBIC)

    def wave(self,t,anchored=False):
        w,h=self.base.size;x1,y1,x2,y2=self.box
        mesh=[];steps=12
        for i in range(steps):
            a=round(i*h/steps);b=round((i+1)*h/steps)
            def offset(y):
                factor=max(0,min(1,(y2-y)/max(1,y2-y1))) if anchored else 1
                return w*.014*math.sin(t*2.2+y/max(1,h)*4)*factor
            da,db=offset(a),offset(b)
            mesh.append(((0,a,w,b),(da,a,db,b,w+db,b,w+da,a)))
        return self.base.transform((w,h),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)

    def frame(self,t,mode):
        if mode!='tematico':return self.base
        kind=self.kind;x1,y1,x2,y2=self.box;w=x2-x1;h=y2-y1;cx,cy=self.pivot
        image=self.base
        if kind=='rotate':
            speed=24 if self.ident=='terra' else 48 if self.ident=='bola' else 65
            return image.rotate(-t*speed,Image.Resampling.BICUBIC,center=self.pivot)
        if kind=='heartbeat':
            phase=(t*1.12)%1
            pulse=math.exp(-((phase-.15)/.065)**2)+.55*math.exp(-((phase-.32)/.075)**2)
            return self.scale(image,1+.035*pulse,1+.025*pulse)
        if kind=='breathe':
            breath=math.sin(t*1.55)
            return self.scale(image,1+.023*breath,1+.014*breath)
        if kind in ('plant','swim','pages','twist'):
            return self.wave(t,anchored=kind=='plant')
        if kind=='flutter':return self.scale(image,.92+.08*math.cos(t*15),1.)
        if kind=='glow':
            image=Image.new('RGBA',self.base.size)
            halo=self.glow.copy();halo.putalpha(halo.getchannel('A').point(lambda v:round(v*(.65+.3*math.sin(t*2)))))
            image.alpha_composite(halo);image.alpha_composite(self.base);return image
        overlay=Image.new('RGBA',self.base.size);draw=ImageDraw.Draw(overlay)
        if kind=='signal':
            for i in range(3):
                p=(t*.48+i/3)%1;r=min(w,h)*(.12+.38*p)
                alpha=round(125*math.sin(math.pi*p)**2)
                draw.arc((cx-r,cy-r,cx+r,cy+r),205,335,fill=(147,49,30,alpha),width=max(2,round(w*.007)))
        elif kind in ('scan','gleam'):
            p=(t*.32)%1
            xx=x1-30+(w+60)*p
            draw.polygon([(xx-10,y1),(xx+12,y1),(xx+w*.2,y2),(xx+w*.2-22,y2)],fill=(237,215,146,round(105*math.sin(math.pi*p)**2)))
            # Light travels over the object itself, never over empty space.
            overlay.putalpha(ImageChops.multiply(overlay.getchannel('A'),self.mask))
        elif kind=='steam':
            for i in range(4):
                p=(t*.38+i*.25)%1
                xx=cx+w*.12*math.sin(p*3+i);yy=y1+h*.22-h*.2*p
                r=max(2,w*(.018+.045*p))
                draw.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(81,72,55,round(85*math.sin(math.pi*p)**2)))
        elif kind=='bubble':
            for i in range(5):
                p=(t*.32+i*.2)%1;r=max(2,w*.012)
                xx=cx+w*.15*math.sin(i*2);yy=y1+h*(.76-.5*p)
                draw.ellipse((xx-r,yy-r,xx+r,yy+r),outline=(169,89,40,round(150*math.sin(math.pi*p)**2)),width=2)
        elif kind=='water':
            for i in range(2):
                p=(t*.65+i*.5)%1;rx=w*(.14+.27*p);ry=max(2,h*.025*p)
                draw.ellipse((cx-rx,y2-10-ry,cx+rx,y2-10+ry),outline=(68,106,112,round(130*math.sin(math.pi*p)**2)),width=2)
        elif kind=='clock':
            # A stylized second hand; no synthetic dates, numbers or data.
            angle=t*1.6-math.pi/2;r=min(w,h)*.2
            draw.line((cx,cy,cx+r*math.cos(angle),cy+r*math.sin(angle)),fill=(155,47,29,220),width=max(2,round(w*.008)))
            draw.ellipse((cx-3,cy-3,cx+3,cy+3),fill='#a13525')
        else:return image
        result=image.copy();result.alpha_composite(overlay);return result
