"""Small silent recipe demonstrations, using the same native stage as exports."""
import threading
import sqlite3
import time
from PIL import Image

from .core import ROOT,Scene,Settings,digest
from .shotcraft import BY_ID,VERSION,selected_recipe,FAMILY_BY_RECIPE

LOCK=threading.Lock()
POSTERS=ROOT/'overview/assets/shotcraft-posters'


def _video_waiting():
    """Gallery requests must not starve a render waiting for the same lease."""
    database=ROOT/'.private/queue.sqlite3'
    if not database.is_file():return False
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=2) as db:
        return db.execute("SELECT 1 FROM jobs WHERE status='fila' OR (status='agendado' AND scheduled<=?) LIMIT 1",(time.time(),)).fetchone() is not None


def poster(recipe,style='editorial',vertical=False,finish='vidro_avancado'):
    if recipe not in BY_ID:raise FileNotFoundError('Receita não encontrada')
    Settings(shotcraft_estilo=style,shotcraft_acabamento=finish)
    target=POSTERS/finish/style/(recipe+('-vertical' if vertical else '-horizontal')+'.png')
    if not target.is_file():raise FileNotFoundError('Exemplo ainda não preparado')
    return target


def example(settings):
    recipe=selected_recipe({},settings)
    if recipe=='comparacao_revelada':
        text='Compare um computador de mesa com um notebook. Cada equipamento tem características próprias.'
        labels=[('Computador','computador'),('Notebook','computador')];composition='comparacao'
    elif recipe=='linha_tempo':
        text='Primeiro surge uma pergunta, depois vem a observação. Por fim, construímos uma explicação.'
        labels=[('Pergunta','mensagem'),('Observação','pensador'),('Explicação','livro')];composition='linha_do_tempo'
    elif recipe in ('rede_conexoes','mapa_mental','cascata_diagrama'):
        text='Um computador e um celular trocam dados por uma rede digital. A conexão permite compartilhar informações.'
        labels=[('Computador','computador'),('Rede digital','mensagem'),('Celular','celular')];composition='rede'
    elif recipe in ('lista_progressiva','conectores_etapas'):
        text='Primeiro, observe uma flor e formule uma pergunta. Depois, registre a observação com um lápis.'
        labels=[('Flor','folha'),('Pergunta','mensagem'),('Lápis','documento')];composition='processo'
    else:
        text='Computadores, castelos e o cérebro representam assuntos diferentes. Cada explicação pede uma imagem relacionada ao que é narrado.'
        labels=[('Computador','computador'),('Castelo','documento'),('Cérebro','cerebro')];composition='conceito'
    from .speech import phrases
    units=phrases(text)
    scene=Scene(titulo='Uma ideia ganha movimento',narracao_ptbr=text,texto_na_tela=[p[0] for p in labels]).model_dump()
    board={'momentos':[{'frase':i,'titulo':('Uma ideia ganha movimento' if i==0 else 'Clareza para cada descoberta'),
        'composicao':composition,'elementos':[{'rotulo':label,'icone':icon} for label,icon in labels],
        'receita':recipe,'linguagem':FAMILY_BY_RECIPE[recipe],
        'foco':0,'motivo':'Demonstração local da receita escolhida.'} for i in range(len(units))]}
    return scene,board


def prepare(recipe,style='editorial',energy='equilibrada',vertical=False,model='auto',finish='vidro_avancado'):
    if recipe not in BY_ID:raise FileNotFoundError('Receita não encontrada')
    settings=Settings(animacao='shotcraft',shotcraft_receita=recipe,shotcraft_estilo=style,shotcraft_intensidade=energy,shotcraft_modelo=model,shotcraft_acabamento=finish)
    from .shotcraft_remotion import fingerprint
    key=digest(VERSION,fingerprint(),recipe,style,energy,vertical,model,finish,'recipe-preview-v3');target=ROOT/'output/shotcraft-previews'/(key+'.webp')
    with LOCK:
        if target.exists():return target
        if _video_waiting():raise ValueError('Há um vídeo na fila. O exemplo de composição continua disponível; a demonstração animada pode ser carregada depois.')
        from .core import ProcessingLock
        lease=ProcessingLock(ROOT/'.private/processing.lock')
        if not lease.acquire():raise ValueError('Há um processamento em andamento. Aguarde para gerar uma demonstração nova; prévias já prontas continuam disponíveis.')
        from .motion import Animator
        animator=None
        try:
            scene,board=example(settings);beat={**board['momentos'][0],'inicio':0,'fim':4}
            size=(360,640) if vertical else (640,360)
            animator=Animator(scene,settings,0,1,[beat],ROOT/'output/shotcraft-previews',[],canvas_size=size,mobile=vertical)
            frames=[animator.frame(i/10) for i in range(40)]
            target.parent.mkdir(parents=True,exist_ok=True)
            partial=target.with_suffix('.partial');frames[0].save(partial,format='WEBP',save_all=True,append_images=frames[1:],
                duration=100,loop=0,quality=78,method=3)
            partial.replace(target)
        finally:
            if animator:animator.close()
            lease.release()
    return target
