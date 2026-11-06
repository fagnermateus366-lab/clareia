"""Illustrated motion graphics. Frames stream to FFmpeg; no per-frame disk files."""
from __future__ import annotations

from bisect import bisect_right
import math
import hashlib
import re

from PIL import Image, ImageDraw, ImageOps

from .core import digest, read_json
from .diagram_layout import DATE_PATTERN, LAYOUT_VERSION, diagram_layout
from .transitions import transition_frame
from .visuals import PALETTES, font, fit, draw_lines, wrap, match_contextual_image


def ease(t):
    t = max(0., min(1., t))
    return 1 - (1-t)**3


def drawing_timing(length, count, speed):
    """Reserve an entrance and a reading hold; never carry ink into the next phrase."""
    start=min(.45,length*.08)
    hold=min(1.2,length*.18)
    slot=max(.01,(length-start-hold)/max(1,count))*(.5/speed)
    return start,slot


def icon(draw, kind, cx, cy, r, color, ink, phase=0.):
    """Small, authorial vector illustrations, drawn at the output resolution."""
    def pts(values):
        return [(cx+x*r, cy+y*r) for x,y in values]
    def line(values, width=4, fill=None):
        draw.line(pts(values), fill=fill or ink, width=max(2,round(width*r/64)), joint='curve')
    def ellipse(box, fill=None, outline=None, width=4):
        draw.ellipse((cx+box[0]*r,cy+box[1]*r,cx+box[2]*r,cy+box[3]*r),
                     fill=fill, outline=outline, width=max(2,round(width*r/64)))
    def rect(box, fill=None, outline=ink, radius=.1):
        draw.rounded_rectangle((cx+box[0]*r,cy+box[1]*r,cx+box[2]*r,cy+box[3]*r),
                               radius=r*radius,fill=fill,outline=outline,width=max(2,round(4*r/64)))
    if kind == 'computador':
        rect((-.8,-.6,.8,.4), color)
        line([(-.8,.18),(.8,.18)]); line([(0,.4),(0,.75),(-.45,.75),(.45,.75)])
        line([(-.55,-.35),(-.22,-.35)],3); line([(-.55,-.14),(.45,-.14)],3)
        # Activity inside the screen is independent of object entrance.
        px=-.45+(phase*.34)%1*.85
        rect((px,-.48,px+.12,-.4),ink,ink,radius=.01)
    elif kind == 'globo':
        ellipse((-.8,-.8,.8,.8),color,ink)
        meridian=.15+.42*abs(math.cos(phase*.65))
        ellipse((-meridian,-.8,meridian,.8),None,ink,3)
        line([(-.8,0),(.8,0)],3); line([(-.65,-.43),(.65,-.43)],2); line([(-.65,.43),(.65,.43)],2)
    elif kind in ('professor','pensador','leitor','celular','personagem'):
        ellipse((-.3,-.95,.3,-.36),None,ink,3)
        line([(0,-.36),(0,.45),(-.45,.95)],3);line([(0,.45),(.45,.95)],3)
        gesture=.12*math.sin(phase*2)
        if kind=='pensador':
            line([(0,-.14),(.45,.05),(.26,-.4)],3);line([(0,-.1),(-.45,.3)],3)
            for x,y,s in [(.4,-1,.07),(.65,-1.25,.1),(.97,-1.5,.16)]:ellipse((x-s,y-s,x+s,y+s),None,ink,2)
        elif kind=='leitor':
            line([(0,-.12),(-.5,.15),(-.35,.4)],3);line([(0,-.12),(.5,.15),(.35,.4)],3)
            rect((-.4,.15,.4,.58),None,ink,.03);line([(0,.15),(0,.58)],2)
        elif kind=='celular':
            line([(0,-.12),(.45,.2),(.65,-.18+gesture)],3);line([(0,-.12),(-.45,.25)],3)
            rect((.5,-.5+gesture,.77,-.12+gesture),None,ink,.03)
        else:
            line([(0,-.12),(.5,-.1),(.95,-.62+gesture)],3);line([(0,-.12),(-.55,.25+gesture)],3)
        ellipse((-.13,-.73,-.07,-.67),ink);ellipse((.07,-.73,.13,-.67),ink)
        draw.arc((cx-.12*r,cy-.68*r,cx+.14*r,cy-.45*r),0,160,ink,max(2,round(r*.035)))
    elif kind == 'pessoa':
        ellipse((-.34,-.85,.34,-.16),color,ink)
        draw.arc((cx-.68*r,cy-.1*r,cx+.68*r,cy+1.1*r),180,360,ink,max(3,round(r*.07)))
        line([(-.68,.5),(-.68,.8),(.68,.8),(.68,.5)])
        line([(.4,.12),(.9,-.1+.12*math.sin(phase*2))],4)
    elif kind == 'mensagem':
        rect((-.85,-.65,.85,.38),color)
        line([(-.5,.38),(-.5,.8),(-.04,.38)])
        for j,x in enumerate((-.4,0,.4)):
            y=-.15-.08*math.sin(phase*3-j)
            ellipse((x-.07,y-.07,x+.07,y+.07),ink)
    elif kind == 'cerebro':
        for x,y in [(-.35,-.35),(.35,-.35),(-.45,.17),(.45,.17),(0,-.55)]:
            ellipse((x-.4,y-.35,x+.4,y+.4),color,ink,3)
        line([(0,-.58),(0,.55)],3); line([(-.5,-.1),(-.23,-.1),(-.2,.2)],3)
        line([(.52,-.15),(.27,-.15),(.27,.18)],3)
    elif kind == 'engrenagem':
        for j in range(8):
            a=j*math.pi/4+phase*.15
            line([(math.cos(a)*.52, math.sin(a)*.52),(math.cos(a)*.88,math.sin(a)*.88)],12)
        ellipse((-.64,-.64,.64,.64),color,ink)
        ellipse((-.23,-.23,.23,.23),None,ink)
    elif kind == 'escudo':
        draw.polygon(pts([(-.7,-.6),(0,-.85),(.7,-.6),(.6,.28),(0,.85),(-.6,.28)]), fill=color)
        line([(-.7,-.6),(0,-.85),(.7,-.6),(.6,.28),(0,.85),(-.6,.28),(-.7,-.6)])
        line([(-.32,0),(-.06,.25),(.38,-.25)],5)
    elif kind == 'relogio':
        ellipse((-.8,-.8,.8,.8),color,ink)
        a=-math.pi/2+phase*.25
        line([(0,0),(.48*math.cos(a),.48*math.sin(a))],4); line([(0,0),(.35,.2)],4)
    elif kind == 'folha':
        ellipse((-.55,-.8,.65,.6),color,ink)
        line([(-.55,.85),(.35,-.4)],4); line([(-.05,.15),(.4,.13)],3)
    elif kind == 'moeda':
        ellipse((-.8,-.8,.8,.8),color,ink); ellipse((-.59,-.59,.59,.59),None,ink,2)
        line([(.3,-.4),(-.25,-.4),(-.25,0),(.25,0),(.25,.4),(-.3,.4)],3); line([(0,-.6),(0,.6)],3)
    elif kind == 'lampada':
        ellipse((-.57,-.75,.57,.38),color,ink); rect((-.28,.3,.28,.73),color,radius=.04)
        line([(-.2,.9),(.2,.9)],3)
        for a in [-2.8,-2.1,-1.05,-.3]:
            line([(math.cos(a)*.85,math.sin(a)*.85),(math.cos(a)*1.08,math.sin(a)*1.08)],3)
    elif kind == 'livro':
        rect((-.88,-.66,.88,.68),color); line([(0,-.66),(0,.68)],3)
        for y in [-.35,-.08,.19]:
            line([(-.65,y),(-.22,y)],2); line([(.22,y),(.65,y)],2)
    else:
        rect((-.6,-.82,.6,.82),color)
        for y in [-.38,-.08,.22,.5]: line([(-.37,y),(.37,y)],3)


class Animator:
    def __init__(self, scene, settings, index, total, beats, path, images, *, canvas_size=None, mobile=False):
        self.mobile = mobile
        self.mobile_layout = settings.composicao_shorts
        self.w,self.h = canvas_size or ((1920,1080) if settings.formato=='16:9' else (1080,1920))
        self.portrait = self.h>self.w
        self.bg,self.card,self.fg,self.accent,self.muted = PALETTES[settings.estilo]
        self.style=scene.get('animacao','herdar')
        if self.style=='herdar':self.style=settings.animacao
        from .video_backgrounds import selection,canvas as background_canvas,identity as background_identity
        from .video_palettes import PALETTES as VIDEO_PALETTES
        self.bg,self.card,self.fg,self.accent,self.muted=VIDEO_PALETTES[selection(scene,settings)[0]]
        from .caption_presentation import large_enabled
        self.highlights=settings.destaques_animados and large_enabled(settings)
        self.hand_speed=settings.velocidade_mao
        self.camera_dynamic=settings.camera_dinamica
        self.figure_movement=settings.movimento_figuras
        self.animate=scene.get('animar_elementos')
        if self.animate is None:self.animate=settings.animar_elementos
        self.static_image=settings.imagem_estatica
        self.transition=scene.get('transicao','herdar')
        if self.transition=='herdar':self.transition=settings.transicao
        self.transition_duration=scene.get('duracao_transicao') or settings.duracao_transicao
        if self.style=='colagem_documental':
            from .collage_pacing import passage_duration
            self.transition_duration=passage_duration(self.transition,self.transition_duration)
        self.transition_scope=settings.aplicar_transicao
        self.previous_frame=None
        self.previous_collage=None
        self.asset_box=None
        self.asset_name=None
        if self.style in ('quadro','mao','historia','historia_ilustrada'):
            self.bg,self.card,self.fg,self.accent,self.muted='#fcfaf5','#eeeae0','#242b2a','#176b52','#70766f'
        self.scene=scene
        self.hand=None
        if self.style=='mao':
            from .core import ROOT
            self.hand=Image.open(ROOT/'overview/assets/mao-marcador.png').convert('RGBA')
            self.hand.thumbnail((420,420) if not self.portrait else (360,360))
        self.beats = beats
        self.starts = [b['inicio'] for b in beats]
        self.background_key=background_identity(scene,settings,path)
        self.base = background_canvas(scene,settings,path,(self.w,self.h),self.bg)
        d=ImageDraw.Draw(self.base)
        portrait_key=[]
        portrait=None
        if settings.pesquisa_externa and settings.retratos_autores:
            for person in read_json(path/'pesquisa.json',{}).get('retratos',[]):
                if person['pessoa'].casefold() not in scene['narracao_ptbr'].casefold():continue
                asset=(path/'assets'/person['arquivo']).resolve()
                if asset.parent!=(path/'assets').resolve() or not asset.is_file():continue
                portrait=(person,asset)
                portrait_key=[person,digest(asset.read_bytes().hex())]
                break
        self.author_portrait=bool(portrait)
        self.person=portrait[0] if portrait else None
        self.person_image=Image.open(portrait[1]).convert('RGB') if portrait else None
        self.margin=36 if self.mobile else 76 if self.portrait else 100
        m=self.margin
        self.content_right=self.w-m-(460 if portrait and not self.portrait else 0)
        # Quiet drafting grid supports the illustrated, explanatory composition.
        for x in range(0,self.w,60): d.line((x,0,x,self.h-150),fill=self.card,width=1)
        for y in range(180,self.h-150,60): d.line((0,y,self.w,y),fill=self.card,width=1)
        title_width=(self.w-2*m-350) if portrait and self.portrait else self.w-2*m
        f,lines,s=fit(d,scene['titulo'],title_width,2,54,True)
        end=draw_lines(d,(m,65),lines,f,s,self.fg)
        self.top=max(320,end+150) if not self.portrait else max(700 if portrait else 410,end+140)
        self.bottom=self.h-250
        if self.mobile:self.top=max(330,end+120);self.bottom=self.h-70
        self.portrait_box=None
        if portrait:
            self.portrait_box=(self.w-m-300,85,300,375) if self.portrait else (self.w-m-380,self.top-65,360,450)
            if self.mobile:self.top=max(self.top,650)
        self.asset=None
        backdrop_name=selection(scene,settings)[1]
        reference_images=images if scene.get('imagem') else [name for name in images if name!=backdrop_name]
        selected=match_contextual_image(scene,reference_images,path,settings.modo_visual,index)
        use_image=scene['tipo_visual']=='imagem_do_usuario' or settings.modo_visual=='imagem_do_usuario'
        if use_image and not reference_images:
            raise ValueError('Este modo precisa de uma imagem ou página de PDF na fonte.')
        asset_hash=''
        if selected:
            self.asset_name=selected
            target=(path/'assets'/selected).resolve()
            if target.parent != (path/'assets').resolve() or not target.is_file():
                raise ValueError('Imagem não pertence ao projeto')
            asset_hash=digest(target.read_bytes().hex())
            self.asset=ImageOps.exif_transpose(Image.open(target)).convert('RGBA' if self.style in ('colagem_documental','shotcraft') else 'RGB')
        self.key=digest('motion-v10-scene-passages',self.style,self.hand_speed if self.style=='mao' else None,self.highlights,scene['titulo'],scene.get('fontes'),settings.estilo,settings.formato,
                        index,total,[{k:v for k,v in b.items() if k not in ('inicio','fim')} for b in beats],selected,asset_hash)
        if self.background_key:self.key=digest(self.key,'video-background-v1',self.background_key)
        if portrait_key:self.key=digest(self.key,portrait_key)
        if self.mobile:self.key=digest(self.key,'mobile-stage-v2-balanced',canvas_size,self.mobile_layout)
        if portrait_key and self.style!='historia_ilustrada':self.key=digest(self.key,'stable-portrait-v1',self.static_image)
        if self.style=='historia':self.key=digest(self.key,'cartoon-v2')
        if self.style=='historia_ilustrada':
            from .illustrated import asset_fingerprint
            self.key=digest(self.key,asset_fingerprint(),self.camera_dynamic)
        if self.style!='historia_ilustrada':self.key=digest(self.key,LAYOUT_VERSION)
        if self.transition!='padrao' or not self.animate:
            self.key=digest(self.key,'transitions-v1',self.transition,self.transition_duration,self.transition_scope,self.animate)
        if self.transition=='papel_amassado':
            from .paper_transition import fingerprint
            self.key=digest(self.key,fingerprint())
        if self.asset is not None and self.style!='historia_ilustrada':
            self.key=digest(self.key,'stable-reference-v1',self.static_image)
        self.textures={}
        self.layouts={}
        self.story=None
        if self.style=='historia':
            from .cartoon import StoryStage
            self.story=StoryStage(self)
        elif self.style=='historia_ilustrada':
            from .illustrated import IllustratedStage
            self.story=IllustratedStage(self)
        elif self.style=='colagem_documental':
            from .collage import CollageStage
            self.story=CollageStage(self,path)
        elif self.style=='shotcraft':
            from .shotcraft_remotion import ShotcraftStage
            self.story=ShotcraftStage(self,settings,path)

    def close(self):
        if self.style=='shotcraft' and self.story:self.story.close()

    def diagram_top(self,beat):
        width=self.content_right-self.margin
        if self.style=='tipografia':
            from .speech import phrases
            units=phrases(self.scene['narracao_ptbr'])
            words=units[min(beat['frase'],len(units)-1)].split()
            heights=[self.text(' '.join(words[i:i+4]),width-20,76 if self.portrait else 88,bold=True,max_lines=3).height
                     for i in range(0,len(words),4)]
            return self.top+max(290 if self.portrait else 250,77+max(heights,default=0))
        size=(54 if self.portrait else 57) if self.highlights else (48 if self.portrait else 46)
        height=self.text(beat['titulo'],width-20 if self.highlights else width,size,bold=True).height
        return max(self.top,self.top-100+20+height+32 if self.highlights else self.top-95+25+height+24)

    def set_previous(self,frame,collage=None):
        if self.transition!='nenhuma':
            self.previous_frame=frame
            self.previous_collage=collage
            self.key=digest(self.key,'previous-context',hashlib.sha256(frame.tobytes()).hexdigest())

    def text(self, text, width, size, color=None, bold=False, max_lines=2):
        key=(text,int(width),size,color,bold,max_lines)
        if key not in self.textures:
            scratch=Image.new('RGBA',(int(width),300))
            d=ImageDraw.Draw(scratch)
            if size<=22:
                face=font(size,bold)
                lines=wrap(d,text,face,width)
                if len(lines)>max_lines:lines=lines[:max_lines-1]+[lines[max_lines-1].rstrip(' .')+'…']
            else:face,lines,size=fit(d,text,width,max_lines,size,bold)
            height=math.ceil(size*1.32*len(lines))+8
            layer=Image.new('RGBA',(int(width),height))
            draw_lines(ImageDraw.Draw(layer),(0,0),lines,face,size,color or self.fg)
            self.textures[key]=layer
        return self.textures[key]

    def connection(self,d,a,b,p,arrow=True,packet=0.):
        if p<=0:return
        x1,y1=a; x2,y2=b
        ex=x1+(x2-x1)*p;ey=y1+(y2-y1)*p
        d.line((x1,y1,ex,ey),fill=self.accent,width=5)
        if arrow and p>.95:
            ang=math.atan2(y2-y1,x2-x1)
            d.polygon([(ex,ey),(ex-19*math.cos(ang-.45),ey-19*math.sin(ang-.45)),
                       (ex-19*math.cos(ang+.45),ey-19*math.sin(ang+.45))],fill=self.accent)
        if p>.95:
            q=packet%1
            x=x1+(x2-x1)*q;y=y1+(y2-y1)*q
            d.ellipse((x-9,y-9,x+9,y+9),fill=self.fg)

    def paste_label(self,canvas,texture,x,y,reveal=1,line_height=46):
        x,y=round(x),round(y)
        box=texture.getbbox()
        used=box[2] if box else texture.width
        canvas.paste(self.bg,(x-6,y-3,x+used+6,y+texture.height+3))
        if reveal>=1:
            canvas.paste(texture,(x,y),texture);return None
        rows=max(1,math.ceil(texture.height/line_height));row_height=texture.height/rows
        amount=max(0,reveal)*rows;full=min(rows,int(amount))
        if full:
            tile=texture.crop((0,0,texture.width,round(full*row_height)))
            canvas.paste(tile,(x,y),tile)
        if full<rows:
            edge=round(used*(amount-full));start=round(full*row_height)
            if edge:
                tile=texture.crop((0,start,edge,round((full+1)*row_height)))
                canvas.paste(tile,(x,y+start),tile)
            return x+edge,y+start+row_height*.7

    def paint_portrait(self,canvas,t,beat,local):
        if self.person_image is None:return
        if (self.static_image or not self.animate) and self.style!='historia_ilustrada':t=2.;local=2.
        x,y,pw,ph=self.portrait_box
        entered=ease(t/.85)
        named=self.person['pessoa'].casefold() in (' '.join(e['rotulo'] for e in beat['elementos'])+' '+beat['titulo']).casefold()
        emphasis=(1-ease(local/1.2)) if named and (not self.static_image or self.style=='historia_ilustrada') else 0
        zoom=1.025+.012*math.sin(t*.8)+.018*emphasis
        image=ImageOps.fit(self.person_image,(round(pw*zoom),round(ph*zoom)),method=Image.Resampling.BICUBIC,centering=(.5,.35))
        image=image.crop(((image.width-pw)//2,(image.height-ph)//2,(image.width+pw)//2,(image.height+ph)//2))
        mask=Image.new('L',(pw,ph));ImageDraw.Draw(mask).rounded_rectangle((0,0,pw-1,ph-1),24,fill=255)
        tile=Image.new('RGBA',(pw+20,ph+20))
        tile.paste(image,(10,10),mask)
        td=ImageDraw.Draw(tile)
        td.rounded_rectangle((8,8,pw+11,ph+11),25,outline=self.accent,width=3+round(emphasis*3))
        angle=1.1*math.sin(t*.75)-3*(1-entered)
        tile=tile.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        tile.putalpha(tile.getchannel('A').point(lambda a:round(a*entered)))
        dx=4*math.sin(t*.65);dy=6*math.sin(t*.9)+(1-entered)*28
        canvas.paste(tile,(round(x+pw/2-tile.width/2+dx),round(y+ph/2-tile.height/2+dy)),tile)
        name=self.text(self.person['pessoa'],pw+30,31 if not self.portrait else 27,bold=True)
        canvas.paste(name,(x-5,y+ph+32),name)
        credit=self.text('Foto: '+self.person['autor_foto']+' · '+self.person['licenca'],pw+35,15,self.muted,max_lines=2)
        canvas.paste(credit,(x-5,y+ph+32+name.height+4),credit)

    def large_words(self,canvas,beat,local,length,top,width):
        if not self.highlights and self.style!='tipografia':return
        if not self.animate:
            text=beat['titulo'];part=1;size=57 if not self.portrait else 54
            y=top+25 if self.style=='tipografia' else top-100
        elif self.style=='tipografia':
            from .speech import phrases
            phrase=phrases(self.scene['narracao_ptbr'])[min(beat['frase'],len(phrases(self.scene['narracao_ptbr']))-1)]
            words=phrase.split();chunks=[' '.join(words[i:i+4]) for i in range(0,len(words),4)]
            slot=length/max(1,len(chunks));index=min(len(chunks)-1,int(max(0,local)/slot))
            text=chunks[index];part=local-index*slot
            size=88 if not self.portrait else 76;y=top+25
        else:
            words=beat['titulo'].split();count=max(1,min(len(words),math.ceil(local/.16)))
            text=' '.join(words[:count]);part=local;size=57 if not self.portrait else 54;y=top-100
        layer=self.text(text,width-20,size,self.fg if self.style in ('quadro','mao','recortes') else self.accent,True,max_lines=3 if self.style=='tipografia' else 2)
        dy=round((1-ease(part/.3))*20)
        if self.style=='recortes':
            box=layer.getbbox();used=box[2] if box else layer.width
            d=ImageDraw.Draw(canvas);d.polygon([(self.margin-10,y+dy-5),(self.margin+used+14,y+dy-10),
                (self.margin+used+8,y+dy+layer.height),(self.margin-7,y+dy+layer.height+5)],fill='#ead8a7')
        canvas.paste(layer,(self.margin,y+dy),layer)
        return y+dy+layer.height

    def _frame_raw(self,t):
        idx=max(0,bisect_right(self.starts,t)-1)
        beat=self.beats[idx]
        local=t-beat['inicio'];length=max(.4,beat['fim']-beat['inicio'])
        progress=min(1,local/length)
        if self.story:
            return self.story.frame(t if self.animate else beat['inicio']+length*.85,beat,
                                    local if self.animate else length*.85,length)
        canvas=self.base.copy();d=ImageDraw.Draw(canvas)
        m=self.margin;w=self.w;top=self.top;bottom=self.bottom
        sketch=self.style in ('quadro','mao');pen_tip=None
        # Title and header entrance
        enter=ease(min(1.0,local/.45)) if self.animate else 1;head_shift=int((1-enter)*25)
        if self.highlights or self.style=='tipografia':
            self.large_words(canvas,beat,local,length,top,self.content_right-m)
            if self.style!='tipografia':
                full=self.text(beat['titulo'],self.content_right-m-20,57 if not self.portrait else 54,
                               bold=True,max_lines=2)
                top=max(top,top-100+20+full.height+32)
            else:
                from .speech import phrases
                phrase=phrases(self.scene['narracao_ptbr'])[min(beat['frase'],len(phrases(self.scene['narracao_ptbr']))-1)]
                words=phrase.split()
                heights=[self.text(' '.join(words[i:i+4]),self.content_right-m-20,
                                   76 if self.portrait else 88,bold=True,max_lines=3).height
                         for i in range(0,len(words),4)]
                top+=max(290 if self.portrait else 250,25+20+max(heights,default=0)+32)
        else:
            head=self.text(beat['titulo'],self.content_right-m,46 if not self.portrait else 48,self.accent,True)
            canvas.paste(head,(m,top-95+head_shift),head)
            top=max(top,top-95+25+head.height+24)
        kind=beat['composicao']
        elements=beat['elementos']
        # A year is context, never a communicating node in a network diagram.
        context=[]
        if kind=='rede':
            context=[e for e in elements if re.fullmatch(r'(?:[Aa]nos |[Dd]écada de )?\d{3,4}',e['rotulo'])]
            elements=[e for e in elements if e not in context]
        n=len(elements)
        date_pattern=DATE_PATTERN
        if n==2 and any(re.fullmatch(date_pattern,e['rotulo']) for e in elements):
            kind='linha_do_tempo'
        if context:
            tex=self.text(' / '.join(e['rotulo'] for e in context),250,28,self.muted,True)
            canvas.paste(tex,(self.content_right-250,top+6),tex)
            top+=tex.height+24
        if self.asset is not None and self.static_image:
            # All moments share one image anchor, even when their headings wrap
            # to different heights. Only the diagram changes around the image.
            reserves=[]
            for b in self.beats:
                dates=[e['rotulo'] for e in b['elementos'] if b['composicao']=='rede' and re.fullmatch(r'(?:[Aa]nos |[Dd]écada de )?\d{3,4}',e['rotulo'])]
                reserves.append(self.diagram_top(b)+(self.text(' / '.join(dates),250,28,self.muted,True).height+24 if dates else 0))
            top=max(reserves)
        if self.asset is not None:
            aw=int((self.content_right-m)*(.46 if not self.portrait else 1))
            ah=int((bottom-top)*(.42 if self.portrait else .9))
            asset_enter=ease(min(1.0,t/.65))
            sway_y=int(5*math.sin(t*.75))
            sway_x=int(3*math.cos(t*.60))
            asset_y=top+int((1-asset_enter)*35)+sway_y
            asset_x=m+sway_x
            scene_dur=max(1.0,self.beats[-1]['fim'])
            scene_p=min(1.0,t/scene_dur)
            zoom=1.0+.035*math.sin(scene_p*math.pi)
            pan_y=.45+.06*math.sin(t*.40)
            if self.static_image or not self.animate:
                asset_x=m;asset_y=top;zoom=1.;pan_y=.5
            pic=ImageOps.contain(self.asset,(int(aw*zoom),int(ah*zoom)))
            mask=Image.new('L',(aw,ah))
            ImageDraw.Draw(mask).rounded_rectangle((0,0,aw-1,ah-1),22,fill=255)
            tile=Image.new('RGBA',(aw,ah),(0,0,0,0))
            bg_card=Image.new('RGB',(aw,ah),self.card)
            bg_card.paste(pic,((aw-pic.width)//2,int((ah-pic.height)*pan_y)))
            tile.paste(bg_card,(0,0),mask)
            td=ImageDraw.Draw(tile)
            td.rounded_rectangle((1,1,aw-2,ah-2),22,outline=self.accent,width=2)
            canvas.paste(tile,(asset_x,asset_y),tile)
            self.asset_box=(asset_x,asset_y,asset_x+aw,asset_y+ah)
            if self.portrait:top+=ah+65
            else:m+=aw+75
        area_w=self.content_right-m
        stacked=self.portrait or self.asset is not None
        layout_key=(kind,tuple((e['rotulo'],e['icone']) for e in elements),m,top,bottom)
        if layout_key not in self.layouts:
            self.layouts[layout_key]=diagram_layout(self,elements,kind,(m,top,self.content_right,bottom))
        nodes=self.layouts[layout_key]
        positions=[node['center'] for node in nodes]
        # Stagger reveals over the first 45% of the spoken phrase.
        stride=min(.6,length*.14)
        if sketch:
            start,slot=drawing_timing(length,n,self.hand_speed if self.style=='mao' else .75)
            reveals=[max(0,min(1,(local-start-j*slot)/slot)) for j in range(n)]
        else:reveals=[ease((local-j*stride)/.48) for j in range(n)]
        if not self.animate:reveals=[1.]*n
        pairs=[]
        if kind in ('processo','linha_do_tempo'): pairs=[(j,j+1) for j in range(n-1)]
        elif kind=='rede':pairs=[(j,k) for j in range(n) for k in range(j+1,n)]
        elif kind=='ciclo':pairs=[(j,(j+1)%n) for j in range(n)]
        elif kind=='conceito':pairs=[(0,j) for j in range(1,n)]
        if kind=='comparacao':
            mid=m+area_w/2
            d.line((mid,top,mid,bottom-15),fill=self.muted,width=2)
        if kind=='linha_do_tempo' and not stacked:
            d.text((m,top-20),'LINHA DO TEMPO',font=font(21,True),fill=self.muted)
        for j,k in pairs:
            self.connection(d,positions[j],positions[k],min(reveals[j],reveals[k]),
                            kind in ('processo','ciclo'),local*.32+j*.28 if self.animate else 0)
        for j,(element,node) in enumerate(zip(elements,nodes)):
            x,y=node['center']
            p=reveals[j]
            if p<=0:continue
            if not sketch:y+=int((1-p)*18)
            pulse=1+.025*math.sin(local*2.4+j) if self.animate else 1
            base_radius=node['radius']
            r=base_radius*(.75+.25*p)*pulse
            if sketch:r=base_radius
            d.ellipse((x-r-20,y-r-20,x+r+20,y+r+20),fill=self.bg)
            if self.style=='recortes':
                tilt=7*math.sin(local*1.5+j) if self.animate else 0
                d.polygon([(x-r-16,y-r+tilt),(x+r+24,y-r-8),(x+r+15,y+r+18),(x-r-20,y+r+8)],fill='#e9dfc8')
            if self.style=='infografico':
                d.rounded_rectangle((x-r-16,y-r-16,x+r+16,y+r+16),20,fill=self.card,outline=self.accent,width=2)
            label=element['rotulo']
            percentage=re.search(r'(?<!\d)(\d{1,3})(?:[,.](\d+))?\s*%',label)
            if re.fullmatch(date_pattern,label):
                tex=node['year']
                tip=self.paste_label(canvas,tex,*node['year_xy'],p if sketch else 1,tex.height)
                if sketch and 0<p<1:pen_tip=tip
                if node['prefix'] is not None:
                    self.paste_label(canvas,node['prefix'],*node['prefix_xy'],p if sketch else 1)
                continue
            elif percentage and 0<=float(percentage[1]+'.'+(percentage[2] or '0'))<=100:
                value=float(percentage[1]+'.'+(percentage[2] or '0'))
                cell=max(7,round(r*.17));space=round(cell*1.4)
                for cell_index in range(100):
                    gx=x-space*4.5+(cell_index%10)*space
                    gy=y-space*4.5+(cell_index//10)*space
                    color=self.accent if cell_index<round(value)*p else self.card
                    d.rounded_rectangle((gx-cell/2,gy-cell/2,gx+cell/2,gy+cell/2),2,fill=color)
            else:
                kind_icon=element['icone']
                lower=label.lower()
                if any(term in lower for term in ('arpanet','nsfnet','conexão','tcp/ip','rede nacional')):kind_icon='computador'
                elif lower=='cern' or any(term in lower for term in ('universidade','ufrj','agency')):kind_icon='livro'
                elif any(term in lower for term in ('usuários','residências')):kind_icon='pessoa'
                elif lower in ('eua','união soviética','brasil','suíça'):kind_icon='globo'
                if sketch:
                    from .sketch import SketchPen
                    pen=SketchPen()
                    if kind_icon=='pessoa':kind_icon='personagem'
                    icon(pen,kind_icon,x,y,r,self.bg,self.fg,0 if p<1 or not self.animate else local)
                    tip=pen.render(canvas,min(1,p/.72),self.fg)
                    if 0<p<.72:pen_tip=tip
                else:icon(d,kind_icon,x,y,r,self.accent,self.fg,local if self.animate else 0)
            label_reveal=max(0,min(1,(p-.72)/.28)) if sketch else 1
            tex=node['texture']
            label_x,label_y=node['label_xy']
            if not sketch:label_y+=int((1-p)*18)
            tip=self.paste_label(canvas,tex,label_x,label_y,label_reveal)
            if sketch and .72<p<1 and tip:pen_tip=tip
        self.paint_portrait(canvas,t,beat,local)
        if self.hand is not None and pen_tip:
            canvas.paste(self.hand,(round(pen_tip[0]-self.hand.width*.162),round(pen_tip[1]-self.hand.height*.124)),self.hand)
        return canvas

    def frame(self,t):
        idx=max(0,bisect_right(self.starts,t)-1)
        beat=self.beats[idx];local=t-beat['inicio']
        if self.style=='colagem_documental':
            duration=beat.get('transicao_s',min(self.transition_duration,max(.01,(beat['fim']-beat['inicio'])*.5)))
            if self.transition!='nenhuma' and idx==0 and self.previous_frame is not None and duration>0 and local<duration:
                return self.story.passage(t,idx,local,duration,self.transition)
            # A within-scene sticker replacement has no cinematic effect and
            # inserts no pause into the voice. The parchment stays anchored.
            if idx and self.animate:
                from .collage_pacing import context_identity
                duration=min(1.,max(.01,(beat['fim']-beat['inicio'])*.35))
                if local<duration and context_identity(self.beats[idx-1])!=context_identity(beat):
                    return self.story.passage(t,idx,local,duration,'padrao')
            return self._frame_raw(t)
        canvas=self._frame_raw(t)
        duration=beat.get('transicao_s',self.transition_duration)
        if idx or self.previous_frame is None or self.transition=='nenhuma' or duration<=0 or local>=duration:return canvas
        style='dissolver' if self.transition=='padrao' else self.transition
        return transition_frame(self.previous_frame,canvas,style,local/duration)
