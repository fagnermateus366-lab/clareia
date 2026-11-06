"""Align approved visual/caption units to continuous speech using local ASR."""
from __future__ import annotations

from difflib import SequenceMatcher
import re
import threading
import unicodedata

import soundfile as sf

from .core import binary, run

VERSION = 'continuous-word-alignment-v1'
LOCK = threading.RLock()
_model = None


def tokens(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))
    return re.findall(r'[a-z0-9]+', text)


def ensure_ready():
    from .dictation import status
    if not status()['pronto']:
        raise ValueError('A fala contínua precisa do alinhamento local do ditado. Prepare o ditado local ou selecione Leitura original nas configurações da voz.')


def release():
    global _model
    with LOCK:
        _model = None


def recognize(path):
    global _model
    from . import dictation
    ensure_ready()
    converted = path.with_suffix('.alignment.wav')
    with LOCK, dictation.LOCK:
        try:
            run([binary('ffmpeg'), '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', '16000', converted])
            data, rate = sf.read(converted, dtype='float32')
            if rate != 16000:
                raise ValueError('Taxa de áudio inválida para sincronizar a fala.')
            if _model is None:
                _model = dictation._model()
            segments, _ = _model.transcribe(data, language='pt', beam_size=5, word_timestamps=True,
                                             vad_filter=False, condition_on_previous_text=False)
            return [{'texto': w.word, 'inicio': float(w.start), 'fim': float(w.end)}
                    for segment in segments for w in (segment.words or [])]
        finally:
            converted.unlink(missing_ok=True)


def align(units, words, duration):
    """Keep approved text, using recognition only for its timestamps."""
    from .speech_integrity import validate
    validate(' '.join(units), words)
    expected, offsets = [], [0]
    for unit in units:
        part = tokens(unit)
        if not part:
            raise ValueError('Há um trecho sem palavras para sincronizar.')
        expected.extend(part); offsets.append(len(expected))
    actual, times = [], []
    last = 0.
    for word in words:
        start, end = float(word['inicio']), float(word['fim'])
        if not (0 <= start < end <= duration + .15) or start < last - .1:
            continue
        start, end = max(last, start), min(end, duration)
        if end <= start:
            continue
        for token in tokens(word['texto']):
            actual.append(token); times.append((start, end))
        last = start
    matches = {}
    for block in SequenceMatcher(None, expected, actual, autojunk=False).get_matching_blocks():
        for i in range(block.size):
            matches[block.a + i] = times[block.b + i]
    coverage = len(matches) / max(1, len(expected))
    if coverage < .72 or len(matches) < min(3, len(expected)):
        raise ValueError('A fala ficou pronta, mas o alinhamento não reconheceu o roteiro com segurança. Gere outra prévia ou use Leitura original.')
    anchors = sorted(matches)
    def boundary(position):
        if position == 0:
            return 0.
        if position == len(expected):
            return duration
        if position in matches:
            return matches[position][0]
        before = next((i for i in reversed(anchors) if i < position), None)
        after = next((i for i in anchors if i > position), None)
        if before is None:
            return matches[after][0] * position / after
        left = matches[before][1]
        if after is None:
            return left + (duration - left) * (position - before - 1) / (len(expected) - before - 1)
        right = max(left, matches[after][0])
        return left + (right - left) * (position - before - 1) / (after - before - 1)
    boundaries = [boundary(i) for i in offsets]
    if any(b - a < .03 for a, b in zip(boundaries, boundaries[1:])):
        raise ValueError('Não foi possível separar os tempos das legendas com segurança. Gere outra prévia ou use Leitura original.')
    cues = []
    for i, unit in enumerate(units):
        start, end = boundaries[i], boundaries[i + 1]
        last_word = offsets[i + 1] - 1
        if i + 1 < len(units) and last_word in matches:
            end = min(end, max(start + .03, matches[last_word][1]))
        cues.append({'inicio': start, 'fim': end, 'texto': unit})
    return cues, round(coverage, 4)


def captions(path, units, *, delivery=None, protected=(), words=None):
    duration = sf.info(path).duration
    if len(units) == 1 and delivery is None:
        return [{'inicio': 0., 'fim': duration, 'texto': units[0]}], 1.
    words = recognize(path) if words is None else words
    rhythm = {}
    if delivery is not None:
        from .speech_rhythm import adjust
        words, rhythm = adjust(path, words, delivery, protected)
        duration = sf.info(path).duration
    cues, coverage = align(units, words, duration)
    return (cues, coverage, rhythm) if delivery is not None else (cues, coverage)
