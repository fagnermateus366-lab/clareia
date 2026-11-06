"""Brazilian Microsoft online voices through edge-tts; no local voice model."""
from __future__ import annotations

import asyncio
from difflib import SequenceMatcher
from html import unescape
from importlib.util import find_spec
import re
import tempfile

import numpy as np
import soundfile as sf

from .core import binary, read_json, run, write_json

VERSION = 'microsoft-continuous-v2-word-timing'
VOICES = {
    'ms_antonio': ('pt-BR-AntonioNeural', 'Antonio', 'Masculina brasileira · experimente em documentários e histórias'),
    'ms_francisca': ('pt-BR-FranciscaNeural', 'Francisca', 'Feminina brasileira · experimente em explicações e narrativas'),
    'ms_thalita': ('pt-BR-ThalitaMultilingualNeural', 'Thalita', 'Feminina brasileira · voz multilíngue, configurada em português do Brasil'),
    'ms_brian': ('en-US-BrianMultilingualNeural', 'Brian', 'Masculina multilíngue · experimente em documentários e relatos. Reconhece português pelo texto; ouça e confira a pronúncia'),
    'ms_andrew': ('en-US-AndrewMultilingualNeural', 'Andrew', 'Masculina multilíngue · experimente em mensagens motivacionais e histórias. Reconhece português pelo texto; ouça e confira a pronúncia'),
    'ms_emma': ('en-US-EmmaMultilingualNeural', 'Emma', 'Feminina multilíngue · experimente em reflexões e narrativas. Reconhece português pelo texto; ouça e confira a pronúncia'),
}
NOTICE = ('Microsoft online · sem chave e sem baixar modelos. Requer internet e envia o texto da narração à Microsoft. '
          'Integração comunitária via Edge; a disponibilidade pode mudar. Os modos ajustam ritmo e altura, '
          'sem estilos emocionais nativos. Ouça a amostra antes de escolher.')


def catalog():
    installed = find_spec('edge_tts') is not None
    return [{'id':key, 'nome':name, 'motor':'Microsoft · online', 'instalada':installed,
             'online':True, 'idioma':'pt-BR', 'multilingue':'Multilingual' in native, 'descricao':description+'. '+NOTICE}
            for key, (native, name, description) in VOICES.items()]


def controls(speed, delivery):
    from .voices import DELIVERIES
    style = DELIVERIES[delivery]
    pace = float(speed)*style['velocidade']
    if not .5 <= pace <= 2:
        raise ValueError('Ritmo da voz Microsoft fora do intervalo permitido.')
    # Send prosody to the service, without stretching the generated waveform.
    return {'rate':f'{round((pace-1)*100):+d}%',
            'pitch':f"{round((style['pitch']-1)*200):+d}Hz"}


def _tokens(text):
    return re.findall(r'\w+', unescape(text).casefold())


def validate_boundaries(spoken, boundaries):
    expected = _tokens(spoken)
    actual = _tokens(' '.join(c['texto'] for c in boundaries))
    tail = min(8,len(expected))
    if (not expected or actual[-tail:] != expected[-tail:]
            or SequenceMatcher(None, expected, actual, autojunk=False).ratio() < .98):
        raise RuntimeError('A Microsoft não confirmou a narração completa. Tente gerar novamente; o áudio incompleto não foi usado.')


async def _download(spoken, name, prosody, target):
    import edge_tts
    boundaries = []
    communicate = edge_tts.Communicate(spoken, name, **prosody, boundary='WordBoundary',
                                       connect_timeout=15, receive_timeout=60)
    with target.open('wb') as output:
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                output.write(chunk['data'])
            elif chunk['type'] == 'WordBoundary':
                start, duration = chunk['offset']/10_000_000, chunk['duration']/10_000_000
                boundaries.append({'inicio':start, 'fim':start+duration, 'texto':unescape(chunk['text'])})
    return boundaries


def generate(spoken, voice, speed, delivery, target):
    if voice not in VOICES:raise ValueError('Voz Microsoft inválida.')
    if find_spec('edge_tts') is None:
        raise RuntimeError('Instale as dependências do Clareia para habilitar as vozes Microsoft online.')
    meta = target.with_suffix('.json')
    if target.is_file() and meta.is_file():return target
    target.parent.mkdir(parents=True, exist_ok=True)
    # Each attempt owns its temporary files, including on timeout or disconnect.
    with tempfile.TemporaryDirectory(prefix='ms-', dir=target.parent) as work:
        from pathlib import Path
        work = Path(work)
        mp3, wav = work/'fala.mp3', work/'fala.wav'
        for attempt in range(2):
            try:
                boundaries = asyncio.run(asyncio.wait_for(
                    _download(spoken, VOICES[voice][0], controls(speed, delivery), mp3), timeout=180))
                validate_boundaries(spoken, boundaries)
                break
            except Exception as exc:
                if attempt:
                    raise RuntimeError('Não foi possível concluir a voz Microsoft online. Confira a internet ou escolha uma voz local. '
                                       'Nenhuma outra voz foi usada no lugar.') from exc
        run([binary('ffmpeg'), '-v','error','-y','-i',mp3,'-ar',24000,'-ac',1,wav])
        audio, rate = sf.read(wav, dtype='float32')
        if rate != 24000 or len(audio) < 2400 or not np.isfinite(audio).all() or np.max(np.abs(audio)) < .001:
            raise RuntimeError('A Microsoft retornou áudio vazio ou inválido. Tente novamente.')
        duration = len(audio)/rate
        if not boundaries or boundaries[-1]['fim'] > duration+.35:
            raise RuntimeError('A narração Microsoft terminou antes do texto. Tente novamente.')
        from .speech import phrases
        from .speech_alignment import align
        captions,_ = align(phrases(spoken),boundaries,duration)
        write_json(meta, {'versao':VERSION, 'voz':VOICES[voice][0], 'legendas':captions,'palavras':boundaries})
        import os
        os.replace(wav, target)
    return target


def write_scene(raw, part, reflection_pause=0, *, with_words=False):
    """Use one continuous reading, inserting only an explicitly requested pause."""
    audio, rate = sf.read(part, dtype='float32')
    metadata=read_json(part.with_suffix('.json'))
    boundaries = metadata['legendas']
    words=[dict(w) for w in metadata.get('palavras',[])]
    duration = len(audio)/rate
    cues = [{**c, 'fim':min(c['fim'], duration)} for c in boundaries]
    if reflection_pause:
        question = next((i for i,c in enumerate(cues) if '?' in c['texto']), None)
        if question is not None:
            end_time = cues[question]['fim']
            if question+1 < len(cues) and cues[question+1]['inicio'] > end_time:
                end_time = (end_time+cues[question+1]['inicio'])/2
            end = min(len(audio), round(end_time*rate))
            pause = np.zeros(round(reflection_pause*rate), dtype='float32')
            audio = np.r_[audio[:end], pause, audio[end:]]
            for cue in cues[question+1:]:
                cue['inicio'] += len(pause)/rate
                cue['fim'] += len(pause)/rate
            for word in words:
                if word['inicio'] >= end_time:
                    word['inicio'] += len(pause)/rate
                    word['fim'] += len(pause)/rate
    # Keep the exact frame convention used by scene_audio (24fps, 24kHz).
    padding = (-len(audio)) % 1000
    sf.write(raw, np.r_[audio, np.zeros(padding,dtype='float32')], rate, subtype='PCM_16')
    return (cues,words) if with_words else cues
