"""Local voice catalog, model provenance and reproducible Piper downloads."""
from __future__ import annotations
from typing import Literal, Annotated
from pydantic import StringConstraints
from .narration_styles import MOTIVATIONAL_STYLES,tone_guide

VoiceId=Literal['pf_dora','pm_alex','pm_santa','piper_cadu','piper_faber','piper_jeff',
                'ms_antonio','ms_francisca','ms_thalita','ms_brian','ms_andrew','ms_emma'] | Annotated[str, StringConstraints(pattern=r'^clone_[0-9a-f]{12}$')]
Delivery = Literal['natural','documental','reflexiva','envolvente','suspense','terror','misterio','motivacional',
    'motivacional_intenso','motivacional_suave','motivacional_acolhedor','motivacional_epico',
    'motivacional_determinado','motivacional_reflexivo']
VOICES=[
    {'id':'pf_dora','nome':'Dora','motor':'Kokoro','descricao':'Feminina · experimente em explicações e histórias'},
    {'id':'pm_alex','nome':'Alex','motor':'Kokoro','descricao':'Masculina · experimente em explicações diretas'},
    {'id':'pm_santa','nome':'Santa','motor':'Kokoro','descricao':'Masculina · experimente em narração reflexiva'},
    {'id':'piper_cadu','nome':'Cadu','motor':'Piper','descricao':'Masculina brasileira · compare em aulas e documentários'},
    {'id':'piper_faber','nome':'Faber','motor':'Piper','descricao':'Masculina brasileira · compare em histórias e reflexão'},
    {'id':'piper_jeff','nome':'Jeff','motor':'Piper','descricao':'Masculina brasileira · compare em apresentações e conceitos'},
]
PIPER_HASHES={
    'cadu':'765f0809a6ea9035d4a6d0d008dbf8876e68b2dd32029312672fa8f405bdb535',
    'faber':'858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7',
    'jeff':'3a6f4c46355813c2b7bbc4d16b6d13d60ed72074b952a393baace82a7d0c94b5',
}
DELIVERIES={
    'natural':{'nome':'Natural','velocidade':1.,'pausa':.16,'pitch':1.},
    'documental':{'nome':'Documental · firme e pausada','velocidade':.95,'pausa':.24,'pitch':.97},
    'reflexiva':{'nome':'Reflexiva · calma e contemplativa','velocidade':.9,'pausa':.32,'pitch':1.},
    'envolvente':{'nome':'Envolvente · ritmo mais vivo','velocidade':1.04,'pausa':.18,'pitch':1.015},
    'suspense':{'nome':'Suspense · tensão contida','velocidade':.98,'pausa':.18,'pitch':.99,
                'descricao':'Ritmo atento e tensão discreta, sem alongar palavras. A interpretação depende do motor de voz.'},
    'terror':{'nome':'Terror · sombrio e firme','velocidade':.97,'pausa':.20,'pitch':.98,
              'descricao':'Leitura sóbria e levemente mais grave nas vozes prontas. Sem efeitos ou gritos; vozes clonadas mantêm o timbre salvo.'},
    'misterio':{'nome':'Mistério · curioso e investigativo','velocidade':.99,'pausa':.18,'pitch':1.,
                'descricao':'Cadência investigativa, com perguntas claras e sem pausas longas. A interpretação depende do motor de voz.'},
    **{key:{k:v for k,v in style.items() if k in ('nome','velocidade','pausa','pitch','descricao')}
       for key,style in MOTIVATIONAL_STYLES.items()},
}

SAMPLE_TEXTS = {
    'suspense':'A porta estava fechada por dentro. Mesmo assim, alguém deixou uma carta sobre a mesa. Quem poderia ter entrado naquela noite?',
    'terror':'A casa parecia vazia. Então, no andar de cima, ouvimos passos. Paramos para escutar. Os passos também pararam.',
    'misterio':'Um detalhe não combina com os outros. A fotografia mostra uma janela aberta, mas ninguém se lembra dela. Vamos examinar as pistas.',
    'motivacional':'Você não precisa resolver tudo hoje. Escolha um passo possível e comece por ele. Reconheça o caminho que já percorreu. Pequenos avanços também fazem diferença.',
}
for _delivery in MOTIVATIONAL_STYLES:
    SAMPLE_TEXTS.setdefault(_delivery,SAMPLE_TEXTS['motivacional'])


def delivery_guide(settings):
    direction = {
        'suspense':'tensão contida: apresente pistas numa sequência clara e mantenha a curiosidade, sem antecipar a conclusão',
        'terror':'atmosfera sombria e sóbria: descreva com precisão e firmeza, sem gritos, exageros ou sensacionalismo',
        'misterio':'curiosidade investigativa: conecte as pistas e diferencie o que é conhecido das hipóteses',
        'motivacional':'presença acolhedora e confiança: use palavras concretas, incentive passos possíveis, sem promessas milagrosas, culpa ou frases de efeito vazias',
    }.get(settings.estilo_locucao)
    if settings.estilo_locucao in MOTIVATIONAL_STYLES:
        direction=MOTIVATIONAL_STYLES[settings.estilo_locucao]['interpretacao']
    if not direction:return tone_guide(settings)
    return tone_guide(settings)+('\nDIREÇÃO DA NARRAÇÃO: '+direction+'. Preserve o plano, a clareza e os fatos das fontes. '
            'Não invente acontecimentos para criar clima. Use português brasileiro falado, períodos conectados e pontuação natural. '
            'Evite reticências, frases fragmentadas e palavras esticadas. Não escreva rubricas, SSML ou instruções de atuação no texto falado.\n')


def model_path(voice):
    from .core import MODELS
    if voice not in {v['id'] for v in VOICES if v['motor']=='Piper'}:raise ValueError('Voz Piper inválida')
    return MODELS/'piper'/f'pt_BR-{voice.removeprefix("piper_")}-medium.onnx'


def catalog():
    from .core import MODELS
    from .cloned_voices import catalog as cloned_catalog
    from .microsoft_speech import catalog as microsoft_catalog
    return [{**v,'instalada':model_path(v['id']).is_file() if v['motor']=='Piper' else (MODELS/'kokoro/kokoro-v1.0.onnx').is_file()} for v in VOICES] + microsoft_catalog() + cloned_catalog()


def download_piper(callback=print):
    import hashlib,os,httpx
    from .core import MODELS,write_json
    folder=MODELS/'piper';folder.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name,expected in PIPER_HASHES.items():
        base=f'https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/{name}/medium/'
        filename=f'pt_BR-{name}-medium.onnx';target=folder/filename
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            callback('Baixando voz '+name+' (~63 MB)')
            temp=target.with_suffix('.partial')
            with httpx.stream('GET',base+filename,follow_redirects=True,timeout=120) as response:
                response.raise_for_status()
                with open(temp,'wb') as out:
                    for chunk in response.iter_bytes():out.write(chunk)
            if hashlib.sha256(temp.read_bytes()).hexdigest()!=expected:
                temp.unlink();raise RuntimeError('Checksum inválido da voz '+name)
            os.replace(temp,target)
        for suffix in (filename+'.json','MODEL_CARD'):
            dest=folder/(suffix if suffix!='MODEL_CARD' else name+'-MODEL_CARD.md')
            if not dest.exists():
                response=httpx.get(base+suffix,follow_redirects=True,timeout=60);response.raise_for_status()
                dest.write_bytes(response.content)
        hashes[name]=expected
    write_json(folder/'sha256.json',hashes)

