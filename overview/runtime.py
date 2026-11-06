"""Per-operation model routing; concurrent requests never share a provider choice."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from inspect import signature

_settings=ContextVar('clareia_model_settings',default=None)


def current_settings():return _settings.get()


def local_model(settings=None):
    from .core import MODEL
    cfg=settings if settings is not None else current_settings()
    # A cloud writer's identifier must never be sent to the local Ollama server.
    return cfg.roteiro_modelo if cfg and cfg.roteiro_provedor=='local' and cfg.roteiro_modelo else MODEL


def gemini_only(settings=None):
    cfg=settings if settings is not None else current_settings()
    return bool(cfg and cfg.roteiro_provedor=='gemini' and cfg.gemini_projeto_completo)


def small_local(settings=None):
    cfg=settings if settings is not None else current_settings()
    return (not cfg or cfg.roteiro_provedor=='local') and local_model(cfg) in {'qwen2.5:1.5b','qwen2.5:3b'}


@contextmanager
def model_runtime(settings):
    token=_settings.set(settings)
    try:yield
    finally:_settings.reset(token)


def using_settings(fn):
    sig=signature(fn)
    @wraps(fn)
    def wrapped(*args,**kwargs):
        settings=sig.bind(*args,**kwargs).arguments['settings']
        with model_runtime(settings):return fn(*args,**kwargs)
    return wrapped
