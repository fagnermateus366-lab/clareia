"""Subject-specific cutouts. Selection is prepared once, never during frame drawing."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path
import hashlib
import io
import re
import time
import unicodedata
from urllib.parse import urlparse

from PIL import Image

from .core import ROOT, MODELS, digest, read_json, write_json

ASSETS = ROOT/'overview/assets/collage'
LIBRARY = MODELS/'colagem'
VERSION = 'collage-library-v1'


def normalize(text):
    return re.sub(r'[^a-z0-9 ]', ' ', ''.join(c for c in unicodedata.normalize('NFKD',str(text).lower()) if not unicodedata.combining(c))).strip()


@lru_cache(maxsize=1)
def catalog():
    return read_json(ASSETS/'catalog.json',[])


def content_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def fingerprint():
    return digest(VERSION,content_hash(ASSETS/'parchment.png'),catalog(),
                  [content_hash(ASSETS/n) for n in ('turbine-mast.png','turbine-rotor.png','turbine-pivots.json')],
                  [(r['id'],content_hash(ASSETS/r['file'])) for r in catalog()])


STOP={'de','da','do','das','dos','a','o','os','as','um','uma','e','com','para','em','the','of','and','an','no','na','por'}
EXCLUSIONS={
    'onda':('onda de radio','ondas de radio','onda sonora','onda eletromagnetica','onda de choque'),
    'banco':('banco de dados','banco de sangue','banco de areia','banco de praca'),
    'folha':('folha de pagamento','folha de papel','folha de caderno'),
    'terra':('terra cultivada','terra fertil','terra vermelha','terra agricola'),
}


def affinity(query, terms):
    """An exact noun wins; broad topic matches never beat its specific object."""
    q=normalize(query)
    tokens=set(q.split())-STOP
    if not tokens:return 0
    best=0
    for term in terms:
        term=normalize(term)
        words=set(term.split())-STOP
        common=tokens & words
        if not common:continue
        score=12 if q==term else 8+len(words) if re.match(re.escape(term)+r'\b',q) else 0
        if not score and words<=tokens and q.split()[0] in words:score=7+len(words)
        if not score and tokens<=words:score=4+len(tokens)/len(words)
        best=max(best,score)
    return best


def choose(query, records, used=(), blocked=()):
    counts=Counter(used)
    ranked=[(affinity(query,r.get('tags',[])),r) for r in records if r['id'] not in blocked
            and not any(term in normalize(query) for term in EXCLUSIONS.get(r['id'],()))]
    ranked=[(s,r) for s,r in ranked if s>=4]
    if not ranked:return None
    # Variety only among semantically equivalent candidates. Never choose an
    # unrelated figure just because it has not appeared recently.
    best=max(s for s,_ in ranked)
    near=[(s,r) for s,r in ranked if s>=best-1]
    return min(near,key=lambda item:(counts[item[1]['id']],-item[0],item[1]['id']))[1]


def scene_key(scene,board):
    clean=[{k:v for k,v in b.items() if k not in ('inicio','fim','fala_inicio','transicao_s')} for b in board['momentos']]
    return digest(scene['narracao_ptbr'],scene.get('figuras_colagem',''),clean)


def resolve(record,path):
    if not record:return None
    kind=record.get('kind','library')
    root=ASSETS if kind=='library' else path/'assets' if kind=='user' else LIBRARY if kind=='commons' else None
    if root is None:return None
    target=(root/record['file']).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():return None
    return target


def user_records(path):
    sources=read_json(path/'sources.json',{})
    metadata=sources.get('imagens_meta',{})
    records=[]
    for name in sources.get('imagens',[]):
        meta=metadata.get(name,{})
        tags=[Path(name).stem,meta.get('identificacao','')]
        words=meta.get('palavras_chave',[])
        tags+=words if isinstance(words,list) else [words]
        r={'id':'user:'+name,'file':name,'kind':'user','tags':tags,'name':meta.get('identificacao') or Path(name).stem}
        if resolve(r,path):records.append(r)
    return records


def commons_candidates(query):
    """Opt-in, free Commons API. Only supported reusable licenses are cached."""
    from .portraits import api,plain
    from .research import fetch
    key=digest('commons-cutout-v2',normalize(query))
    index=LIBRARY/(key+'.json')
    saved=read_json(index,{})
    if saved and (saved.get('records') or time.time()-saved.get('checked',0)<86400):
        return [r for r in saved.get('records',[]) if (LIBRARY/r['file']).is_file()],saved.get('error','')
    records=[];error=''
    try:
        data=api('commons.wikimedia.org',{'action':'query','generator':'search','gsrsearch':query+' filetype:bitmap -intitle:"captured by" -intitle:"taken by"',
            'gsrnamespace':6,'gsrlimit':6,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':900})
        for page in sorted(data.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',999)):
            info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
            val=lambda name:plain(meta.get(name,{}).get('value',''))
            if affinity(query,[page.get('title',''),val('ImageDescription'),val('Categories')])<4:continue
            license=val('LicenseShortName')
            if not (license.lower() in ('public domain','cc0','cc0 1.0') or re.fullmatch(r'CC BY [1-4]\.0',license,re.I)):continue
            url=info.get('thumburl') or info.get('url','')
            if urlparse(url).scheme!='https' or urlparse(url).hostname not in ('upload.wikimedia.org','thumb.wikimedia.org'):continue
            _,body,_=fetch(url,6_000_000)
            with Image.open(io.BytesIO(body)) as source:
                if source.width*source.height>25_000_000:continue
                image=source.convert('RGBA');image.thumbnail((1200,1200))
            name=digest(page['title'],content_hash_bytes(body))+'.png'
            LIBRARY.mkdir(parents=True,exist_ok=True);image.save(LIBRARY/name)
            records.append({'id':'commons:'+name,'file':name,'kind':'commons','name':page['title'].removeprefix('File:'),
                'tags':[query],'source':info.get('descriptionurl',''),'author':val('Artist'),'license':license,
                'license_url':val('LicenseUrl'),'query':query,'illustrative':True})
            if len(records)>=2:break
        if not records:error='Nenhuma imagem reutilizável encontrada; usar texto ou figura do acervo pertinente.'
    except Exception as exc:
        error='Busca indisponível: '+str(exc)[:180]
    write_json(index,{'query':query,'checked':time.time(),'records':records,'error':error})
    return records,error


def content_hash_bytes(body):
    return hashlib.sha256(body).hexdigest()


def prepare_project(path,scenes,boards,settings,cancel=None):
    selected=[(s,b) for s,b in zip(scenes,boards) if (settings.animacao if s.get('animacao','herdar')=='herdar' else s['animacao'])=='colagem_documental']
    if not selected:return
    manifest={'version':VERSION,'scenes':{},'warnings':[],'online':settings.colagem_buscar_figuras}
    used=[];queries={};online_count=0
    library=[{**r,'kind':'library'} for r in catalog()]
    users=user_records(path)
    for scene,board in selected:
        overrides=[q.strip()[:120] for q in re.split(r'[;\n]',scene.get('figuras_colagem','')) if q.strip()]
        n=0;moments=[];subjects={}
        for beat in board['momentos']:
            figures=[];blocked=[]
            for element in beat['elementos']:
                if cancel is not None and cancel.exists():return
                query=overrides[n] if n<len(overrides) else element.get('recorte') or element['rotulo'];n+=1
                record=subjects.get(normalize(query))
                continuing=record is not None and record['id'] not in blocked
                if not continuing:record=choose(query,users,used,blocked) or choose(query,library,used,blocked)
                if not continuing and settings.colagem_buscar_figuras and (not record or Counter(used)[record['id']]>0):
                    if query not in queries and online_count<64:
                        online_count+=1;queries[query]=commons_candidates(query)
                    candidates,error=queries.get(query,([], 'Limite de 64 buscas novas nesta renderização.'))
                    alternative=choose(query,candidates,used,blocked)
                    if alternative and (not record or Counter(used)[alternative['id']]<Counter(used)[record['id']]):record=alternative
                    if error:manifest['warnings'].append({'query':query,'detail':error})
                if record:
                    record={**record,'query':query};target=resolve(record,path)
                    record['hash']=content_hash(target)
                    blocked.append(record['id']);used.append(record['id'])
                    subjects.setdefault(normalize(query),record)
                else:manifest['warnings'].append({'query':query,'detail':'Sem recorte correspondente. Usado símbolo ilustrativo com legenda.'})
                figures.append(record)
            moments.append(figures)
        manifest['scenes'][scene_key(scene,board)]=moments
    write_json(path/'cache/collage/selection.json',manifest)
    export=path/'export';export.mkdir(exist_ok=True)
    rows=['# Figuras da colagem documental','',
          'Os recortes gerados do acervo são ilustrações genéricas; não são fotografias documentais de pessoas ou acontecimentos específicos.','']
    credited=set()
    for moments in manifest['scenes'].values():
        for figures in moments:
            for r in figures:
                if not r or r['id'] in credited:continue
                credited.add(r['id'])
                rows.append(f"- {r['name']} · {r.get('author','Acervo ilustrativo local')} · {r.get('license','Gerado com ImageGen' if r['kind']=='library' else 'Imagem fornecida pelo usuário')}"+(f" · {r['source']}" if r.get('source') else ''))
    if manifest['warnings']:
        rows+=['','## Figuras sem correspondência ou busca indisponível','']
        rows += [f"- {r['query']}: {r['detail']}" for r in manifest['warnings']]
    (export/'creditos-colagem.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')


def selections(path,scene,beats):
    saved=read_json(path/'cache/collage/selection.json',{})
    records=saved.get('scenes',{}).get(scene_key(scene,{'momentos':beats}))
    if records is not None:return records
    # Posters and direct rendering remain completely offline.
    used=[];result=[];subjects={}
    for beat in beats:
        blocked=[];row=[]
        for e in beat['elementos']:
            query=e.get('recorte') or e['rotulo']
            r=subjects.get(normalize(query))
            if r is None or r['id'] in blocked:r=choose(query,catalog(),used,blocked)
            row.append(r)
            if r:used.append(r['id']);blocked.append(r['id']);subjects.setdefault(normalize(query),r)
        result.append(row)
    return result
