"""Isolated Remotion plates inside Clareia's existing narration/export pipeline.

Old animation styles never call this module. Only closed, text/image props enter
the renderer. Remotion creates a silent plate; existing voice/captions/music are
composed by the original Python/FFmpeg pipeline. One browser page at a time.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

from PIL import Image,ImageOps

from .core import ROOT,CREATE_FLAGS,binary,digest,read_json,write_json,run
from .shotcraft import VERSION,PALETTES

RENDERER=ROOT/'overview/shotcraft_renderer'
LOCK=threading.RLock()


def node_binary():
    found=shutil.which('node')
    if found:return found
    bundled=Path(sys.base_prefix).parent/'node/bin/node.exe'
    if bundled.is_file():return str(bundled)
    raise ValueError('Node.js não encontrado para o novo motor ShotCraft. As animações anteriores continuam disponíveis.')


def fingerprint():
    paths=[RENDERER/'package.json',RENDERER/'render.mjs',*sorted((RENDERER/'src').rglob('*'))]
    return digest(VERSION,[(str(p.relative_to(RENDERER)),hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths if p.is_file()])


def available():
    return (RENDERER/'node_modules/@remotion/renderer/package.json').is_file()


def photo_data(image):
    if image is None:return None
    image=ImageOps.exif_transpose(image)
    alpha=(image.mode in ('RGBA','LA') and image.getchannel('A').getextrema()[0]<255) or 'transparency' in image.info
    picture=image.convert('RGBA' if alpha else 'RGB');picture.thumbnail((1920,1920),Image.Resampling.LANCZOS)
    buffer=io.BytesIO();picture.save(buffer,format='PNG' if alpha else 'JPEG',**({} if alpha else {'quality':93}))
    return 'data:image/'+('png' if alpha else 'jpeg')+';base64,'+base64.b64encode(buffer.getvalue()).decode('ascii')


def manifest(animator,settings):
    from .shotcraft_figures import apply,data_uri
    from .speech import phrases
    # Direct posters/previews have no model plan; resolve the same safe nouns.
    import copy
    moments=apply({'momentos':copy.deepcopy(animator.beats)},phrases(animator.scene['narracao_ptbr']),animator.scene,settings=settings,strict=True,photo=animator.asset is not None)['momentos']
    figures={e['figura']:data_uri(e['figura']) for b in moments for e in b['elementos'] if e.get('figura') and not b.get('receita','').startswith('volume_')}
    from .shotcraft_figures import catalog as figure_catalog
    known={record['id'] for record in figure_catalog()}
    if moments and all(b.get('receita','').startswith('volume_') for b in moments):
        from .three_catalog import SUBJECT_IDS
        known&=SUBJECT_IDS
    manual=[key.strip() for key in animator.scene.get('shotcraft_figuras','').split(';') if key.strip() in known]
    sequence=manual if len(manual)>1 and animator.scene.get('distribuicao_figuras','tempo_igual')=='tempo_igual' else []
    if any(not b.get('receita','').startswith('volume_') for b in moments):
        for key in sequence:figures[key]=data_uri(key)
    duration=max(b['fim'] for b in animator.beats)
    result={'width':animator.w,'height':animator.h,'fps':24,'durationInFrames':max(1,math.ceil(duration*24)),
        'theme':settings.shotcraft_estilo,'finish':settings.shotcraft_acabamento,'energy':settings.shotcraft_intensidade,'family':settings.shotcraft_modelo,
        'animate':animator.animate,'camera':animator.camera_dynamic,'title':animator.scene['titulo'],
        'moments':moments,'figures':figures,'photo':photo_data(animator.asset),'staticPhoto':animator.static_image,'manualFigures':sequence}
    if any(b.get('receita','').startswith('volume_') for b in moments):
        assets=ROOT/'overview/three_gallery/public'
        result['threeAssets']={key:'data:'+mime+';base64,'+base64.b64encode((assets/name).read_bytes()).decode('ascii') for key,name,mime in
            [('model','models/clareia-robot.glb','model/gltf-binary'),('font','fonts/noto_sans_pt.typeface.json','application/json')]}
        result['threeOptions']=animator.scene.get('three_options') or settings.three_options.model_dump()
    return result


def _stop_owned_tree(proc):
    import psutil
    if proc.poll() is not None:return
    try:
        owned=psutil.Process(proc.pid);children=owned.children(recursive=True)
        for child in reversed(children):
            try:child.terminate()
            except psutil.Error:pass
        proc.terminate();proc.wait(timeout=10)
    except (psutil.Error,subprocess.TimeoutExpired):
        if proc.poll() is None:proc.kill();proc.wait()


def plate(props,path,key,*,pause_file=None):
    """Atomic cached silent plate. No restart of the user's browser or studio."""
    if not available():raise ValueError('O motor ShotCraft ainda não está instalado. Use instalar-shotcraft.bat; os estilos anteriores foram preservados.')
    cache=path/'cache/sc';target=cache/(key+'.mp4');marker=cache/(key+'.json')
    with LOCK:
        record=read_json(marker,{})
        if target.is_file() and record.get('bytes')==target.stat().st_size and record.get('frames')==props['durationInFrames']:return target
        cache.mkdir(parents=True,exist_ok=True);manifest_path=cache/(key+'.props.json');write_json(manifest_path,props)
        bundle=ROOT/'output/shotcraft-bundles'/fingerprint();temporary=cache/(key+'.partial.mp4')
        logfile=cache/(key+'.log');pause_file=pause_file or path/'pause.request'
        args=[node_binary(),str(RENDERER/'render.mjs'),str(manifest_path.resolve()),str(temporary.resolve()),str(bundle.resolve()),str(pause_file.resolve())]
        started=time.monotonic()
        peak_rss=0;last_progress=None
        import psutil
        from .core import set_status
        state=read_json(path/'status.json',{})
        if state.get('status')=='renderizando':
            set_status(path,'renderizando','ShotCraft · preparando o novo modelo de animação',state.get('progresso',0))
        with logfile.open('w',encoding='utf-8') as log:
            proc=subprocess.Popen(args,cwd=RENDERER,stdout=log,stderr=log,creationflags=CREATE_FLAGS)
            try:
                while proc.poll() is None:
                    if pause_file.exists():
                        from .render import Paused
                        raise Paused('Animação ShotCraft pausada; voz e cenas prontas preservadas.')
                    try:
                        parent=psutil.Process(proc.pid);rss=parent.memory_info().rss
                        for child in parent.children(recursive=True):
                            try:rss+=child.memory_info().rss
                            except psutil.Error:pass
                        peak_rss=max(peak_rss,rss)
                    except psutil.Error:pass
                    if state.get('status')=='renderizando':
                        import re
                        content=logfile.read_text('utf-8',errors='replace')[-1000:]
                        progress=re.findall(r'Progress (\d+)%',content)
                        if progress and progress[-1]!=last_progress:
                            last_progress=progress[-1]
                            set_status(path,'renderizando',f'ShotCraft · novo modelo de animação · {last_progress}%',state.get('progresso',0))
                    time.sleep(.2)
                if proc.returncode:
                    detail=logfile.read_text('utf-8',errors='replace')[-2400:]
                    raise RuntimeError('O novo motor ShotCraft não concluiu esta cena. A narração foi preservada. '+detail)
            finally:_stop_owned_tree(proc)
        info=json.loads(run([binary('ffprobe'),'-v','error','-show_entries','stream=codec_type,width,height:format=duration','-of','json',temporary]))
        video=next((s for s in info.get('streams',[]) if s.get('codec_type')=='video'),{})
        seconds=props['durationInFrames']/props['fps']
        if (video.get('width'),video.get('height'))!=(props['width'],props['height']) or abs(float(info.get('format',{}).get('duration',0))-seconds)>.1:
            raise RuntimeError('A duração ou o formato da animação ShotCraft não corresponde à narração. A cena não foi aceita.')
        temporary.replace(target)
        write_json(marker,{'bytes':target.stat().st_size,'frames':props['durationInFrames'],'duracao_s':seconds,
            'tempo_s':round(time.monotonic()-started,3),'motor':'Remotion 4.0.538','concorrencia':1,'fonte':fingerprint()})
        record=read_json(marker);record['pico_rss_soma_mb']=round(peak_rss/1024**2,1);write_json(marker,record)
        return target


class FrameReader:
    """Decode at most one frame, at the exact stage size, from a silent plate."""
    def __init__(self,path,width,height):
        self.path=path;self.width=width;self.height=height;self.proc=None;self.index=-1;self.last=None

    def close(self):
        if self.proc:
            if self.proc.poll() is None:self.proc.kill()
            self.proc.wait();self.proc.stdout.close();self.proc=None

    def frame(self,seconds):
        index=max(0,int(seconds*24+1e-5))
        if self.proc is None or index<self.index or index-self.index>48:
            self.close()
            self.proc=subprocess.Popen([binary('ffmpeg'),'-v','error','-threads','1','-ss',f'{index/24:.6f}','-i',str(self.path),
                '-an','-sn','-threads','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=CREATE_FLAGS)
            self.index=index-1;self.last=None
        while self.index<index:
            data=bytearray();required=self.width*self.height*3
            while len(data)<required:
                part=self.proc.stdout.read(required-len(data))
                if not part:break
                data.extend(part)
            if len(data)!=required:
                if self.last is None:raise RuntimeError('O quadro da animação ShotCraft não pôde ser lido.')
                self.index=index;break
            self.last=Image.frombytes('RGB',(self.width,self.height),bytes(data));self.index+=1
        return self.last.copy()


class ShotcraftStage:
    def __init__(self,animator,settings,path):
        self.a=animator;self.path=path;self.settings=settings;self.props=manifest(animator,settings);self.reader=None
        animator.bg,animator.card,animator.fg,animator.accent,animator.muted=PALETTES[settings.shotcraft_estilo]
        animator.key=digest(animator.key,fingerprint(),self.props)
        self.key=animator.key

    def frame(self,t,*args):
        if self.reader is None:
            target=plate(self.props,self.path,self.key)
            self.reader=FrameReader(target,self.a.w,self.a.h)
        return self.reader.frame(t-getattr(self,'frame_offset',0))

    def close(self):
        if self.reader:self.reader.close();self.reader=None
