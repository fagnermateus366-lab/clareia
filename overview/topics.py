"""Read topic references and reusable illustrations before writing a video."""
from __future__ import annotations

from urllib.parse import urlparse
import re
import unicodedata

from .core import read_json,write_json
from . import research

STOP=set('a o as os e de do da dos das em no na nos nas um uma uns umas para por com que como qual quais quem quando onde se eu me meu minha voce voces quero queria gostaria preciso favor faca fazer crie criar gere gerar explique explicar conte contar fale falar mostre mostrar sobre acerca respeito video videos roteiro tema assunto bem tudo so seja pode poderia traga trazer coloque colocar descreva descrever detalhadamente'.split())
ANGLES={'historia','misterio','curiosidades','curiosidade','explicacao','entender','conhecer'}
NEWS=('agenciabrasil.ebc.com.br','bbc.com','bbc.co.uk','globo.com','cnnbrasil.com.br','reuters.com',
      'apnews.com','dw.com','nationalgeographic.com','nationalgeographicbrasil.com','britannica.com',
      'revistapesquisa.fapesp.br','super.abril.com.br','mundoeducacao.uol.com.br','brasilescola.uol.com.br')


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(text).casefold()) if not unicodedata.combining(c))


def subject(topic):
    words=[];seen=set()
    for word in re.findall(r'[\w-]+',topic):
        token=normalize(word)
        if token in STOP or token in seen or len(token)<2:continue
        seen.add(token);words.append(word)
    core=[w for w in words if normalize(w) not in ANGLES]
    return ' '.join(core or words)[:180] or topic.strip()[:180]


def relevant(text,query):
    tokens={normalize(w) for w in re.findall(r'\w+',query) if len(w)>=2}
    body=normalize(text)
    matched={w for w in tokens if re.search(r'\b'+re.escape(w)+r's?\b',body)}
    return bool(matched) and len(matched)>=min(2,len(tokens))


def source_rank(url):
    rank=research.priority(url)
    if rank<=1:return rank
    host=(urlparse(url).hostname or '').lower()
    if any(host==d or host.endswith('.'+d) for d in NEWS):return 2
    if host=='wikipedia.org' or host.endswith('.wikipedia.org'):return 3
    return 4


def check_pause(path):
    if (path/'pause.request').exists():
        from .render import Paused
        raise Paused('Pesquisa pausada. Retome para continuar.')


def encyclopedia(query):
    """A real public API fallback, never a model-generated reference."""
    from .portraits import api
    data=api('pt.wikipedia.org',{'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':0,
        'gsrlimit':3,'prop':'extracts|info','explaintext':1,'inprop':'url','redirects':1})
    docs=[]
    for page in sorted(data.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',999)):
        if page.get('fullurl') and page.get('extract'):
            docs.append({'url':page['fullurl'],'titulo':page.get('title',''),'paginas':[{'texto':page['extract'],'pagina':None}],
                         'consultada_em':research.date.today().isoformat()})
    return docs


def collect_media(path,query,update):
    from .topic_media import collect
    from .render import Paused
    try:return collect(path,query,update)
    except Paused:raise
    except Exception as exc:
        report={'busca':query,'imagens':[],'tentativas':[{'erro':str(exc)[:250]}],
                'aviso':'A busca de imagens não pôde ser concluída. O roteiro pode continuar e você pode adicionar imagens na revisão.'}
        write_json(path/'topic-images.json',report)
        return report


def discover(path,topic,update):
    query=subject(topic)
    update('Pesquisando referências sobre '+query,.02)
    queries=[query,query+' (site:gov.br OR site:jus.br OR site:edu.br)',query+' história contexto documentos']
    results=[];seen=set();attempts=[]
    for search in queries:
        check_pause(path)
        try:hits=research.search(search)
        except (ValueError,OSError,RuntimeError,research.httpx.HTTPError) as exc:
            attempts.append({'consulta':search,'erro':str(exc)[:180]});continue
        for hit in hits:
            url=hit.get('url','')
            if url.startswith(('https://','http://')) and url not in seen:
                results.append(hit);seen.add(url)
    sources=[];domains=set()

    def add(doc):
        text='\n\n'.join(p['texto'] for p in doc['paginas'])[:24000]
        if len(text)<600 or not relevant(doc['titulo']+' '+text,query):
            raise ValueError('Página sem conteúdo suficiente e pertinente ao assunto.')
        host=urlparse(doc['url']).hostname or ''
        if host in domains:return
        rank=source_rank(doc['url'])
        sources.append({'id':'F'+str(len(sources)+1),'origem':doc['url'],'titulo':doc['titulo'],'texto':text,
                        'pesquisada':True,'consultada_em':doc['consultada_em'],
                        'tipo_fonte':'institucional' if rank<=1 else 'jornalistica' if rank==2 else 'enciclopedia' if rank==3 else 'publica',
                        'prioritaria':rank<=1})
        domains.add(host)

    for hit in sorted(results,key=lambda h:source_rank(h['url']))[:16]:
        check_pause(path)
        host=urlparse(hit['url']).hostname or ''
        if host in domains:continue
        if re.search(r'/(?:handle|sophia_web)/',urlparse(hit['url']).path) or (host=='repositorio.usp.br' and urlparse(hit['url']).path.startswith('/item/')):continue
        update('Lendo referência sobre o assunto · '+host,.04+.01*len(sources))
        try:add(research.document(hit['url'],path))
        except (ValueError,OSError,RuntimeError,research.httpx.HTTPError) as exc:
            attempts.append({'url':hit['url'],'erro':str(exc)[:180]})
        if len(sources)>=3:break
    if not sources:
        check_pause(path);update('Consultando uma fonte enciclopédica sobre '+query,.06)
        try:
            for doc in encyclopedia(query):
                try:add(doc)
                except ValueError as exc:attempts.append({'url':doc['url'],'erro':str(exc)[:180]})
                if len(sources)>=2:break
        except (ValueError,OSError,RuntimeError,research.httpx.HTTPError) as exc:
            attempts.append({'servico':'Wikipedia','erro':str(exc)[:180]})
    report={'assunto':topic,'busca':query,'consultas':queries,'fontes':[{k:v for k,v in s.items() if k!='texto'} for s in sources],'tentativas':attempts}
    write_json(path/'topic-research.json',report)
    if not sources:
        raise ValueError('Não foi possível ler referências sobre este assunto nesta tentativa. Confira a conexão e tente novamente; o assunto foi preservado e nenhuma referência foi inventada.')
    existing=read_json(path/'sources.json',{})
    write_json(path/'sources.json',{**existing,'fontes':sources,'imagens':existing.get('imagens',[]),'imagens_meta':existing.get('imagens_meta',{})})
    (path/'fontes.md').write_text('\n\n'.join('## ['+s['id']+'] '+s['origem']+'\n\n'+s['texto'] for s in sources),encoding='utf-8')
    check_pause(path)
    report['imagens']=collect_media(path,query,update)
    write_json(path/'topic-research.json',report)
    record=read_json(path/'topic.json',{});record['pesquisa_pendente']=False;write_json(path/'topic.json',record)
    return sources
