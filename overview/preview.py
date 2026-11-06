"""Short previews use the actual local voice and renderer, with no LLM request."""
from .core import ROOT, Scene, Settings, digest, write_json


def prepare(settings: Settings,source_path=None):
    values={k:getattr(settings,k) for k in ('voz','estilo_locucao','velocidade','formato','animacao','velocidade_mao','destaques_animados','estilo')}
    from .caption_presentation import identity
    values.update(identity(settings))
    background=None
    from .video_backgrounds import STYLES,resolve
    if settings.imagem_fundo and settings.animacao in STYLES and not (settings.tipo_video=='shorts' and settings.modo_shorts in ('fotos','clipes')):
        if source_path is None:raise ValueError('Abra o projeto para testar a imagem de fundo.')
        background=resolve(source_path,settings.imagem_fundo)
        values.update(imagem_fundo=settings.imagem_fundo,intensidade_fundo=settings.intensidade_fundo)
    if settings.animacao=='shotcraft':
        from .shotcraft_types import SHOT_FIELDS
        values.update({k:getattr(settings,k).model_dump() if k=='shotcraft_ia' else getattr(settings,k) for k in SHOT_FIELDS})
    if settings.tipo_video=='shorts':
        values.update(tipo_video='shorts',legenda_shorts=settings.legenda_shorts,efeito_legenda=settings.efeito_legenda,
                      posicao_legenda=settings.posicao_legenda,modo_shorts=settings.modo_shorts,composicao_shorts=settings.composicao_shorts,minutos=1)
    from .runtime import gemini_only
    if gemini_only(settings):
        for field in ('roteiro_provedor','roteiro_modelo','gemini_projeto_completo','gemini_modelo_voz','gemini_voz','gemini_voz_secundaria'):values[field]=getattr(settings,field)
    for field in ('animar_elementos','imagem_estatica','transicao','duracao_transicao','aplicar_transicao'):
        if getattr(settings,field)!=getattr(Settings(),field):values[field]=getattr(settings,field)
    if settings.animacao in ('historia_ilustrada','colagem_documental'):values['camera_dinamica']=settings.camera_dinamica
    cfg=Settings(**values,modo_visual='slide')
    key=digest('animation-preview-v4-scene-passages',values)
    if background:key=digest(key,'background-v1',digest(background.read_bytes().hex()))
    if cfg.tipo_video=='shorts' and cfg.modo_shorts=='animacoes':key=digest(key,'animation-default-discreet-captions-v1')
    if cfg.animacao=='shotcraft':
        from .shotcraft import VERSION
        from .shotcraft_remotion import fingerprint
        key=digest(key,VERSION,fingerprint())
    from .timeline import transition_durations,VERSION as TIMELINE_VERSION
    if any(transition_durations({},cfg,2)[1]):key=digest(key,TIMELINE_VERSION)
    if cfg.transicao=='papel_amassado':
        from .paper_transition import fingerprint
        key=digest(key,fingerprint())
    if cfg.animacao!='historia_ilustrada':
        from .diagram_layout import LAYOUT_VERSION
        key=digest(key,LAYOUT_VERSION)
    if cfg.animacao=='historia':key=digest(key,'cartoon-v2')
    if cfg.animacao=='historia_ilustrada':
        from .illustrated import asset_fingerprint
        key=digest(key,asset_fingerprint())
    if cfg.animacao=='colagem_documental':
        values['movimento_figuras']=settings.movimento_figuras
        cfg.movimento_figuras=settings.movimento_figuras
        from .collage_assets import fingerprint
        from .collage import VERSION
        key=digest(key,VERSION,fingerprint(),settings.movimento_figuras)
    path=ROOT/'output/animation-previews'/key
    path.mkdir(parents=True,exist_ok=True)
    demo_images=[]
    if cfg.tipo_video=='shorts' and cfg.modo_shorts=='fotos':
        from .short_photos import demo_photos
        demo_images=demo_photos(path/'assets')
    if background:
        import shutil
        (path/'assets').mkdir(exist_ok=True)
        shutil.copy2(background,path/'assets'/background.name)
        demo_images.append(background.name)
    scene=Scene(titulo='Uma ideia ganha forma',narracao_ptbr='Uma pergunta desperta a curiosidade. Um exemplo transforma a ideia em compreensão.',texto_na_tela=['Pergunte','Observe','Entenda']).model_dump()
    if background:scene['usar_imagem']=False
    board={'momentos':[
        {'frase':0,'titulo':'Uma pergunta desperta a curiosidade','composicao':'conceito','elementos':[{'rotulo':'Uma pergunta','icone':'pensador'},{'rotulo':'Curiosidade','icone':'mensagem'}]},
        {'frase':1,'titulo':'Um exemplo faz a ideia ganhar vida','composicao':'conceito','elementos':[{'rotulo':'Um exemplo','icone':'professor'},{'rotulo':'Compreensão','icone':'leitor'}]}]}
    if cfg.animacao=='historia':
        scene=Scene(titulo='Uma história ganha vida',narracao_ptbr='Um senhor caminha pela rua. Ele para, observa a casa e acena para uma vizinha.',texto_na_tela=['Uma história em movimento']).model_dump()
        board={'momentos':[
            {'frase':0,'titulo':'Um passeio pela rua','composicao':'conceito','ambiente':'rua','elenco':[{'nome':'O senhor','tipo':'idoso','acao':'andar'}],'elementos':[{'rotulo':'Senhor','icone':'pessoa'},{'rotulo':'Rua','icone':'documento'}]},
            {'frase':1,'titulo':'Um encontro no caminho','composicao':'conceito','ambiente':'rua','elenco':[{'nome':'O senhor','tipo':'idoso','acao':'gesticular'},{'nome':'A vizinha','tipo':'pessoa','acao':'observar'}],'elementos':[{'rotulo':'Casa','icone':'documento'},{'rotulo':'Vizinha','icone':'pessoa'}]}]}
    if cfg.animacao=='historia_ilustrada':
        scene=Scene(titulo='Uma ideia, uma descoberta',narracao_ptbr='Um senhor caminha pela rua. Ele para e reflete sobre uma ideia. Surpreso, ele descobre uma nova possibilidade.',texto_na_tela=['Observe','Reflita','Descubra']).model_dump()
        board={'momentos':[
            {'frase':j,'titulo':title,'composicao':'conceito','ambiente':'rua','elenco':[{'nome':'O senhor','tipo':'idoso','acao':action,'expressao':mood}],'elementos':[{'rotulo':'Ideia','icone':'lampada'},{'rotulo':'Descoberta','icone':'pessoa'}]}
            for j,(title,action,mood) in enumerate([('Um passeio pelo bairro','andar','serena'),('Um momento de reflexão','pensar','reflexiva'),('Uma nova possibilidade','observar','surpresa')])]}
    if cfg.animacao=='colagem_documental':
        scene=Scene(titulo='Figuras que ganham vida no papel',narracao_ptbr='Um avião cruza o céu e um navio navega sobre as ondas. O DNA, o cérebro, o coração e os pulmões ajudam a explicar a vida. Engrenagens, lâmpadas, painéis solares e turbinas mostram diferentes formas de usar energia.',texto_na_tela=['Transporte','Vida','Energia']).model_dump()
        board={'momentos':[
            {'frase':0,'titulo':'O mundo em movimento','composicao':'conceito','elementos':[{'rotulo':'Transporte aéreo','icone':'globo','recorte':'avião'},{'rotulo':'Transporte marítimo','icone':'globo','recorte':'navio'}]},
            {'frase':1,'titulo':'A vida tem movimento','composicao':'conceito','elementos':[{'rotulo':'DNA','icone':'cerebro','recorte':'DNA'},{'rotulo':'Cérebro','icone':'cerebro','recorte':'cérebro'},{'rotulo':'Coração','icone':'cerebro','recorte':'coração'},{'rotulo':'Pulmões','icone':'cerebro','recorte':'pulmões'}]},
            {'frase':2,'titulo':'Mecanismos e energia','composicao':'conceito','elementos':[{'rotulo':'Engrenagem','icone':'engrenagem','recorte':'engrenagem'},{'rotulo':'Lâmpada','icone':'lampada','recorte':'lâmpada'},{'rotulo':'Energia solar','icone':'lampada','recorte':'painel solar'},{'rotulo':'Energia eólica','icone':'lampada','recorte':'turbina eólica'}]}]}
    scenes=[scene];boards=[board]
    if cfg.animacao=='shotcraft':
        from .shotcraft_previews import example
        scene,board=example(cfg);scenes=[scene];boards=[board]
    if cfg.animacao=='colagem_documental':
        # Show an actual scene boundary as well as a quiet sticker replacement;
        # one scene alone cannot demonstrate the scene-only default passage.
        scenes=[
            Scene(titulo='Introdução: figuras no papel',narracao_ptbr='Um avião cruza o céu e um navio navega sobre as ondas.',texto_na_tela=['Transporte'],etapa='introducao').model_dump(),
            Scene(titulo='Explicação: vida e energia',narracao_ptbr='O DNA, o cérebro, o coração e os pulmões ajudam a explicar a vida. Engrenagens, lâmpadas, painéis solares e turbinas mostram diferentes formas de usar energia.',texto_na_tela=['Vida','Energia'],etapa='explicacao').model_dump()]
        boards=[{'momentos':[{**board['momentos'][0],'frase':0}]},
                {'momentos':[{**b,'frase':i} for i,b in enumerate(board['momentos'][1:])]}]
    write_json(path/'project.json',{'titulo':scene['titulo'],'config':cfg.model_dump()})
    write_json(path/'sources.json',{'fontes':[],'imagens':demo_images})
    write_json(path/'script.json',scenes)
    from .storyboard import board_key
    for selected,selected_board in zip(scenes,boards):
        story_key=board_key(selected,story=cfg.animacao in ('historia','historia_ilustrada'),collage=cfg.animacao=='colagem_documental',settings=cfg)
        write_json(path/'cache/storyboard'/(story_key+'.json'),selected_board)
    return key,path,cfg


def preview_path(key):
    if len(key)!=24 or any(c not in '0123456789abcdef' for c in key):raise FileNotFoundError()
    path=ROOT/'output/animation-previews'/key
    if not (path/'project.json').is_file():raise FileNotFoundError()
    return path
