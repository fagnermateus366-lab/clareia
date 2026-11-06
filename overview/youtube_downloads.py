"""Single bounded subprocess for explicit public-media imports."""
import shutil
import subprocess
import sys
import threading
import time
import uuid

from .core import ROOT,CREATE_FLAGS,read_json,write_json
from .youtube_music import token,alive,kill_tree


class DownloadJobs:
    def __init__(self,storage,module):
        self.storage=storage;self.module=module;self.lock=threading.RLock()

    def path(self,key):return self.storage()/'jobs'/(token(key,32)+'.json')

    def update(self,key,**fields):
        data=read_json(self.path(key),{})
        write_json(self.path(key),data|fields|{'atualizado':time.time()})

    def public(self,data):
        return {k:v for k,v in data.items() if k in ('id','estado','mensagem','progresso','video','clipe','qualidade','criado','atualizado','baixados_bytes','total_bytes')}

    def active(self):
        with self.lock:
            for path in (self.storage()/'jobs').glob('*.json'):
                data=read_json(path,{})
                if data.get('estado') not in ('aguardando','baixando','convertendo'):continue
                if alive(data) or time.time()-data.get('atualizado',0)<5:return self.public(data)
                self.update(data['id'],estado='erro',mensagem='A importação anterior foi interrompida. Você pode tentar novamente.')
        return None

    def get(self,key):
        self.active();data=read_json(self.path(key))
        if not data:raise FileNotFoundError('Importação não encontrada.')
        return self.public(data)

    def cancel(self,key):
        data=self.get(key)
        if data['estado'] in ('aguardando','baixando','convertendo'):self.path(key).with_suffix('.cancel').touch()
        return data

    def start(self,video,quality):
        with self.lock:
            previous=self.active()
            if previous:
                if previous['video']['id']==video['id'] and previous['qualidade']==quality:return previous
                raise ValueError('Já há um clipe sendo importado. Aguarde ou cancele a importação atual.')
            key=uuid.uuid4().hex
            data={'id':key,'estado':'aguardando','mensagem':'Preparando a importação do clipe…','progresso':0,
                  'video':video,'qualidade':quality,'criado':time.time(),'atualizado':time.time()}
            write_json(self.path(key),data)
            threading.Thread(target=self.coordinate,args=(key,),daemon=True,name='clareia-clip-import').start()
            return self.public(data)

    def coordinate(self,key):
        proc=None
        try:
            proc=subprocess.Popen([sys.executable,'-m',self.module,'--worker',key],cwd=ROOT,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=CREATE_FLAGS)
            started=time.monotonic();cancel=self.path(key).with_suffix('.cancel')
            while proc.poll() is None:
                if cancel.exists() or time.monotonic()-started>300:
                    kill_tree(proc)
                    if read_json(self.path(key),{}).get('estado')!='concluido':
                        self.update(key,estado='cancelado' if cancel.exists() else 'erro',mensagem='Importação cancelada.' if cancel.exists() else 'A importação demorou demais. Tente um clipe mais curto.')
                    return
                time.sleep(.2)
            if read_json(self.path(key),{}).get('estado') in ('aguardando','baixando','convertendo'):
                self.update(key,estado='erro',mensagem='Não foi possível concluir a importação do clipe.')
        except Exception:
            if proc and proc.poll() is None:kill_tree(proc)
            self.update(key,estado='erro',mensagem='Não foi possível iniciar a importação do clipe.')
        finally:
            path=self.storage()/'incoming'/key
            if path.resolve().parent==(self.storage()/'incoming').resolve():shutil.rmtree(path,ignore_errors=True)
