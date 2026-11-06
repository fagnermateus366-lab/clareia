"""Append local scene illustrations without rebuilding or reinterpreting sources."""
import hashlib
import io
from pathlib import Path
import re
import threading
import uuid

from PIL import Image,ImageOps
from .core import read_json,write_json

MAX_BYTES=20*1024*1024
MAX_FILES=12
LOCK=threading.RLock()


def append_images(path,files,description='',guard=lambda:None):
    if not files or len(files)>MAX_FILES:raise ValueError('Envie de 1 a 12 imagens por vez.')
    prepared=[]
    for filename,data in files:
        if len(data)>MAX_BYTES:raise ValueError('Cada imagem pode ter até 20 MB.')
        try:
            with Image.open(io.BytesIO(data)) as original:
                if original.format not in ('PNG','JPEG','WEBP'):raise ValueError('Formato não aceito')
                if original.width*original.height>25_000_000:raise ValueError('Imagem muito grande')
                original.load()
                image=ImageOps.exif_transpose(original).convert('RGBA')
                image.thumbnail((3840,3840),Image.Resampling.LANCZOS)
                out=io.BytesIO();image.save(out,format='PNG');normalized=out.getvalue()
        except Exception as exc:
            raise ValueError('Use imagens PNG, JPG ou WebP válidas, com até 25 megapixels.') from exc
        name='media-'+hashlib.sha256(normalized).hexdigest()[:24]+'.png'
        filename=Path(filename.replace('\\','/')).name[:180] or 'Imagem'
        filename=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',filename)
        label=description.strip()[:500] or Path(filename).stem
        meta={'identificacao':label,'nome_original':filename,'palavras_chave':[w.casefold() for w in re.findall(r'\w+',label) if len(w)>2],'adicionada_na_revisao':True}
        prepared.append((name,normalized,filename,data,meta))
    with LOCK:
        guard()
        sources=read_json(path/'sources.json',{'fontes':[],'imagens':[]})
        sources.setdefault('imagens',[]);sources.setdefault('imagens_meta',{})
        assets=path/'assets';assets.mkdir(exist_ok=True)
        originals=path/'originais/media';originals.mkdir(parents=True,exist_ok=True)
        created=[];added=[]
        try:
            for name,data,filename,original,meta in prepared:
                if name not in sources['imagens']:
                    target=assets/name
                    if not target.exists():target.write_bytes(data);created.append(target)
                    saved=originals/(uuid.uuid4().hex+'-'+Path(filename).stem[:40]+Path(filename).suffix[:6])
                    saved.write_bytes(original);created.append(saved)
                    sources['imagens'].append(name)
                sources['imagens_meta'][name]=meta
                if name not in added:added.append(name)
            write_json(path/'sources.json',sources)
        except Exception:
            for target in created:target.unlink(missing_ok=True)
            raise
    return {'adicionadas':added,'imagens':sources['imagens'],'imagens_meta':sources['imagens_meta']}
