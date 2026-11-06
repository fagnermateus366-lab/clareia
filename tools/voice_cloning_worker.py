"""Isolated speech worker. Run with the model's Python, never Clareia's venv."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.models/voice-cloning'
for key, value in {
    'HF_HOME': str(BASE / 'cache/huggingface'), 'HF_HUB_OFFLINE': '1',
    'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1', 'HF_HUB_DISABLE_TELEMETRY': '1',
    'TRANSFORMERS_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false',
    'OMP_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4',
    'PKUSEG_HOME': str(BASE / 'cache/pkuseg'),
}.items():
    os.environ[key] = value


class Engine:
    def __init__(self, name, variant=None):
        print(f'Carregando {name}...', file=sys.stderr, flush=True)
        import torch
        torch.set_num_threads(4)
        self.torch = torch
        self.name = name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.prompt_key = None
        if name == 'chatterbox':
            if torch.version.hip:
                # MIOpen BatchNorm fails on this Windows gfx1200 runtime.
                # Native Torch GPU kernels keep the model on the Radeon.
                torch.backends.cudnn.enabled = False
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            config = BASE / 'runtime.json'
            settings = json.loads(config.read_text(encoding='utf-8')) if config.is_file() else {}
            self.variant = variant or settings.get('variant', 'multilingual-v3')
            if self.variant == 'multilingual-v3':
                self.model = ChatterboxMultilingualTTS.from_local(
                    BASE / 'models/chatterbox-multilingual', self.device, t3_model='v3')
            elif self.variant == 'pt-br':
                self.model = self._load_ptbr(ChatterboxMultilingualTTS)
            else:
                raise ValueError('Versão do Chatterbox desconhecida.')
        else:
            raise ValueError('Motor de voz desconhecido.')
        print(f'{name} pronto em {self.device}.', file=sys.stderr, flush=True)

    def _load_ptbr(self, model_class):
        from safetensors.torch import load_file
        from chatterbox.models.voice_encoder import VoiceEncoder
        from chatterbox.models.t3 import T3
        from chatterbox.models.t3.modules.t3_config import T3Config
        from chatterbox.models.s3gen import S3Gen
        from chatterbox.models.tokenizers import MTLTokenizer
        source = BASE / 'models/chatterbox-pt-br'
        shared = BASE / 'models/chatterbox-multilingual'
        ve = VoiceEncoder()
        ve.load_state_dict(self.torch.load(shared / 've.pt', map_location='cpu', weights_only=True))
        t3 = T3(T3Config.multilingual())
        t3.load_state_dict(load_file(source / 't3_pt_br.safetensors'), strict=True)
        s3gen = S3Gen()
        incompatible = s3gen.load_state_dict(load_file(source / 's3gen_v3.safetensors'), strict=False)
        # The official safetensors omits only deterministic STFT buffers,
        # recreated by S3Tokenizer. Every learned parameter must be present.
        if set(incompatible.missing_keys) - {'tokenizer._mel_filters', 'tokenizer.window'} or incompatible.unexpected_keys:
            raise RuntimeError('Checkpoint S3Gen incompatível: ' + str(incompatible))
        for model in (ve, t3, s3gen):
            model.to(self.device).eval()
        tokenizer = MTLTokenizer(str(source / 'grapheme_mtl_merged_expanded_v1.json'))
        return model_class(t3, s3gen, ve, tokenizer, self.device)

    def generate(self, request):
        import numpy as np
        import soundfile as sf
        text = str(request['text']).strip()
        if not text or len(text) > 3000:
            raise ValueError('Informe um texto entre 1 e 3000 caracteres.')
        reference = Path(request['reference'])
        target = Path(request['output'])
        target.parent.mkdir(parents=True, exist_ok=True)
        seed = int(request.get('seed', 42))
        self.torch.manual_seed(seed)
        np.random.seed(seed)
        started = time.monotonic()
        print(f'Gerando {len(text)} caracteres com {self.name}...', file=sys.stderr, flush=True)
        key = (str(reference), reference.stat().st_mtime_ns, request.get('expression', .5))
        if self.prompt_key != key:
            self.model.prepare_conditionals(str(reference), exaggeration=float(request.get('expression', .5)))
        self.prompt_key = key
        with self.torch.inference_mode():
            audio = self.model.generate(text, language_id='pt',
                exaggeration=float(request.get('expression', .5)), cfg_weight=float(request.get('fidelity', 0.)),
                temperature=float(request.get('temperature', .8)), repetition_penalty=1.2,
                min_p=.05, top_p=1.).detach().float().cpu().numpy().squeeze()
        rate = self.model.sr
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if rate != 24000 or len(audio) < rate * .08 or not np.isfinite(audio).all() or np.max(np.abs(audio)) < .001:
            raise RuntimeError('O motor produziu áudio vazio ou inválido.')
        temporary = target.with_suffix('.partial.wav')
        sf.write(temporary, audio, rate, subtype='PCM_16')
        temporary.replace(target)
        return {'ok': True, 'file': str(target), 'duration': len(audio) / rate,
                'seconds': time.monotonic() - started, 'device': self.device,
                'gpu': self.torch.cuda.get_device_name(0) if self.device == 'cuda' else None,
                'sample_rate': rate, 'peak': float(np.max(np.abs(audio))), 'variant': self.variant}


def main():
    # HIP libraries can write directly to fd 1. Keep those diagnostics out of
    # the JSON protocol pipe as well as Python-level progress messages.
    protocol = os.fdopen(os.dup(sys.stdout.fileno()), 'w', encoding='utf-8', buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', required=True, choices=['chatterbox'])
    parser.add_argument('--variant', choices=['multilingual-v3', 'pt-br'])
    parser.add_argument('--request', type=Path)
    args = parser.parse_args()
    engine = None
    if args.request:
        requests = [args.request.read_text(encoding='utf-8')]
    else:
        requests = sys.stdin
    for line in requests:
        try:
            request = json.loads(line)
            with redirect_stdout(sys.stderr):
                if engine is None:
                    engine = Engine(args.engine, args.variant)
                result = engine.generate(request)
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            result = {'ok': False, 'error': str(exc), 'type': type(exc).__name__}
        print(json.dumps(result, ensure_ascii=False), file=protocol, flush=True)


if __name__ == '__main__':
    main()
