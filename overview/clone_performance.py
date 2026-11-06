"""Conservative narration direction without changing a cloned speaker's pitch."""
from __future__ import annotations

import numpy as np

VERSION = 'clone-performance-v2-saved-expression'
MODES = {'natural', 'original'}


def direction(profile, text, delivery):
    from .voices import DELIVERIES
    if delivery not in DELIVERIES:
        raise ValueError('Modo de locução inválido.')
    # Listening comparison selected the saved expression, without automatic
    # style/question boosts. Delivery still controls the chosen pace/pauses.
    return {'expression': profile['expressividade'], 'fidelity': profile.get('fidelidade', 0.),
            'temperature': profile.get('variacao', .8)}


def trim_dead_air(audio, rate):
    """Remove only excess quiet at synthetic clip edges; retain breathing room."""
    audio = np.asarray(audio, dtype=np.float32)
    frame = max(1, round(rate * .02))
    if len(audio) < frame * 5:
        return audio
    count = len(audio) // frame
    rms = np.sqrt(np.mean(audio[:count * frame].reshape(count, frame) ** 2, axis=1))
    threshold = max(.00001, float(rms.max()) * .01)
    active = np.flatnonzero(rms > threshold)
    if len(active) < 3:
        return audio
    first, last = int(active[0] * frame), int((active[-1] + 1) * frame)
    # Don't shave ordinary breaths or alter pauses inside the utterance.
    start = max(0, first - round(rate * .08)) if first > rate * .28 else 0
    end = min(len(audio), last + round(rate * .12)) if len(audio) - last > rate * .28 else len(audio)
    result = audio[start:end].copy()
    fade = min(round(rate * .003), len(result))
    if start and fade:
        result[:fade] *= np.linspace(0, 1, fade)
    if end < len(audio) and fade:
        result[-fade:] *= np.linspace(1, 0, fade)
    return result


def pause_after(text, delivery):
    """Added silence complements pauses already produced by the voice model."""
    from .voices import DELIVERIES
    ending = text.rstrip().rstrip('”"\')')
    if ending.endswith((',', ';', ':')):
        seconds = .035
    elif ending.endswith('?'):
        seconds = .16
    elif ending.endswith('!'):
        seconds = .09
    else:
        seconds = .11
    return seconds * (DELIVERIES[delivery]['pausa'] / DELIVERIES['natural']['pausa'])
