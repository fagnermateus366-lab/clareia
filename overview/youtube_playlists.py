"""Channel-owned playlist choices and resumable, duplicate-safe inclusion."""
import re

import httpx

from .core import read_json,write_json,set_status
from . import youtube_upload as oauth

PLAYLISTS_URL='https://www.googleapis.com/youtube/v3/playlists'
ITEMS_URL='https://www.googleapis.com/youtube/v3/playlistItems'
EDIT_SCOPES={'https://www.googleapis.com/auth/youtube.force-ssl','https://www.googleapis.com/auth/youtube'}


def normalize(values):
    if values is None:return []
    if not isinstance(values,list) or len(values)>100:raise ValueError('Escolha até 100 playlists na lista do canal.')
    result=[]
    for value in values:
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{10,100}',value):
            raise ValueError('Escolha uma playlist válida na lista do canal.')
        if value not in result:result.append(value)
    return result


def can_edit(cid):
    with oauth.LOCK:token=oauth._read_secret('channel:'+cid) or {}
    return bool(set(token.get('scopes',[]))&EDIT_SCOPES)


def _owner(client,cid):
    actual,_=oauth._owned_channel(client,oauth._access_token(cid))
    if actual!=cid:raise ValueError('A conexão pertence a outro canal. Reconecte o canal escolhido antes de selecionar playlists.')


def _get(client,cid,url,params):
    response=oauth._authorized(client,cid,'GET',url,params=params)
    if response.status_code!=200:raise ValueError(oauth._api_error(response))
    return response.json()


def listing(cid):
    from .youtube import channel_id
    channel_id(cid)
    if not oauth.connected(cid):raise ValueError('Conecte este canal com Google para buscar suas playlists.')
    items={};seen=set();page=''
    try:
        with httpx.Client(timeout=30,follow_redirects=False) as client:
            _owner(client,cid)
            while True:
                params={'part':'snippet,status,contentDetails','mine':'true','maxResults':50}
                if page:params['pageToken']=page
                data=_get(client,cid,PLAYLISTS_URL,params)
                for item in data.get('items',[]):
                    snippet=item.get('snippet',{})
                    if snippet.get('channelId')!=cid:continue
                    pid=normalize([item['id']])[0]
                    items[pid]={'id':pid,'titulo':snippet.get('title','Playlist sem título'),
                        'privacidade':item.get('status',{}).get('privacyStatus',''),
                        'videos':item.get('contentDetails',{}).get('itemCount',0)}
                page=data.get('nextPageToken','')
                if not page:break
                if page in seen or len(seen)>=200:raise ValueError('O YouTube não concluiu a lista de playlists. Tente atualizar a lista novamente.')
                seen.add(page)
    except httpx.HTTPError:raise ValueError('Não foi possível buscar as playlists. Confira a internet e clique em Atualizar playlists.') from None
    return {'canal':cid,'itens':sorted(items.values(),key=lambda p:p['titulo'].casefold()),'pode_editar':can_edit(cid)}


def validate_selection(cid,values):
    selected=normalize(values)
    if not selected:return selected
    if not can_edit(cid):raise ValueError('Reconecte este canal com Google e autorize o gerenciamento de playlists antes de usar esta seleção.')
    try:
        with httpx.Client(timeout=30,follow_redirects=False) as client:
            _owner(client,cid)
            for start in range(0,len(selected),50):
                batch=selected[start:start+50]
                data=_get(client,cid,PLAYLISTS_URL,{'part':'snippet','id':','.join(batch),'maxResults':50})
                owned={p['id'] for p in data.get('items',[]) if p.get('snippet',{}).get('channelId')==cid}
                if not set(batch)<=owned:raise ValueError('Uma playlist escolhida não está mais disponível neste canal. Atualize a lista e revise sua seleção.')
    except httpx.HTTPError:raise ValueError('Não foi possível conferir as playlists. Confira a internet e tente novamente.') from None
    return selected


def apply_selection(path):
    state=read_json(path/'youtube-upload.json',{})
    selected=normalize(state.get('playlists',[]))
    if not selected:return oauth.upload_status(path)
    if state.get('file_hash')!=oauth._file_identity(path)[0]:raise ValueError('O vídeo mudou. Revise o arquivo antes de atualizar as playlists.')
    vid=state.get('video_id','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):raise ValueError('O YouTube ainda não confirmou o vídeo para adicionar às playlists.')
    applied=state.setdefault('playlists_aplicadas',{})
    pending=[pid for pid in selected if pid not in applied]
    if pending:
        validate_selection(state['channel'],pending)
        state.update(status='organizando_playlists',message='Arquivo enviado. Incluindo o vídeo nas playlists escolhidas…')
        write_json(path/'youtube-upload.json',state);set_status(path,'enviando_youtube',state['message'],1)
        try:
            with httpx.Client(timeout=30,follow_redirects=False) as client:
                for pid in pending:
                    if (path/'pause.request').exists():
                        from .render import Paused
                        raise Paused('Arquivo enviado. Inclusão nas playlists pausada; retome para continuar com o mesmo vídeo.')
                    data=_get(client,state['channel'],ITEMS_URL,{'part':'id,snippet','playlistId':pid,'videoId':vid,'maxResults':1})
                    items=data.get('items',[])
                    if items:item_id=items[0]['id']
                    else:
                        response=oauth._authorized(client,state['channel'],'POST',ITEMS_URL,params={'part':'snippet'},
                            json={'snippet':{'playlistId':pid,'resourceId':{'kind':'youtube#video','videoId':vid}}})
                        if response.status_code not in (200,201):raise ValueError('O vídeo já foi enviado, mas não foi possível incluir em uma playlist. '+oauth._api_error(response))
                        item_id=response.json().get('id')
                        if not item_id:raise ValueError('O YouTube não confirmou a inclusão na playlist. Retome para conferir o mesmo vídeo.')
                    applied[pid]=item_id;write_json(path/'youtube-upload.json',state)
        except httpx.HTTPError:raise ValueError('O vídeo já foi enviado. A conexão falhou ao atualizar as playlists; retome para conferir e continuar sem reenviar o vídeo.') from None
    state.update(status='enviado',message='Arquivo enviado ao YouTube e incluído nas playlists selecionadas.')
    write_json(path/'youtube-upload.json',state);set_status(path,'enviado_youtube',state['message'],1)
    return oauth.upload_status(path)
