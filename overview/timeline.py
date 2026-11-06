"""Keep scene changes silent and start each spoken phrase on its finished visual."""
from __future__ import annotations

import copy
import math

import numpy as np
import soundfile as sf

from .core import digest,read_json,write_json
from .storyboard import timed

VERSION='transition-speech-sync-v3-word-clocks'
FPS=24


def transition_durations(scene,settings,count,has_previous=False,board=None):
    if board is not None and len(board['momentos'])!=count:raise ValueError('Storyboard e áudio têm números diferentes de frases.')
    style=scene.get('animacao','herdar')
    if style=='herdar':style=settings.animacao
    effect=scene.get('transicao','herdar')
    if effect=='herdar':effect=settings.transicao
    length=scene.get('duracao_transicao') or settings.duracao_transicao
    if style=='colagem_documental':
        from .collage_pacing import passage_duration
        length=passage_duration(effect,length)
    durations=[0.]*count
    if effect!='nenhuma' and has_previous and count:durations[0]=length
    return effect,durations


def synchronize(scene,settings,path,board,audio,meta,has_previous=False):
    """Insert silence into a separate cached WAV; preserve every original sample.

    Visual starts and spoken cues have separate clocks. Changes start on a video
    frame; speech resumes on a frame after the entire transition has finished.
    Original inter-phrase pauses, teaching pauses and trailing audio stay intact.
    """
    effect,requested=transition_durations(scene,settings,len(meta['legendas']),has_previous,board)
    if not any(requested):return audio,meta,timed(board,meta['legendas'],meta['duracao'])
    if len(board['momentos'])!=len(meta['legendas']):raise ValueError('Storyboard e áudio têm números diferentes de frases.')
    key=digest(VERSION,meta['hash'],effect,requested,FPS)
    folder=path/'cache/audio';folder.mkdir(parents=True,exist_ok=True)
    wav=folder/('timed-'+key+'.wav');json_path=wav.with_suffix('.json')
    saved=read_json(json_path)
    if wav.is_file() and saved and saved.get('bytes')==wav.stat().st_size:
        beats=[{**b,**clock} for b,clock in zip(board['momentos'],saved['clocks'])]
        return wav,saved['audio'],beats
    result=copy.deepcopy(meta);result['hash']=key;result['transicoes']=[]
    shift=0;cursor=0;clocks=[]
    temporary=wav.with_suffix('.partial.wav')
    with sf.SoundFile(audio) as source:
        rate=source.samplerate;quantum=rate/FPS
        if not quantum.is_integer():raise ValueError('Taxa de áudio incompatível com a sincronização de quadros.')
        quantum=int(quantum)
        with sf.SoundFile(temporary,'w',samplerate=rate,channels=source.channels,subtype='PCM_16') as out:
            for i,(cue,seconds) in enumerate(zip(meta['legendas'],requested)):
                position=round(cue['inicio']*rate)
                if position<cursor or position>len(source):raise ValueError('Limites de áudio inválidos na narração.')
                out.write(source.read(position-cursor,dtype='int16',always_2d=True));cursor=position
                pad=(-((position+shift)%quantum))%quantum if seconds else 0
                gap=math.ceil(seconds*FPS)*quantum if seconds else 0
                visual=(position+shift+pad)/rate
                if pad+gap:out.write(np.zeros((pad+gap,source.channels),dtype='int16'))
                shift+=pad+gap
                result['legendas'][i]['inicio']=(position+shift)/rate
                result['legendas'][i]['fim']=cue['fim']+shift/rate
                clocks.append({'inicio':visual,'fala_inicio':result['legendas'][i]['inicio'],'transicao_s':gap/rate})
                if gap:result['transicoes'].append({'momento':i,'inicio':visual,'fim':visual+gap/rate,'efeito':effect})
            while True:
                chunk=source.read(24000,dtype='int16',always_2d=True)
                if not len(chunk):break
                out.write(chunk)
            ending=(-out.tell())%quantum
            if ending:out.write(np.zeros((ending,source.channels),dtype='int16'))
            result['duracao']=out.tell()/rate
    import os
    os.replace(temporary,wav)
    for i,clock in enumerate(clocks):clock['fim']=clocks[i+1]['inicio'] if i+1<len(clocks) else result['duracao']
    if result.get('palavras'):
        for word in result['palavras']:
            index=max((i for i,c in enumerate(meta['legendas']) if c['inicio']<=word['inicio']+.001),default=0)
            delta=result['legendas'][index]['inicio']-meta['legendas'][index]['inicio']
            word['inicio']+=delta;word['fim']+=delta
    write_json(json_path,{'audio':result,'clocks':clocks,'bytes':wav.stat().st_size})
    beats=[{**b,**clock} for b,clock in zip(board['momentos'],clocks)]
    return wav,result,beats
