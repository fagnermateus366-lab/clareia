"""Verified human entities + licensed Commons portraits, with provenance and credits."""
from __future__ import annotations
import io
import re
import unicodedata
from urllib.parse import urlencode

from lxml import html
from PIL import Image, ImageOps

from .core import digest, write_json
from .research import fetch


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c)).strip()


def api(host,params):
    import json
    _,body,_=fetch('https://'+host+'/w/api.php?'+urlencode({'format':'json',**params}),3_000_000)
    return json.loads(body)


def plain(value):
    try:return html.fromstring('<div>'+value+'</div>').text_content().strip()
    except ValueError:return value


def portrait(path,name):
    found=api('www.wikidata.org',{'action':'wbsearchentities','search':name,'language':'pt','limit':5,'type':'item'})
    candidates=[]
    for entity in found.get('search',[]):
        labels=[entity.get('label','')]+(entity.get('aliases') or [])
        if any(norm(label)==norm(name) for label in labels):candidates.append(entity['id'])
    if not candidates:raise ValueError('Identidade sem correspondência única')
    entities=api('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(candidates),'props':'claims|labels','languages':'pt|en'})['entities']
    humans=[(qid,e) for qid,e in entities.items() if any(
        c.get('mainsnak',{}).get('datavalue',{}).get('value',{}).get('id')=='Q5' for c in e.get('claims',{}).get('P31',[]))]
    # Books, hospitals and awards sharing the person's name are not portrait candidates.
    if len(humans)!=1:raise ValueError('Identidade sem correspondência humana única')
    qid,entity=humans[0]
    claims=entity.get('claims',{})
    images=claims.get('P18',[])
    if not images:raise ValueError('Sem retrato identificado')
    filename=images[0]['mainsnak']['datavalue']['value']
    data=api('commons.wikimedia.org',{'action':'query','titles':'File:'+filename,'prop':'imageinfo',
        'iiprop':'url|extmetadata','iiurlwidth':640,'iiextmetadatafilter':'LicenseShortName|LicenseUrl|Artist|Credit|Attribution'})
    page=next(iter(data.get('query',{}).get('pages',{}).values()))
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
    license=plain(meta.get('LicenseShortName',{}).get('value',''))
    # Conservative supported set. Others can be reviewed manually outside this automated feature.
    if not (license.lower() in ('public domain','cc0','cc0 1.0') or re.fullmatch(r'CC BY [1-4]\.0',license,re.I)):
        raise ValueError('Licença fora do conjunto suportado automaticamente')
    url=info.get('thumburl') or info.get('url')
    if not url:raise ValueError('Arquivo de retrato indisponível')
    final,body,_=fetch(url,4_000_000)
    with Image.open(io.BytesIO(body)) as photo:
        if photo.width*photo.height>25_000_000:raise ValueError('Retrato grande demais')
        photo=ImageOps.contain(photo.convert('RGB'),(640,800))
        asset='retrato-'+digest(qid,filename)+'.png'
        (path/'assets').mkdir(exist_ok=True)
        photo.save(path/'assets'/asset)
    return {'pessoa':name,'wikidata':qid,'arquivo':asset,'fonte':info.get('descriptionurl','https://commons.wikimedia.org/wiki/File:'+filename.replace(' ','_')),
            'url_original':final,'licenca':license,'licenca_url':meta.get('LicenseUrl',{}).get('value',''),
            'autor_foto':plain(meta.get('Artist',{}).get('value','')),'credito':plain(meta.get('Credit',{}).get('value',''))}


def collect(path,names):
    photos=[];skipped=[]
    for name in names:
        try:photos.append(portrait(path,name))
        except Exception as exc:skipped.append({'pessoa':name,'motivo':str(exc)[:180]})
    export=path/'export';export.mkdir(exist_ok=True)
    lines=['# Créditos das imagens de pessoas','Retratos associados a entidades humanas identificadas no Wikidata. Nenhum retrato é inventado ou gerado por IA.']
    for p in photos:
        lines += [f"## {p['pessoa']}",f"Foto: {p['autor_foto']} · {p['licenca']}",p['fonte'],p['licenca_url'],p['credito']]
    for s in skipped:lines.append(f"Sem retrato automático para {s['pessoa']}: {s['motivo']}")
    (export/'creditos-imagens.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    write_json(path/'retratos-nao-incluidos.json',skipped)
    return photos
