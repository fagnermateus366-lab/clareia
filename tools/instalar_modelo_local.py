"""Install an explicitly chosen model in Clareia's own Ollama storage."""
from pathlib import Path
import argparse,json,shutil,sys,time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
import httpx,psutil
from overview.core import JobLock,MODEL,MODELS,OLLAMA_URL,write_json
from overview.llm import ensure_ollama


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',choices=['gemma4:12b','qwen2.5:1.5b','qwen2.5:3b'])
    model=parser.parse_args().model
    folder=ROOT/'output'/('local-model-install-'+str(time.time_ns()));folder.mkdir()
    report={'model':model,'ok':False,'default':MODEL}
    try:
        with JobLock(folder):
            health=httpx.get('http://127.0.0.1:7860/api/health',timeout=10).json()
            if health.get('ocupado'):raise RuntimeError('Há processamento ativo. Aguarde a conclusão.')
            ensure_ollama()
            port=int(OLLAMA_URL.rsplit(':',1)[1])
            owners={c.pid for c in psutil.net_connections(kind='tcp') if c.status=='LISTEN' and c.laddr.port==port}
            assert len(owners)==1,'Porta Ollama inesperada'
            process=psutil.Process(owners.pop())
            assert Path(process.environ().get('OLLAMA_MODELS','')).resolve()==(MODELS/'ollama').resolve(),'Ollama não pertence a este aplicativo'
            before=httpx.get(OLLAMA_URL+'/api/tags',timeout=10).json()['models']
            version=httpx.get(OLLAMA_URL+'/api/version',timeout=10).json()
            report.update(version=version,models_before=before,disk_free_before=shutil.disk_usage(ROOT).free)
            write_json(folder/'report.json',report)
            last_print=0;last_status=None;success=False
            with httpx.stream('POST',OLLAMA_URL+'/api/pull',json={'model':model,'stream':True},
                              timeout=httpx.Timeout(180,connect=30)) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:continue
                    event=json.loads(line)
                    if event.get('error'):raise RuntimeError(event['error'])
                    status=event.get('status','');now=time.monotonic()
                    if status!=last_status or now-last_print>=15:
                        progress={'status':status}
                        if event.get('total'):
                            progress['percent']=round(event.get('completed',0)*100/event['total'],1)
                        print(json.dumps(progress,ensure_ascii=False),flush=True)
                        write_json(folder/'progress.json',event)
                        last_status=status;last_print=now
                    if status=='success':success=True
            if not success:raise RuntimeError('Download interrompido antes da confirmação de instalação.')
            after=httpx.get(OLLAMA_URL+'/api/tags',timeout=10).json()['models']
            by_name={m['name']:m for m in after}
            assert model in by_name,'Modelo ausente após o download'
            assert all(by_name[m['name']]['digest']==m['digest'] for m in before),'Um modelo anterior foi alterado'
            assert MODEL=='qwen3:14b'
            info=httpx.post(OLLAMA_URL+'/api/show',json={'model':model},timeout=30)
            info.raise_for_status();write_json(folder/'model-info.json',info.json())
            report.update(ok=True,models_after=after,previous_digests_preserved=True,
                          disk_free_after=shutil.disk_usage(ROOT).free)
    except Exception as exc:
        report['error']=str(exc);raise
    finally:
        write_json(folder/'report.json',report)
        print('Relatório: '+str(folder/'report.json'),flush=True)


if __name__=='__main__':main()
