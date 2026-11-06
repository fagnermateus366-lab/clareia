"""Independent display controls; subtitle downloads always retain the speech."""
FIELDS=('legendas_grandes','legendas_rodape','fundo_legenda_rodape','cor_legenda_rodape','cor_fundo_rodape')

def large_enabled(settings):
    if settings.legendas_grandes is not None:return settings.legendas_grandes
    return not(settings.tipo_video=='shorts' and settings.modo_shorts=='animacoes')

def state(settings):
    large=settings.tipo_video=='shorts' and large_enabled(settings)
    footer=settings.legendas_rodape=='sim' or settings.legendas_rodape=='auto' and not large
    return large,footer

def identity(settings):
    from .core import Settings
    default=Settings()
    values={k:getattr(settings,k) for k in FIELDS if getattr(settings,k)!=getattr(default,k)}
    return values

def footer_style(settings):
    return dict(footer_background=settings.fundo_legenda_rodape,footer_text=settings.cor_legenda_rodape,footer_color=settings.cor_fundo_rodape)

def files(cues,words,settings,srt,ass):
    from .render import subtitle_files
    large,footer=state(settings)
    subtitle_files(cues,srt,ass,settings.formato=='9:16',words=words if large else None,
        caption_style=settings.legenda_shorts,caption_effect=settings.efeito_legenda,caption_position=settings.posicao_legenda,
        caption_preset=settings.modelo_legenda,**footer_style(settings))
    paths=[ass] if large or footer else []
    if large and footer:
        second=ass.with_name(ass.stem+'.footer.ass')
        subtitle_files(cues,srt.with_name(srt.stem+'.footer.srt'),second,settings.formato=='9:16',**footer_style(settings))
        paths.append(second)
    return paths
