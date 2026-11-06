"""Instala os modelos gratuitos. Não envia fontes e não usa chave."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from overview.core import MODEL, MODELS, OLLAMA_URL, ROOT, binary, run, write_json
from overview.llm import ensure_ollama

ASSETS={
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin",
}
EXPECTED={
    "kokoro-v1.0.onnx":"beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a",
    "voices-v1.0.bin":"bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
}


def main():
    if '--api-only' in sys.argv or '--check-only' in sys.argv:
        print('Verificando o ambiente sem baixar modelos locais de IA.',flush=True)
        from overview.render import choose_encoder
        print('Encoder testado: '+choose_encoder(),flush=True)
        if ' ass ' not in run([binary('ffmpeg'),'-hide_banner','-filters']):
            raise RuntimeError('O FFmpeg precisa de libass para montar o vídeo com legendas.')
        if '--api-only' in sys.argv:
            print('Pronto. Execute iniciar-api.bat, cadastre sua chave Gemini e marque o processamento completo.',flush=True)
        else:
            print('Ambiente verificado. Execute novamente sem -SemModelos para preparar a IA local.',flush=True)
        return
    target=MODELS/"kokoro"
    target.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name,url in ASSETS.items():
        output=target/name
        if not output.exists():
            print("Baixando "+name,flush=True)
            urllib.request.urlretrieve(url,str(output)+".partial")
            os.replace(str(output)+".partial",output)
        hashes[name]=hashlib.sha256(output.read_bytes()).hexdigest()
        if hashes[name]!=EXPECTED[name]:
            raise RuntimeError(f"Checksum inválido em {name}. Remova o arquivo e execute novamente.")
    write_json(target/"sha256.json",hashes)
    print("Verificando FFmpeg…",flush=True)
    from overview.render import choose_encoder
    print("Encoder testado: "+choose_encoder(),flush=True)
    # O pacote imageio-ffmpeg oferece fallback; FFmpeg precisa de libass.
    filters=run([binary("ffmpeg"),"-hide_banner","-filters"])
    if " ass " not in filters:
        raise RuntimeError("Este FFmpeg não tem libass. Instale o build completo gratuito do FFmpeg e execute novamente.")
    ensure_ollama()
    import httpx
    present=httpx.get(OLLAMA_URL+"/api/tags",timeout=10).json()["models"]
    if not any(m["name"]==MODEL for m in present):
        print("Baixando "+MODEL+" (~9,3 GB). O download pode ser retomado.",flush=True)
        with httpx.stream("POST",OLLAMA_URL+"/api/pull",json={"model":MODEL},timeout=None) as response:
            response.raise_for_status()
            last=-1
            for line in response.iter_lines():
                data=json.loads(line)
                if "error" in data:
                    raise RuntimeError(data["error"])
                percent=int(data.get("completed",0)/max(data.get("total",1),1)*100)
                if percent!=last and percent%5==0:
                    print(data.get("status",""),str(percent)+"%",flush=True)
                    last=percent
    print("Gerando amostras de voz…",flush=True)
    from overview.voices import download_piper
    download_piper()
    run([sys.executable,"-m","overview","samples"],cwd=ROOT)
    print("Preparando OCR latino local…",flush=True)
    from overview.ocr import engine,release
    engine()
    release()
    from tools.prepare_dictation import main as prepare_dictation
    prepare_dictation()
    from overview.doctor import diagnose
    write_json(ROOT/"output/diagnostico.json",diagnose())
    print("Instalação pronta. Execute iniciar.bat ou: python -m overview serve",flush=True)


if __name__=="__main__":
    main()
