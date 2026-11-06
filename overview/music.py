"""Licensed local music library and bounded-memory, narration-first audio mixing."""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit

import httpx
import numpy as np
import soundfile as sf

from .core import MODELS, ROOT, binary, digest, read_json, run, write_json

VERSION='music-bed-v2'
LIBRARY=MODELS/'music'
CATALOG=ROOT/'overview/assets/music/catalog.json'
SR=48000
LOCK=threading.RLock()
MAX_BYTES=120_000_000


def catalog():
    tracks=read_json(CATALOG,[])
    for path in sorted((LIBRARY/'uploads').glob('*.json')):
        record=read_json(path,{})
        if re.fullmatch(r'user-[a-f0-9]{24}',record.get('id','')):tracks.append(record)
    return tracks


def track_record(track_id):
    if not re.fullmatch(r'[a-z0-9-]{1,80}',track_id):raise ValueError('Faixa de música inválida.')
    record=next((t for t in catalog() if t['id']==track_id),None)
    if record is None:raise ValueError('Música não encontrada na biblioteca. Escolha outra faixa.')
    return record


def track_path(record):
    return LIBRARY/('uploads' if record['id'].startswith('user-') else 'tracks')/(record['id']+'.'+('wav' if record['id'].startswith('user-') else 'mp3'))


def ensure_track(track_id):
    record=track_record(track_id)
    target=track_path(record)
    with LOCK:
        if target.is_file():return target
        if track_id.startswith('user-'):raise ValueError('O arquivo da música importada não está mais disponível.')
        url=record['download']
        parsed=urlsplit(url)
        if parsed.scheme!='https' or parsed.netloc!='incompetech.com' or not parsed.path.startswith('/music/royalty-free/mp3-royaltyfree/'):
            raise ValueError('Origem da música inválida.')
        target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_suffix('.partial')
        try:
            with httpx.stream('GET',url,timeout=45,follow_redirects=False) as response:
                response.raise_for_status()
                size=0
                with temp.open('wb') as out:
                    for chunk in response.iter_bytes(256*1024):
                        size+=len(chunk)
                        if size>MAX_BYTES:raise ValueError('Música maior que 120 MB.')
                        out.write(chunk)
            if size<1024:raise ValueError('Download da música incompleto.')
            if record.get('sha256'):
                with temp.open('rb') as f:actual_hash=hashlib.file_digest(f,'sha256').hexdigest()
                if actual_hash!=record['sha256']:raise ValueError('O arquivo da música mudou na origem. Atualize o catálogo antes de usar.')
            os.replace(temp,target)
        except httpx.HTTPError as exc:
            raise ValueError('Não foi possível baixar a música. Tente novamente ou importe um arquivo local.') from exc
        finally:temp.unlink(missing_ok=True)
    return target


def public_catalog():
    return [{k:v for k,v in t.items() if k not in ('download','sha256')}|{'disponivel':track_path(t).is_file()} for t in catalog()]


def fingerprint(track_id):
    path=ensure_track(track_id)
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def import_track(source:Path,title:str,credit:str,*,key=None,metadata=None,staging=None):
    if key is None:
        with source.open('rb') as f:key='user-'+hashlib.file_digest(f,'sha256').hexdigest()[:24]
    if not re.fullmatch(r'user-[a-f0-9]{24}',key):raise ValueError('Identificador de música inválido.')
    target=LIBRARY/'uploads'/(key+'.wav')
    with LOCK:
        target.parent.mkdir(parents=True,exist_ok=True)
        temp=Path(staging) if staging else target.with_suffix('.partial.wav')
        try:
            run([binary('ffmpeg'),'-y','-v','error','-i',source,'-vn','-t','1800.1','-ar',SR,'-ac',2,'-c:a','pcm_f32le',temp],timeout=180)
            info=sf.info(temp)
            if not 1<=info.duration<=1800:raise ValueError('Use uma música de 1 segundo a 30 minutos.')
            os.replace(temp,target)
        except RuntimeError as exc:raise ValueError('Não foi possível ler o áudio. Use MP3, WAV, FLAC, OGG ou M4A válido.') from exc
        finally:temp.unlink(missing_ok=True)
        record={'id':key,'nome':title[:100] or source.stem[:100],'categoria':'Minhas músicas','uso':'Faixa importada por você.','autor':'Arquivo local','duracao_s':round(info.duration,2),'licenca':'Conforme sua autorização de uso','fonte':'','credito':credit.strip()[:2000] or 'Faixa importada: '+(title[:100] or source.stem[:100])+'. Créditos não informados.','recomendada':False}
        record.update({k:v for k,v in (metadata or {}).items() if k in ('categoria','uso','autor','licenca','fonte','youtube_id','origem','licenca_origem')})
        write_json(target.with_suffix('.json'),record)
    return record


def decoded_track(track_id,cancel=None):
    path=ensure_track(track_id)
    key=fingerprint(track_id)
    target=LIBRARY/'decoded'/(key+'.wav')
    with LOCK:
        if not target.is_file():
            target.parent.mkdir(parents=True,exist_ok=True)
            from .render import execute
            temp=target.with_suffix('.partial.wav')
            try:
                execute([binary('ffmpeg'),'-y','-v','error','-i',path,'-vn','-t',1800,'-ar',SR,'-ac',2,'-af','highpass=f=60,lowpass=f=10000','-c:a','pcm_f32le',temp],target.parent,cancel or target.parent/'unused.cancel')
                os.replace(temp,target)
            finally:temp.unlink(missing_ok=True)
    return target,key


def audio_stats(path,step=960):
    """20 ms envelope and active RMS without retaining the decoded soundtrack."""
    energy=[];peak=0.
    with sf.SoundFile(path) as f:
        if f.samplerate!=SR or f.channels!=2:raise ValueError('Áudio de mixagem deve estar em estéreo a 48 kHz.')
        for block in f.blocks(blocksize=step,dtype='float32',always_2d=True):
            if not np.isfinite(block).all():raise ValueError('Áudio contém amostras inválidas.')
            energy.append(float(np.mean(block.astype('float64')**2)))
            peak=max(peak,float(np.max(np.abs(block))))
    rms=np.sqrt(np.asarray(energy))
    active=rms[rms>max(.0001,float(np.max(rms,initial=0))*.04)]
    return rms,float(np.sqrt(np.mean(active**2))) if len(active) else 0.,peak


def speech_envelope(rms,reference,duck=True):
    # Look ahead by 160 ms and hold for 200 ms, so music never swells between words.
    active=rms>max(.001,reference*.12)
    held=np.zeros(len(active),dtype=bool)
    for offset in range(-8,11):
        if offset<0:held[:offset]|=active[-offset:]
        elif offset>0:held[offset:]|=active[:-offset]
        else:held|=active
    env=np.ones(len(active),dtype=np.float32)
    value=1.
    for i,on in enumerate(held):
        goal=1. if on or not duck else 10**(3/20)
        value+=(goal-value)*(1-math.exp(-.02/(.06 if on else .8)))
        env[i]=value
    return env


class LoopReader:
    """Seamless linear overlap at the tail/head of each track, read in small blocks."""
    def __init__(self,path,start,end):
        self.file=sf.SoundFile(path);self.start=start;self.length=end-start
        self.fade=min(SR*2,self.length//4);self.period=self.length-self.fade;self.position=0

    def read(self,count):
        pieces=[]
        while count:
            p=self.position%self.period
            n=min(count,self.period-p,self.fade-p if p<self.fade else count)
            self.file.seek(self.start+p)
            head=self.file.read(n,dtype='float32',always_2d=True)
            if p<self.fade:
                self.file.seek(self.start+self.period+p)
                tail=self.file.read(n,dtype='float32',always_2d=True)
                mix=((p+np.arange(n))/self.fade).astype('float32')[:,None]
                head=tail*(1-mix)+head*mix
            pieces.append(head);self.position+=n;count-=n
        return np.concatenate(pieces)

    def close(self):self.file.close()


def mix_audio(voice:Path,settings,out:Path,cancel=None):
    """Keep narration timing intact. Music stays 14–30 dB below active speech RMS."""
    from .render import Paused
    music,key=decoded_track(settings.musica_fundo,cancel)
    vrms,vref,vpeak=audio_stats(voice)
    mrms,mref,_=audio_stats(music)
    if vref<1e-6:raise ValueError('Narração silenciosa: não é possível equilibrar a música com a voz.')
    audible=np.flatnonzero(mrms>max(.00002,mref*.005))
    if len(audible)<2 or mref<1e-6:raise ValueError('A música está silenciosa. Escolha outra faixa.')
    # A static voice gain preserves phrasing/dynamics; reserve headroom for mixing.
    voice_gain=min(10**(-20/20)/vref,10**(-3/20)/max(vpeak,1e-9))
    reference=vref*voice_gain
    bed_target=0. if settings.volume_musica_db<=-60 else reference*10**(settings.volume_musica_db/20)
    gain=bed_target/mref
    env=speech_envelope(vrms,vref,settings.reduzir_musica_na_fala)
    loop=LoopReader(music,int(audible[0])*960,min(sf.info(music).frames,(int(audible[-1])+1)*960))
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=out.with_suffix('.partial.wav');peak=0.;voice_energy=0.;bed_energy=0.;speech_samples=0
    with sf.SoundFile(voice) as src:
        frames=len(src);position=0
        try:
            with sf.SoundFile(temp,'w',samplerate=SR,channels=2,subtype='FLOAT') as dst:
                for block in src.blocks(blocksize=960,dtype='float32',always_2d=True):
                    if cancel and cancel.exists():raise Paused()
                    n=len(block);idx=min(position//960,len(env)-1)
                    bed=loop.read(n)*gain
                    # Cap unusually loud passages against the same speech reference.
                    local=float(np.sqrt(np.mean(bed.astype('float64')**2)))
                    if local>bed_target*1.5:bed*=bed_target*1.5/local
                    begin=float(env[max(0,idx-1)]);end=float(env[idx])
                    bed*=np.linspace(begin,end,n,dtype='float32')[:,None]
                    samples=position+np.arange(n)
                    fade_in=np.clip(samples/(SR*.8),0,1)
                    fade_out=np.clip((frames-1-samples)/(SR*1.6),0,1)
                    bed*=np.minimum(fade_in,fade_out).astype('float32')[:,None]
                    narration=block*voice_gain
                    result=narration+bed
                    peak=max(peak,float(np.max(np.abs(result))))
                    if vrms[idx]>max(.001,vref*.12):
                        voice_energy+=float(np.sum(narration.astype('float64')**2));bed_energy+=float(np.sum(bed.astype('float64')**2));speech_samples+=n
                    dst.write(result);position+=n
            master=min(1.,10**(-1.5/20)/max(peak,1e-9))
            with sf.SoundFile(temp) as src2,sf.SoundFile(out,'w',samplerate=SR,channels=2,subtype='PCM_24') as dst:
                for block in src2.blocks(blocksize=SR,dtype='float32',always_2d=True):
                    if cancel and cancel.exists():raise Paused()
                    dst.write(block*master)
        finally:loop.close();temp.unlink(missing_ok=True)
    report={'versao':VERSION,'faixa':settings.musica_fundo,'arquivo_sha256':key,'duracao_s':frames/SR,'amostras':frames,'volume_relativo_db':settings.volume_musica_db,'reducao_na_fala':settings.reduzir_musica_na_fala,'musica_voz_db_medido':round(10*math.log10(max(bed_energy,1e-20)/max(voice_energy,1e-20)),2),'pico_dbfs':round(20*math.log10(max(peak*master,1e-12)),2),'ganho_voz':voice_gain*master,'emenda_s':loop.fade/SR}
    return report


def credit_text(track_id):
    t=track_record(track_id)
    return t['credito']+'\n\nTratamento no vídeo: volume ajustado, repetição com emendas suaves, fades e redução durante a fala.\n'


def mix_video(source:Path,target:Path,settings,cache:Path,cancel:Path):
    from .render import execute
    voice=cache/'narracao-mix.wav';mixed=cache/'trilha-mix.wav'
    execute([binary('ffmpeg'),'-y','-v','warning','-i',source,'-vn','-ar',SR,'-ac',2,'-c:a','pcm_f32le',voice],cache,cancel)
    report=mix_audio(voice,settings,mixed,cancel)
    credits=credit_text(settings.musica_fundo)
    execute([binary('ffmpeg'),'-y','-v','warning','-i',source,'-i',mixed,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar',SR,'-metadata','comment='+credits,'-movflags','+faststart',target],cache,cancel)
    return report
