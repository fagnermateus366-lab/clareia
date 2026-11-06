"""Reject missing narration instead of stretching captions over absent speech."""
from __future__ import annotations

from difflib import SequenceMatcher
import hashlib

from .core import digest, read_json, write_json

VERSION = 'spoken-content-v1'


class IncompleteNarration(ValueError):
    pass


def validate(text, words):
    from .speech import normalize
    from .speech_alignment import tokens
    expected = tokens(normalize(text))
    actual = tokens(normalize(' '.join(w['texto'] for w in words)))
    matched = set()
    for block in SequenceMatcher(None, expected, actual, autojunk=False).get_matching_blocks():
        matched.update(range(block.a, block.a + block.size))
    count = len(expected)
    coverage = len(matched) / max(1, count)
    longest = run = 0
    for i in range(count):
        run = 0 if i in matched else run + 1
        longest = max(longest, run)
    window = min(8, count)
    tail = sum(i in matched for i in range(count-window, count)) / max(1, window)
    head = sum(i in matched for i in range(window)) / max(1, window)
    # ASR may miss an isolated word. A missing clause or conclusion must never
    # be interpolated into the subtitle timeline and accepted as finished.
    if (not count or coverage < .85 or longest >= 4 or head < .7 or tail < .7
            or (count >= 4 and (not matched or max(matched) < count-3))):
        raise IncompleteNarration(
            'A voz não confirmou com segurança todo o texto da narração, incluindo o final. '
            'O vídeo não será concluído com uma explicação cortada. Tente gerar novamente.')
    return {'versao': VERSION, 'cobertura': round(coverage, 4),
            'inicio': round(head, 4), 'final': round(tail, 4), 'maior_lacuna': longest}


def fingerprint(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def check_audio(path, text, cache):
    from .speech_alignment import recognize
    checksum = fingerprint(path)
    record_path = cache / (digest(VERSION, text, checksum) + '.json')
    saved = read_json(record_path)
    if saved:
        validate(text, saved['palavras'])
        return saved['palavras'], saved['verificacao']
    words = recognize(path)
    report = validate(text, words)
    write_json(record_path, {'sha256': checksum, 'palavras': words, 'verificacao': report})
    return words, report
