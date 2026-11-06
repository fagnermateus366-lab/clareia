"""Planos visuais locais, independentes da voz e ligados às frases originais."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal
import re

from .core import digest, read_json, write_json
from .speech import phrases

ICONS = ['computador', 'globo', 'documento', 'livro', 'pessoa', 'mensagem',
         'cerebro', 'engrenagem', 'escudo', 'relogio', 'folha', 'moeda', 'lampada','professor','pensador','leitor','celular']


class Element(BaseModel):
    rotulo: str = Field(min_length=1, max_length=42)
    icone: Literal['computador', 'globo', 'documento', 'livro', 'pessoa', 'mensagem',
                   'cerebro', 'engrenagem', 'escudo', 'relogio', 'folha', 'moeda', 'lampada','professor','pensador','leitor','celular']


class Actor(BaseModel):
    nome: str = Field(min_length=1,max_length=35)
    tipo: Literal['pessoa','idoso','menina','lobo','cientista','professor'] = 'pessoa'
    acao: Literal['andar','correr','gesticular','observar','conversar','pensar','apontar','ler'] = 'gesticular'
    expressao: Literal['auto','serena','reflexiva','surpresa'] = 'auto'


class Beat(BaseModel):
    frase: int = Field(ge=0)
    titulo: str = Field(min_length=1, max_length=65)
    composicao: Literal['rede', 'processo', 'comparacao', 'linha_do_tempo', 'ciclo', 'conceito']
    elementos: list[Element] = Field(min_length=2, max_length=4)
    ambiente: Literal['rua','floresta','sala','escola','laboratorio','campo'] | None = None
    elenco: list[Actor] = Field(default_factory=list,max_length=3)


class Board(BaseModel):
    momentos: list[Beat] = Field(min_length=1)


class CollageElement(Element):
    recorte: str = Field(max_length=120)


class CollageBeat(Beat):
    elementos: list[CollageElement] = Field(min_length=2,max_length=4)


class CollageBoard(Board):
    momentos: list[CollageBeat] = Field(min_length=1)


def grounded(board, units):
    """Conservative relations: never turn an ordinary statement into a cycle/comparison."""
    identities={}
    for beat in board.momentos:
        phrase=units[beat.frase].lower()
        # The local model sometimes defaults every action to a gesture. Explicit
        # narration verbs take precedence, and walking needs lexical support.
        action=next((value for pattern,value in [
            (r'convers|dialog','conversar'),(r'acena|acenou','gesticular'),
            (r'corre\b|corrend|correu','correr'),(r'\bcaminh(?:a|am|ando|ava|avam|aram|ou|ar)\b|passeia|atravess|andando|\banda\b','andar'),
            (r'observ|\bolha\b|olhando','observar'),(r'\bpensa|reflet','pensar'),
            (r'\blê\b|\bleu\b|\bler\b|lendo','ler'),(r'aponta|apontou','apontar')]
            if re.search(pattern,phrase)),None)
        named=[a for a in beat.elenco if a.nome.casefold() in phrase or a.nome.casefold().split()[0] in phrase]
        if beat.elenco and re.match(r'(?:ele|ela)\b',phrase) and beat.elenco[0] not in named:named.append(beat.elenco[0])
        for actor in beat.elenco:
            identity=actor.nome.casefold();actor.tipo=identities.setdefault(identity,actor.tipo)
            if action and (actor in named or not named):actor.acao=action
            elif actor.acao in ('andar','correr') and not action:actor.acao='gesticular'
            if actor.acao=='pensar':actor.expressao='reflexiva'
        if beat.composicao=='ciclo' and not re.search(r'cicl|repet|novamente|retorn|volta|recorr',phrase):
            beat.composicao='conceito'
        if beat.composicao=='comparacao' and (len(beat.elementos)!=2 or not re.search(
                r'compar|enquanto|difer|maior|menor|mais .+ que|menos .+ que|versus| ao contrário',phrase)):
            beat.composicao='conceito'
    result=board.model_dump()
    # Empty new fields must not invalidate any existing style's visual cache.
    for beat in result['momentos']:
        for element in beat['elementos']:
            if not element.get('recorte'):element.pop('recorte',None)
    return result


def board_key(scene, story=False, collage=False, settings=None):
    from .runtime import current_settings
    cfg=settings or current_settings()
    if cfg:
        from .shotcraft import enabled,key_for
        if enabled(scene,cfg):return key_for(scene,cfg)
    base = digest('storyboard-colagem-v2' if collage else 'storyboard-historia-v1' if story else 'storyboard-v1', scene['narracao_ptbr'], scene['titulo'], scene['texto_na_tela'])
    from .runtime import gemini_only,current_settings,local_model
    from .core import MODEL
    cfg=settings or current_settings()
    if cfg and cfg.tipo_roteiro=='motivacional':base=digest(base,'motivational-visuals-v1')
    if gemini_only(settings):base=digest(base,'gemini-project-v1',(settings or current_settings()).roteiro_modelo)
    elif local_model(settings)!=MODEL:base=digest(base,'ollama-model-v1',local_model(settings))
    return digest(base, scene.get('figuras_colagem','')) if collage else base


def plan(scene, path, story=False, collage=False):
    """One composition per spoken phrase; validate coverage, never execute model code."""
    from .runtime import current_settings
    cfg=current_settings()
    if cfg:
        from .shotcraft import enabled,plan as shot_plan
        if enabled(scene,cfg):return shot_plan(scene,path,cfg)
    units = phrases(scene['narracao_ptbr'])
    schema=CollageBoard if collage else Board
    key = board_key(scene,story,collage)
    target = path / 'cache/storyboard' / (key + '.json')
    saved = read_json(target)
    if saved:
        board = schema.model_validate(saved)
        if [b.frase for b in board.momentos] == list(range(len(units))):
            return grounded(board,units), key
    from .llm import ask
    prompt = (
        'Planeje ilustrações didáticas animadas para uma narração JÁ APROVADA. Não reescreva a fala. '
        'Crie exatamente um momento para CADA frase numerada a partir de zero, em ordem. '
        'Cada momento deve ilustrar especificamente aquela frase e acrescentar uma imagem explicativa, '
        'em vez de repetir os mesmos tópicos. titulo curto, 2 a 4 elementos com rótulos concisos. '
        'Use somente fatos e relações explícitos no roteiro. Não invente estatísticas, causas, locais ou datas. '
        'rede: entidades que se conectam/trocam mensagens; processo: sequência explícita; '
        'comparacao: dois lados explicitamente comparados; linha_do_tempo: datas ou evolução temporal; '
        'ciclo: repetição explícita; conceito: conceito central e seus aspectos, sem seta causal. '
        'Varie as composições quando o assunto mudar. Use ícones semânticos escolhidos da lista do schema. '
        'Rótulos com nomes próprios e datas podem manter algarismos. Não inclua instruções de desenho ou código. '
        f'\nTEMA: {scene["titulo"]}\nROTEIRO COMPLETO: {scene["narracao_ptbr"]}\nFRASES:\n' +
        '\n'.join(f'{i}: {unit}' for i, unit in enumerate(units)) +
        '\nPONTOS DE DESTAQUE NA TELA (somente quando sustentados pela fala): '+
        ' / '.join(scene['texto_na_tela']))
    from .runtime import current_settings
    cfg=current_settings()
    if cfg and cfg.tipo_roteiro=='motivacional':
        prompt=prompt.replace('Planeje ilustrações didáticas animadas','Planeje imagens e animações de uma mensagem motivacional')
        prompt+='\nPriorize uma situação humana e visual simples por momento, coerente com a mensagem. Não transforme a narração em aula, prova, estatística ou diagrama causal ausente. As imagens devem apoiar o sentimento e o passo concreto sem competir com as legendas.'
    correction = ''
    if collage:
        prompt += ('\nMODO COLAGEM DOCUMENTAL: cada elemento tem recorte, uma consulta livre e específica de objeto visual '
                   'em português (por exemplo: avião comercial, antena parabólica, microscópio, pulmões, urna eleitoral). '
                   'Não existe lista fechada de figuras: escolha objetos fiéis àquela frase. Varie as figuras ao mudar a ideia; '
                   'não recicle pessoa/globo/lâmpada para todos os conceitos. Use 2 a 3 recortes distintos por frase quando '
                   'houver objetos relevantes. Para ideia abstrata sem objeto honesto, use recorte vazio e deixe a tipografia '
                   'explicar. Nunca use uma pessoa genérica como retrato de uma pessoa real. Não acrescente números ou fatos. '
                   'Os ícones do schema são apenas fallback; a consulta recorte é o principal no novo estilo. '
                   '\nFIGURAS SUGERIDAS PELO USUÁRIO (somente se pertinentes): '+scene.get('figuras_colagem',''))
        if scene.get('imagem') and scene.get('usar_imagem',True):
            prompt+='\nHá uma imagem principal escolhida para esta cena. Use somente 2 elementos de apoio, distintos e pertinentes à fala.'
    if story:
        prompt+='\nMODO HISTÓRIA ANIMADA: em cada momento escolha ambiente e elenco (1 a 3 personagens articulados). Mantenha exatamente nome e tipo da mesma pessoa entre frases. Escolha ações que ilustrem a frase: andar/correr só se há deslocamento narrado; observar, pensar, ler, apontar ou gesticular conforme a ação descrita. Use expressao reflexiva para reflexão/pensamento, surpresa quando houver espanto explícito e serena nos demais casos. Chapeuzinho usa tipo menina; lobo usa lobo; idosos usam idoso. Sem local explícito, use sala como cenário didático neutro. Não invente pessoas históricas, fatos ou ações materiais ausentes. Um personagem genérico pode representar o aprendiz em assunto abstrato. Não há sincronização labial.'
    for _ in range(3):
        board = schema.model_validate(ask(prompt + correction, schema.model_json_schema(), path))
        if [b.frase for b in board.momentos] == list(range(len(units))):
            result=grounded(board,units)
            write_json(target, result)
            return result, key
        correction = f'\nCORRIJA: índices frase devem ser exatamente {list(range(len(units)))}. Nenhuma omissão ou repetição.'
    raise RuntimeError('O planejamento visual não cobriu todas as frases. Tente retomar; o roteiro foi preservado.')


def timed(board, cues, duration):
    if len(board['momentos']) != len(cues):
        raise ValueError('Storyboard e áudio têm números diferentes de frases; refaça o planejamento.')
    return [{**b, 'inicio': c['inicio'],
             'fim': cues[i+1]['inicio'] if i+1 < len(cues) else duration}
            for i, (b, c) in enumerate(zip(board['momentos'], cues))]
