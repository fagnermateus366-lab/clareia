"""Offline contextual illustrations for the new renderer, separate from Vox.

IDs are data, never URLs or programs. Only reviewed, locally vendored SVGs can
enter a render. Selection favors an explicit subject over a broad topic.
"""
from __future__ import annotations

import base64
from functools import lru_cache
import hashlib
import re
import unicodedata
from pathlib import Path

from .core import ROOT,digest,read_json

VERSION='shotcraft-art-direction-v3-selection-policy'
ASSETS=ROOT/'overview/assets/shotcraft-figures'
REVISION='b6b55fef1e8636b540a6d016a4729ca8cdf2e60b'
SOURCE='https://github.com/jdecked/twemoji'
GROUPS=[('tecnologia','Tecnologia e comunicação'),('ciencia','Ciência e pesquisa'),
 ('corpo','Corpo e saúde'),('religiao','Religiões e espiritualidade'),('historia','História e patrimônio'),
 ('terror','Terror e mistério'),('natureza','Natureza e ambiente'),('espaco','Espaço e clima'),
 ('sociedade','Sociedade e trabalho'),('cotidiano','Vida cotidiana'),('cultura','Cultura e educação'),
 ('conceitos','Ideias e motivação')]
GROUPS += [('psicologia','Psicologia e percepção'),('filosofia','Filosofia e significado'),
           ('relacoes','Relações e vínculos'),('desafios','Desafios e superação')]

# id | upstream SVG codepoint (or local drawing) | name | exact subject aliases
DATA={
'tecnologia':'''computador|1f5a5|Computador|computador;desktop;pc;informática
notebook|1f4bb|Notebook|notebook;laptop;computador portátil
celular|1f4f1|Celular|celular;smartphone;telefone móvel
robo|1f916|Robô|robô;robótica;automação;inteligência artificial
satelite|1f6f0|Satélite|satélite;satélites;gps
antena|1f4e1|Antena de comunicação|antena;antenas;transmissão;telecomunicação
controle|1f3ae|Controle de jogos|videogame;controle de jogo;jogos digitais
camera|1f4f7|Câmera fotográfica|câmera;fotografia;fotografar
microfone|1f399|Microfone|microfone;narração;podcast;voz;vozes
fone|1f3a7|Fones de ouvido|fone;fones;escutar;áudio
teclado|2328|Teclado|teclado;digitar;digitação
mouse|1f5b1|Mouse|mouse;cursor;clique
bateria|1f50b|Bateria|bateria;pilha;carga elétrica
tomada|1f50c|Plugue elétrico|tomada;plugue;energia elétrica
chip|custom|Processador|processador;cpu;microprocessador;chip
memoria_ram|custom|Memória RAM|memória ram;memória do computador;memória digital;ram
servidor|custom|Servidor|servidor de rede;servidores;data center;datacenter
rede_digital|custom|Rede digital|rede digital;rede de computadores;internet;conexão de rede''',
'ciencia':'''microscopio|1f52c|Microscópio|microscópio;microscopia;micróbio;microrganismo
telescopio|1f52d|Telescópio|telescópio;observatório;astronomia
tubo_ensaio|1f9ea|Tubo de ensaio|tubo de ensaio;experimento;química;reagente
placa_petri|1f9eb|Placa de cultura|placa de petri;cultura de bactéria;bactéria;bactérias
dna|1f9ec|DNA|dna;genética;gene;genes;hereditariedade
atomo|269b|Átomo|átomo;atômico;física quântica;partícula
ima|1f9f2|Ímã|ímã;magnetismo;campo magnético
balanca|2696|Balança|balança;equilíbrio;pesagem;justiça
regua|1f4cf|Régua|régua;medida;medição;comprimento
compasso|1f9ed|Bússola|bússola;orientação geográfica;campo terrestre
engrenagem|2699|Engrenagem|engrenagem;mecanismo;máquina;máquinas
ferramentas|1f6e0|Ferramentas|ferramentas;construção;consertar;engenharia''',
'corpo':'''cerebro|1f9e0|Cérebro|cérebro;memória humana;mente;lembrança;esquecimento;hipocampo;neurônio
coracao|1fac0|Coração anatômico|coração;circulação;cardíaco;batimento
pulmoes|1fac1|Pulmões|pulmão;pulmões;respiração;respirar
dente|1f9b7|Dente|dente;dentes;dentista;odontologia
osso|1f9b4|Osso|osso;ossos;esqueleto;fratura
olho|1f441|Olho|olho;olhos;visão;enxergar
ouvido|1f442|Ouvido|ouvido;orelha;audição;ouvir
mao|270b|Mão|mão;mãos;tato;gesto
estetoscopio|1fa7a|Estetoscópio|estetoscópio;exame médico;consulta médica
comprimido|1f48a|Comprimido|comprimido;medicamento;remédio
seringa|1f489|Seringa|seringa;vacina;vacinação
curativo|1fa79|Curativo|curativo;ferimento;cicatrização''',
'religiao':'''igreja|26ea|Igreja|igreja;cristianismo;capela;catedral
cruz|271d|Cruz cristã|cruz cristã;crucifixo;cristão;cristã;cristãos
mesquita|1f54c|Mesquita|mesquita;islã;islamismo;muçulmano
lua_islamica|262a|Lua e estrela|símbolo islâmico;lua crescente islâmica
caaba|1f54b|Caaba|caaba;kaaba;meca
sinagoga|1f54d|Sinagoga|sinagoga;judaísmo;judeu;tradição judaica
estrela_davi|2721|Estrela de Davi|estrela de davi;símbolo judaico
menora|1f54e|Menorá|menorá;menorah;hanucá
templo|1f6d5|Templo hindu|templo hindu;hinduísmo;hindu;mandir
roda_dharma|2638|Roda do Dharma|dharma;budismo;budista
yin_yang|262f|Yin e Yang|yin yang;taoísmo;taoísta
contas|1f4ff|Contas de oração|contas de oração;rosário;terço;japamala
oracao|1f64f|Oração|oração;orar;rezar;prece
vela|1f56f|Vela|vela;velas;vigília;luz de vela''',
'historia':'''pergaminho|1f4dc|Pergaminho|pergaminho;manuscrito;documento antigo;escritura antiga
castelo|1f3f0|Castelo|castelo;medieval;idade média;fortaleza
arquitetura_classica|1f3db|Arquitetura clássica|templo grego;colunas clássicas;grécia antiga;roma antiga;arquitetura clássica
anf ora|1f3fa|Ânfora|ânfora;cerâmica antiga;vaso antigo
coroa|1f451|Coroa|coroa;monarquia;realeza;rei;rainha
espadas|2694|Espadas cruzadas|espada;espadas;batalha;guerra antiga
escudo|1f6e1|Escudo|escudo;proteção;defesa
mapa|1f5fa|Mapa|mapa;mapas;cartografia;território
navio_vela|26f5|Barco à vela|barco à vela;veleiro;navegações;caravela
relogio_areia|231b|Ampulheta|ampulheta;passagem do tempo;tempo histórico
moai|1f5ff|Moai|moai;ilha de páscoa;rapa nui
piramide|custom|Pirâmide|pirâmide;pirâmides;egito antigo;faraó''',
'terror':'''fantasma|1f47b|Fantasma|fantasma;fantasmas;assombração;assombrado
cranio|1f480|Crânio|crânio;crânios;morte;mortalidade
caixao|26b0|Caixão|caixão;caixões;funeral
lapide|1faa6|Lápide|lápide;cemitério;túmulo;sepultura
morcego|1f987|Morcego|morcego;morcegos
aranha|1f577|Aranha|aranha;aranhas;aracnídeo
teia|1f578|Teia de aranha|teia;teia de aranha
abobora|1f383|Abóbora de Halloween|halloween;abóbora de halloween
vampiro|1f9db|Vampiro|vampiro;vampiros;drácula
zumbi|1f9df|Zumbi|zumbi;zumbis;morto vivo
porta|1f6aa|Porta|porta;portas;passagem;entrada
lanterna|1f526|Lanterna|lanterna;exploração no escuro;escuridão''',
'natureza':'''arvore|1f333|Árvore|árvore;árvores;floresta;bosque
conifera|1f332|Pinheiro|pinheiro;conífera;taiga
palmeira|1f334|Palmeira|palmeira;coqueiro;trópico
folha|1f343|Folha vegetal|folha vegetal;folha de árvore;folhagem
planta|1f331|Planta brotando|planta;broto;germinação;semente;crescimento vegetal
flor|1f33b|Girassol|girassol;flor;flores;fotossíntese
cacto|1f335|Cacto|cacto;caatinga;deserto
cogumelo|1f344|Cogumelo|cogumelo;fungo;fungos
montanha|26f0|Montanha|montanha;montanhas;relevo
onda_mar|1f30a|Onda do mar|onda do mar;oceano;mar;ondas do mar
agua|1f4a7|Gota de água|água;gota;hidratação;beber água
planeta|1f30e|Planeta Terra|planeta terra;globo terrestre;continente;planeta
leao|1f981|Leão|leão;leões;felino africano
borboleta|1f98b|Borboleta|borboleta;metamorfose;inseto
abelha|1f41d|Abelha|abelha;abelhas;polinização;mel
peixe|1f41f|Peixe|peixe;peixes;vida aquática''',
'espaco':'''foguete|1f680|Foguete|foguete;foguetes;lançamento espacial
lua|1f315|Lua|lua;lua cheia;lunar
sol|2600|Sol|sol;solar;estrela solar
estrela|2b50|Estrela|estrela;estrelas;constelação
cometa|2604|Cometa|cometa;cometas;meteoro
galaxia|1f30c|Via Láctea|galáxia;via láctea;cosmos;universo
nuvem|2601|Nuvem|nuvem;nuvens;nebulosidade
chuva|1f327|Chuva|chuva;chuvas;precipitação
raio|26a1|Raio|raio;relâmpago;descarga elétrica
vulcao|1f30b|Vulcão|vulcão;erupção;lava
neve|2744|Floco de neve|neve;gelo;congelamento
tornado|1f32a|Tornado|tornado;furacão;ciclone''',
'sociedade':'''banco_financeiro|1f3e6|Banco financeiro|banco financeiro;instituição financeira;crédito bancário
dinheiro|1f4b0|Dinheiro|dinheiro;riqueza;finanças;capital financeiro
moeda|1fa99|Moeda|moeda;moedas;dinheiro metálico
cartao_credito|1f4b3|Cartão de crédito|cartão de crédito;pagamento;compras
fabrica|1f3ed|Fábrica|fábrica;indústria;produção industrial
escritorio|1f3e2|Escritório|escritório;empresa;empresas
construcao|1f3d7|Construção|obra;construção civil;guindaste
urna|1f5f3|Urna de votação|urna;votação;eleição;voto
aperto_maos|1f91d|Aperto de mãos|acordo;aperto de mãos;parceria;cooperação
familia|1f46a|Família|família;familiares;parentes
megafone|1f4e3|Megafone|megafone;comunicado;anúncio;protesto
maleta|1f4bc|Maleta|maleta;profissão;trabalho;carreira''',
'cotidiano':'''casa|1f3e0|Casa|casa;casas;moradia;lar
cama|1f6cf|Cama|cama;dormir;sono;descanso
cadeira|1fa91|Cadeira|cadeira;assento;sentar
carro|1f697|Carro|carro;automóvel;dirigir
onibus|1f68c|Ônibus|ônibus;transporte público
bicicleta|1f6b2|Bicicleta|bicicleta;ciclismo;pedalar
aviao|2708|Avião|avião;aviões;voo;aviação
trem|1f686|Trem|trem;ferrovia;locomotiva
chave|1f511|Chave|chave;chaves;abrir fechadura
cadeado|1f512|Cadeado|cadeado;segurança;privacidade;senha
cafe|2615|Café|café;cafés;cafeína
pao|1f35e|Pão|pão;pães;padaria
queijo|1f9c0|Queijo|queijo;queijos
maca|1f34e|Maçã|maçã;fruta;alimentação''',
'cultura':'''livro|1f4d6|Livro aberto|livro aberto;livro;leitura;bíblia;alcorão;texto sagrado
livros|1f4da|Pilha de livros|livros;biblioteca;estudo;conhecimento
escola|1f3eb|Escola|escola;ensino;educação
formatura|1f393|Formatura|formatura;graduação;universidade;diploma
paleta|1f3a8|Paleta de pintura|pintura;arte;artes;paleta
mascaras|1f3ad|Máscaras de teatro|teatro;dramaturgia;máscaras teatrais
violao|1f3b8|Violão|violão;guitarra;instrumento de cordas
piano|1f3b9|Piano|piano;teclado musical
claquete|1f3ac|Claquete|cinema;filme;claquete;filmagem
jornal|1f4f0|Jornal|jornal;notícia;jornalismo
lupa|1f50e|Lupa|lupa;investigação;pesquisa;curiosidade
lapis|270f|Lápis|lápis;escrita;escrever;roteiro''',
'conceitos':'''lampada|1f4a1|Lâmpada|lâmpada;ideia;ideias;inspiração
pergunta|2753|Interrogação|pergunta;dúvida;questionamento
alvo|1f3af|Alvo|meta;objetivo;foco;alvo
trofeu|1f3c6|Troféu|troféu;vitória;conquista;sucesso
medalha|1f3c5|Medalha|medalha;premiação;esporte
quebra_cabeca|1f9e9|Quebra-cabeça|quebra cabeça;enigma;solução;peça
ponte|1f309|Ponte|ponte;travessia;superar obstáculo
escada|1fa9c|Escada|escada;degrau;progresso;avançar
ancora|2693|Âncora|âncora;estabilidade;ancorar
coracao_afeto|2764|Coração de afeto|amor;afeto;carinho;empatia
relogio|23f0|Despertador|relógio;horário;prazo;tempo
semaforo|1f6a6|Semáforo|semáforo;trânsito;sinalização''',
}
DATA['religiao']+='\novelha|1f411|Ovelha|ovelha;rebanho\npomba|1f54a|Pomba|pomba;pombas'
DATA['natureza']+='\ncamelo|1f42a|Camelo|camelo;camelos\nilha|1f3dd|Ilha|ilha;ilhas\nrosa|1f339|Rosa|rosa;rosas\nrosa_murcha|1f940|Flor murcha|flor murcha;rosa murcha\ntronco|1fab5|Tronco|tronco;madeira'
DATA['cotidiano']+='\npessoa|1f9cd|Pessoa em pé|pessoa em pé;uma pessoa\nespelho|1fa9e|Espelho|espelho;espelhos\njarra|1fad7|Líquido sendo servido|servir líquido;despejar líquido\nbarco|1f6f6|Canoa|canoa;barco a remo'
DATA['sociedade']+='\npessoas|1f465|Pessoas|pessoas;grupo de pessoas\ncorrente|1f517|Elos de corrente|elos;corrente metálica'
DATA['conceitos']+='\npegadas|1f463|Pegadas|pegadas;passos\nmeditacao|1f9d8|Meditação|meditação;meditar'
DATA['cultura']+='\nmoldura|1f5bc|Imagem em moldura|imagem;quadro;moldura'

@lru_cache(maxsize=1)
def catalog():
    result=[]
    for group,rows in DATA.items():
        for row in rows.splitlines():
            key,code,name,terms=row.split('|');key=key.replace(' ','')
            # A broad field is never represented by a generic proxy object.
            if key=='lupa':terms='lupa;vidro de aumento'
            if key=='livro':terms='livro aberto;livro físico;volume encadernado'
            if key=='livros':terms='pilha de livros;estante de livros;biblioteca física'
            if key=='lampada':terms='lâmpada;lâmpada elétrica;iluminação elétrica'
            if key=='moldura':terms='moldura;quadro na parede;imagem emoldurada'
            result.append({'id':key,'codigo':code,'nome':name,'grupo':group,'termos':terms.split(';'),
                'arquivo':key+'.svg','previa':'/api/shotcraft/figures/'+key+'/preview'})
    from .shotcraft_art_direction import compositions
    result.extend(compositions())
    return result

def normalize(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',str(text).lower()) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+',' ',text).strip()

def affinity(query,record,context=''):
    q=normalize(query);ctx=normalize(context)
    if q in ('memoria','memorias'):
        if re.search(r'\bram\b|computador|digital|processador',ctx):q='memoria ram'
        elif re.search(r'cerebro|humana|mente|lembr|esquec',ctx):q='memoria humana'
    if q in ('rede','redes') and re.search(r'internet|computador|digital|roteador',ctx):q='rede digital'
    if q in ('banco','bancos') and re.search(r'credito|dinheiro|financeir|emprestimo',ctx):q='banco financeiro'
    # Specific collocations eliminate common noun collisions before scoring.
    exclusions={'cerebro':('memoria ram','memoria do computador','memoria digital'),
                'nuvem':('computacao em nuvem','nuvem digital','cloud'),
                'folha':('folha de pagamento','folha de papel'),
                'onda_mar':('onda sonora','onda de radio','onda eletromagnetica'),
                'coracao_afeto':('anatomia','circulacao','cardiaco'),
                'lua':('lua islamica','simbolo islamico')}
    if any(x in q for x in exclusions.get(record['id'],())):return 0
    scores=[]
    for term in record['termos']:
        term=normalize(term)
        if q==term:scores.append(30+len(term.split()))
        elif re.search(r'\b'+re.escape(term)+r'\b',q):scores.append(18+len(term.split())*2)
        elif len(term.split())>1 and set(term.split())<=set(q.split()):scores.append(12)
    score=max(scores,default=0)
    if not score:return 0
    # A context cue breaks ties but can never turn an unrelated object into a hit.
    if any(re.search(r'\b'+re.escape(normalize(term))+r'\b',ctx) for term in record['termos']):score+=2
    return score

def choose(query,context='',preferred='',used=(),allowed=None):
    ranked=[(affinity(query,r,context),r) for r in catalog() if allowed is None or r['id'] in allowed]
    ranked=[(score,r) for score,r in ranked if score>=12]
    if not ranked:return None
    best=max(s for s,_ in ranked)
    near=[(score,r) for score,r in ranked if score>=best-1]
    # Variety breaks semantic ties only; an unrelated image is never substituted.
    return min(near,key=lambda item:(used.count(item[1]['id']),item[1]['id']!=preferred,-item[0],item[1]['id']))[1]


# Broad illustrations are opt-in through the project's thematic mode. Keep
# this separate from exact matching so rigorous review retains its semantics.
# Each pool also includes subjects with genuine meshes for the 3D library.
THEMATIC_POOLS={
    'tecnologia':('computador','celular','robo','satelite'),
    'ciencia':('microscopio','atomo','telescopio','livro'),
    'corpo':('cerebro','curativo','coracao','livro'),
    'religiao':('vela','livro','oracao'),
    'historia':('relogio_areia','livro','pergaminho'),
    'terror':('vela','fantasma','lanterna','arvore'),
    'natureza':('arvore','planta','folha','atomo'),
    'espaco':('telescopio','satelite','atomo','planeta'),
    'sociedade':('balanca','aperto_maos','pessoas','ponte'),
    'cotidiano':('relogio_areia','livro','casa','celular'),
    'cultura':('livro','microfone','camera','lapis'),
    'conceitos':('cerebro','ponte','escada','ligar_ideias'),
    'psicologia':('cerebro','balanca','livro','identidade_reflexo'),
    'filosofia':('balanca','relogio_areia','livro','cerebro'),
    'relacoes':('ponte','aperto_maos','cuidado_reciproco','livro'),
    'desafios':('escada','ponte','arvore','relogio_areia'),
}
THEMATIC_CUES={
    'tecnologia':'tecnologia;digital;software;computacao;internet;inteligencia artificial;informatica',
    'ciencia':'ciencia;cientifico;pesquisa;experimento;quimica;fisica;biologia;laboratorio',
    'corpo':'saude;medicina;corpo;doenca;tratamento;hospital;nutricao',
    'religiao':'religiao;religioso;espiritual;fe;oracao;cristianismo;isla;judaismo;budismo;hinduismo;taoismo',
    'historia':'historia;historico;passado;antiguidade;civilizacao;seculo;patrimonio',
    'terror':'terror;suspense;assombracao;fantasma;sombrio;medo do desconhecido',
    'natureza':'natureza;ambiente;ecologia;floresta;vegetacao;animal;conservacao',
    'espaco':'espaco;universo;astronomia;cosmos;espacial;planeta;clima',
    'sociedade':'sociedade;social;politica;economia;trabalho;profissao;comunidade;financeiro',
    'cotidiano':'cotidiano;rotina;casa;diario;viagem;transporte',
    'cultura':'cultura;educacao;ensino;estudo;aprendizado;aprendizagem;arte;musica;literatura',
    'conceitos':'ideia;conceito;objetivo;foco;motivacao;prioridade;clareza',
    'psicologia':'psicologia;mente;emocao;memoria;atencao;autoconhecimento;concentracao;silencio;solidao',
    'filosofia':'filosofia;etica;existencia;sentido da vida;reflexao;estoicismo',
    'relacoes':'relacao;relacionamento;amizade;familia;dialogo;vinculo;amor;empatia',
    'desafios':'superacao;persistencia;resiliencia;coragem;desafio;recomeco;constancia;progresso',
}


def selection_mode(settings):
    # Standalone exact-selection callers retain their old behavior; every
    # project pipeline explicitly supplies Settings (whose default is thematic).
    return getattr(settings,'shotcraft_selecao_figuras','rigoroso')


def choose_thematic(context,scene,*,preferred='',used=(),allowed=None):
    """Deterministic local fallback: phrase, scene, then a broad thematic pool.

    It changes illustrations only. Never turn an asset's name into a caption
    or claim that a symbolic subject is a literal depiction of the narration.
    """
    local=context+' '+scene.get('prompt_visual','')
    whole=' '.join([scene['titulo'],scene['narracao_ptbr'],*scene.get('texto_na_tela',[])])
    for text in (local,whole):
        found=choose(text,whole,preferred,used,allowed=allowed)
        if found:return found
    records={r['id']:r for r in catalog()}
    texts=[(normalize(local),3),(normalize(scene['titulo']),4),(normalize(whole),1)]
    scores={group:sum(weight for text,weight in texts for cue in cues.split(';')
                     if re.search(r'\b'+re.escape(cue)+r'(?:s|es)?\b',text))
            for group,cues in THEMATIC_CUES.items()}
    group=max(scores,key=scores.get) if any(scores.values()) else 'conceitos'
    pool=[records[key] for key in THEMATIC_POOLS[group] if allowed is None or key in allowed]
    if not pool:
        pool=[records[key] for key in THEMATIC_POOLS['conceitos'] if allowed is None or key in allowed]
    if not pool:return None
    # Retain the illustration on a cached re-validation; variation breaks ties
    # only for a fresh choice, never during the preflight/export passes.
    return min(pool,key=lambda r:(r['id']!=preferred if preferred in {p['id'] for p in pool} else False,
                                  used.count(r['id']),THEMATIC_POOLS.get(group,()).index(r['id']) if r['id'] in THEMATIC_POOLS[group] else 99))


PICTURE_RECIPES={'pilha_cartoes','camadas_profundidade','camera_suave','foco_luz','destaque_icone',
    'baralho_distribuido','carrossel_horizontal','carrossel_vertical','grade_mosaico','vidro_flutuante',
    'vidro_vitrine','rede_conexoes','traco_progressivo','lista_progressiva','grade_paineis','comparacao_revelada'}

class ArtDirectionError(ValueError):
    def __init__(self,message,*,details=None):
        super().__init__(message)
        self.details=details or []

def shortlist(text,limit=24):
    ranked=sorted(((affinity(text,r),r) for r in catalog()),key=lambda item:(-item[0],item[1]['id']))
    return [r for score,r in ranked if score>=12][:limit]

def apply(board,units,scene,*,strict=False,history=None,photo=False,settings=None):
    manual=[v.strip() for v in scene.get('shotcraft_figuras','').split(';') if v.strip()]
    known={r['id']:r for r in catalog()};used=history if history is not None else [];missing=[];details=[]
    for beat in board['momentos']:
        from .three_catalog import BY_RECIPE as volumes,SUBJECT_IDS
        mesh_art=volumes.get(beat.get('receita',''),{}).get('acervo3d',False)
        context=scene['titulo']+' '+(units[beat['frase']] if beat['frase']<len(units) else beat['titulo'])
        vague=set();beat_missing=[]
        for i,e in enumerate(beat['elementos']):
            if beat.get('receita','').startswith('volume_') and not mesh_art:
                e.update(figura='',tipo_arte='geometria3d',figura_motivo='Sólido tridimensional com rótulo da narração.')
                continue
            # Validate every explicit choice here. The timed primary-figure
            # sequence is composed against the real audio clock in Remotion.
            explicit=known.get(manual[i]) if i<len(manual) and (not mesh_art or manual[i] in SUBJECT_IDS) else None
            thematic=False
            query=e.get('consulta_figura') or e['rotulo']
            intention=e.get('intencao_visual','')
            found=explicit or choose(query+' '+intention,context,e.get('figura',''),used,allowed=SUBJECT_IDS if mesh_art else None)
            if mesh_art and i<len(manual) and manual[i] not in SUBJECT_IDS:found=None
            if not found and not mesh_art:
                # Anaphora and abstract statements can use a curated symbolic
                # scene supported by this very phrase. Never a category badge.
                candidates=[(affinity(context+' '+beat['titulo']+' '+intention,r),r) for r in catalog() if r['codigo']=='composite']
                candidates=[(score,r) for score,r in candidates if score>=18]
                if candidates:
                    best=max(s for s,_ in candidates);near=[r for s,r in candidates if s>=best-2]
                    found=min(near,key=lambda r:(used.count(r['id']),r['id']!=e.get('figura'),r['id']))
            if not found and selection_mode(settings)=='tematico':
                found=choose_thematic(context,scene,preferred=e.get('figura',''),used=used,allowed=SUBJECT_IDS if mesh_art else None)
                thematic=found is not None
            e['figura']=found['id'] if found else ''
            # Describe the illustration actually selected. A provider's old
            # generic-icon explanation must not survive a validated replacement.
            e['figura_motivo']=('Escolhida por você: '+found['nome'] if explicit else
                'Ilustração temática de apoio: '+found['nome'] if thematic else
                'Composição de sentido: '+found['sentido'] if found and found['codigo']=='composite' else
                'Objeto relacionado à fala: '+found['nome'] if found else 'A direção de arte precisa de uma ilustração pertinente.')
            e['justificativa_visual']=e['figura_motivo']
            e['natureza_visual']='metaforica' if thematic or found and found['codigo']=='composite' else 'direta'
            e['tipo_arte']='malha3d' if mesh_art else 'vetorial'
            if found and normalize(e['rotulo']) in {'assunto','imagem','ideia','conceito','exemplo'}:
                vague.add(id(e))
                if normalize(found.get('sentido') or found['nome']) in normalize(context):e['rotulo']=(found.get('sentido') or found['nome'])[:42]
            if found:used.append(found['id'])
            elif (mesh_art or beat.get('receita') in PICTURE_RECIPES) and not (photo and i==0):
                missing.append(e['rotulo']);beat_missing.append(e['rotulo'])
        if beat_missing:
            details.append({'frase':beat['frase'],'texto':units[beat['frase']] if 0<=beat['frase']<len(units) else beat['titulo'],
                            'elementos':list(dict.fromkeys(beat_missing))})
        # Do not display two identical empty abstractions such as "Assunto"
        # and "Imagem" as if they were separate visual information.
        kept=[];seen=set()
        for e in beat['elementos']:
            if e.get('figura') in seen and id(e) in vague:continue
            kept.append(e);seen.add(e.get('figura'))
        beat['elementos']=kept
    if strict and missing:
        raise ArtDirectionError('Revise a direção de arte: faltam figuras ou metáforas justificadas para '+', '.join(dict.fromkeys(missing))+'. Cartões sem imagem não serão exportados. Escolha figuras na cena ou detalhe a intenção visual.',details=details)
    return board

def path_for(key):
    if key not in {r['id'] for r in catalog()}:raise FileNotFoundError('Figura não encontrada')
    target=ASSETS/(key+'.svg')
    if not target.is_file():raise FileNotFoundError('Figura não instalada')
    return target

@lru_cache(maxsize=256)
def data_uri(key):
    return 'data:image/svg+xml;base64,'+base64.b64encode(path_for(key).read_bytes()).decode('ascii')

def fingerprint():
    return digest(VERSION,catalog(),read_json(ASSETS/'manifest.json',{}))

def credits(boards):
    meshes=any(b.get('receita','').startswith('volume_') for board in boards for b in board['momentos'])
    volume_credit='Modelos e objetos 3D: modelagem original do Clareia. Fonte Noto Sans: SIL Open Font License 1.1.\n' if meshes else ''
    keys={e.get('figura') for board in boards for b in board['momentos'] for e in b['elementos'] if e.get('tipo_arte') not in ('malha3d','geometria3d')}
    records=[r for r in catalog() if r['id'] in keys]
    if not records:return volume_credit
    source=(
        'Twemoji graphics by Twitter, Inc. and other contributors (including the jdecked/twemoji contributors). '
        'Licensed under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n'
        'Source: https://github.com/jdecked/twemoji · revision '+REVISION+'\n'
        ) if any(r['codigo']!='custom' for r in records) else ''
    return ('# Ilustrações das animações ShotCraft\n\n'+volume_credit+source+
        'As ilustrações são apresentadas em composições, tamanhos e sombras próprios do Clareia. '
        +('Os desenhos locais foram criados para o Clareia. ' if any(r['codigo']=='custom' for r in records) else '')+'\n\n'
        'Figuras utilizadas: '+', '.join(r['nome'] for r in records)+'.\n')
