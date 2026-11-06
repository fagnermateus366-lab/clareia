"""Independent text-only providers for the lesson plan and YouTube copy."""
from .core import StageAI,Settings,MODEL,read_json,write_json


def choice(value=None):
    selected=value if isinstance(value,StageAI) else StageAI.model_validate(value or {})
    if selected.ativa and selected.provedor!='local' and not selected.modelo:
        raise ValueError('Escolha o modelo da IA específica desta etapa.')
    return selected


def settings_for(settings,stage,override=None):
    selected=choice(override if override is not None else getattr(settings,stage+'_ia'))
    if not selected.ativa:return settings
    return settings.model_copy(update={'roteiro_provedor':selected.provedor,'roteiro_modelo':selected.modelo,
                                       'gemini_projeto_completo':False})


def identity(settings):
    return {'provedor':settings.roteiro_provedor,'modelo':settings.roteiro_modelo or (MODEL if settings.roteiro_provedor=='local' else '')}


def save_youtube_choice(path,value):
    selected=choice(value)
    info=read_json(path/'project.json')
    settings=Settings.model_validate(info['config'])
    if settings.youtube_ia!=selected:
        info['config']={**info['config'],'youtube_ia':selected.model_dump()}
        write_json(path/'project.json',info)
    return selected
