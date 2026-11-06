"""Archival paper collage: real raster cutouts, paper placement and camera travel."""
from __future__ import annotations

from functools import lru_cache
import math
import os
from pathlib import Path
import random

import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps

from .collage_assets import ASSETS,fingerprint,resolve,selections,content_hash,normalize
from .core import digest,read_json
from .visuals import font
from .collage_motion import StickerRig,pose,PROFILES,VERSION as MOTION_VERSION
from .collage_pacing import VERSION as PACING_VERSION

VERSION='documentary-collage-v10-density-2-3-'+MOTION_VERSION+'-'+PACING_VERSION
INK='#292a25';RED='#ad2d20';CREAM='#eee2c8';MUSTARD='#c6a24b'


@lru_cache(maxsize=64)
def face(size,kind='headline'):
    names={'headline':'impact.ttf','type':'courbd.ttf','serif':'times.ttf'}
    target=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/names[kind]
    return ImageFont.truetype(str(target),size) if target.exists() else font(size,True)


def text_tile(text,width,size,kind='type',color=INK,max_lines=3,max_height=None):
    """Wrap complete labels, including long individual words, with measured height."""
    d=ImageDraw.Draw(Image.new('RGBA',(1,1)))
    for actual in range(size,7 if max_height is not None else 17,-1):
        f=face(actual,kind);parts=[]
        for word in str(text).split():
            part=''
            for c in word:
                if part and d.textlength(part+c,font=f)>width:parts.append(part);part=''
                part+=c
            if part:parts.append(part)
        lines=[];line=''
        for word in parts:
            candidate=(line+' '+word).strip()
            if line and d.textlength(candidate,font=f)>width:lines.append(line);line=word
            else:line=candidate
        if line:lines.append(line)
        if len(lines)>max_lines:continue
        line_h=math.ceil(actual*1.26)
        result=Image.new('RGBA',(max(1,math.ceil(max((d.textlength(l,font=f) for l in lines),default=1))),line_h*len(lines)+8))
        draw=ImageDraw.Draw(result)
        for i,line in enumerate(lines):draw.text((0,i*line_h),line,font=f,fill=color,stroke_width=0)
        if max_height is not None:
            # Fit the visible letters, without changing the paper or its slot.
            box=result.getbbox()
            if box:result=result.crop(box)
            if result.height>max_height:continue
        return result
    raise ValueError('Rótulo muito extenso para o cartão de colagem.')


def torn_sheet(size,seed=0,color=CREAM):
    w,h=size;rng=random.Random(str(seed));layer=Image.new('RGBA',size)
    points=[]
    for x in range(4,w-4,12):points.append((x,rng.randrange(2,8)))
    for y in range(4,h-4,12):points.append((w-rng.randrange(2,8),y))
    for x in range(w-5,3,-12):points.append((x,h-rng.randrange(2,8)))
    for y in range(h-5,3,-12):points.append((rng.randrange(2,8),y))
    ImageDraw.Draw(layer).polygon(points,fill=color)
    # Actual paper grain, not animated noise; stable for the entire shot.
    paper=ImageOps.fit(Image.open(ASSETS/'parchment.png').convert('RGB'),size)
    tint=Image.new('RGB',size,color)
    paper=Image.blend(tint,paper,.16)
    paper.putalpha(layer.getchannel('A'))
    return paper


def with_shadow(tile,radius=7):
    alpha=tile.getchannel('A');shadow=Image.new('RGBA',tile.size,'#15130f')
    shadow.putalpha(alpha.point(lambda x:round(x*.26)).filter(ImageFilter.GaussianBlur(radius)))
    out=Image.new('RGBA',(tile.width+24,tile.height+24))
    out.alpha_composite(shadow,(10,14));out.alpha_composite(tile,(2,2))
    return out


def photo_cutout(image,size,*,preserve_color=False):
    source=image.convert('RGBA')
    if preserve_color:source=ImageOps.contain(source,size,method=Image.Resampling.LANCZOS)
    else:source.thumbnail(size,Image.Resampling.LANCZOS)
    if preserve_color:
        paper=torn_sheet((source.width+26,source.height+26),'photo')
        paper.alpha_composite(source,(13,13));return paper
    gray=ImageOps.autocontrast(ImageOps.grayscale(source))
    sepia=ImageOps.colorize(gray,'#252924','#e5d6b8').convert('RGBA')
    sepia.putalpha(source.getchannel('A'))
    # A modest dot screen retains photographic detail at output resolution.
    values=np.array(gray,dtype=np.float32);yy,xx=np.indices(values.shape)
    screen=((xx+yy)%6==0)&(values<180)
    arr=np.array(sepia);arr[screen,:3]=(arr[screen,:3]*.82).astype('uint8')
    sepia=Image.fromarray(arr)
    if source.getchannel('A').getextrema()[0]<250:return sepia
    paper=torn_sheet((sepia.width+26,sepia.height+26),'photo')
    paper.alpha_composite(sepia,(13,13));return paper


def fallback_kind(element):
    """Use a symbolic subject, without inventing a portrait or another claim."""
    label=normalize(element['rotulo']);query=normalize(element.get('recorte',''))
    if any(word in label.split() for word in ('misterio','pergunta','duvida','incerteza')):return 'question'
    if 'banco de dados' in label+' '+query:return 'computador'
    if any(word in label.split() for word in ('banco','bancos')):return 'bank'
    if any(word in label.split() for word in ('nome','pseudonimo','identidade')):return 'identity'
    return element.get('icone','documento')


def fallback_icon(element,size):
    """A reusable vector symbol inside the existing paper; the caption names it once."""
    from .motion import icon
    kind=fallback_kind(element);symbol=Image.new('RGBA',(1024,1024));draw=ImageDraw.Draw(symbol)
    if kind=='question':
        mark=text_tile('?',840,800,'headline',max_height=840)
        symbol.alpha_composite(mark,((1024-mark.width)//2,(1024-mark.height)//2))
    elif kind=='bank':
        draw.line([(104,332),(512,112),(920,332),(104,332)],fill=INK,width=40,joint='curve')
        for x in (224,416,608,800):draw.line((x,416,x,796),fill=INK,width=48)
        draw.line((128,852,896,852),fill=INK,width=40);draw.line((84,936,940,936),fill=INK,width=40)
    elif kind=='identity':
        draw.rounded_rectangle((100,196,924,828),radius=60,outline=INK,width=32)
        draw.ellipse((208,308,400,500),outline=INK,width=28)
        draw.arc((164,500,444,760),180,360,fill=INK,width=28)
        for y in (376,512,648):draw.line((536,y,828,y),fill=INK,width=28)
    else:icon(draw,kind,512,472,400,'#ddd0b4',INK,0)
    box=symbol.getbbox()
    if box:symbol=symbol.crop(box)
    return ImageOps.contain(symbol,size,method=Image.Resampling.LANCZOS)


def cells_for(n,bounds,composition,variant=0):
    l,t,r,b=bounds;w=r-l;h=b-t;gap=40
    if n==1:return [(l,t,r,b)]
    if h>w*1.15:
        if n<=3:return [(l,t+i*h/n+gap/2,r,t+(i+1)*h/n-gap/2) for i in range(n)]
    if n==2:return [(l,t,l+w/2-gap/2,b),(l+w/2+gap/2,t,r,b)]
    if n==4 and w>h*2.2:
        return [(l+i*w/4+gap/2,t,l+(i+1)*w/4-gap/2,b) for i in range(4)]
    if n==3 and w>h*1.5 and composition=='conceito':
        hero=(l,t,l+w*.52-gap/2,b)
        side=[(l+w*.52+gap/2,t+i*h/2+gap/2,r,t+(i+1)*h/2-gap/2) for i in range(2)]
        return [hero,*side]
    cols=2;rows=math.ceil(n/cols)
    return [(l+(i%cols)*w/cols+gap/2,t+(i//cols)*h/rows+gap/2,
             l+(i%cols+1)*w/cols-gap/2,t+(i//cols+1)*h/rows-gap/2) for i in range(n)]


def figure_pose(ident,mode,t,phase=0):
    """Motion stays inside the reserved sticker envelope; labels never rotate."""
    return pose(ident,mode,t,phase)


class CollageStage:
    def __init__(self,a,path):
        self.a=a;self.path=path;self.w=a.w;self.h=a.h
        self.paper=ImageOps.fit(Image.open(ASSETS/'parchment.png').convert('RGB'),(a.w,a.h),method=Image.Resampling.LANCZOS)
        self.selection=selections(path,a.scene,a.beats);self.nodes={};self.geometry={};self.headers={};self.labels={};self.turbines={};self.rigs={};self.shared={}
        self.display_indices=[list(range(min(len(beat['elementos']),2 if a.asset is not None else 3))) for beat in a.beats]
        self.passages={}
        self.movement=a.scene.get('movimento_figuras','herdar')
        if self.movement=='herdar':self.movement=a.figure_movement
        if not a.animate:self.movement='nenhum'
        m=a.margin if a.mobile else 76 if a.portrait else 90
        self.scene_title=text_tile(a.scene['titulo'].upper(),a.w-2*m-180,23,'type',max_lines=2)
        self.foot=text_tile('COLAGEM DOCUMENTAL  /  RECORTES ILUSTRATIVOS',a.w-2*m,19,'type',INK)
        self.counters=[text_tile(f'{i+1:02} / {len(a.beats):02}',160,23,'type',RED) for i in range(len(a.beats))]
        hashes=[]
        for row in self.selection:
            for record in row:
                p=resolve(record,path)
                if p:hashes.append((record['id'],content_hash(p)))
        a.key=digest(a.key,VERSION,fingerprint(),self.selection,hashes,a.camera_dynamic,self.movement,a.scene.get('figuras_colagem',''),self.display_indices)
        heading_size=58 if a.asset is not None else (68 if a.portrait else 74)
        self.headers={i:text_tile(b['titulo'].upper(),a.w-2*m,heading_size,'headline',max_lines=2) for i,b in enumerate(a.beats)}
        # A wrapped heading must not move every image in the next phrase.
        self.content_top=max(300,max(145+title.height+48 for title in self.headers.values()))
        self.reference=None;self.reference_key=None;self.support_bounds=(m,self.content_top,a.w-m,a.h-210)
        if a.mobile:self.support_bounds=(m,self.content_top,a.w-m,a.h-74)
        if a.asset is not None:
            bottom=a.h-(74 if a.mobile else 210)
            if a.portrait:
                photo_bottom=self.content_top+round((bottom-self.content_top)*(.48 if a.mobile else .60))
                box=(m,self.content_top,a.w-m,photo_bottom)
                self.support_bounds=(m,photo_bottom+38,a.w-m,bottom)
            else:
                photo_right=round(a.w*.66)
                box=(m,self.content_top,photo_right,bottom)
                self.support_bounds=(photo_right+50,self.content_top,a.w-m,bottom)
            a.asset_box=box
            self.reference=with_shadow(photo_cutout(a.asset,(box[2]-box[0]-52,box[3]-box[1]-52),preserve_color=True))
            self.reference_key=('reference',digest(a.asset.tobytes().hex()))
        self.background=self.paper.copy().convert('RGBA')
        d=ImageDraw.Draw(self.background)
        d.line((m,68,self.w-m,68),fill=INK,width=2)
        if not a.mobile:
            d.line((m,self.h-168,self.w-m,self.h-168),fill=(68,56,36,140),width=2)
            self.background.alpha_composite(self.foot,(m,self.h-151))
        for i,beat in enumerate(a.beats):self.prepare(i,beat)

    def prepare(self,i,beat):
        a=self.a;w=self.w;h=self.h;m=a.margin if a.mobile else 76 if a.portrait else 90
        indices=self.display_indices[i];elements=[beat['elementos'][j] for j in indices]
        cells=cells_for(len(elements),self.support_bounds,beat['composicao'],i)
        if a.mobile and a.mobile_layout=='equilibrada':
            left,top,right,bottom=self.support_bounds;n=len(elements);gap=30
            cols=min(2,n);rows=math.ceil(n/cols);width=right-left
            height=min(bottom-top,430 if rows==1 else 760)
            origin=top+(bottom-top-height)/2
            cw=(width-gap*(cols-1))/cols;ch=(height-gap*(rows-1))/rows
            cells=[]
            for j in range(n):
                x=left+(j%cols)*(cw+gap)
                if n==3 and j==2:x=left+(width-cw)/2
                y=origin+(j//cols)*(ch+gap)
                cells.append((x,y,x+cw,y+ch))
        elif a.mobile:
            left,top,right,bottom=self.support_bounds;n=len(elements);gap=26
            step=(bottom-top-gap*(n-1))/max(1,n)
            cells=[(left,top+j*(step+gap),right,top+j*(step+gap)+step) for j in range(n)]
        elif a.asset is None:
            left,top,right,bottom=self.support_bounds;n=len(elements);gap=40
            width=(right-left-gap*(n-1))/n
            cells=[(left+j*(width+gap),top,left+j*(width+gap)+width,bottom) for j in range(n)]
        elif not a.portrait and len(elements)>1:
            left,top,right,bottom=self.support_bounds;n=len(elements);height=(bottom-top)/n
            cells=[(left,top+j*height+14,right,top+(j+1)*height-14) for j in range(n)]
        source=self.selection[i] if i<len(self.selection) else []
        records=[source[j] if j<len(source) else None for j in indices]
        identities=[(records[j]['id'] if records[j] else None,e['rotulo'].casefold()) for j,e in enumerate(elements)]
        if i and len(cells)==len(self.geometry[i-1]) and set(cells)=={g['cell'] for g in self.geometry[i-1]}:
            # Preserve the screen position of a continuing subject, even when
            # the writer lists that same subject in a different order.
            available=list(cells);assigned={}
            for j,identity in enumerate(identities):
                previous=next((g for g in self.geometry[i-1] if g['identity']==identity and g['cell'] in available),None)
                if previous:assigned[j]=previous['cell'];available.remove(previous['cell'])
            cells=[assigned[j] if j in assigned else available.pop(0) for j in range(len(cells))]
        nodes=[];geometry=[];labels=[];rigs=[]
        for j,(e,cell) in enumerate(zip(elements,cells)):
            x1,y1,x2,y2=cell;cw,ch=round(x2-x1),round(y2-y1)
            label=text_tile(e['rotulo'],cw-64,36 if a.mobile else (28 if a.asset is not None else 33) if ch>300 else 26,max_lines=4 if a.asset is not None else 3)
            record=records[j]
            target=resolve(record,self.path)
            label_h=label.height+30
            art_h=max(40,ch-label_h-46);art_w=cw-60
            tile=Image.new('RGBA',(cw,art_h+16))
            pivot=None
            if target and record['id']=='turbina-eolica':
                mast=Image.open(ASSETS/'turbine-mast.png').convert('RGBA')
                rotor=Image.open(ASSETS/'turbine-rotor.png').convert('RGBA')
                mh=round(art_h*.68);scale=mh/mast.height
                mast=mast.resize((round(mast.width*scale),mh),Image.Resampling.LANCZOS)
                radius=min(round(art_h*.29),round((cw-80)/2))
                rotor=rotor.resize((radius*2,radius*2),Image.Resampling.LANCZOS)
                hub_x=cw//2;hub_y=radius+16
                pivot=read_json(ASSETS/'turbine-pivots.json')['mast']
                mx=round(hub_x-pivot[0]*scale);my=round(hub_y-pivot[1]*scale)
                tile.alpha_composite(with_shadow(mast),(mx-2,my-2))
                self.turbines[(i,j)]=(rotor,(hub_x-radius,hub_y-radius))
            elif target:
                with Image.open(target) as source:
                    art=source.convert('RGBA')
                if record.get('kind','library')!='library':art=photo_cutout(art,(art_w-24,art_h-24))
                art=ImageOps.contain(art,(art_w-24,art_h-24),method=Image.Resampling.LANCZOS)
                raw_w,raw_h=art.size
                art=with_shadow(art)
                ax=(cw-art.width)//2;ay=round((art_h-art.height)/2)+12
                pivot=(ax+2+raw_w/2,ay+2+raw_h*(.578 if record['id']=='relogio' else .5))
                tile.alpha_composite(art,(ax,ay))
                # Small translucent tape stays on the clipping, away from its caption.
                td=ImageDraw.Draw(tile);tw=min(105,round(art.width*.42));th=min(28,max(12,round(art.height*.09)))
                tx=max(20,(cw-tw)//2);ty=ay+3
                if PROFILES.get(record['id'])!='rotate':
                    td.polygon([(tx,ty),(tx+tw,ty+5),(tx+tw-5,ty+th+5),(tx-4,ty+th)],fill=(199,169,89,105))
                # A brass pin settles at the paper's upper edge.
                if int(digest(record['id'])[:6],16)%3==1 and PROFILES.get(record['id'])!='rotate':
                    cx=cw//2+40;cy=ay+20
                    td.ellipse((cx-9,cy-7,cx+11,cy+13),fill=(30,23,11,80))
                    td.ellipse((cx-8,cy-8,cx+8,cy+8),fill='#907327',outline='#574314',width=2)
                    td.ellipse((cx-5,cy-5,cx+2,cy+1),fill='#d0b568')
            else:
                card=torn_sheet((cw-50,max(90,art_h-18)),e['rotulo'],'#ddd0b4')
                # Preserve the original card and caption positions. A missing
                # image gets a related symbol, never a second copy of the name.
                visible_height=min(card.height,tile.height-12)
                concept=fallback_icon(e,(card.width-60,max(1,visible_height-12)))
                card.alpha_composite(concept,((card.width-concept.width)//2,(visible_height-concept.height)//2))
                tile.alpha_composite(with_shadow(card),(14,10))
            paper=torn_sheet((label.width+32,label_h),'label:'+e['rotulo'])
            paper.alpha_composite(label,(16,9))
            lx=(cw-paper.width)//2;ly=ch-label_h-10
            labels.append((with_shadow(paper,3),(round(x1+lx),round(y1+ly))))
            nodes.append(tile);geometry.append({'cell':cell,'label':(x1+lx,y1+ly,x1+lx+paper.width,y1+ly+paper.height),'record':record['id'] if record else None,'identity':identities[j]})
            rigs.append(StickerRig(tile,record['id'] if record else None,pivot))
        self.nodes[i]=nodes;self.geometry[i]=geometry;self.labels[i]=labels;self.rigs[i]=rigs
        self.shared[i]=[]
        if i:
            used=set()
            for j,g in enumerate(geometry):
                for old,previous in enumerate(self.geometry[i-1]):
                    if old not in used and g['identity']==previous['identity'] and g['cell']==previous['cell']:
                        self.shared[i].append((old,j));used.add(old);break

    def relations_layer(self,idx,local):
        a=self.a;beat=a.beats[idx];content=Image.new('RGBA',(self.w,self.h))
        geometries=self.geometry[idx]
        if beat['composicao'] in ('processo','linha_do_tempo','rede','ciclo') and len(geometries)==2:
            one,two=[g['cell'] for g in geometries]
            if one[2]<two[0]:
                x1=one[2]-8;x2=two[0]+8;y=(one[1]+one[3])/2
                part=min(1,max(0,(local-.35)/.65)) if a.animate and idx==0 and a.previous_frame is None else 1
                cd=ImageDraw.Draw(content);end=x1+(x2-x1)*part
                cd.line((x1,y,end,y),fill=RED,width=5)
                if part==1:cd.polygon([(end,y),(end-14,y-8),(end-14,y+8)],fill=RED)
        return self.camera(content,0)

    def entry(self,idx,j,local):
        if not self.a.animate or idx or self.a.previous_frame is not None:return 1.
        p=max(0,min(1,(local-j*.10)/.85))
        return p*p*(3-2*p)

    def art_layer(self,t,idx,local,length,omit=(),only=None,*,enter=True):
        a=self.a;beat=a.beats[idx];content=Image.new('RGBA',(self.w,self.h))
        geometries=self.geometry[idx]
        # Relationships are only shown for explicit process/timeline/network plans.
        if only is None:content.alpha_composite(self.relations_layer(idx,local))
        for j,(tile,g) in enumerate(zip(self.nodes[idx],geometries)):
            if j in omit or only is not None and j not in only:continue
            x1,y1,x2,y2=g['cell']
            # One entrance at the start; a transition already introduces later
            # figures. Do not fade/pop them in a second time underneath it.
            eased=self.entry(idx,j,local) if enter else 1.
            # Global scene time prevents a repeated figure's motion restarting.
            motion_time=t*.3
            art=self.rigs[idx][j].frame(motion_time,self.movement)
            if (idx,j) in self.turbines:
                rotor,xy=self.turbines[(idx,j)];art=tile.copy()
                angle=-motion_time*70 if self.movement=='tematico' else 0
                art.alpha_composite(rotor.rotate(angle,Image.Resampling.BICUBIC,expand=False),xy)
            # Phase belongs to the subject, not its position in the beat list.
            phase=int(digest(g['identity'])[:6],16)%11
            dx,dy,sway=figure_pose(g['record'],self.movement,motion_time,phase)
            dx*=.45;dy*=.45;sway*=.45
            angle=(1-eased)*(-2 if phase%2 else 2)+sway
            settled=art.rotate(angle,Image.Resampling.BICUBIC,expand=False) if angle else art
            if eased<1:
                settled=settled.copy();settled.putalpha(settled.getchannel('A').point(lambda v:round(v*eased)))
            # Crop the displaced art to its own cell before compositing, so even
            # tall spinning blades cannot cover a neighboring label.
            bounded=Image.new('RGBA',tile.size)
            bounded.alpha_composite(settled,(round(dx),round(dy+(1-eased)*28)))
            content.alpha_composite(bounded,(round(x1),round(y1)))
        return self.camera(content,t)

    def camera(self,content,t):
        a=self.a
        if a.animate and a.camera_dynamic:
            # A single, tiny travel across the entire scene. Never reset zoom
            # or reverse its direction on every spoken phrase.
            p=max(0,min(1,t/max(1,a.beats[-1]['fim'])));zoom=1+.004*p*p*(3-2*p)
            if zoom>1:
                sw,sh=round(self.w*zoom),round(self.h*zoom)
                content=content.resize((sw,sh),Image.Resampling.BICUBIC)
                x=round((sw-self.w)*.5);y=round((sh-self.h)*.5)
                content=content.crop((x,y,x+self.w,y+self.h))
        return content

    def frame(self,t,beat,local,length,omit=()):
        a=self.a;idx=a.beats.index(beat);canvas=self.background.copy()
        d=ImageDraw.Draw(canvas);m=a.margin if a.mobile else 76 if a.portrait else 90
        canvas.alpha_composite(self.scene_title,(m,88))
        counter=self.counters[idx];canvas.alpha_composite(counter,(self.w-m-counter.width,88))
        title=self.headers[idx];canvas.alpha_composite(title,(m,145))
        d.line((m,145+title.height+12,min(self.w-m,m+title.width*.55),145+title.height+7),fill=RED,width=7)
        canvas.alpha_composite(self.art_layer(t,idx,local,length,omit))
        for j,(label,xy) in enumerate(self.labels[idx]):
            if j not in omit:
                p=self.entry(idx,j,local)
                self.place(canvas,label,xy,p,(0,round((1-p)*28)))
        if self.reference is not None:
            x1,y1,x2,y2=a.asset_box
            # Same pixels, same anchor in every phrase; the camera never moves it.
            canvas.alpha_composite(self.reference,(x1+(x2-x1-self.reference.width)//2,y1+(y2-y1-self.reference.height)//2))
        return canvas.convert('RGB')

    @staticmethod
    def place(canvas,image,xy,opacity=1.,offset=(0,0)):
        if opacity<=0:return
        if opacity<1:
            image=image.copy();image.putalpha(image.getchannel('A').point(lambda v:round(v*opacity)))
        canvas.alpha_composite(image,(round(xy[0]+offset[0]),round(xy[1]+offset[1])))

    @staticmethod
    def layer(image,xy,key,anchor,kind,index=0):
        box=image.getbbox()
        if box is None:return None
        return {'image':image.crop(box),'xy':(xy[0]+box[0],xy[1]+box[1]),'key':key,
                'anchor':anchor,'kind':kind,'index':index}

    def sticker(self,t,idx,j):
        beat=self.a.beats[idx];g=self.geometry[idx][j]
        art=self.art_layer(t,idx,1.,beat['fim']-beat['inicio'],only={j},enter=False)
        identity=g['record'] or g['identity']
        return self.layer(art,(0,0),('art',identity),g['cell'],'art',j)

    def snapshot(self,t,idx):
        # Store compact foreground layers, not another Animator or a chain of
        # previous scenes. The renderer can reuse this even on a cached scene.
        a=self.a;m=76 if a.portrait else 90;layers=[]
        layers.append(self.layer(self.scene_title,(m,88),('scene-title',a.scene['titulo']),(m,88),'heading'))
        counter=self.counters[idx]
        xy=(self.w-m-counter.width,88)
        layers.append(self.layer(counter,xy,('counter',idx,len(a.beats)),xy,'heading'))
        title=self.headers[idx]
        heading=Image.new('RGBA',(self.w,self.content_top))
        heading.alpha_composite(title,(m,145))
        ImageDraw.Draw(heading).line((m,145+title.height+12,min(self.w-m,m+title.width*.55),145+title.height+7),fill=RED,width=7)
        layers.append(self.layer(heading,(0,0),('heading',a.beats[idx]['titulo']),(m,145),'heading'))
        relation=self.camera(self.relations_layer(idx,2.),t)
        layers.append(self.layer(relation,(0,0),('relation',a.beats[idx]['composicao'],tuple(g['cell'] for g in self.geometry[idx])),(0,0),'relation'))
        for j,g in enumerate(self.geometry[idx]):
            layers.append(self.sticker(t,idx,j))
            label,xy=self.labels[idx][j]
            layers.append(self.layer(label,xy,('label',g['identity'][1]),xy,'label',j))
        if self.reference is not None:
            x1,y1,x2,y2=a.asset_box
            xy=(x1+(x2-x1-self.reference.width)//2,y1+(y2-y1-self.reference.height)//2)
            layers.append(self.layer(self.reference,xy,self.reference_key,a.asset_box,'reference'))
        return [layer for layer in layers if layer is not None]

    @staticmethod
    def flow(progress):
        p=max(0.,min(1.,progress));return p*p*(3-2*p)

    @staticmethod
    def drift(style,amount,incoming,kind):
        # Travel is measured in a few pixels around each clipping's anchor;
        # no screen-sized slides, flashes, zooms or moving paper in Vox.
        distance=14 if kind=='heading' else 36
        if style in ('deslizar_esquerda','empurrar','revelar'):dx,dy=distance,8
        elif style=='deslizar_direita':dx,dy=-distance,8
        elif style in ('deslizar_baixo','revelar_cima'):dx,dy=0,-distance
        else:dx,dy=0,distance
        if not incoming:dx,dy=-dx*.65,-dy*.65
        return dx*amount,dy*amount

    def passage(self,t,idx,local,duration,style):
        a=self.a;beat=a.beats[idx];p=max(0.,min(1.,local/duration))
        if p<=0:
            return a._frame_raw(beat['inicio']-.001) if idx else a.previous_frame.copy()
        if p>=1:return a._frame_raw(t)
        if idx not in self.passages:
            old=self.snapshot(beat['inicio']-.001,idx-1) if idx else a.previous_collage
            incoming=self.snapshot(beat['inicio']+duration,idx)
            pairs=[];used=set()
            for j,new in enumerate(incoming):
                for k,previous in enumerate(old or []):
                    if k not in used and new['key']==previous['key'] and new['anchor']==previous['anchor']:
                        pairs.append((k,j));used.add(k);break
            # Keep only the active boundary; long scripts must not retain two
            # duplicate photographic foregrounds for every phrase forever.
            self.passages={idx:(old,incoming,pairs)}
        old,incoming,pairs=self.passages[idx]
        result=self.background.copy()
        if old is None:
            # A preceding non-collage model has no reusable paper layers. It
            # fades in place rather than being pushed across the screen.
            result=Image.blend(a.previous_frame.convert('RGBA'),result,self.flow(p/.45))
        old_shared={k for k,_ in pairs};new_shared={j for _,j in pairs}
        for k,layer in enumerate(old or []):
            if k in old_shared:continue
            delay=min(3,layer['index'])*.025 if layer['kind'] in ('art','label') else 0
            q=self.flow((p-delay)/.43)
            self.place(result,layer['image'],layer['xy'],1-q,self.drift(style,q,False,layer['kind']))
        for j,layer in enumerate(incoming):
            if j in new_shared:continue
            delay=.30+min(3,layer['index'])*.045 if layer['kind'] in ('art','label') else .38
            q=self.flow((p-delay)/(1-delay))
            self.place(result,layer['image'],layer['xy'],q,self.drift(style,1-q,True,layer['kind']))
        for _,j in pairs:
            layer=incoming[j]
            if layer['kind']=='art':layer=self.sticker(t,idx,layer['index'])
            self.place(result,layer['image'],layer['xy'])
        return result.convert('RGB')
