"""Immutable local media imports and phrase-anchored cuts for phone videos."""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image,ImageFilter,ImageOps
from .core import CREATE_FLAGS,ReelsMediaCue,binary,digest,read_json,run,write_json
from .reels_styles import filter_frame

VERSION='reels-media-v2-continuous'
VIDEO_EXT={'.mp4','.mov','.m4v','.webm','.mkv'}
IMAGE_EXT={'.png','.jpg','.jpeg','.webp'}
MAX_BYTES=200*1024*1024
MAX_TOTAL=500*1024*1024


def probe(source):
    try:
        info=json.loads(run([binary('ffprobe'),'-v','error','-show_entries',
            'stream=codec_type,width,height,duration:format=duration','-of','json',source],timeout=30))
        video=next(s for s in info['streams'] if s.get('codec_type')=='video')
        duration=float(video.get('duration') or info.get('format',{}).get('duration',0))
        w,h=int(video['width']),int(video['height'])
        if not math.isfinite(duration) or not 0<duration<=1800 or not 1<=w<=4096 or not 1<=h<=4096:raise ValueError()
        return {'duracao_s':duration,'largura':w,'altura':h}
    except (RuntimeError,ValueError,KeyError,StopIteration,subprocess.TimeoutExpired) as exc:
        raise ValueError('Use um clipe válido de até 30 minutos e resolução de até 4096 × 4096.') from exc


def import_files(path,files,guard=lambda:None):
    """Validate every file before committing a mixed image/video batch."""
    from .review_media import LOCK
    if not files or len(files)>12:raise ValueError('Envie de 1 a 12 fotos ou clipes por vez.')
    if sum(f.stat().st_size for f in files)>MAX_TOTAL:raise ValueError('Envie até 500 MB por vez.')
    assets=path/'assets';assets.mkdir(parents=True,exist_ok=True)
    prepared=[]
    with tempfile.TemporaryDirectory(prefix='reels-',dir=assets) as temp:
        temp=Path(temp)
        for source in files:
            ext=source.suffix.lower();filename=source.name[:180]
            if source.stat().st_size>MAX_BYTES:raise ValueError('Cada clipe pode ter até 200 MB.')
            if ext in VIDEO_EXT:
                meta=probe(source)
                with source.open('rb') as handle:sha=hashlib.file_digest(handle,'sha256').hexdigest()[:24]
                name='clip-'+sha+ext;poster='poster-'+sha+'.jpg';target=temp/poster
                run([binary('ffmpeg'),'-y','-v','error','-threads','1','-i',source,'-map','0:v:0',
                     '-frames:v','1','-vf','scale=320:320:force_original_aspect_ratio=decrease','-threads','1',target],timeout=45)
                prepared.append((name,source,{**meta,'nome_original':filename,'miniatura':poster},(poster,target),'videos'))
            elif ext in IMAGE_EXT:
                if source.stat().st_size>20*1024*1024:raise ValueError('Cada foto pode ter até 20 MB.')
                try:
                    with Image.open(source) as original:
                        if original.format not in ('PNG','JPEG','WEBP') or original.width*original.height>25_000_000:raise ValueError()
                        im=ImageOps.exif_transpose(original).convert('RGB');im.thumbnail((3840,3840),Image.Resampling.LANCZOS)
                        buf=io.BytesIO();im.save(buf,format='PNG');data=buf.getvalue()
                except (OSError,ValueError,Image.DecompressionBombError) as exc:
                    raise ValueError('Use fotos PNG, JPG ou WebP válidas de até 25 megapixels.') from exc
                name='media-'+hashlib.sha256(data).hexdigest()[:24]+'.png';target=temp/name;target.write_bytes(data)
                prepared.append((name,target,{'nome_original':filename,'identificacao':source.stem,'adicionada_na_revisao':True},None,'imagens'))
            else:raise ValueError('Use PNG, JPG, WebP, MP4, MOV, M4V, WebM ou MKV.')
        with LOCK:
            guard();sources=read_json(path/'sources.json',{'fontes':[]});created=[];added=[]
            try:
                for name,source,meta,poster,kind in prepared:
                    sources.setdefault(kind,[]);sources.setdefault(kind+'_meta',{})
                    for target_name,original in [(name,source)]+([poster] if poster else []):
                        target=assets/target_name
                        if not target.exists():
                            try:os.link(original,target)
                            except OSError:shutil.copy2(original,target)
                            created.append(target)
                    if name not in sources[kind]:sources[kind].append(name)
                    sources[kind+'_meta'][name]=meta
                    if name not in added:added.append(name)
                write_json(path/'sources.json',sources)
            except Exception:
                for target in created:target.unlink(missing_ok=True)
                raise
    return {k:sources.get(k,{} if k.endswith('_meta') else []) for k in ('imagens','imagens_meta','videos','videos_meta')}|{'adicionadas':added}


def asset(path,name,sources):
    target=(path/'assets'/name).resolve()
    if name not in sources.get('imagens',[])+sources.get('videos',[]) or target.parent!=(path/'assets').resolve() or not target.is_file():
        raise ValueError('Uma mídia escolhida não pertence ao projeto. Confira a biblioteca de fotos e clipes.')
    return target


def selected(settings,path):
    sources=read_json(path/'sources.json',{})
    names=settings.midias_reels if settings.modo_shorts=='clipes' else settings.fotos_shorts
    names=names or (sources.get('imagens',[])+sources.get('videos',[]) if settings.modo_shorts=='clipes' else sources.get('imagens',[]))
    if not names:raise ValueError('Adicione e selecione pelo menos uma foto ou clipe para a sequência.')
    for name in names:asset(path,name,sources)
    return list(dict.fromkeys(names))


def validate(settings,path,scenes):
    from .speech import phrases
    sources=read_json(path/'sources.json',{})
    selected(settings,path)
    anchors=set();first={}
    for cue in settings.trechos_reels:
        asset(path,cue.arquivo,sources)
        if settings.modo_shorts=='fotos' and cue.arquivo in sources.get('videos',[]):raise ValueError('Escolha Fotos e clipes para usar um vídeo.')
        if cue.cena>=len(scenes) or cue.frase>=len(phrases(scenes[cue.cena]['narracao_ptbr'])):
            raise ValueError('O roteiro mudou. Confira a cena e a frase dos trechos de mídia antes de renderizar.')
        if (cue.cena,cue.frase) in anchors:raise ValueError('Escolha somente uma mídia para iniciar em cada frase da cena.')
        anchors.add((cue.cena,cue.frase));first[cue.cena]=min(first.get(cue.cena,cue.frase),cue.frase)
        if cue.arquivo in sources.get('videos',[]):
            duration=sources.get('videos_meta',{}).get(cue.arquivo,{}).get('duracao_s',0)
            if cue.entrada_s>=duration or cue.saida_s is not None and cue.saida_s>duration+.01:
                raise ValueError('O corte escolhido ultrapassa a duração original do clipe.')
    if any(i!=0 for i in first.values()):raise ValueError('A primeira mídia de cada cena precisa começar na primeira frase.')


def crop_position(position):
    return {'esquerda':(0.,.5),'direita':(1.,.5),'superior':(.5,0.),'inferior':(.5,1.)}.get(position,(.5,.5))


def fit_image(image,mode='inteira',position='centro'):
    if mode=='preencher':return ImageOps.fit(image,(1080,1920),Image.Resampling.LANCZOS,centering=crop_position(position))
    if mode=='esticar':return image.resize((1080,1920),Image.Resampling.LANCZOS)
    background=ImageOps.fit(image,(270,480)).filter(ImageFilter.GaussianBlur(14)).resize((1080,1920),Image.Resampling.BILINEAR)
    foreground=ImageOps.contain(image,(1016,1800),Image.Resampling.LANCZOS)
    background.paste(foreground,((1080-foreground.width)//2,(1920-foreground.height)//2))
    return background


class VideoReader:
    """Sequential decoder, retaining one frame rather than the whole clip."""
    def __init__(self,path,mode,position='centro'):
        self.path=path;self.mode=mode;self.position=position;self.proc=None;self.index=-1;self.last=None

    def close(self):
        if self.proc:
            if self.proc.poll() is None:self.proc.kill()
            self.proc.wait();self.proc.stdout.close();self.proc=None

    def frame(self,seconds):
        index=max(0,int(seconds*24))
        if self.proc is None or index<self.index or index-self.index>48:
            self.close()
            if self.mode=='preencher':
                x,y=crop_position(self.position)
                vf=f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)*{x}:(ih-oh)*{y},setsar=1'
            elif self.mode=='esticar':vf='scale=1080:1920,setsar=1'
            else:vf='split=2[bg][fg];[bg]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:1,scale=1080:1920[base];[fg]scale=1016:1800:force_original_aspect_ratio=decrease[pic];[base][pic]overlay=(W-w)/2:(H-h)/2,setsar=1'
            self.proc=subprocess.Popen([binary('ffmpeg'),'-v','error','-threads','1','-ss',f'{index/24:.6f}','-i',str(self.path),
                '-an','-sn','-filter_complex_threads','1','-filter_complex',f'[0:v:0]fps=24,{vf}',
                '-threads','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=CREATE_FLAGS)
            self.index=index-1;self.last=None
        while self.index<index:
            data=bytearray();required=1080*1920*3
            while len(data)<required:
                part=self.proc.stdout.read(required-len(data))
                if not part:break
                data.extend(part)
            if len(data)!=required:
                if self.last is None:raise ValueError('Não foi possível decodificar este ponto do clipe. Confira o início e o fim do corte.')
                self.index=index;break
            self.last=Image.frombytes('RGB',(1080,1920),bytes(data));self.index+=1
        return self.last.copy()


class MediaPlayback:
    """One playback clock for the full render, never reset by a scene boundary."""
    def __init__(self):
        self.elapsed=0.;self.heads={};self.last=None


def continuous_slots(names,sources,elapsed,duration,index):
    spans=[float(sources['videos_meta'][n]['duracao_s']) for n in names]
    position=elapsed%sum(spans);item=0
    while position>=spans[item]-1e-7:
        position-=spans[item];item=(item+1)%len(names)
    slots=[];heads=[];local=0.
    while local<duration-1e-7:
        slots.append((local,ReelsMediaCue(arquivo=names[item],cena=index,frase=0)));heads.append(max(0.,position))
        local+=spans[item]-position;item=(item+1)%len(names);position=0.
    return slots,heads


class MediaAnimator:
    def __init__(self,scene,settings,index,total,beats,path,images,*,playback=None):
        self.path=path;self.settings=settings;self.sources=read_json(path/'sources.json',{})
        self.duration=max(.1,beats[-1]['fim']);self.readers=OrderedDict();self.pictures=OrderedDict()
        self.style='midias';self.story=None;self.w,self.h=1080,1920;self.previous_frame=None
        self.transition=scene.get('transicao','herdar')
        if self.transition=='herdar':self.transition=settings.transicao
        self.transition_duration=scene.get('duracao_transicao') or settings.duracao_transicao
        playback=playback if playback is not None else MediaPlayback()
        previous=playback.last;self.playheads=[];self.continuous_from_previous=False
        cues=sorted((c for c in settings.trechos_reels if c.cena==index),key=lambda c:c.frase)
        if cues:self.slots=[(0. if c.frase==0 else beats[c.frase]['inicio'],c) for c in cues]
        else:
            names=selected(settings,path)
            if settings.continuar_clipes and not settings.trechos_reels and all(n in self.sources.get('videos',[]) for n in names):
                self.slots,self.playheads=continuous_slots(names,self.sources,playback.elapsed,self.duration,index)
            else:
                if len(names)>=total:names=names[math.floor(index*len(names)/total):math.floor((index+1)*len(names)/total)]
                else:names=[names[index%len(names)]]
                self.slots=[(self.duration*i/len(names),ReelsMediaCue(arquivo=n,cena=index,frase=0)) for i,n in enumerate(names)]
        planned=bool(self.playheads)
        for i,(start,cue) in enumerate(self.slots):
            end=self.slots[i+1][0] if i+1<len(self.slots) else self.duration
            identity=(cue.arquivo,cue.entrada_s,cue.saida_s)
            head=self.playheads[i] if planned else playback.heads.get(identity,0.) if settings.continuar_clipes and not cue.reiniciar else 0.
            if not planned:self.playheads.append(head)
            video=cue.arquivo in self.sources.get('videos',[])
            if i==0:self.continuous_from_previous=bool(video and settings.continuar_clipes and not cue.reiniciar and previous and previous[0]==identity and abs(previous[1]-head)<1e-6)
            playback.heads[identity]=head+max(0.,end-start)
            playback.last=(identity,playback.heads[identity]) if video else None
        playback.elapsed+=self.duration
        fingerprints=[]
        for _,cue in self.slots:
            target=asset(path,cue.arquivo,self.sources)
            with target.open('rb') as handle:fingerprints.append((cue.arquivo,hashlib.file_digest(handle,'sha256').hexdigest()))
        self.key=digest(VERSION,fingerprints,[(t,c.model_dump()) for t,c in self.slots],self.duration,self.playheads,
                        settings.enquadramento_reels,settings.posicao_recorte_reels,self.continuous_from_previous,
                        settings.filtro_reels,settings.transicao_midias_shorts,settings.duracao_transicao_midias,self.transition,self.transition_duration)

    def close(self):
        for reader in self.readers.values():reader.close()
        self.readers.clear();self.pictures.clear()

    def set_previous(self,frame,collage=None):
        if self.continuous_from_previous:return
        if self.transition!='nenhuma':self.previous_frame=frame;self.key=digest(self.key,hashlib.sha256(frame.tobytes()).hexdigest())

    def picture(self,slot,seconds):
        start,cue=self.slots[slot];name=cue.arquivo
        mode=self.settings.enquadramento_reels if cue.ajuste=='herdar' else cue.ajuste
        position=self.settings.posicao_recorte_reels if cue.posicao_recorte=='herdar' else cue.posicao_recorte
        if name in self.sources.get('videos',[]):
            duration=self.sources['videos_meta'][name]['duracao_s'];end=cue.saida_s or duration;span=end-cue.entrada_s
            seconds=max(0,seconds)+self.playheads[slot]
            offset=seconds%span if cue.fim=='repetir' else min(seconds,max(0,span-1/24))
            moment=min(max(cue.entrada_s,end-1/24),cue.entrada_s+offset)
            key=(name,mode,position)
            if key not in self.readers:self.readers[key]=VideoReader(asset(self.path,name,self.sources),mode,position)
            self.readers.move_to_end(key)
            while len(self.readers)>2:self.readers.popitem(last=False)[1].close()
            canvas=self.readers[key].frame(moment)
        else:
            key=(name,mode,position)
            if key not in self.pictures:
                with Image.open(asset(self.path,name,self.sources)) as im:self.pictures[key]=fit_image(ImageOps.exif_transpose(im).convert('RGB'),mode,position)
            self.pictures.move_to_end(key)
            while len(self.pictures)>3:self.pictures.popitem(last=False)
            canvas=self.pictures[key].copy()
            if self.settings.animar_elementos:
                end=self.slots[slot+1][0] if slot+1<len(self.slots) else self.duration
                phase=min(1,max(0,seconds/max(.1,end-start)))
                zoom=1+.018*math.sin(math.pi*phase)
                canvas=ImageOps.fit(canvas.resize((round(1080*zoom),round(1920*zoom)),Image.Resampling.BICUBIC),(1080,1920))
        return filter_frame(canvas,self.settings.filtro_reels)

    def _frame_raw(self,t):
        slot=max((i for i,(start,_) in enumerate(self.slots) if start<=t),default=0)
        start,cue=self.slots[slot];local=max(0,t-start);canvas=self.picture(slot,local)
        transition=cue.transicao if cue.transicao!='herdar' else self.settings.transicao_midias_shorts
        following=self.slots[slot+1][0] if slot+1<len(self.slots) else self.duration
        fade=min(self.settings.duracao_transicao_midias,(following-start)*.45)
        if slot and transition!='nenhuma' and local<fade:
            from .transitions import transition_frame
            old=self.picture(slot-1,max(0,start-self.slots[slot-1][0]-1/24))
            canvas=transition_frame(old,canvas,'dissolver' if transition=='padrao' else transition,local/fade)
        return canvas

    def frame(self,t):
        canvas=self._frame_raw(t)
        if self.previous_frame is None or self.transition=='nenhuma' or t>=self.transition_duration:return canvas
        from .transitions import transition_frame
        return transition_frame(self.previous_frame,canvas,'dissolver' if self.transition=='padrao' else self.transition,t/self.transition_duration)
