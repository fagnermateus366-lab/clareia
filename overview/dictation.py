"""Portuguese microphone dictation. Audio stays local and is deleted after use."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import threading

from .core import MODELS, binary, run

MODEL_DIR = MODELS / 'dictation-small'
MAX_BYTES = 20 * 1024 * 1024
MAX_SECONDS = 180
LOCK = threading.Lock()
FORMATS = {'audio/webm': 'matroska', 'video/webm': 'matroska',
           'audio/ogg': 'ogg', 'audio/mp4': 'mov', 'audio/x-m4a': 'mov',
           'audio/wav': 'wav', 'audio/x-wav': 'wav'}


class NotReadyError(RuntimeError):
    pass


class BusyError(RuntimeError):
    pass


def status():
    installed = importlib.util.find_spec('faster_whisper') is not None
    ready = installed and all((MODEL_DIR / f).is_file() for f in
                              ('model.bin', 'config.json', 'tokenizer.json', 'vocabulary.txt'))
    return {'pronto': ready, 'local': True, 'idioma': 'pt-BR',
            'max_segundos': MAX_SECONDS, 'max_bytes': MAX_BYTES}


def _model():
    if not status()['pronto']:
        raise NotReadyError('O ditado local ainda não está instalado. Execute instalar-ditado.bat na pasta do aplicativo e tente novamente.')
    from faster_whisper import WhisperModel
    # No downloads or provider calls in this path; keep the video GPU free.
    return WhisperModel(str(MODEL_DIR), device='cpu', compute_type='int8',
                        cpu_threads=4, num_workers=1, local_files_only=True)


def transcribe(data: bytes, content_type: str):
    audio_format = FORMATS.get(content_type.split(';')[0].lower().strip())
    if not audio_format:
        raise ValueError('Formato de gravação não aceito. Use áudio WebM, OGG, MP4 ou WAV.')
    if not data:
        raise ValueError('A gravação está vazia. Fale e tente novamente.')
    if len(data) > MAX_BYTES:
        raise ValueError('A gravação é muito grande. Grave um trecho menor.')
    if not LOCK.acquire(blocking=False):
        raise BusyError('Outro ditado está sendo transcrito. Aguarde terminar e tente novamente.')
    try:
        with tempfile.TemporaryDirectory(prefix='clareia-ditado-') as folder:
            source = Path(folder) / 'recording'
            target = Path(folder) / 'speech.wav'
            source.write_bytes(data)
            try:
                # Force the browser's container: never accept playlists or remote URLs.
                # Decode at most one second beyond the limit, even with a forged duration.
                run([binary('ffmpeg'), '-nostdin', '-y', '-v', 'error',
                     '-protocol_whitelist', 'file,pipe', '-f', audio_format, '-i', source,
                     '-t', str(MAX_SECONDS + 1), '-vn', '-ac', '1', '-ar', '16000',
                     '-c:a', 'pcm_s16le', target], timeout=35)
                import soundfile as sf
                samples, rate = sf.read(target, dtype='float32')
            except Exception as exc:
                raise ValueError('Não foi possível ler a gravação. Verifique o microfone e grave novamente.') from exc
            seconds = len(samples) / rate
            if seconds > MAX_SECONDS:
                raise ValueError('Grave até 3 minutos por vez. Você pode continuar ditando no mesmo campo.')
            if seconds < .3 or not len(samples) or abs(samples).max() < .003:
                raise ValueError('Não ouvi fala na gravação. Confira o microfone e tente novamente.')
            model = _model()
            try:
                segments, _ = model.transcribe(samples, language='pt', beam_size=5,
                                                vad_filter=True, condition_on_previous_text=False)
                text = ' '.join(s.text.strip() for s in segments if s.text.strip()).strip()
            finally:
                # Each recording releases its model; no permanent RAM reservation.
                del model
            if not text:
                raise ValueError('Não consegui reconhecer a fala. Fale mais perto do microfone e tente novamente.')
            return {'texto': text, 'idioma': 'pt-BR', 'duracao_s': round(seconds, 2)}
    finally:
        LOCK.release()
