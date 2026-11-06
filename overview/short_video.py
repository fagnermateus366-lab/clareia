"""Phone compositions and real-file eligibility for YouTube Shorts."""
from __future__ import annotations

import hashlib
import json
from PIL import Image, ImageDraw, ImageOps

from .core import Settings, binary, digest, read_json, run

VERSION = 'mobile-composition-v2-balanced'
MAX_SECONDS = 180.
# Reserve the right rail and bottom controls of short-video players.
STAGE = (48, 112, 936, 1432)
CAPTION_BOX = (64, 1460, 936, 1660)


def stage_bounds(settings):
    from .caption_presentation import state,large_enabled
    if not large_enabled(settings):
        return (24,48,1020,1816) if state(settings)[1] else (0,0,1080,1920)
    return (48,440,936,1696) if settings.posicao_legenda=='superior' else STAGE


def caption_box(position,index=0):
    if position=='alternada':position=('superior','centro','inferior')[index%3]
    return {'superior':(64,160,936,360),'centro':(64,860,936,1060)}.get(position,CAPTION_BOX)


def is_short(settings):
    return settings.tipo_video == 'shorts'


def verify_export(path, settings):
    if not is_short(settings):return None
    try:
        raw = json.loads(run([binary('ffprobe'),'-v','error','-show_entries',
                              'stream=codec_type,width,height,duration:format=duration','-of','json',path/'export/video.mp4'],timeout=30))
    except (RuntimeError,ValueError) as exc:
        raise ValueError('Não foi possível conferir o MP4 deste Shorts. Renderize novamente antes de enviar.') from exc
    video = next((s for s in raw.get('streams',[]) if s.get('codec_type')=='video'),{})
    seconds = max(float(raw.get('format',{}).get('duration',0)),float(video.get('duration',0)))
    width,height = video.get('width',0),video.get('height',0)
    if not width or height <= width or abs(width/height-9/16) > .005:
        raise ValueError('Este projeto é Reels / Shorts, mas o MP4 salvo não está em 9:16. Renderize novamente antes de enviar.')
    if not 0 < seconds <= MAX_SECONDS:
        raise ValueError(f'O vídeo tem {seconds:.1f} segundos. Shorts do YouTube precisam de até 180 segundos. '
                         'Revise a duração ou escolha Vídeo comum; a narração não será cortada.')
    return {'tipo':'shorts','largura':width,'altura':height,'duracao_s':seconds,'elegivel':True}


def verify_project_export(path):
    data = read_json(path/'project.json',{})
    return verify_export(path,Settings.model_validate(data.get('config',{})))


def animator_for(scene,settings,index,total,beats,path,images,*,playback=None):
    from .motion import Animator
    if not is_short(settings):
        from .scene_images import animator_for_images
        return animator_for_images(scene,settings,index,total,beats,path,images)
    if settings.modo_shorts in ('fotos','clipes'):
        from .reels_media import MediaAnimator
        return MediaAnimator(scene,settings,index,total,beats,path,images,playback=playback)
    return MobileAnimator(scene,settings,index,total,beats,path,images)


class MobileAnimator:
    """Reflow inside a portrait stage at native pixels, with separate captions.

    The existing drawing engines receive a taller, narrower canvas, so images,
    diagrams and actors are composed vertically rather than scaling a 16:9 frame.
    """
    def __init__(self,scene,settings,index,total,beats,path,images):
        from .motion import Animator
        self.bounds=stage_bounds(settings)
        left,top,right,bottom = self.bounds
        self.inner = Animator(scene,settings,index,total,beats,path,images,
                              canvas_size=(right-left,bottom-top),mobile=True)
        self.w,self.h = 1080,1920
        self.style = self.inner.style
        self.transition,self.transition_duration = self.inner.transition,self.inner.transition_duration
        self.previous_frame = None
        self.story = self  # Renderer can request a snapshot; passages use full frames.
        self.filter=settings.filtro_reels
        self.key = digest(VERSION,self.inner.key,self.bounds,CAPTION_BOX,settings.legenda_shorts,settings.efeito_legenda,settings.posicao_legenda,settings.composicao_shorts,self.filter)
        self.background = Image.new('RGB',(self.w,self.h),self.inner.bg)
        if self.inner.background_key:
            from .video_backgrounds import canvas
            self.background=canvas(scene,settings,path,(self.w,self.h),self.inner.bg)
        if self.style == 'colagem_documental':
            from .collage import ASSETS
            self.background = ImageOps.fit(Image.open(ASSETS/'parchment.png').convert('RGB'),(self.w,self.h))
        self.mask = Image.new('L',(right-left,bottom-top))
        ImageDraw.Draw(self.mask).rounded_rectangle((0,0,self.mask.width-1,self.mask.height-1),32,fill=255)
        self.total,self.index = total,index

    def snapshot(self,*args):return None

    def close(self):self.inner.close()

    def set_previous(self,frame,collage=None):
        if self.transition != 'nenhuma':
            self.previous_frame = frame
            self.key = digest(self.key,hashlib.sha256(frame.tobytes()).hexdigest())

    def _frame_raw(self,t):
        canvas = self.background.copy()
        stage = self.inner._frame_raw(t)
        canvas.paste(stage,self.bounds[:2],self.mask)
        from .reels_styles import filter_frame
        return filter_frame(canvas,self.filter)

    def frame(self,t):
        canvas = self._frame_raw(t)
        if self.previous_frame is None or self.transition=='nenhuma' or t>=self.transition_duration:
            return canvas
        from .transitions import transition_frame
        effect = 'dissolver' if self.transition=='padrao' else self.transition
        return transition_frame(self.previous_frame,canvas,effect,t/self.transition_duration)
