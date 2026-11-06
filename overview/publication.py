"""One scheduled job owns rendering, writing and upload until publication is confirmed."""
from __future__ import annotations

import uuid

from .core import digest, read_json, write_json, set_status


def settings_for_schedule(path, channel='', title='', brief='', privacy='public', made_for_kids=False, run_id=None, *, include_sources=False, include_credits=False, playlists=None, youtube_ia=None):
    from .youtube import channels,channel_id,clean
    from .youtube_upload import connected
    if not channel:
        choices=[c for c in channels() if connected(c['id'])]
        channel=next((c['id'] for c in choices if c.get('padrao')),choices[0]['id'] if len(choices)==1 else '')
    if not channel:raise ValueError('Conecte e selecione um canal do YouTube antes de agendar a publicação automática.')
    channel_id(channel)
    if not connected(channel):raise ValueError('O canal escolhido não está conectado. Conecte-o com Google antes de agendar.')
    requested=title.strip()
    if requested and (len(requested)>100 or clean(requested)!=requested):
        raise ValueError('Use um título de publicação de até 100 caracteres, sem os sinais < ou > e sem quebras de linha.')
    if privacy not in ('public','unlisted','private'):raise ValueError('Escolha uma visibilidade válida.')
    from .youtube_playlists import validate_selection
    selected=validate_selection(channel,playlists)
    from .stage_ai import choice
    stored=read_json(path/'project.json',{}).get('config',{}).get('youtube_ia')
    ai=choice(youtube_ia if youtube_ia is not None else stored)
    return {'canal':channel,'titulo':requested,'orientacao':brief.strip(),'privacidade':privacy,
            'conteudo_infantil':bool(made_for_kids),'run_id':run_id or uuid.uuid4().hex,
            'incluir_fontes':bool(include_sources),'incluir_creditos':bool(include_credits),'playlists':selected,'youtube_ia':ai.model_dump()}


def run_scheduled(path, render):
    from .youtube import metadata
    from .youtube_upload import prepare_upload,upload,upload_status,confirm_upload,_file_identity
    from .render import Paused
    task=read_json(path/'task.json',{})
    checkpoint=read_json(path/'scheduled-publication.json',{})
    legacy_id='legacy-'+str(task.get('job_id',path.name))
    options=task.get('opcoes') or (checkpoint.get('options') if checkpoint.get('run_id')==legacy_id else None) or settings_for_schedule(path,run_id=legacy_id)
    if not task.get('opcoes'):
        task['opcoes']=options;write_json(path/'task.json',task)
    if options.get('youtube_ia') is not None:
        from .stage_ai import save_youtube_choice
        save_youtube_choice(path,options['youtube_ia'])
    if checkpoint.get('run_id')!=options['run_id']:
        checkpoint={'run_id':options['run_id'],'stage':'render' if read_json(path/'script.json') else 'script','options':options}
        write_json(path/'scheduled-publication.json',checkpoint)
    def paused():
        if (path/'pause.request').exists():raise Paused('Fluxo agendado pausado. Retome para continuar da etapa preservada.')
    paused()
    if checkpoint['stage']=='script':
        from .projects import generate
        generate(path)
        checkpoint.update(stage='render',gerou_roteiro=True);write_json(path/'scheduled-publication.json',checkpoint)
    paused()
    input_hash=digest(read_json(path/'project.json',{}).get('config'),read_json(path/'script.json',[]),read_json(path/'pronuncia.json',{}))
    try:compatible=checkpoint.get('file_hash')==_file_identity(path)[0] and checkpoint.get('input_hash')==input_hash
    except ValueError:compatible=False
    if checkpoint['stage']=='render' or not compatible:
        checkpoint.update(stage='render');write_json(path/'scheduled-publication.json',checkpoint)
        render()
        if read_json(path/'status.json',{}).get('status')=='pausado':raise Paused('Renderização pausada. O fluxo continuará antes de publicar.')
        if read_json(path/'status.json',{}).get('status')!='concluido':raise ValueError('A renderização não confirmou um vídeo pronto para publicação.')
        checkpoint.update(stage='metadata',file_hash=_file_identity(path)[0],input_hash=input_hash);write_json(path/'scheduled-publication.json',checkpoint)
    paused()
    if checkpoint['stage']=='metadata':
        set_status(path,'preparando_publicacao','Preparando uma descrição sobre o assunto do vídeo e o título do agendamento',.99)
        cfg=read_json(path/'project.json',{}).get('config',{})
        texts=metadata(path,regenerate=True,use_ai=not cfg.get('roteiro_pronto') or bool(options.get('youtube_ia',{}).get('ativa')),title=options['titulo'],brief=options['orientacao'],auto_title=not options['titulo'],
                       include_sources=options.get('incluir_fontes',False),include_credits=options.get('incluir_creditos',False),youtube_ia=options.get('youtube_ia'))
        info=read_json(path/'project.json')
        if info.get('titulo_automatico'):
            info['titulo']=texts['titulo'];write_json(path/'project.json',info)
        checkpoint['titulo_publicado']=texts['titulo'];write_json(path/'scheduled-publication.json',checkpoint)
        set_status(path,'concluido','Vídeo pronto. Preparando o envio automático ao YouTube.',1)
        prepare_upload(path,options['canal'],options['privacidade'],options['conteudo_infantil'],playlists=options.get('playlists',[]))
        checkpoint['stage']='upload';write_json(path/'scheduled-publication.json',checkpoint)
    paused()
    # Resumable sessions are reused after a pause/restart; no second upload job is created.
    if checkpoint['stage']!='complete':
        state=upload_status(path)
        if not (state.get('arquivo_atual') and state.get('video_id') and state.get('playlists_concluidas')):
            upload(path)
        confirmed=confirm_upload(path,options['privacidade'])
        checkpoint.update(stage='complete',video_id=confirmed['video_id'],url=confirmed['url'])
        write_json(path/'scheduled-publication.json',checkpoint)
    set_status(path,'enviado_youtube','Fluxo agendado concluído: vídeo criado e publicação confirmada no YouTube.',1)

