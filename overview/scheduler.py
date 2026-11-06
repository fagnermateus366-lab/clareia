"""Persistent serial queue: due appointments wait until the complete flow finishes."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import logging
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
import traceback

import psutil

from .core import ProcessingLock, read_json, set_status, write_json

PENDING = ('fila', 'agendado', 'executando')


class Scheduler:
    def __init__(self, database, active, execute, *, clock=time.time, lock_factory=ProcessingLock):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.active, self.execute = active, execute
        self.clock, self.lock_factory = clock, lock_factory
        self.opened_at = clock()
        self.mutex = threading.RLock()
        self.stop_event = threading.Event()
        self.thread = None
        self.pid = os.getpid()
        self.created = psutil.Process().create_time()
        with self.transaction() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL,
                    path TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL,
                    submitted REAL NOT NULL, scheduled REAL, status TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT '', started REAL, finished REAL,
                    owner INTEGER, owner_created REAL, previous TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_pending_project ON jobs(path)
                    WHERE status IN ('fila','agendado','executando');
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, job INTEGER, project TEXT,
                    title TEXT NOT NULL, status TEXT NOT NULL, message TEXT NOT NULL,
                    created REAL NOT NULL, seen INTEGER NOT NULL DEFAULT 0
                );
            ''')
            if 'options' not in {row['name'] for row in db.execute('PRAGMA table_info(jobs)')}:
                db.execute("ALTER TABLE jobs ADD COLUMN options TEXT NOT NULL DEFAULT '{}'")
            # Existing pending appointments adopt the requested render → publish flow.
            db.execute("UPDATE jobs SET kind='render_youtube' WHERE scheduled IS NOT NULL AND kind='render' AND status IN ('fila','agendado')")
            for job in db.execute("SELECT * FROM jobs WHERE kind='render_youtube' AND scheduled IS NOT NULL AND status IN ('fila','agendado') AND options='{}'").fetchall():
                from .publication import settings_for_schedule
                path=Path(job['path'])
                try:
                    options=settings_for_schedule(path,run_id='legacy-'+str(job['id']))
                except (ValueError,FileNotFoundError):
                    # A channel may be connected later, before this appointment starts.
                    continue
                db.execute('UPDATE jobs SET options=? WHERE id=?',(json.dumps(options,ensure_ascii=False),job['id']))
                write_json(path/'agendamento.json',{**options,'horario':datetime.fromtimestamp(job['scheduled'],timezone.utc).isoformat()})
        self.recover()

    @contextmanager
    def transaction(self):
        with self.mutex:
            db = sqlite3.connect(self.database, timeout=15)
            db.row_factory = sqlite3.Row
            try:
                db.execute('BEGIN IMMEDIATE')
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    def _notify(self, db, job, status, message):
        db.execute('INSERT INTO notifications(job,project,title,status,message,created) VALUES(?,?,?,?,?,?)',
                   (job['id'], job['project'], job['title'], status, message, self.clock()))

    def _finish(self, db, job, status, message, *, update_project=True):
        db.execute('UPDATE jobs SET status=?,message=?,finished=? WHERE id=?',
                   (status, message, self.clock(), job['id']))
        if update_project and (Path(job['path']) / 'project.json').is_file():
            set_status(Path(job['path']), status, message)
        self._notify(db, job, status, message)

    def recover(self):
        with self.transaction() as db:
            for job in db.execute("SELECT * FROM jobs WHERE status='executando'").fetchall():
                try:
                    alive = abs(psutil.Process(job['owner']).create_time() - job['owner_created']) < .1
                except (psutil.Error, TypeError):
                    alive = False
                if not alive:
                    state=read_json(Path(job['path'])/'status.json',{})
                    if job['kind']=='render_youtube':
                        checkpoint=read_json(Path(job['path'])/'scheduled-publication.json',{})
                        options=json.loads(job['options'])
                        if checkpoint.get('stage')=='complete' and checkpoint.get('run_id')==options.get('run_id'):
                            self._finish(db,job,'enviado_youtube','Publicação do fluxo agendado confirmada no YouTube.')
                        else:
                            status='agendado' if job['scheduled'] is not None else 'fila'
                            message='Fluxo interrompido. Aguardando a vez para retomar a criação/publicação preservada.'
                            db.execute('UPDATE jobs SET status=?,message=?,owner=NULL,owner_created=NULL WHERE id=?',(status,message,job['id']))
                            set_status(Path(job['path']),status,message)
                        continue
                    if job['kind'] in ('youtube','render_youtube') and state.get('status')!='enviado_youtube' and (job['kind']=='youtube' or read_json(Path(job['path'])/'scheduled-publication.json',{}).get('stage')=='upload'):
                        result=read_json(Path(job['path'])/'youtube-upload.json',{})
                        if result.get('video_id') and result.get('status')=='enviado' and all(pid in result.get('playlists_aplicadas',{}) for pid in result.get('playlists',[])):
                            message=result.get('message','Arquivo enviado ao YouTube.')
                            set_status(Path(job['path']),'enviado_youtube',message,1)
                            self._finish(db,job,'enviado_youtube',message,update_project=False)
                            continue
                        from .youtube_upload import interrupted
                        message='Envio interrompido. Retome para consultar e aproveitar os bytes recebidos pelo YouTube.'
                        interrupted(Path(job['path']),message,paused=True)
                        self._finish(db,job,'pausado',message,update_project=False)
                        continue
                    if state.get('status') in ('concluido','revisao','erro','pausado','enviado_youtube'):
                        self._finish(db, job, state['status'], state.get('mensagem','Tarefa finalizada'), update_project=False)
                    else:
                        self._finish(db, job, 'pausado', 'Processamento interrompido. Revise e retome para aproveitar o cache.')
            for job in db.execute("SELECT * FROM jobs WHERE status='agendado' AND scheduled<?", (self.opened_at,)).fetchall():
                message='Horário alcançado. Aguardando a vez para criar e publicar o vídeo.'
                db.execute('UPDATE jobs SET message=? WHERE id=?',(message,job['id']))
                if (Path(job['path'])/'project.json').is_file():set_status(Path(job['path']),'agendado',message)

    def submit(self, path, kind='render', scheduled=None, options=None):
        path = Path(path).resolve()
        now = self.clock()
        if scheduled is not None and scheduled <= now:
            raise ValueError('Escolha uma data e um horário no futuro.')
        info = read_json(path / 'project.json')
        if not info:
            raise FileNotFoundError('Projeto não encontrado')
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM jobs WHERE path=? AND status IN ('fila','agendado','executando')", (str(path),)).fetchone():
                raise ValueError('Este projeto já está na fila, agendado ou em execução. Cancele a espera antes de alterar.')
            state = 'agendado' if scheduled is not None else 'fila'
            message = 'Agendado para criar e publicar. Se o estúdio estiver ocupado, aguardará a vez.' if scheduled is not None else 'Na fila. Inicia automaticamente quando chegar a sua vez.'
            previous = json.dumps(read_json(path / 'status.json', {}), ensure_ascii=False)
            if scheduled is not None and kind=='render':kind='render_youtube'
            row = db.execute('INSERT INTO jobs(project,path,title,kind,submitted,scheduled,status,message,previous,options) VALUES(?,?,?,?,?,?,?,?,?,?)',
                             (path.name, str(path), info['titulo'], kind, now, scheduled, state, message, previous,json.dumps(options or {},ensure_ascii=False)))
            set_status(path, state, message)
            if kind=='roteiro':
                from .production_time import requested
                requested(path,now,row.lastrowid)
            return {'id': row.lastrowid, 'status': state, 'agendado_para': scheduled}

    def pending(self, path):
        with self.transaction() as db:
            return db.execute("SELECT 1 FROM jobs WHERE path=? AND status IN ('fila','agendado','executando')", (str(Path(path).resolve()),)).fetchone() is not None

    def snapshot(self):
        with self.transaction() as db:
            rows = db.execute("SELECT * FROM jobs WHERE status IN ('fila','agendado','executando') ORDER BY CASE WHEN status='executando' THEN 0 WHEN scheduled IS NULL THEN 1 ELSE 2 END, CASE WHEN scheduled IS NULL THEN id ELSE scheduled END,id").fetchall()
            history = db.execute("SELECT * FROM jobs WHERE status NOT IN ('fila','agendado','executando') ORDER BY id DESC LIMIT 40").fetchall()
        def public(job):
            record = {k: job[k] for k in ('id','project','title','kind','status','message','submitted','scheduled','started','finished')}
            record['atrasado']=job['status']=='agendado' and job['scheduled']<=self.clock()
            record['publication']=json.loads(job['options']) if job['kind']=='render_youtube' else None
            if job['status']=='executando':
                record['message'] = read_json(Path(job['path'])/'status.json',{}).get('mensagem','Processamento em andamento')
            return record
        return {'tarefas': [public(j) for j in rows], 'historico': [public(j) for j in history], 'ocupado': self.active.locked()}

    def cancel(self, job_id):
        import json
        with self.transaction() as db:
            job = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            if not job:
                raise FileNotFoundError('Tarefa não encontrada')
            if job['status'] not in ('fila','agendado'):
                raise ValueError('A tarefa já iniciou ou terminou. Use Pausar para interromper um processamento.')
            self._finish(db, job, 'cancelado', 'Espera cancelada pelo usuário.', update_project=False)
            path = Path(job['path'])
            if (path / 'project.json').is_file():
                write_json(path / 'status.json', json.loads(job['previous']))
                if job['kind']=='youtube':
                    from .youtube_upload import cancelled
                    cancelled(path)

    def notifications(self):
        with self.transaction() as db:
            rows = db.execute('SELECT * FROM notifications ORDER BY id DESC LIMIT 100').fetchall()
            unread = db.execute('SELECT COUNT(*) FROM notifications WHERE seen=0').fetchone()[0]
        return {'itens': [dict(row) for row in rows], 'nao_lidas': unread}

    def mark_read(self, through):
        with self.transaction() as db:
            db.execute('UPDATE notifications SET seen=1 WHERE id<=?', (through,))

    def tick(self):
        """Check appointments even while the separate worker renders a long video."""
        selected = None
        lease = None
        acquired = False
        try:
            with self.transaction() as db:
                now = self.clock()
                due = db.execute("SELECT * FROM jobs WHERE status='agendado' AND scheduled<=? ORDER BY scheduled,id", (now,)).fetchall()
                waiting = db.execute("SELECT * FROM jobs WHERE status='fila' ORDER BY id LIMIT 1").fetchone()
                running = db.execute("SELECT 1 FROM jobs WHERE status='executando'").fetchone()
                acquired = not running and self.active.acquire(blocking=False)
                if acquired:
                    lease = self.lock_factory()
                    if not lease.acquire():
                        self.active.release(); acquired = False
                for job in due:
                    if acquired and not waiting and selected is None:
                        selected=job
                    else:
                        message='Horário alcançado. Aguardando o fluxo anterior terminar, incluindo o envio ao YouTube.'
                        if job['message']!=message:
                            db.execute('UPDATE jobs SET message=? WHERE id=?',(message,job['id']))
                            if (Path(job['path'])/'project.json').is_file():set_status(Path(job['path']),'agendado',message)
                if waiting and acquired:
                    selected = waiting
                if selected:
                    path = Path(selected['path'])
                    if not (path / 'project.json').is_file():
                        self._finish(db, selected, 'erro', 'Projeto não encontrado para processamento.', update_project=False)
                        selected = None
                    else:
                        db.execute("UPDATE jobs SET status='executando',message='Processamento em andamento',started=?,owner=?,owner_created=? WHERE id=?",
                                   (now, self.pid, self.created, selected['id']))
                        (path / 'pause.request').unlink(missing_ok=True)
                        write_json(path / 'task.json', {'tipo': selected['kind'], 'iniciado': now,'job_id':selected['id'],
                                                      'agendado_para':selected['scheduled'],'opcoes':json.loads(selected['options'])})
                        set_status(path, 'fila', 'Iniciando processamento')
            if selected:
                try:
                    threading.Thread(target=self._work, args=(dict(selected), lease), daemon=True).start()
                except Exception:
                    with self.transaction() as db:
                        message='Não foi possível iniciar o processamento. Tente executar novamente.'
                        if selected['kind']=='youtube' or (selected['kind']=='render_youtube' and read_json(Path(selected['path'])/'scheduled-publication.json',{}).get('stage')=='upload'):
                            from .youtube_upload import interrupted
                            interrupted(Path(selected['path']),message)
                            self._finish(db,selected,'erro',message,update_project=False)
                        else:self._finish(db, selected, 'erro', message)
                    raise
                acquired = False  # ownership transferred to worker
        finally:
            if acquired:
                if lease: lease.release()
                self.active.release()

    def _work(self, job, lease):
        path = Path(job['path'])
        try:
            self.execute(path, job['kind'], lease)
            state = read_json(path / 'status.json', {})
            outcome = state.get('status')
            if outcome not in ('concluido','revisao','pausado','erro','enviado_youtube'):
                raise RuntimeError('A tarefa terminou sem confirmar um resultado. Consulte o projeto.')
            with self.transaction() as db:
                self._finish(db, job, outcome, state.get('mensagem', 'Tarefa finalizada'), update_project=False)
        except Exception as exc:
            from .render import Paused
            state = 'pausado' if isinstance(exc, Paused) else 'erro'
            message = (str(exc) or 'Pausado. O cache foi preservado.') if state == 'pausado' else str(exc)[-800:]
            if state == 'erro':
                (path / 'erro.log').write_text(traceback.format_exc(), encoding='utf-8')
            with self.transaction() as db:
                if job['kind']=='youtube' or (job['kind']=='render_youtube' and read_json(path/'scheduled-publication.json',{}).get('stage')=='upload'):
                    from .youtube_upload import interrupted
                    interrupted(path,message,paused=state=='pausado')
                    self._finish(db,job,state,message,update_project=False)
                else:self._finish(db, job, state, message)
        finally:
            lease.release()
            self.active.release()

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        def loop():
            while not self.stop_event.is_set():
                try:
                    self.tick()
                except Exception:
                    logging.exception('Falha ao verificar a fila de processamento')
                self.stop_event.wait(.25)
        self.thread = threading.Thread(target=loop, name='clareia-scheduler', daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
