"""Generate complete thoughts independently of visual/caption segmentation."""
from __future__ import annotations

import math
import re
import hashlib

import numpy as np
import soundfile as sf

VERSION = 'continuous-cloned-narration-v4-portuguese'
RECOVERY_VERSION = 'whole-thought-recovery-v2'
PACING_VERSION = 'complete-thought-cadence-v2'


def _pieces(sentence, max_chars, max_words):
    while len(sentence) > max_chars or len(sentence.split()) > max_words:
        words = list(re.finditer(r'\S+', sentence))
        limit = min(max_chars, words[max_words - 1].end()) if len(words) >= max_words else max_chars
        cuts = [m.end() for m in re.finditer(r'[,;:]\s+', sentence[:limit]) if m.start() > limit // 3]
        if cuts:
            end = cuts[-1]
        else:
            end = next((m.start() for m in reversed(words) if 0 < m.start() <= limit), limit)
        yield sentence[:end].strip()
        sentence = sentence[end:].strip()
    if sentence:
        yield sentence


def groups(text, reflection_pause=0, max_chars=420, max_words=70):
    result, buffer, reflected = [], '', False
    def flush(reflection=False):
        nonlocal buffer
        if buffer:
            result.append({'texto': buffer, 'reflexao': reflection}); buffer = ''
    for paragraph in re.split(r'\n\s*\n', text.strip()):
        paragraph_start = len(result)
        sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
        for sentence in sentences:
            for piece in _pieces(sentence, max_chars, max_words):
                joined = (buffer + ' ' + piece).strip()
                if len(joined) > max_chars or len(joined.split()) > max_words:
                    flush()
                buffer = (buffer + ' ' + piece).strip()
                if reflection_pause and not reflected and '?' in piece:
                    flush(True); reflected = True
        flush()
        # A short isolated last sentence loses the preceding context and often
        # changes pronunciation/cadence. Move whole sentences, never fragments,
        # from its predecessor while preserving reflection/paragraph boundaries.
        if len(result)-paragraph_start >= 2:
            previous, final = result[-2:]
            if not previous['reflexao'] and len(final['texto'].split()) < 24:
                sentences = re.split(r'(?<=[.!?])\s+', previous['texto'])
                while len(sentences) > 1 and len(final['texto'].split()) < 24:
                    head = ' '.join(sentences[:-1])
                    tail = sentences[-1]+' '+final['texto']
                    if len(head.split()) < 20 or len(tail) > max_chars or len(tail.split()) > max_words:
                        break
                    previous['texto'], final['texto'] = head, tail
                    sentences.pop()
    return result


def spoken_text(text):
    from .narration_language import prepare
    return prepare(text)


def cadence(audio, rate, text, settings):
    """Assess actual delivery, discounting long dead air; never change its tempo."""
    from .speech_alignment import tokens
    from .voices import DELIVERIES
    words = tokens(text)
    seconds = len(audio)/rate
    frame = max(1,round(rate*.01)); count = len(audio)//frame
    quiet_seconds = 0.
    if count:
        rms = np.sqrt(np.mean(audio[:count*frame].reshape(count,frame)**2,axis=1))
        quiet = rms < max(.00001,float(rms.max())*.018)
        edges = np.diff(np.r_[False,quiet,False].astype('int8'))
        for a,b in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
            if (b-a)*frame/rate >= .4:
                quiet_seconds += max(0,(b-a)*frame/rate-.2)
    effective = max(.1,float(seconds-quiet_seconds))
    tempo = settings.velocidade*DELIVERIES[settings.estilo_locucao]['velocidade']
    ppm = 60*len(words)/effective/tempo
    syllables = sum(max(1,len(re.findall(r'[aeiou]+',word))) for word in words)
    syllables_s = syllables/effective/tempo
    # A long technical word need not be rushed; both measures must be low.
    # A deliberate short question need not be faster to sound natural. Retry
    # long sluggish readings or truly extreme slowness, rather than chasing WPM.
    question = text.rstrip().rstrip('”"\')').endswith('?')
    slow = ((len(words)>=18 and not question and ppm<110 and syllables_s<4.)
            or (len(words)>=35 and ppm<105 and syllables_s<3.8)
            or (len(words)>=18 and ppm<80 and syllables_s<3.))
    penalty = max(0,110-ppm)+2*max(0,ppm-175)
    return {'palavras_por_minuto':round(ppm,2), 'silabas_por_segundo':round(syllables_s,2),
            'lento':slow, 'penalidade':round(penalty,3)}


def checked_passages(text, voice, settings, cache, glossary, recovery, depth=0, pacing=None):
    """Keep complete thoughts; split only a passage whose actual speech failed."""
    from .speech import SR, synthesize
    from .clone_performance import trim_dead_air
    from .speech_integrity import IncompleteNarration, check_audio
    from .narration_language import check_pairs
    failure = None; best = None
    for attempt in range(2):
        retry = {'seed': 43} if attempt else {}
        part, spoken = synthesize(spoken_text(text), voice, settings.velocidade, cache/'passagens',
                                  glossary, settings.estilo_locucao, **retry)
        audio, rate = sf.read(part, dtype='float32')
        if rate != SR:
            raise ValueError('Taxa de áudio incompatível com a narração.')
        audio = trim_dead_air(audio, rate)
        # Recognition sees precisely the samples that will enter the video.
        checksum = hashlib.sha256(audio.tobytes()).hexdigest()[:24]
        probe = cache/'verificacao'/(checksum+'.wav')
        probe.parent.mkdir(parents=True, exist_ok=True)
        sf.write(probe, audio, rate, subtype='PCM_16')
        try:
            words, proof = check_audio(probe, spoken, cache/'verificacao')
            check_pairs(text,words)
            rhythm = cadence(audio,rate,spoken,settings)
            # A complete but markedly slow reading gets at most one fresh
            # whole-thought generation. Keep the same voice/reference/controls.
            rank = (rhythm['penalidade'], -proof.get('cobertura',1.))
            if best is None or rank < best[0]:
                best = (rank, (text,audio,words), rhythm, attempt)
            if not rhythm['lento']:
                break
        except IncompleteNarration as exc:
            failure = exc
            recovery.append({'caracteres':len(text), 'tentativa':attempt+1, 'nivel':depth})
        finally:
            probe.unlink(missing_ok=True)
    if best is not None:
        if pacing is not None:
            pacing.append({**best[2], 'tentativa_escolhida':best[3]+1})
        return [best[1]]
    # Retain complete sentences first. Never recover a failed sentence by
    # resetting the voice every three or four words.
    if depth >= 2 or len(text.split()) < 24:
        raise failure
    pieces = groups(text, max_chars=max(120, len(text)//2),
                    max_words=max(12, len(text.split())//2))
    if len(pieces) < 2:
        raise failure
    result = []
    for piece in pieces:
        result.extend(checked_passages(piece['texto'], voice, settings, cache,
                                       glossary, recovery, depth+1, pacing))
    return result


def write(raw, text, voice, settings, cache, glossary, reflection_pause):
    from .speech import SR, normalize, phrases
    from .clone_performance import pause_after
    from . import speech_alignment
    units = [normalize(unit, glossary) for unit in phrases(text)]
    speech_alignment.ensure_ready()
    # Complete thoughts stay together, but long monologues can drift into a
    # sleepy cadence. Keep a few full sentences per generation, never captions.
    passages = groups(text, reflection_pause, max_chars=340, max_words=56)
    samples, protected, recognized, recovery, pacing = 0, [], [], [], []
    generated = 0
    with sf.SoundFile(raw, 'w', samplerate=SR, channels=1, subtype='PCM_16') as out:
        for passage in passages:
            checked = checked_passages(passage['texto'], voice, settings, cache, glossary, recovery, pacing=pacing)
            for index, (spoken, audio, words) in enumerate(checked):
                generated += 1
                recognized.extend({**w, 'inicio': w['inicio']+samples/SR,
                                    'fim': w['fim']+samples/SR} for w in words)
                out.write(audio); samples += len(audio)
                reflect = passage['reflexao'] and index+1 == len(checked)
                gap = pause_after(spoken, settings.estilo_locucao) + (reflection_pause if reflect else 0.)
                silence = np.zeros(int(SR * gap), dtype='float32')
                if reflect:
                    protected.append((samples, samples+len(silence)))
                out.write(silence); samples += len(silence)
        ending = math.ceil(samples / 1000) * 1000 - samples
        out.write(np.zeros(ending, dtype='float32'))
    cues, coverage, rhythm = speech_alignment.captions(raw, units, delivery=settings.estilo_locucao,
                                                     protected=protected, words=recognized)
    return cues, {'fala_continua': True, 'passagens_voz': generated,
                  'trechos_recuperados': len(recovery),
                  'ritmo_passagens': pacing,
                  'versao_ritmo': PACING_VERSION,
                  'recuperacao_voz': RECOVERY_VERSION,
                  'alinhamento': speech_alignment.VERSION, 'cobertura_alinhamento': coverage, **rhythm}
