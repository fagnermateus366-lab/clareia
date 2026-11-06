"""Optional, equally timed reference photos in a normal-video scene.

The original renderer still lays out each photo. Only the selected image changes;
narration, phrase animation time, framing and subtitle timing remain continuous.
"""
from collections import OrderedDict
import math
from PIL import Image
from .core import digest


def animator_for_images(scene,settings,index,total,beats,path,images):
    from .motion import Animator
    names=scene.get('imagens_cena',[]) if scene.get('usar_imagem',True) else []
    if len(names)>5:raise ValueError('Escolha até cinco imagens por cena.')
    if len(names)!=len(set(names)):raise ValueError('Escolha imagens diferentes para a sequência da cena.')
    hashes=[]
    for name in names:
        target=(path/'assets'/name).resolve()
        if name not in images or target.parent!=(path/'assets').resolve() or not target.is_file():
            raise ValueError('Uma imagem da sequência não pertence ao projeto.')
        hashes.append((name,digest(target.read_bytes().hex())))
    if len(names)<2:
        return Animator({**scene,'imagem':names[0]} if names else scene,settings,index,total,beats,path,images)
    return ImageSequence(scene,settings,index,total,beats,path,images,names,hashes)


class ImageSequence:
    def __init__(self,scene,settings,index,total,beats,path,images,names,hashes):
        self.scene,self.settings,self.index,self.total,self.beats,self.path,self.images=scene,settings,index,total,beats,path,images
        self.names=names;self.duration=beats[-1]['fim'];self.slot=self.duration/len(names)
        self.fade=min(.45,self.slot*.15) if scene.get('transicao_imagens','dissolver')=='dissolver' else 0
        self.children=OrderedDict();self.previous_frame=None;self.previous_collage=None
        first=self._child(0);self.style=first.style;self.w,self.h=first.w,first.h
        self.transition,self.transition_duration=first.transition,first.transition_duration
        self.story=self
        self.key=digest('scene-reference-sequence-v1',first.key,hashes,self.duration,self.fade)
        self.image_cues=[{'arquivo':name,'inicio':i*self.slot,'fim':(i+1)*self.slot} for i,name in enumerate(names)]

    def _index(self,t):return min(len(self.names)-1,max(0,int(max(0,t)/self.slot)))

    def _child(self,index):
        from .motion import Animator
        if index in self.children:
            self.children.move_to_end(index);return self.children[index]
        child=Animator({**self.scene,'imagem':self.names[index],'imagens_cena':[]},self.settings,self.index,self.total,self.beats,self.path,self.images)
        if child.style=='shotcraft':
            # Render only this image's interval plus its outgoing dissolve,
            # instead of producing the whole scene five times.
            offset=index*self.slot
            length=min(self.duration,(index+1)*self.slot+self.fade)-offset
            child.story.props.update(timeOffset=offset,durationInFrames=max(1,math.ceil(length*24)))
            child.story.frame_offset=offset
            child.key=digest(child.key,'sequence-interval-v1',offset,length)
            child.story.key=child.key
        if index==0 and self.previous_frame is not None:child.set_previous(self.previous_frame,self.previous_collage)
        self.children[index]=child
        while len(self.children)>2:
            _,old=self.children.popitem(last=False);old.close()
        return child

    def set_previous(self,frame,collage=None):
        self.previous_frame,self.previous_collage=frame,collage
        self._child(0).set_previous(frame,collage)
        self.key=digest(self.key,'previous-context',self._child(0).key)

    def _frame_raw(self,t):return self._child(self._index(t))._frame_raw(t)

    def frame(self,t):
        index=self._index(t);current=self._child(index).frame(t)
        local=t-index*self.slot
        if index and self.fade and local<self.fade:
            previous=self._child(index-1).frame(t)
            progress=max(0,min(1,local/self.fade));progress=progress*progress*(3-2*progress)
            return Image.blend(previous.convert('RGB'),current.convert('RGB'),progress)
        return current

    def snapshot(self,t,index):return self._child(self._index(t)).story.snapshot(t,index)

    def close(self):
        for child in self.children.values():child.close()
        self.children.clear()
