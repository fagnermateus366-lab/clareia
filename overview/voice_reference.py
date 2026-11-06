"""Lightweight reference preparation; preserve pitch, pauses and the original."""
from pathlib import Path
import hashlib
import numpy as np
import soundfile as sf

VERSION = 2


def prepare(source, target):
    audio, rate = sf.read(source, dtype='float32')
    if rate != 24000 or audio.ndim != 1 or not np.isfinite(audio).all():
        raise ValueError('A amostra deve ser um áudio mono de 24 kHz válido.')
    if len(audio) < 5 * rate:
        raise ValueError('Grave uma amostra entre 5 e 60 segundos.')
    hop = rate // 50
    frames = np.pad(audio, (0, (-len(audio)) % hop)).reshape(-1, hop)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    high, low = np.quantile(rms, [.9, .1])
    threshold = max(.002, min(float(low) * 2.5, float(high) * .22))
    active = rms > threshold
    if active.sum() * .02 < 3:
        raise ValueError('A amostra tem pouca fala aproveitável. Grave pelo menos 5 segundos falando, sem longos silêncios.')
    clipped = np.mean(np.abs(frames) >= .995, axis=1)
    width = min(500, len(frames))  # the decoder consumes at most ten seconds
    starts = list(range(0, len(frames) - width + 1, 5))
    if starts[-1] != len(frames) - width:
        starts.append(len(frames) - width)
    def score(start):
        window = active[start:start + width]
        return window.mean() + .2 * window[:min(300, width)].mean() - 2 * clipped[start:start + width].mean()
    start = max(starts, key=score)
    present = np.flatnonzero(active[start:start + width])
    first = max(start * hop, (start + int(present[0])) * hop - int(.12 * rate))
    last = min(len(audio), (start + width) * hop, (start + int(present[-1]) + 1) * hop + int(.12 * rate))
    excerpt = audio[first:last].copy()
    signal = frames[start:start + width][active[start:start + width]]
    signal_rms = float(np.sqrt(np.mean(signal ** 2)))
    peak = float(np.max(np.abs(excerpt)))
    # Constant gain only: no pitch shift, noise gate, compressor or time warp.
    gain = min(4., .18 / max(signal_rms, 1e-6), .95 / max(peak, 1e-6))
    excerpt *= gain
    target = Path(target)
    temporary = target.with_suffix('.partial.wav')
    sf.write(temporary, excerpt, rate, subtype='PCM_16')
    temporary.replace(target)
    warnings = []
    if np.mean(np.abs(audio) >= .995) > .001:
        warnings.append('A gravação tem picos saturados. Regravar com volume menor pode melhorar a semelhança.')
    if signal_rms < .02:
        warnings.append('O volume original é baixo. Aproxime o microfone e evite ruído de fundo.')
    if active.mean() < .5:
        warnings.append('Há bastante silêncio na gravação. Foi selecionado um trecho com mais sinal de fala.')
    return {'versao': VERSION, 'inicio_s': round(first / rate, 3),
            'duracao_s': round(len(excerpt) / rate, 3), 'duracao_original_s': round(len(audio) / rate, 3),
            'ganho': round(gain, 4), 'avisos': warnings,
            'hash': hashlib.sha256(target.read_bytes()).hexdigest()}
