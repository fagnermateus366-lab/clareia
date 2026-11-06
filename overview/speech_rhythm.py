"""Shorten excess acoustic silence while protecting speech and reflection pauses."""
from __future__ import annotations

import numpy as np
import soundfile as sf

VERSION = 'acoustic-cadence-v2'
LIMITS = {'natural': .35, 'envolvente': .24, 'documental': .45, 'reflexiva': .60,
          'suspense': .40, 'terror': .42, 'misterio': .37, 'motivacional': .32}
from .narration_styles import MOTIVATIONAL_STYLES
LIMITS.update({key:style['limite_pausa'] for key,style in MOTIVATIONAL_STYLES.items()})


def _voiced(audio, rate, frame):
    """Protect periodic speech even when it is as quiet as the noise floor."""
    width = frame*4
    count = len(audio)//frame
    mask = np.zeros(count, dtype=bool)
    low, high = max(1, round(rate/400)), min(width-1, round(rate/70))
    for index in range(0, count-3, 2):
        block = audio[index*frame:index*frame+width].astype('float64')
        block -= block.mean()
        energy = float(block @ block)
        if energy < 1e-10:
            continue
        spectrum = np.fft.rfft(block, n=2*width)
        correlation = np.fft.irfft(spectrum*spectrum.conj(), n=2*width)[:width]
        # Normalize for the overlap at each lag, so a quiet vowel is protected
        # just as strongly as a loud one. Noise lacks the periodic correlation.
        lags = np.arange(low, high+1)
        prefix = np.r_[0., np.cumsum(block*block)]
        norm = np.sqrt((prefix[width-lags])*(prefix[width]-prefix[lags]))
        strength = np.max(correlation[lags]/np.maximum(norm, 1e-15), initial=0.)
        if strength > .65:
            mask[max(0,index-1):min(count,index+5)] = True
    return mask


def _pause_limit(words, start, end, delivery):
    previous = next((w for w in reversed(words) if w['inicio'] <= start+.03), None)
    if previous is None:
        return None
    # ASR may assign most of the silence to a word such as "você". The
    # waveform determines the quiet interval; those timestamps cannot veto it.
    punctuation = str(previous['texto']).rstrip().rstrip('”"\')')[-1:]
    base = LIMITS[delivery]
    if punctuation in ('.', '!'):
        return base+.10
    if punctuation == '?':
        return base+.18
    if punctuation in (',', ';', ':'):
        return base*.70
    return base*.50


def adjust(path, words, delivery, protected=()):
    audio, rate = sf.read(path, dtype='float32')
    frame = max(1, round(rate * .01))
    count = len(audio) // frame
    if not count:
        return words, {'pausas_encurtadas': 0, 'silencio_reduzido_s': 0.}
    rms = np.sqrt(np.mean(audio[:count*frame].reshape(count, frame)**2, axis=1))
    peak = float(rms.max())
    threshold = max(.00001, peak*.018)
    voiced = _voiced(audio, rate, frame)
    quiet = (rms <= threshold) & ~voiced
    changes = np.diff(np.r_[False, quiet, False].astype('int8'))
    runs = list(zip(np.flatnonzero(changes == 1)*frame, np.flatnonzero(changes == -1)*frame))
    margin = round(.04 * rate)
    cuts, shortened = [], 0
    active = rms[rms > peak*.08]
    noise_ceiling = max(.00001, min(float(np.median(active))*.025, peak*.004)) if len(active) else .00001
    for left, right in runs:
        if right-left < .40*rate or left <= margin or right >= len(audio)-margin:
            continue
        if np.median(rms[left//frame:right//frame]) > noise_ceiling:
            continue  # Audible breath/fricative, rather than synthetic dead air.
        limit = _pause_limit(words, left/rate, right/rate, delivery)
        if limit is None:
            continue
        regions = [(left, right)]
        for a,b in protected:
            regions = [(x,y) for c,d in regions for x,y in ((c,min(d,a)),(max(c,b),d)) if y>x]
        changed = False
        for left, right in regions:
            desired = round(limit*rate)
            take = right-left-max(desired, 2*margin)
            if take < .15*rate:
                continue
            middle = (left+right)//2
            cut_start = middle-take//2
            cuts.append((cut_start, cut_start+take)); changed = True
        if changed:
            shortened += 1
    cuts.sort()
    if not cuts:
        return words, {'pausas_encurtadas': 0, 'silencio_reduzido_s': 0., 'cadencia': VERSION}
    chunks, cursor = [], 0
    for start, end in cuts:
        if start < cursor:
            raise ValueError('Intervalos de silêncio sobrepostos na narração.')
        chunks.append(audio[cursor:start]); cursor = end
    chunks.append(audio[cursor:])
    result = np.concatenate(chunks)
    result = np.pad(result, (0, (-len(result)) % 1000))
    temporary = path.with_suffix('.rhythm.wav')
    sf.write(temporary, result, rate, subtype='PCM_16'); temporary.replace(path)
    def shifted(seconds):
        position = round(seconds*rate)
        removed = sum(max(0, min(position, end)-start) for start,end in cuts if position > start)
        return (position-removed)/rate
    aligned = [{**w, 'inicio': shifted(w['inicio']), 'fim': shifted(w['fim'])} for w in words]
    return aligned, {'pausas_encurtadas': shortened, 'cadencia': VERSION,
                     'silencio_reduzido_s': round(sum(b-a for a,b in cuts)/rate, 4)}
