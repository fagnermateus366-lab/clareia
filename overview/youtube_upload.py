"""Google desktop OAuth with PKCE and resumable uploads of existing local MP4s."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import urlencode, urlparse

import httpx

from .core import ROOT, digest, read_json, write_json, set_status
from .providers import protect

VAULT = ROOT / '.private' / 'youtube-oauth.json'
LOCK = threading.RLock()
ATTEMPTS = {}
SCOPES = ('https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/youtube.force-ssl')
AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
CHANNEL_URL = 'https://www.googleapis.com/youtube/v3/channels'
UPLOAD_URL = 'https://www.googleapis.com/upload/youtube/v3/videos'
CHUNK_SIZE = 8 * 1024 * 1024
WAIT = time.sleep


def _read_secret(key):
    encrypted = read_json(VAULT, {}).get(key)
    if not encrypted:return None
    try:return json.loads(protect(base64.b64decode(encrypted), decrypt=True).decode('utf-8'))
    except (ValueError,UnicodeError,TypeError):
        raise ValueError('O Windows não liberou a conexão do YouTube nesta execução. Reinicie por atualizar-estudio.bat na sua sessão do Windows; os dados protegidos foram preservados.') from None


def _save_secret(key, value):
    saved = read_json(VAULT, {})
    if value is None:saved.pop(key,None)
    else:saved[key] = base64.b64encode(protect(json.dumps(value,ensure_ascii=False).encode('utf-8'))).decode('ascii')
    write_json(VAULT,saved)


def configuration():
    saved=read_json(VAULT,{})
    return {'configurado':'client' in saved,'canais_conectados':sum(k.startswith('channel:') for k in saved)}


def validate_vault():
    with LOCK:
        if 'client' in read_json(VAULT,{}):_read_secret('client')


def configure(document):
    try:
        raw=json.loads(document)
        client=raw['installed']
        cid=client['client_id'];secret=client['client_secret']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.apps\.googleusercontent\.com',cid) or not isinstance(secret,str) or not 1<=len(secret)<=1000:
            raise ValueError()
    except (ValueError,KeyError,TypeError):
        raise ValueError('Selecione o JSON de um cliente OAuth do tipo Aplicativo para computador, baixado do Google Cloud. Uma chave de API Gemini não serve para conectar o YouTube.') from None
    with LOCK:
        existing=_read_secret('client')
        if existing and existing['client_id']!=cid and configuration()['canais_conectados']:
            raise ValueError('Desconecte os canais antes de trocar o cliente OAuth para outro projeto Google.')
        _save_secret('client',{'client_id':cid,'client_secret':secret})
    return configuration()


def connected(cid):
    return 'channel:'+cid in read_json(VAULT,{})


def disconnect(cid):
    # Local disconnection never revokes other channels that share a Google grant.
    with LOCK:
        if connected(cid):_save_secret('channel:'+cid,None)


def begin_connection(origin, expected=''):
    url=urlparse(origin)
    if url.scheme!='http' or url.hostname not in ('127.0.0.1','localhost') or url.path not in ('','/'):
        raise ValueError('Abra o estúdio no endereço local para conectar o Google.')
    with LOCK:
        client=_read_secret('client')
        if not client:raise ValueError('Configure o cliente OAuth do Google antes de conectar um canal.')
        now=time.time()
        for key in list(ATTEMPTS):
            if ATTEMPTS[key]['expires']<now:ATTEMPTS.pop(key)
        attempt=secrets.token_urlsafe(32);state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64)
        redirect=origin.rstrip('/')+'/api/youtube/oauth/callback'
        ATTEMPTS[attempt]={'state':state,'verifier':verifier,'redirect':redirect,'client':client,
                           'expected':expected,'expires':now+600,'status':'aguardando','message':'Aguardando autorização no Google.'}
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).rstrip(b'=').decode('ascii')
        params={'client_id':client['client_id'],'redirect_uri':redirect,'response_type':'code','scope':' '.join(SCOPES),
                'access_type':'offline','prompt':'consent select_account','state':state,'code_challenge':challenge,'code_challenge_method':'S256'}
        return {'id':attempt,'url':AUTH_URL+'?'+urlencode(params)}


def connection_status(attempt):
    with LOCK:
        data=ATTEMPTS.get(attempt)
        if not data:raise ValueError('Conexão expirada. Clique em Conectar com Google novamente.')
        if data['expires']<time.time() and data['status']=='aguardando':
            data.update(status='erro',message='O prazo de autorização expirou. Conecte novamente.')
        return {k:data[k] for k in ('status','message','channel') if k in data}


def _api_error(response):
    if response.status_code==401:return 'Sua autorização do YouTube expirou ou foi revogada. Conecte o canal novamente.'
    try:
        error=response.json().get('error',{})
        reasons=[e.get('reason','') for e in error.get('errors',[])] if isinstance(error,dict) else [error]
        if isinstance(error,dict):reasons.append(error.get('status',''))
    except (ValueError,TypeError,AttributeError):reasons=[]
    if any(r in reasons for r in ('accessNotConfigured','SERVICE_DISABLED')):
        return 'Ative a YouTube Data API v3 no mesmo projeto Google do cliente OAuth.'
    if any(r in reasons for r in ('quotaExceeded','dailyLimitExceeded','rateLimitExceeded')):
        return 'A cota da API do YouTube foi atingida. Aguarde a renovação da cota e retome o envio.'
    if 'uploadLimitExceeded' in reasons:return 'O canal atingiu o limite de envios do YouTube. Aguarde e tente novamente.'
    if response.status_code==403:return 'O Google recusou a operação. Confira se a YouTube Data API v3 está ativa e reconecte o canal com as permissões solicitadas.'
    if response.status_code>=500:return 'O YouTube está temporariamente indisponível. Você pode retomar o envio.'
    return f'O YouTube recusou a operação (HTTP {response.status_code}). Confira os dados e a autorização do canal.'


def _owned_channel(client, access):
    response=client.get(CHANNEL_URL,params={'part':'id,snippet','mine':'true'},headers={'Authorization':'Bearer '+access})
    if response.status_code!=200:raise ValueError(_api_error(response))
    items=response.json().get('items',[])
    if len(items)!=1:raise ValueError('Não foi possível identificar um único canal autorizado. Conecte novamente e escolha o canal desejado no Google.')
    item=items[0]
    from .youtube import channel_id
    return channel_id(item['id']),item.get('snippet',{}).get('title','Meu canal')


def finish_connection(state,code='',error=''):
    with LOCK:
        attempt=next((a for a in ATTEMPTS.values() if secrets.compare_digest(a['state'],state)),None) if state else None
        if not attempt or attempt['expires']<time.time() or attempt['status']!='aguardando':
            raise ValueError('Autorização inválida, já utilizada ou expirada. Inicie uma nova conexão no estúdio.')
        attempt['status']='conectando'  # consume state before any network call
    try:
        if error or not code:raise ValueError('A autorização foi cancelada ou recusada no Google. Você pode tentar novamente.')
        config=attempt['client']
        with httpx.Client(timeout=30,follow_redirects=False) as client:
            response=client.post(TOKEN_URL,data={**config,'code':code,'code_verifier':attempt['verifier'],
                                 'redirect_uri':attempt['redirect'],'grant_type':'authorization_code'})
            if response.status_code!=200:raise ValueError('O Google não concluiu a autorização. Confira o cliente OAuth e conecte novamente.')
            token=response.json()
            granted=set(token.get('scope','').split())
            if not set(SCOPES).issubset(granted):raise ValueError('Autorize o envio de vídeos, a identificação do canal e o gerenciamento de playlists. Conecte novamente para concluir.')
            cid,name=_owned_channel(client,token['access_token'])
        if attempt['expected'] and attempt['expected']!=cid:
            raise ValueError('O canal escolhido no Google é diferente do canal solicitado no estúdio. Conecte novamente e selecione o canal correto.')
        with LOCK:
            old=_read_secret('channel:'+cid) or {}
            refresh=token.get('refresh_token') or old.get('refresh_token')
            if not refresh:raise ValueError('O Google não forneceu autorização para manter a conexão. Conecte novamente e autorize o acesso.')
            _save_secret('channel:'+cid,{'access_token':token['access_token'],'refresh_token':refresh,
                        'expires':time.time()+float(token.get('expires_in',3600)),'client_id':config['client_id'],'scopes':sorted(granted)})
            from .youtube import channels,save_channel
            existing=next((c for c in channels() if c['id']==cid),{})
            save_channel(existing.get('nome',name),cid,existing.get('padrao',False))
            attempt.update(status='conectado',message='Canal conectado. Você já pode enviar o vídeo diretamente.',channel=cid)
            return connection_status(next(k for k,v in ATTEMPTS.items() if v is attempt))
    except httpx.HTTPError:
        message='Não foi possível conversar com o Google. Confira sua conexão e conecte novamente.'
    except (KeyError,TypeError,ValueError) as exc:
        message=str(exc) if isinstance(exc,ValueError) else 'O Google devolveu uma autorização incompleta. Conecte novamente.'
    with LOCK:attempt.update(status='erro',message=message)
    raise ValueError(message)


def _access_token(cid,force=False):
    with LOCK:
        token=_read_secret('channel:'+cid)
        config=_read_secret('client')
        if not token or not config:raise ValueError('Conecte este canal com Google antes de enviar o vídeo.')
        if token.get('client_id')!=config['client_id']:raise ValueError('A conexão pertence a outro cliente OAuth. Conecte o canal novamente.')
        if not force and token.get('expires',0)>time.time()+90:return token['access_token']
        try:
            response=httpx.post(TOKEN_URL,data={**config,'refresh_token':token['refresh_token'],'grant_type':'refresh_token'},timeout=30)
        except httpx.HTTPError:raise ValueError('Não foi possível renovar a conexão do Google. Confira a internet e tente retomar.') from None
        if response.status_code!=200:raise ValueError('Sua autorização do Google expirou ou foi revogada. Conecte o canal novamente.')
        data=response.json()
        token.update(access_token=data['access_token'],expires=time.time()+float(data.get('expires_in',3600)))
        if data.get('scope'):token['scopes']=data['scope'].split()
        _save_secret('channel:'+cid,token)
        return token['access_token']


def _authorized(client,cid,method,url,**kwargs):
    headers=kwargs.pop('headers',{})
    for attempt in range(2):
        token=_access_token(cid,force=attempt==1)
        response=client.request(method,url,headers={**headers,'Authorization':'Bearer '+token},**kwargs)
        if response.status_code!=401:return response
    raise ValueError(_api_error(response))


def _session_key(path):return 'upload:'+digest(str(Path(path).resolve()))


def _file_identity(path):
    video=path/'export/video.mp4'
    if not video.is_file() or not video.stat().st_size:raise ValueError('Renderize o vídeo antes de enviar ao YouTube.')
    info=video.stat()
    return digest(info.st_size,info.st_mtime_ns),info.st_size


def upload_status(path):
    state=read_json(path/'youtube-upload.json',{})
    result={k:v for k,v in state.items() if k not in ('request','file_hash')}
    result['retomavel']=_session_key(path) in read_json(VAULT,{}) and not state.get('video_id')
    try:result['arquivo_atual']=state.get('file_hash')==_file_identity(path)[0]
    except ValueError:result['arquivo_atual']=False
    result['playlists_concluidas']=all(pid in state.get('playlists_aplicadas',{}) for pid in state.get('playlists',[]))
    return result


def prepare_upload(path,cid,privacy,made_for_kids,*,restart=False,playlists=None):
    from .youtube import metadata
    from .youtube_playlists import validate_selection
    fingerprint,total=_file_identity(path)
    from .short_video import verify_project_export
    short_info=verify_project_export(path)
    if read_json(path/'status.json',{}).get('status') not in ('concluido','enviado_youtube','erro_youtube','pausado_youtube'):
        raise ValueError('Renderize o roteiro revisado antes de enviar o vídeo ao YouTube.')
    if not connected(cid):raise ValueError('Conecte o canal com Google para enviar sem baixar o vídeo.')
    selected=validate_selection(cid,playlists)
    old=read_json(path/'youtube-upload.json',{})
    if old.get('file_hash')==fingerprint and old.get('channel')==cid and old.get('video_id'):
        old['playlists']=selected
        done=all(pid in old.get('playlists_aplicadas',{}) for pid in selected)
        if done and old.get('status') in ('erro','pausado','organizando_playlists'):
            old.update(status='enviado',message='Arquivo enviado ao YouTube.' if not selected else 'Arquivo enviado ao YouTube e incluído nas playlists selecionadas.')
            set_status(path,'enviado_youtube',old['message'],1)
        write_json(path/'youtube-upload.json',old)
        return upload_status(path)
    with LOCK:
        session=_read_secret(_session_key(path))
        if session and old.get('video_id'):
            _save_secret(_session_key(path),None);session=None
        if restart:
            changed=session and (session.get('file_hash')!=fingerprint or session.get('channel')!=cid)
            if old.get('status')!='expirado' and not changed:
                raise ValueError('Uma nova sessão só é necessária quando o envio expirou ou o arquivo/canal mudou.')
            _save_secret(_session_key(path),None);session=None
        if session:
            if session.get('file_hash')!=fingerprint or session.get('channel')!=cid:
                raise ValueError('Há um envio pendente de outro arquivo ou canal neste projeto. Retome o arquivo original antes de substituir o vídeo.')
            if selected!=old.get('playlists',[]):raise ValueError('Retome o envio com as playlists escolhidas ao iniciá-lo. Você poderá alterar a seleção depois do envio.')
            request=session['request']
        else:
            data=metadata(path)
            request={'titulo':data['titulo'],'descricao':data['descricao'],'privacy':privacy,'made_for_kids':made_for_kids}
        state={'status':'fila','message':'Envio na fila. O MP4 será lido diretamente do projeto.',
               'tipo_video':'shorts' if short_info else 'video','shorts':short_info,
               'channel':cid,'file_hash':fingerprint,'total':total,'sent':old.get('sent',0) if session else 0,
               'request':request,'privacy':request['privacy'],'made_for_kids':request['made_for_kids'],
               'playlists':selected,'playlists_aplicadas':{}}
        write_json(path/'youtube-upload.json',state)
        return upload_status(path)


def _session_url(value):
    url=urlparse(value)
    if url.scheme!='https' or url.netloc not in ('www.googleapis.com','youtube.googleapis.com') or url.path!='/upload/youtube/v3/videos' or url.fragment:
        raise ValueError('O Google devolveu um endereço de envio inesperado. O envio foi interrompido.')
    return value


def _offset(response,total):
    value=response.headers.get('Range','')
    if not value:return 0
    match=re.fullmatch(r'bytes=0-(\d+)',value)
    if not match or not 0<=int(match[1])<total:raise ValueError('O YouTube devolveu uma posição de envio inválida. Tente retomar.')
    return int(match[1])+1


def _progress(path,state,status,message,sent=None):
    if sent is not None:state['sent']=sent
    state.update(status=status,message=message)
    write_json(path/'youtube-upload.json',state)
    set_status(path,'enviando_youtube',message,state.get('sent',0)/max(1,state['total']))


def _complete(path,state,response):
    data=response.json();vid=data.get('id','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):raise ValueError('O YouTube não confirmou o identificador do vídeo. Retome o envio para consultar o resultado.')
    if data.get('snippet',{}).get('channelId',state['channel'])!=state['channel']:
        raise ValueError('O YouTube retornou um canal diferente do esperado. Confira o canal antes de continuar.')
    privacy=data.get('status',{}).get('privacyStatus',state['privacy'])
    state.update(status='enviado',message='Arquivo enviado ao YouTube. O YouTube ainda pode estar processando o vídeo.',
                 sent=state['total'],video_id=vid,url=('https://www.youtube.com/shorts/' if state.get('tipo_video')=='shorts' else 'https://www.youtube.com/watch?v=')+vid,
                 studio='https://studio.youtube.com/video/'+vid+'/edit',privacy=privacy)
    write_json(path/'youtube-upload.json',state)
    set_status(path,'enviando_youtube' if state.get('playlists') else 'enviado_youtube',state['message'],1)
    if state.get('playlists'):
        state.update(status='organizando_playlists',message='Arquivo enviado. Incluindo o vídeo nas playlists escolhidas…')
        write_json(path/'youtube-upload.json',state)
    return upload_status(path)


def upload(path):
    try:
        _upload(path)
        from .youtube_playlists import apply_selection
        return apply_selection(path)
    except httpx.HTTPError:
        raise ValueError('A conexão com o YouTube foi interrompida. Confira a internet e retome o envio.') from None


def _upload(path):
    state=read_json(path/'youtube-upload.json',{})
    fingerprint,total=_file_identity(path)
    if state.get('file_hash')!=fingerprint:raise ValueError('O vídeo mudou depois do pedido de envio. Revise e solicite o envio novamente.')
    if state.get('video_id'):return upload_status(path)
    cid=state['channel']
    with httpx.Client(timeout=httpx.Timeout(120,connect=20),follow_redirects=False) as client:
        actual,_=_owned_channel(client,_access_token(cid))
        if actual!=cid:raise ValueError('A autorização pertence a outro canal. Reconecte o canal escolhido antes de enviar.')
        with LOCK:session=_read_secret(_session_key(path))
        if not session:
            request=state['request']
            response=_authorized(client,cid,'POST',UPLOAD_URL,params={'uploadType':'resumable','part':'snippet,status'},
                        headers={'X-Upload-Content-Length':str(total),'X-Upload-Content-Type':'video/mp4'},
                        json={'snippet':{'title':request['titulo'],'description':request['descricao'],'categoryId':'27'},
                              'status':{'privacyStatus':request['privacy'],'selfDeclaredMadeForKids':request['made_for_kids']}})
            if response.status_code not in (200,201):raise ValueError(_api_error(response))
            session={'url':_session_url(response.headers.get('Location','')),'file_hash':fingerprint,'channel':cid,'request':request}
            with LOCK:_save_secret(_session_key(path),session)
        uri=_session_url(session['url'])
        offset=0;recover=True;failures=0
        with (path/'export/video.mp4').open('rb') as video:
            while True:
                if (path/'pause.request').exists():
                    from .render import Paused
                    raise Paused('Envio pausado. Os bytes confirmados pelo YouTube serão reaproveitados.')
                try:
                    response=None
                    was_probe=recover
                    if recover:
                        response=_authorized(client,cid,'PUT',uri,headers={'Content-Length':'0','Content-Range':f'bytes */{total}'},content=b'')
                        recover=False
                    else:
                        video.seek(offset);chunk=video.read(CHUNK_SIZE)
                        if not chunk:raise ValueError('O YouTube ainda não confirmou o envio completo. Retome para consultar o resultado.')
                        response=_authorized(client,cid,'PUT',uri,headers={'Content-Type':'video/mp4','Content-Length':str(len(chunk)),
                                             'Content-Range':f'bytes {offset}-{offset+len(chunk)-1}/{total}'},content=chunk)
                    if response.status_code in (200,201):return _complete(path,state,response)
                    if response.status_code in (404,410):
                        _progress(path,state,'expirado','A sessão de envio expirou no YouTube. Inicie uma nova sessão para enviar o arquivo novamente.')
                        raise ValueError(state['message'])
                    if response.status_code==308:
                        next_offset=_offset(response,total)
                        if next_offset==offset and not was_probe:failures+=1
                        elif next_offset>offset:failures=0
                        offset=next_offset
                        _progress(path,state,'enviando',f'Enviando diretamente ao YouTube · {offset/total:.0%}',offset)
                        if failures>=3:raise ValueError('O YouTube não confirmou novos bytes. Tente retomar o envio.')
                        continue
                    if response.status_code not in (500,502,503,504,429):raise ValueError(_api_error(response))
                except httpx.HTTPError:
                    pass
                failures+=1
                if failures>3:raise ValueError('A conexão com o YouTube foi interrompida. Clique em Retomar envio para continuar sem começar outro vídeo.')
                _progress(path,state,'enviando','Conexão interrompida. Consultando os bytes recebidos pelo YouTube…',offset)
                retry=response.headers.get('Retry-After','') if response is not None else ''
                WAIT(min(60,float(retry)) if retry.isdigit() else min(2**failures,8));recover=True


def interrupted(path,message,paused=False):
    state=read_json(path/'youtube-upload.json',{})
    if state.get('status')!='expirado':state['status']='pausado' if paused else 'erro'
    state['message']=message
    write_json(path/'youtube-upload.json',state)
    set_status(path,'pausado_youtube' if paused else 'erro_youtube',message,state.get('sent',0)/max(1,state.get('total',1)))


def cancelled(path):
    state=read_json(path/'youtube-upload.json',{})
    state.update(status='cancelado',message='Espera de envio cancelada. O vídeo local foi preservado.')
    write_json(path/'youtube-upload.json',state)


def confirm_upload(path, expected_privacy, timeout=900):
    """Wait for the already-created video; this never starts another upload."""
    state=read_json(path/'youtube-upload.json',{})
    vid=state.get('video_id','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):raise ValueError('O YouTube ainda não confirmou um vídeo para verificar.')
    deadline=time.monotonic()+timeout
    with httpx.Client(timeout=30,follow_redirects=False) as client:
        while True:
            if (path/'pause.request').exists():
                from .render import Paused
                raise Paused('Arquivo enviado. Confirmação de publicação pausada; retome para consultar o mesmo vídeo.')
            try:
                response=_authorized(client,state['channel'],'GET','https://www.googleapis.com/youtube/v3/videos',
                                     params={'part':'snippet,status,processingDetails','id':vid})
            except httpx.HTTPError:
                raise ValueError('O arquivo foi enviado, mas a consulta da publicação falhou por conexão. Retome para verificar o mesmo vídeo.') from None
            if response.status_code!=200:raise ValueError(_api_error(response))
            items=response.json().get('items',[])
            if items:
                item=items[0];status=item.get('status',{});processing=item.get('processingDetails',{})
                if item.get('snippet',{}).get('channelId')!=state['channel']:raise ValueError('A publicação retornada não pertence ao canal agendado.')
                actual=status.get('privacyStatus')
                state['privacy']=actual;write_json(path/'youtube-upload.json',state)
                if actual!=expected_privacy:
                    raise ValueError('O YouTube confirmou visibilidade '+str(actual)+', diferente de '+expected_privacy+'. Confira o vídeo no Studio e retome a confirmação; nenhum vídeo será reenviado.')
                if status.get('uploadStatus') in ('failed','rejected','deleted') or processing.get('processingStatus') in ('failed','terminated'):
                    raise ValueError('O YouTube não concluiu o processamento do vídeo enviado. Confira o motivo no Studio.')
                if status.get('uploadStatus')=='processed' or processing.get('processingStatus')=='succeeded':
                    state.update(status='enviado',message='Publicação confirmada no YouTube · '+{'public':'público','private':'privado','unlisted':'não listado'}[actual],processing='succeeded')
                    write_json(path/'youtube-upload.json',state)
                    set_status(path,'enviado_youtube',state['message'],1)
                    return upload_status(path)
            if time.monotonic()>=deadline:
                raise ValueError('Arquivo enviado. O YouTube ainda está processando; retome a confirmação para consultar o mesmo vídeo, sem reenviar.')
            set_status(path,'enviando_youtube','Arquivo enviado. Aguardando o YouTube concluir o processamento e confirmar a publicação…',1)
            WAIT(3)
