"""One-time download of public speech recognition weights. No microphone access."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from faster_whisper.utils import download_model
    from overview.dictation import MODEL_DIR, status
    if status()['pronto']:
        print('Ditado local já instalado.', flush=True)
        return
    print('Baixando reconhecimento de fala em português (~490 MB, somente nesta instalação)…', flush=True)
    download_model('small', output_dir=str(MODEL_DIR), use_auth_token=False)
    if not status()['pronto']:
        raise RuntimeError('Download incompleto. Execute instalar-ditado.bat novamente.')
    print('Ditado pronto. A fala será transcrita neste computador, sem API.', flush=True)


if __name__ == '__main__':
    main()
