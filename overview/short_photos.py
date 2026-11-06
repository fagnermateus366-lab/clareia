"""A complete-photo slideshow with ambient background and gentle dissolves."""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import math
from PIL import Image,ImageDraw,ImageFilter,ImageOps

from .core import digest

VERSION='short-photo-sequence-v1'


def selected(settings,images,path):
    names=settings.fotos_shorts or images
    if not names:raise ValueError('Adicione pelo menos uma imagem para criar um Shorts com fotos em sequência.')
    result=[]
    for name in dict.fromkeys(names):
        target=(path/'assets'/name).resolve()
        if name not in images or target.parent!=(path/'assets').resolve() or not target.is_file():
            raise ValueError('Uma foto escolhida não pertence ao projeto. Confira as imagens selecionadas.')
        result.append((name,target))
    return result


def gallery_board(scene):
    from .speech import phrases
    return {'momentos':[{'frase':i,'titulo':scene['titulo'],'composicao':'conceito',
                         'elementos':[{'rotulo':scene['titulo'],'icone':'documento'}]}
                        for i,_ in enumerate(phrases(scene['narracao_ptbr']))]}


class PhotoAnimator:
    def __init__(self,scene,settings,index,total,beats,path,images):
        available=selected(settings,images,path)
        if len(available)>=total:
            first=math.floor(index*len(available)/total);end=math.floor((index+1)*len(available)/total)
            available=available[first:end]
        else:available=[available[index%len(available)]]
        self.photos=available;self.duration=max(.1,beats[-1]['fim']);self.cache=OrderedDict()
        self.style='fotos';self.story=None;self.w,self.h=1080,1920
        self.transition=scene.get('transicao','herdar')
        if self.transition=='herdar':self.transition=settings.transicao
        self.transition_duration=scene.get('duracao_transicao') or settings.duracao_transicao
        self.previous_frame=None
        self.moving=settings.animar_elementos
        fingerprints=[]
        for name,target in self.photos:
            with target.open('rb') as f:fingerprints.append((name,hashlib.file_digest(f,'sha256').hexdigest()))
        self.key=digest(VERSION,fingerprints,self.duration,self.moving,self.transition,self.transition_duration,
                        settings.legenda_shorts,settings.efeito_legenda,settings.posicao_legenda)

    def set_previous(self,frame,collage=None):
        if self.transition!='nenhuma':
            self.previous_frame=frame;self.key=digest(self.key,hashlib.sha256(frame.tobytes()).hexdigest())

    def photo(self,index,phase):
        if index not in self.cache:
            image=ImageOps.exif_transpose(Image.open(self.photos[index][1])).convert('RGB')
            background=ImageOps.fit(image,(270,480)).filter(ImageFilter.GaussianBlur(14)).resize((1080,1920),Image.Resampling.BILINEAR)
            background=Image.blend(background,Image.new('RGB',background.size,'#10151a'),.24)
            foreground=ImageOps.contain(image,(1016,1800),Image.Resampling.LANCZOS)
            self.cache[index]=(background,foreground)
            while len(self.cache)>3:self.cache.popitem(last=False)
        self.cache.move_to_end(index)
        background,foreground=self.cache[index];canvas=background.copy()
        zoom=1+.018*math.sin(math.pi*min(1,max(0,phase))) if self.moving else 1
        picture=foreground.resize((round(foreground.width*zoom),round(foreground.height*zoom)),Image.Resampling.BICUBIC) if zoom!=1 else foreground
        canvas.paste(picture,((1080-picture.width)//2,(1920-picture.height)//2))
        return canvas

    def _frame_raw(self,t):
        slot=self.duration/len(self.photos)
        index=min(len(self.photos)-1,max(0,int(t/slot)));local=t-index*slot
        canvas=self.photo(index,local/slot)
        fade=min(.8,slot*.22)
        if index and local<fade:
            previous=self.photo(index-1,1)
            p=local/fade;p=p*p*(3-2*p)
            canvas=Image.blend(previous,canvas,p)
        return canvas

    def frame(self,t):
        canvas=self._frame_raw(t)
        if self.previous_frame is None or self.transition=='nenhuma' or t>=self.transition_duration:return canvas
        from .transitions import transition_frame
        return transition_frame(self.previous_frame,canvas,'dissolver' if self.transition=='padrao' else self.transition,t/self.transition_duration)


def demo_photos(folder):
    """Authorial landscapes solely for a preview, without a network request."""
    folder.mkdir(parents=True,exist_ok=True)
    names=[]
    for i,(sky,land) in enumerate([('#97c9e5','#4f7775'),('#edb88b','#755f82'),('#a8c8b6','#527d52')]):
        name=f'paisagem-demonstracao-{i+1}.png';target=folder/name
        if not target.exists():
            im=Image.new('RGB',(1080,1920),sky);d=ImageDraw.Draw(im)
            d.ellipse((620,250,850,480),fill='#fff1cb')
            d.polygon([(0,1150),(380,640),(790,1190),(1080,810),(1080,1920),(0,1920)],fill=land)
            d.polygon([(0,1450),(480,1130),(1080,1470),(1080,1920),(0,1920)],fill='#243e42')
            im.save(target)
        names.append(name)
    return names
