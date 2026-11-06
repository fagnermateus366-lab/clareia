"""Permanent removal is restricted to validated project trash and owned previews."""
from pathlib import Path
from functools import wraps
import shutil
import threading

from .core import read_json,write_json,worker_active

LOCK=threading.RLock()


def synchronized(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        with LOCK:return fn(*args,**kwargs)
    return wrapped


def _linked(path):
    return path.is_symlink() or path.is_junction()


def _folder(projects):
    root=projects.resolve()
    folder=root/'.trash'
    if _linked(folder) or folder.resolve().parent!=root:
        raise ValueError('A pasta da lixeira não pertence a esta instalação.')
    return folder


def _files_size(target):
    total=0;pending=[target]
    while pending:
        directory=pending.pop()
        for entry in directory.iterdir():
            if _linked(entry) or not entry.resolve().is_relative_to(target):
                raise ValueError('A lixeira contém um atalho de pasta ou arquivo. Nenhum atalho será seguido.')
            if entry.is_dir():pending.append(entry)
            elif entry.is_file():total+=entry.stat().st_size
    return total


def _items(projects):
    folder=_folder(projects)
    if not folder.exists():return []
    items=[]
    for entry in folder.iterdir():
        if _linked(entry):raise ValueError('A lixeira contém um atalho de pasta; a operação foi interrompida.')
        if not entry.is_dir() or not (entry/'project.json').is_file():continue
        if not entry.name or any(c not in '0123456789abcdef-' for c in entry.name):continue
        if entry.resolve().parent!=folder:raise ValueError('Projeto fora da lixeira.')
        info=read_json(entry/'project.json')
        if info.get('id')!=entry.name:raise ValueError('Identificação de projeto inconsistente na lixeira.')
        items.append((entry,info))
    return items


def listing(projects):
    with LOCK:
        return [{**info,'remocao_incompleta':(path/'purge-incomplete.json').is_file(),
                 'excluido_em':read_json(path/'deleted.json',{}).get('excluido_em'),
                 'tamanho_bytes':_files_size(path)} for path,info in _items(projects)]


def empty(projects,expected):
    with LOCK:
        items=_items(projects)
        if not expected or len(expected)!=len(set(expected)) or set(expected)!={p.name for p,_ in items}:
            raise ValueError('A lixeira mudou. Atualize a lista e confirme os projetos novamente.')
        # Validate every absolute target before performing any recursive deletion.
        targets=[]
        for path,_ in items:
            if worker_active(path):raise ValueError('Há um projeto em processamento na lixeira. Aguarde sua conclusão.')
            targets.append((path,_folder(projects),_files_size(path),path.name,'project.json',read_json(path/'project.json')))
        from .scene_preview import STORE
        store=Path(STORE).resolve()
        if store.exists():
            if _linked(Path(STORE)):raise ValueError('A pasta de prévias não pode ser um atalho.')
            originals={str((projects.resolve()/pid).resolve()):pid for pid in expected}
            for entry in store.iterdir():
                if _linked(entry):continue
                if not entry.is_dir() or len(entry.name)!=24 or any(c not in '0123456789abcdef' for c in entry.name):continue
                record=read_json(entry/'scene-preview.json',{})
                if record.get('parent_path') not in originals:continue
                if entry.resolve().parent!=store:raise ValueError('Prévia fora da pasta esperada.')
                targets.insert(0,(entry,store,_files_size(entry),originals[record['parent_path']],'scene-preview.json',record))
        removed=[];errors=[];removed_bytes=0
        failed=set()
        for target,parent,size,key,marker,record in targets:
            if key in failed:continue
            # Recheck immediately before deletion as well as during preflight.
            if _linked(target) or target.resolve().parent!=parent or target==parent:
                raise ValueError('O destino de exclusão foi alterado. Operação interrompida.')
            try:shutil.rmtree(target)
            except OSError:
                failed.add(key)
                # A locked video can leave a partially removed directory. Retain
                # its ownership marker so it remains visible and can be retried.
                if target.is_dir() and not (target/marker).exists():write_json(target/marker,record)
                if target.is_dir() and marker=='project.json':write_json(target/'purge-incomplete.json',{'motivo':'Há arquivos que não puderam ser removidos.'})
                errors.append({'id':key,'mensagem':'Não foi possível remover todos os arquivos. Feche arquivos abertos e tente novamente.'})
            else:
                removed_bytes+=size
                if marker=='project.json':removed.append(key)
        return {'removidos':len(removed),'projetos':removed,'bytes_removidos':removed_bytes,'erros':errors}
