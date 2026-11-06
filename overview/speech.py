from __future__ import annotations

import math
import re
import threading

import numpy as np
from num2words import num2words
import soundfile as sf

from .core import MODELS, binary, digest, read_json, run, write_json

SR = 24000
TTS_LOCK = threading.Lock()
_engine = None
_piper_engines = {}
PRONUNCIATION = {
    "PDF": "pê dê éfe", "CPU": "cê pê u", "GPU": "gê pê u", "IA": "inteligência artificial",
    "VRAM": "memória de vídeo", "RAM": "memória RAM", "API": "a pê i", "APIs": "a pê is",
    "HTML": "agá tê eme éle", "CSS": "cê esse esse", "JSON": "jêison", "MP4": "eme pê quatro",
    "SRT": "esse erre tê", "GB": "gigabytes", "MB": "megabytes", "km": "quilômetros",
    "NotebookLM": "Notebook éle eme", "OpenAI": "Open ei ai", "Python": "Páiton",
}
MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def normalize(text, glossary=None):
    text = re.sub(r"[*_`#]", "", text)
    def date(m):
        from datetime import date as dtdate
        day, month, year = map(int, m.groups())
        try:
            dtdate(year, month, day)
        except ValueError:
            return m.group()
        return f"{num2words(day,lang='pt_BR')} de {MONTHS[month-1]} de {num2words(year,lang='pt_BR')}"
    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", date, text)
    text = re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: f"{num2words(int(m[1]),lang='pt_BR')} horas e {num2words(int(m[2]),lang='pt_BR')} minutos", text)
    text = re.sub(r"R\$\s*([\d.]+(?:,\d{1,2})?)", lambda m: num2words(float(m[1].replace('.','').replace(',','.')),lang='pt_BR',to='currency'), text)
    text = re.sub(r"\b\d{1,3}(?:\.\d{3})+(?:,\d+)?\b", lambda m: m[0].replace('.',''), text)
    text = re.sub(r"\b(\d+),(\d+)\b", lambda m: num2words(int(m[1]),lang='pt_BR') + ' vírgula ' + ' '.join(num2words(int(c),lang='pt_BR') for c in m[2]), text)
    for word, spoken in {**PRONUNCIATION, **(glossary or {})}.items():
        text = re.sub(r"(?<!\w)" + re.escape(word) + r"(?!\w)", lambda _: spoken, text)
    text = re.sub(r"\b\d+\b", lambda m: num2words(int(m[0]),lang='pt_BR') if len(m[0])<16 else ' '.join(m[0]), text)
    text = text.replace('%',' por cento').replace('&',' e ')
    return re.sub(r"\s+", " ", text).strip()


def phrases(text):
    # Cada unidade é sintetizada separadamente; legendas usam os limites reais.
    parts = re.split(r"(?<=[.!?;:])\s+", text.strip())
    result = []
    for part in parts:
        words = part.split()
        while len(words)>22:
            result.append(" ".join(words[:18]) + ",")
            words = words[18:]
        if words:
            result.append(" ".join(words))
    return result


def engine():
    global _engine
    if _engine is None:
        from kokoro_onnx import Kokoro
        from kokoro_onnx.config import EspeakConfig
        import espeakng_loader
        import tempfile
        from pathlib import Path
        import shutil
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(MODELS / "kokoro/kokoro-v1.0.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
        # eSpeak usa caminhos ANSI no Windows. Pastas com acento, como
        # APRESENTAÇÃO, precisam de uma cópia de seus dados em caminho ASCII.
        espeak_config = None
        import os
        if os.name == "nt":
            runtime = Path(tempfile.gettempdir()) / "clareia-espeak-0.2.4"
            runtime.mkdir(exist_ok=True)
            data = runtime / "espeak-ng-data"
            if not (data / "phontab").exists():
                shutil.copytree(espeakng_loader.get_data_path(), data, dirs_exist_ok=True)
            library = runtime / "espeak-ng.dll"
            if not library.exists():
                shutil.copy2(espeakng_loader.get_library_path(), library)
            espeak_config = EspeakConfig(lib_path=str(library), data_path=str(data))
        _engine = Kokoro.from_session(session, str(MODELS / "kokoro/voices-v1.0.bin"), espeak_config=espeak_config)
    return _engine


def release():
    global _engine
    _engine = None
    _piper_engines.clear()
    from .cloned_voices import release as release_cloned
    try:
        release_cloned()
    finally:
        from .speech_alignment import release as release_alignment
        release_alignment()
    import gc
    gc.collect()


def synthesize(text, voice, speed, cache, glossary=None, delivery='natural', *, seed=42):
    from .voices import DELIVERIES,model_path
    style=DELIVERIES[delivery]
    spoken = normalize(text, glossary)
    key = digest("voice-local-v3", spoken, voice, speed,delivery)
    if voice.startswith('ms_'):
        from .microsoft_speech import VERSION, generate
        wav = cache / (digest(VERSION, spoken, voice, speed, delivery)+'.wav')
        return generate(spoken, voice, speed, delivery, wav), spoken
    if voice.startswith('clone_'):
        from .cloned_voices import identity
        key = digest(key, identity(voice))
        if seed != 42:
            key = digest(key, seed)
    wav = cache / (key + ".wav")
    if not wav.exists():
        cache.mkdir(parents=True, exist_ok=True)
        if voice.startswith('clone_'):
            from .cloned_voices import synthesize as clone_synthesize
            retry = {'seed': seed} if seed != 42 else {}
            raw = clone_synthesize(spoken, voice, cache / 'clonadas', delivery=delivery, **retry)
            tempo = speed * style['velocidade']
            if tempo != 1:
                adjusted = wav.with_suffix('.tempo.wav')
                run([binary('ffmpeg'), '-v', 'error', '-y', '-i', raw, '-af', f'atempo={tempo:.6f}', '-ar', SR, '-ac', 1, adjusted])
                audio, rate = sf.read(adjusted, dtype='float32')
                adjusted.unlink()
            else:
                audio, rate = sf.read(raw, dtype='float32')
        elif voice.startswith('piper_'):
            import wave
            from piper import PiperVoice,SynthesisConfig
            path=model_path(voice)
            if not path.is_file():raise RuntimeError('Voz não instalada. Execute instalar.bat para preparar as novas vozes.')
            if voice not in _piper_engines:
                import os,tempfile,shutil
                from pathlib import Path
                from piper.phonemize_espeak import ESPEAK_DATA_DIR
                data=ESPEAK_DATA_DIR
                if os.name=='nt':
                    data=Path(tempfile.gettempdir())/'clareia-piper-1.8.0'/'espeak-ng-data'
                    if not (data/'phontab').exists():shutil.copytree(ESPEAK_DATA_DIR,data,dirs_exist_ok=True)
                _piper_engines[voice]=PiperVoice.load(path,use_cuda=False,espeak_data_dir=data)
            raw=wav.with_suffix('.piper.wav')
            with wave.open(str(raw),'wb') as out:
                _piper_engines[voice].synthesize_wav(spoken,out,syn_config=SynthesisConfig(length_scale=1/(speed*style['velocidade'])))
            converted=wav.with_suffix('.converted.wav')
            run([binary('ffmpeg'),'-v','error','-y','-i',raw,'-ar',SR,'-ac',1,converted])
            audio,rate=sf.read(converted,dtype='float32');raw.unlink();converted.unlink()
        else:audio, rate = engine().create(spoken, voice=voice, speed=speed*style['velocidade'], lang="pt-br")
        if rate != SR or len(audio)<SR*.08 or not np.isfinite(audio).all() or float(np.max(np.abs(audio)))<.001:
            raise RuntimeError("O motor de voz produziu áudio vazio ou inválido")
        sf.write(str(wav)+".partial", audio, SR, format="WAV", subtype="PCM_16")
        if style['pitch']!=1. and not voice.startswith('clone_'):
            shifted=wav.with_suffix('.shift.wav')
            pitch=style['pitch']
            run([binary('ffmpeg'),'-y','-v','error','-i',str(wav)+'.partial','-af',
                 f'asetrate={round(SR*pitch)},aresample={SR},atempo={1/pitch:.6f}','-ar',SR,shifted])
            import os
            os.replace(shifted,str(wav)+'.partial')
        import os
        os.replace(str(wav)+".partial", wav)
    return wav, spoken


def scene_audio(scene, settings, path):
    from .voices import DELIVERIES
    from .runtime import gemini_only
    cloud=gemini_only(settings)
    voice = settings.voz if scene["apresentador"] == 1 else settings.voz_secundaria
    delivery=settings.estilo_locucao
    glossary = read_json(path / "pronuncia.json", {})
    key = digest("scene-audio-v2", scene["narracao_ptbr"], voice, settings.velocidade, glossary)
    pause=float(scene.get('pausa_reflexao_s',0))
    if pause:key=digest('scene-audio-v3',scene['narracao_ptbr'],voice,settings.velocidade,glossary,pause)
    if delivery!='natural' or voice.startswith('piper_'):key=digest(key,delivery,'voice-local-v3')
    if voice.startswith('ms_') and not cloud:
        from .microsoft_speech import VERSION
        key = digest(key, VERSION)
    if voice.startswith('clone_') and not cloud:
        from .cloned_voices import identity
        key = digest(key, identity(voice))
    natural_clone = False
    if voice.startswith('clone_') and not cloud:
        from .cloned_voices import profile
        natural_clone = profile(voice).get('interpretacao', 'natural') == 'natural'
        if natural_clone:
            from .narration_flow import VERSION
            key = digest(key, VERSION)
    if cloud:
        from .gemini_audio import identity
        key=digest('scene-audio-gemini-v1',scene['narracao_ptbr'],*identity(settings,scene['apresentador']==2),glossary,pause)
        voice='gemini:'+(settings.gemini_voz if scene['apresentador']==1 else settings.gemini_voz_secundaria)
    cache = path / "cache/audio"
    cache.mkdir(parents=True, exist_ok=True)
    wav, meta = cache / (key+".wav"), cache / (key+".json")
    if wav.exists() and meta.exists():
        saved = read_json(meta)
        if natural_clone:
            from . import speech_integrity
            from .narration_language import number_pairs, check_pairs
            proof = saved.get('verificacao_voz', {})
            checksum = speech_integrity.fingerprint(wav)
            try:
                from .narration_flow import RECOVERY_VERSION
                if saved.get('trechos_recuperados') and saved.get('recuperacao_voz') != RECOVERY_VERSION:
                    raise speech_integrity.IncompleteNarration('Atualizar recuperação da fala contínua.')
                if (proof.get('versao') != speech_integrity.VERSION or proof.get('sha256') != checksum
                        or not proof.get('pos_processamento')
                        or proof.get('pares_numericos',0) != len(number_pairs(scene['narracao_ptbr']))):
                    recognized, proof = speech_integrity.check_audio(wav, normalize(scene['narracao_ptbr'], glossary), cache/'verificacao')
                    pairs = check_pairs(scene['narracao_ptbr'],recognized)
                    saved['verificacao_voz'] = {**proof, 'sha256': checksum, 'pos_processamento': True, 'pares_numericos':pairs}
                    write_json(meta, saved)
            except speech_integrity.IncompleteNarration:
                pass  # Rebuild from checked passages; never reuse the broken clip.
            else:
                return wav, saved
        else:
            return wav, saved
    raw = cache / (key+"-raw.wav")
    flow = {}
    if natural_clone:
        from .narration_flow import write as write_continuous
        cues, flow = write_continuous(raw, scene['narracao_ptbr'], voice, settings, cache, glossary, pause)
    elif voice.startswith('ms_') and not cloud:
        from .microsoft_speech import write_scene
        part, spoken = synthesize(scene['narracao_ptbr'], voice, settings.velocidade, cache/'microsoft', glossary, delivery)
        cues, words = write_scene(raw, part, pause, with_words=True)
        flow['palavras'] = words
    else:
        cues, samples = [], 0
        paused=False
        with sf.SoundFile(raw, "w", samplerate=SR, channels=1, subtype="PCM_16") as out:
            for phrase in phrases(scene["narracao_ptbr"]):
                if cloud:
                    from .gemini_audio import synthesize as cloud_synthesize
                    part,spoken=cloud_synthesize(phrase,settings,cache/'frases-gemini',glossary,scene['apresentador']==2)
                else:part, spoken = synthesize(phrase, voice, settings.velocidade, cache / "frases", glossary,delivery)
                data, _ = sf.read(part, dtype="float32")
                start = samples/SR
                out.write(data)
                samples += len(data)
                cues.append({"inicio": start, "fim": samples/SR, "texto": spoken})
                extra=pause if pause and not paused and '?' in phrase else 0
                if extra:paused=True
                silence = np.zeros(int(SR*(DELIVERIES[delivery]['pausa']+extra)), dtype="float32")
                out.write(silence)
                samples += len(silence)
            total_samples = math.ceil(samples/1000)*1000  # 24 fps, 24 kHz
            out.write(np.zeros(total_samples-samples, dtype="float32"))
    run([binary("ffmpeg"), "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", SR, "-ac", 1, wav])
    raw.unlink(missing_ok=True)
    data = {"duracao": sf.info(wav).frames/SR, "voz": voice, "legendas": cues, "hash": key, **flow}
    if natural_clone:
        from . import speech_integrity
        # The repaired waveform needs a new downstream cache identity, even
        # when text, voice and all of the user's settings stayed identical.
        checksum = speech_integrity.fingerprint(wav)
        data['hash'] = digest(key, checksum)
        recognized, proof = speech_integrity.check_audio(wav, normalize(scene['narracao_ptbr'], glossary), cache/'verificacao')
        from .narration_language import check_pairs
        pairs = check_pairs(scene['narracao_ptbr'],recognized)
        data['verificacao_voz'] = {**proof, 'sha256': checksum, 'pos_processamento': True, 'pares_numericos':pairs}
    write_json(meta, data)
    return wav, data


def synthesize_settings(text,settings,cache,glossary=None):
    from .runtime import gemini_only
    if gemini_only(settings):
        from .gemini_audio import synthesize as cloud_synthesize
        return cloud_synthesize(text,settings,cache,glossary)
    return synthesize(text,settings.voz,settings.velocidade,cache,glossary,settings.estilo_locucao)
