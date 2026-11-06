import argparse
import json
from pathlib import Path
import sys

from .core import ROOT, Settings, JobLock, project_dir, read_json


def main():
    parser=argparse.ArgumentParser(description="Clareia · vídeos locais em português")
    sub=parser.add_subparsers(dest="command",required=True)
    serve=sub.add_parser("serve",help="Abre a interface local")
    serve.add_argument("--port",type=int,default=7860)
    sub.add_parser("doctor",help="Verifica os componentes instalados")
    sub.add_parser("samples",help="Gera amostras das vozes locais instaladas")
    create=sub.add_parser("create",help="Importa fontes e gera o roteiro; --render faz o fluxo completo")
    create.add_argument("files",nargs="*")
    create.add_argument("--text-file")
    create.add_argument("--url",action="append",default=[])
    create.add_argument("--title",default="Meu vídeo explicativo")
    create.add_argument("--minutes",type=float,default=3)
    create.add_argument("--format",choices=["16:9","9:16"],default="16:9")
    from .voices import catalog, DELIVERIES
    create.add_argument("--voice",default="pf_dora",choices=[v['id'] for v in catalog()])
    create.add_argument('--animation',choices=['ilustracoes','quadro','mao','recortes','tipografia','infografico','colagem_documental','shotcraft'],default='ilustracoes')
    create.add_argument('--delivery',choices=list(DELIVERIES),default='natural')
    create.add_argument('--hand-speed',type=float,choices=[.5,.75,1,1.25],default=.75)
    create.add_argument("--hosts",type=int,choices=[1,2],default=1)
    create.add_argument("--render",action="store_true")
    create.add_argument("--visual",choices=["auto","slide","diagrama","imagem_do_usuario"],default="auto")
    render=sub.add_parser("render",help="Renderiza ou retoma um projeto")
    render.add_argument("id")
    render.add_argument("--pause-after",type=int,help="Pausa de diagnóstico após N cenas")
    script=sub.add_parser("script",help="Gera novamente o roteiro de um projeto, aproveitando as leituras em cache")
    script.add_argument("id")
    args=parser.parse_args()
    if args.command=="serve":
        import uvicorn
        uvicorn.run("overview.server:app",host="127.0.0.1",port=args.port)
    elif args.command=="doctor":
        from .doctor import diagnose
        print(json.dumps(diagnose(),ensure_ascii=False,indent=2))
    elif args.command=="samples":
        from .speech import synthesize,TTS_LOCK,release
        import shutil
        out=ROOT/"output/amostras"
        out.mkdir(parents=True,exist_ok=True)
        with TTS_LOCK:
            from .voices import catalog
            for voice in [v['id'] for v in catalog() if v['instalada'] and not v.get('online')]:
                wav,_=synthesize("Olá! Eu sou uma das vozes do Clareia. Vamos transformar suas fontes em uma explicação clara, com imagens e legendas em português do Brasil.",voice,1,out/"cache")
                shutil.copyfile(wav,out/(voice+".wav"))
                print(voice,flush=True)
        release()
    elif args.command=="create":
        from . import projects
        from .metrics import Metrics
        from .render import render_project
        config=Settings(minutos=args.minutes,formato=args.format,voz=args.voice,apresentadores=args.hosts,modo_visual=args.visual,animacao=args.animation,estilo_locucao=args.delivery,velocidade_mao=args.hand_speed)
        text=Path(args.text_file).read_text(encoding="utf-8") if args.text_file else ""
        path=projects.create(args.title,config,[Path(f).resolve() for f in args.files],text,args.url)
        print("PROJETO="+path.name,flush=True)
        with JobLock(path), Metrics(path/"metrics-e2e.json"):
            projects.generate(path)
            print("ROTEIRO_PRONTO",flush=True)
            if args.render:
                print(json.dumps(render_project(path,config,lambda m,p:print(m,flush=True)),ensure_ascii=False),flush=True)
    elif args.command=="script":
        from .projects import generate
        from .metrics import Metrics
        path=project_dir(args.id)
        with JobLock(path),Metrics(path/"metrics-script.json"):
            generate(path)
        print("ROTEIRO_PRONTO",flush=True)
    elif args.command=="render":
        from .render import render_project
        from .metrics import Metrics
        path=project_dir(args.id)
        settings=Settings.model_validate(read_json(path/"project.json")["config"])
        with JobLock(path), Metrics(path/"metrics-render.json"):
            print(json.dumps(render_project(path,settings,lambda m,p:print(m,flush=True),args.pause_after),ensure_ascii=False),flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}",file=sys.stderr)
        raise
