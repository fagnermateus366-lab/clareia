import platform
import shutil

import httpx
import psutil

from .core import MODEL, MODELS, OLLAMA_URL, binary, run


def diagnose():
    report={"sistema":platform.platform(),"ram_total_gb":round(psutil.virtual_memory().total/2**30,2),
            "modelo":MODEL,"contexto":4096,"tts":"Kokoro ONNX CPU","ocr":"RapidOCR latino ONNX CPU"}
    for name in ("ffmpeg","ffprobe","ollama"):
        try:
            report[name]=binary(name)
        except (RuntimeError,OSError) as exc:
            report[name]=str(exc)
    from .render import choose_encoder
    try:
        report["encoder_testado"]=choose_encoder()
    except Exception as exc:
        report["encoder_testado"]=str(exc)
    report["kokoro_pesos_ok"]=all((MODELS/"kokoro"/f).exists() for f in ("kokoro-v1.0.onnx","voices-v1.0.bin"))
    try:
        report["ollama_modelos"]=httpx.get(OLLAMA_URL+"/api/tags",timeout=4).json()
        report["ollama_gpu"]=httpx.get(OLLAMA_URL+"/api/ps",timeout=4).json()
    except httpx.HTTPError:
        report["ollama_modelos"]="Servidor parado; será iniciado ao gerar roteiro"
    if platform.system()=="Windows":
        try:
            report["gpu_windows"]=run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json"],timeout=15).strip()
        except Exception:
            report["gpu_windows"]="WMI indisponível; use logs do Ollama"
    return report
