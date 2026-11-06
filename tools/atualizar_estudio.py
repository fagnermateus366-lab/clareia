"""Load saved studio changes without interrupting an active render or losing keys."""
from pathlib import Path
import os
import subprocess
import sys
import time
import webbrowser

import httpx
import psutil

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:7860'


def credential_context():
    # Refuse to replace a healthy user process with a restricted process that
    # cannot open the existing DPAPI vault. Never migrate keys to plaintext.
    sys.path.insert(0,str(ROOT))
    from overview.providers import key_status
    if any(s.get('erro') for s in key_status().values()):
        raise RuntimeError('Esta execução não tem acesso à chave protegida pelo Windows. Abra atualizar-estudio.bat diretamente na sua sessão do Windows. O estúdio atual e a chave foram preservados.')
    from overview.youtube_upload import validate_vault
    validate_vault()


def _restart(open_browser=True):
    listeners={c.pid for c in psutil.net_connections(kind='tcp') if c.status=='LISTEN' and c.laddr.port==7860}
    if listeners:
        if len(listeners)!=1:raise RuntimeError('A porta do estúdio está ocupada por processos inesperados.')
        state=httpx.get(URL+'/api/health',timeout=5);state.raise_for_status();state=state.json()
        if not state.get('ok') or not state.get('local'):raise RuntimeError('O serviço nesta porta não é o estúdio local.')
        if state.get('ocupado'):
            print('Há uma tarefa em andamento. Aguarde terminar e execute Atualizar estúdio novamente. Nenhum processo foi interrompido.')
            return 2
        keys=httpx.get(URL+'/api/roteiro/credenciais',timeout=5);keys.raise_for_status()
        if any(v.get('configurada') and not v.get('persistida') for v in keys.json().values()):
            raise RuntimeError('Existe uma chave guardada somente na sessão. Salve-a no estúdio antes de reiniciar.')
        process=psutil.Process(listeners.pop())
        if process.cmdline()[1:]!=['-m','overview','serve','--port','7860'] or Path(process.cwd()).resolve()!=ROOT:
            raise RuntimeError('O processo da porta 7860 não pertence a esta instalação. Nenhum processo foi interrompido.')
        if httpx.get(URL+'/api/health',timeout=5).json().get('ocupado'):
            print('Uma tarefa começou no estúdio. Aguarde terminar antes de atualizar.');return 2
        credential_context()
        process.terminate();process.wait(15)
    else:credential_context()
    (ROOT/'logs').mkdir(exist_ok=True)
    with open(ROOT/'logs/server-atualizado.log','a',encoding='utf-8') as log:
        subprocess.Popen([str(ROOT/'.venv/Scripts/python.exe'),'-m','overview','serve','--port','7860'],cwd=ROOT,
                         stdin=subprocess.DEVNULL,stdout=log,stderr=log,
                         creationflags=(subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP) if os.name=='nt' else 0)
    for _ in range(50):
        try:
            response=httpx.get(URL+'/api/health',timeout=1)
            if response.is_success and response.json().get('ok'):
                print('Estúdio atualizado. Atualize a página para carregar as novas opções.')
                if open_browser:webbrowser.open(URL)
                return 0
        except httpx.HTTPError:pass
        time.sleep(.2)
    raise RuntimeError('O estúdio não respondeu. Consulte logs/server-atualizado.log.')


def main(open_browser=True):
    sys.path.insert(0,str(ROOT))
    from overview.core import ProcessingLock
    lease=ProcessingLock(ROOT/'.private/processing.lock')
    if not lease.acquire():
        print('Há um processamento ativo. A atualização aguarda a liberação do estúdio.',flush=True)
        return 2
    try:return _restart(open_browser)
    finally:lease.release()


def when_idle(open_browser=False):
    """One installation helper; leave a live render untouched until its lease ends."""
    sys.path.insert(0,str(ROOT))
    from overview.core import ProcessingLock,write_json
    helper=ProcessingLock(ROOT/'.private/update-wait.lock')
    if not helper.acquire():return 0
    marker=ROOT/'.private/pending-update.json'
    try:
        credential_context()
        write_json(marker,{'status':'aguardando','pid':os.getpid(),'solicitada_em':time.time()})
        print('Atualização preparada. Aguardando o processamento terminar.',flush=True)
        while True:
            try:
                response=httpx.get(URL+'/api/health',timeout=5);response.raise_for_status();state=response.json()
                if not state.get('ok') or not state.get('local'):raise RuntimeError('O serviço nesta porta não é o estúdio local.')
                busy=state.get('ocupado',True)
            except httpx.ConnectError:busy=False
            if not busy and main(open_browser)==0:
                write_json(marker,{'status':'concluida','pid':os.getpid(),'concluida_em':time.time()})
                return 0
            time.sleep(1)
    except Exception as exc:
        write_json(marker,{'status':'erro','mensagem':str(exc),'pid':os.getpid()})
        raise
    finally:helper.release()


if __name__=='__main__':
    try:sys.exit(when_idle(open_browser='--no-browser' not in sys.argv) if '--when-idle' in sys.argv else main(open_browser='--no-browser' not in sys.argv))
    except Exception as exc:print(str(exc));sys.exit(1)
