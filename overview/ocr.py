"""OCR local em CPU, com modelo latino para português."""
from pathlib import Path
import threading

from .core import MODELS

_lock=threading.Lock()
_engine=None


def engine():
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR
        from rapidocr.utils.typings import LangRec, OCRVersion, ModelType
        target=MODELS/"ocr"
        target.mkdir(parents=True,exist_ok=True)
        _engine=RapidOCR(params={
            "Global.model_root_dir":str(target),
            "Global.log_level":"warning",
            "EngineConfig.onnxruntime.intra_op_num_threads":4,
            "EngineConfig.onnxruntime.inter_op_num_threads":1,
            "Rec.lang_type":LangRec.LATIN,
            "Rec.ocr_version":OCRVersion.PPOCRV5,
            "Rec.model_type":ModelType.MOBILE,
        })
    return _engine


def recognize(image):
    from .runtime import gemini_only,current_settings
    if gemini_only():
        from .gemini_vision import recognize as cloud_recognize
        return cloud_recognize(image,current_settings())
    with _lock:
        result=engine()(image)
    return "\n".join(result.txts or [])


def release():
    global _engine
    _engine=None
