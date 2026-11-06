from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from .voices import VoiceId, Delivery
from .narration_styles import ScriptTone
from .transitions import Transition
from .shotcraft_types import ShotRecipe, ShotArt, ShotEnergy, ShotFamily, ShotFinish, ShotFigureSelection
from .video_palettes import VideoPalette
from .three_options import ThreeOptions

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"
MODELS = ROOT / ".models"
OLLAMA_URL = os.environ.get("CLAREIA_OLLAMA_URL", "http://127.0.0.1:11435")
MODEL = os.environ.get("CLAREIA_MODEL", "qwen3:14b")
CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


class StageAI(BaseModel):
    ativa: bool = False
    provedor: Literal['local','gemini','openrouter','groq'] = 'local'
    modelo: str = Field(default='',max_length=160,pattern=r'^[a-zA-Z0-9_./:@+-]*$')


class ReelsMediaCue(BaseModel):
    arquivo: str = Field(min_length=1,max_length=200,pattern=r'^[^/\\]+$')
    cena: int = Field(ge=0,le=500)
    frase: int = Field(ge=0,le=1000)
    entrada_s: float = Field(default=0,ge=0,le=86400)
    saida_s: float | None = Field(default=None,gt=0,le=86400)
    ajuste: Literal['herdar','inteira','preencher','esticar'] = 'herdar'
    posicao_recorte: Literal['herdar','centro','esquerda','direita','superior','inferior'] = 'herdar'
    reiniciar: bool = False
    fim: Literal['repetir','segurar'] = 'repetir'
    transicao: Transition | Literal['herdar'] = 'herdar'

    @model_validator(mode='after')
    def trim(self):
        if self.saida_s is not None and self.saida_s<=self.entrada_s:
            raise ValueError('O fim do clipe precisa vir depois do início.')
        return self


class Settings(BaseModel):
    minutos: float = Field(default=3, gt=0)
    tom: ScriptTone = "didático"
    formato: Literal["16:9", "9:16"] = "16:9"
    tipo_video: Literal['video','shorts'] = 'video'
    tipo_roteiro: Literal['didatico','motivacional'] = 'didatico'
    publico_motivacional: str = Field(default='',max_length=250)
    legenda_shorts: Literal['amarelo','ciano','branca','vermelho','verde','roxo'] = 'amarelo'
    modelo_legenda: Literal['impacto','faixa_branca','caixa_escura','minimalista','documental','neon','editorial','compacta'] = 'impacto'
    filtro_reels: Literal['original','pb','pb_contraste','sepia','quente','frio','cinema','suave'] = 'original'
    efeito_legenda: Literal['destaque','montagem','maquina'] = 'destaque'
    posicao_legenda: Literal['inferior','superior','centro','alternada'] = 'inferior'
    legendas_grandes: bool | None = None
    legendas_rodape: Literal['auto','sim','nao'] = 'auto'
    fundo_legenda_rodape: Literal['escuro','transparente','claro','personalizado'] = 'escuro'
    cor_legenda_rodape: str = Field(default='#FFFFFF',pattern=r'^#[0-9a-fA-F]{6}$')
    cor_fundo_rodape: str = Field(default='#000000',pattern=r'^#[0-9a-fA-F]{6}$')
    modo_shorts: Literal['animacoes','fotos','clipes'] = 'animacoes'
    composicao_shorts: Literal['equilibrada','coluna'] = 'equilibrada'
    fotos_shorts: list[str] = Field(default_factory=list,max_length=100)
    midias_reels: list[str] = Field(default_factory=list,max_length=100)
    enquadramento_reels: Literal['inteira','preencher','esticar'] = 'inteira'
    posicao_recorte_reels: Literal['centro','esquerda','direita','superior','inferior'] = 'centro'
    continuar_clipes: bool = True
    trechos_reels: list[ReelsMediaCue] = Field(default_factory=list,max_length=100)
    transicao_midias_shorts: Transition = 'dissolver'
    duracao_transicao_midias: float = Field(default=.6,ge=.15,le=2)
    roteiro_pronto: bool = False
    voz: VoiceId = "pf_dora"
    voz_secundaria: VoiceId = 'pm_alex'
    estilo_locucao: Delivery = 'natural'
    animacao: Literal['ilustracoes','quadro','mao','recortes','tipografia','infografico','historia','historia_ilustrada','colagem_documental','shotcraft'] = 'ilustracoes'
    shotcraft_estilo: ShotArt = 'editorial'
    shotcraft_acabamento: ShotFinish = 'vidro_avancado'
    shotcraft_modelo: ShotFamily = 'auto'
    shotcraft_receita: ShotRecipe = 'auto'
    shotcraft_intensidade: ShotEnergy = 'equilibrada'
    shotcraft_selecao_figuras: ShotFigureSelection = 'tematico'
    shotcraft_orientacao: str = Field(default='',max_length=600)
    shotcraft_ia: StageAI = Field(default_factory=StageAI)
    three_options: ThreeOptions = Field(default_factory=ThreeOptions)
    colagem_buscar_figuras: bool = False
    movimento_figuras: Literal['tematico','suave','nenhum'] = 'tematico'
    destaques_animados: bool = True
    camera_dinamica: bool = True
    animar_elementos: bool = True
    imagem_estatica: bool = True
    transicao: Transition = 'padrao'
    duracao_transicao: float = Field(default=.6,ge=.15,le=2)
    aplicar_transicao: Literal['ambos','momentos','cenas'] = 'cenas'
    velocidade_mao: float = Field(default=.75, ge=.5, le=1.25)
    apresentadores: Literal[1, 2] = 1
    estilo: VideoPalette = 'oceano'
    imagem_fundo: str | None = Field(default=None,max_length=200)
    intensidade_fundo: float = Field(default=.28,ge=.05,le=.4)
    modo_visual: Literal["auto", "slide", "diagrama", "imagem_do_usuario"] = "auto"
    velocidade: float = Field(default=1.0, ge=0.75, le=1.3)
    roteiro_provedor: Literal['local', 'gemini', 'openrouter', 'groq'] = 'local'
    roteiro_modelo: str = Field(default='', max_length=160, pattern=r'^[a-zA-Z0-9_./:@+-]*$')
    fonte_ia_automatica: bool = False
    fonte_ia_provedor: Literal['roteiro','local','gemini','openrouter','groq'] = 'roteiro'
    fonte_ia_modelo: str = Field(default='',max_length=160,pattern=r'^[a-zA-Z0-9_./:@+-]*$')
    planejamento_ia: StageAI = Field(default_factory=StageAI)
    youtube_ia: StageAI = Field(default_factory=StageAI)
    gemini_projeto_completo: bool = False
    gemini_modelo_voz: Literal['gemini-3.8-flash-lite-tts','gemini-3.8-flash-tts','gemini-3.1-flash-tts-preview','gemini-2.5-flash-preview-tts','gemini-2.5-pro-preview-tts'] = 'gemini-3.8-flash-lite-tts'
    gemini_voz: str = Field(default='Kore',max_length=30,pattern=r'^[A-Za-z]+$')
    gemini_voz_secundaria: str = Field(default='Puck',max_length=30,pattern=r'^[A-Za-z]+$')
    publico: Literal['iniciante', 'intermediário'] = 'iniciante'
    objetivo_aprendizagem: str = Field(default='', max_length=250)
    ajustar_duracao: bool = True
    pesquisa_externa: bool = False
    retratos_autores: bool = False
    musica_fundo: str = Field(default='',max_length=80,pattern=r'^[a-z0-9-]*$')
    volume_musica_db: float = Field(default=-20,ge=-60,le=-14)
    reduzir_musica_na_fala: bool = True

    @model_validator(mode='after')
    def short_format(self):
        if self.tipo_video == 'shorts':
            self.formato = '9:16'
            if self.minutos > 3:
                raise ValueError('Reels / Shorts aceitam duração alvo de até 3 minutos. Escolha uma duração menor ou Vídeo comum.')
            if self.legendas_grandes and self.modo_shorts=='animacoes' and self.posicao_legenda in ('centro','alternada'):
                raise ValueError('Em animações, escolha legendas em cima ou embaixo para preservar o espaço dos desenhos. Centro e alternância estão disponíveis em Fotos em sequência.')
        return self

    @field_validator('aplicar_transicao')
    @classmethod
    def scene_transitions(cls,value):
        # Accept old projects/favorites, but a phrase or sticker change is not
        # a scene boundary. All animation styles use the same scene-only rule.
        return 'cenas'


class Scene(BaseModel):
    titulo: str = Field(min_length=1, max_length=100)
    narracao_ptbr: str = Field(min_length=5, max_length=3000)
    texto_na_tela: list[str] = Field(min_length=1, max_length=4)
    tipo_visual: Literal["slide", "diagrama", "imagem_do_usuario"] = "slide"
    prompt_visual: str = ""
    duracao_estimada: float = Field(default=20, gt=0)
    fontes: list[str] = Field(default_factory=list)
    apresentador: Literal[1, 2] = 1
    imagem: str | None = None
    imagens_cena: list[str] = Field(default_factory=list,max_length=5,description='Escolha manual de até cinco arquivos já existentes no projeto, em ordem. Na geração do roteiro, deixe vazio; nunca invente nomes de arquivos.')
    transicao_imagens: Literal['dissolver','nenhuma'] = 'dissolver'
    usar_imagem: bool = True
    fundo_cena: Literal['herdar','cor','imagem'] = 'herdar'
    estilo_cena: VideoPalette | Literal['herdar'] = 'herdar'
    imagem_fundo: str | None = Field(default=None,max_length=200,description='Escolha manual de imagem já adicionada ao projeto. Na geração do roteiro deixe vazio.')
    intensidade_fundo: float | None = Field(default=None,ge=.05,le=.4)
    etapa: Literal['introducao','explicacao','exemplo','autoavaliacao','conclusao','aula_curta'] = 'explicacao'
    pausa_reflexao_s: float = Field(default=0, ge=0, le=8)
    animacao: Literal['herdar','ilustracoes','quadro','mao','recortes','tipografia','infografico','historia','historia_ilustrada','colagem_documental','shotcraft'] = 'herdar'
    shotcraft_receita: ShotRecipe | Literal['herdar'] = 'herdar'
    shotcraft_figuras: str = Field(default='',max_length=600)
    distribuicao_figuras: Literal['tempo_igual','por_elemento'] = 'tempo_igual'
    three_options: ThreeOptions | None = Field(default=None,description='Ajustes manuais da galeria 3D. Na geração de roteiro deixe vazio.')
    figuras_colagem: str = Field(default='', max_length=1000)
    movimento_figuras: Literal['herdar','tematico','suave','nenhum'] = 'herdar'
    transicao: Transition | Literal['herdar'] = 'herdar'
    animar_elementos: bool | None = None
    duracao_transicao: float | None = Field(default=None,ge=.15,le=2)


class ScriptBatch(BaseModel):
    cenas: list[Scene] = Field(min_length=1)


def digest(*values):
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    import uuid
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    # Windows/OneDrive/antivírus podem manter o destino brevemente aberto sem
    # FILE_SHARE_DELETE. Repetir a troca preserva a gravação atômica.
    try:
        for attempt in range(20):
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if attempt==19:
                    raise
                time.sleep(min(.02*2**attempt,.25))
    finally:
        temp.unlink(missing_ok=True)


def project_dir(pid):
    if not pid or any(c not in "0123456789abcdef-" for c in pid):
        raise ValueError("Identificador de projeto inválido")
    path = PROJECTS / pid
    if not (path / "project.json").exists():
        raise FileNotFoundError("Projeto não encontrado")
    return path


def binary(name):
    override = os.environ.get("CLAREIA_" + name.upper())
    local = ROOT / "tools" / (name + (".exe" if os.name == "nt" else ""))
    if not override and local.exists():
        return str(local)
    found = override or shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        path = Path(os.environ["LOCALAPPDATA"]) / "Microsoft/WinGet/Links" / (name + ".exe")
        if path.exists():
            return str(path)
        path = Path(os.environ["LOCALAPPDATA"]) / "Programs/Ollama/ollama.exe"
        if name == "ollama" and path.exists():
            return str(path)
    if name == "ffmpeg":
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    raise RuntimeError(f"{name} não encontrado. Consulte o README.")


def run(args, **kwargs):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", creationflags=CREATE_FLAGS, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:] or result.stdout[-4000:])
    return result.stdout


def set_status(path, status, message, progress=0, **extra):
    write_json(path / "status.json", {"status": status, "mensagem": message,
               "progresso": progress, "atualizado": time.time(), **extra})


def worker_active(path):
    import psutil
    record=read_json(path/"worker.json",{})
    try:
        return abs(psutil.Process(record["pid"]).create_time()-record["created"])<.1
    except (psutil.Error,KeyError):
        return False


class ProcessingLock:
    """OS lock shared by the studio, its scheduler and CLI; released on exit/crash."""
    def __init__(self, target=None):
        self.target = target or ROOT / '.private' / 'processing.lock'
        self.file = None

    def acquire(self):
        self.target.parent.mkdir(parents=True, exist_ok=True)
        handle = self.target.open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                if handle.seek(0, 2) == 0:
                    handle.write(b'0'); handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self.file = handle
        return True

    def release(self):
        if self.file:
            self.file.close()
            self.file = None


class JobLock:
    def __init__(self,path,processing_lock=None):
        self.path=path
        self.processing_lock=processing_lock
        self.owns_processing_lock=processing_lock is None

    def __enter__(self):
        if self.owns_processing_lock:
            self.processing_lock=ProcessingLock()
            if not self.processing_lock.acquire():
                raise RuntimeError('Já há um projeto em processamento. Aguarde a conclusão.')
        try:
            return self._enter_project()
        except BaseException:
            if self.owns_processing_lock:self.processing_lock.release()
            raise

    def _enter_project(self):
        import psutil
        self.lock=self.path/"job.lock"
        try:
            self.fd=os.open(self.lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:
            if worker_active(self.path) or time.time()-self.lock.stat().st_mtime<3:
                raise RuntimeError("Este projeto já está em execução em outro processo.")
            self.lock.unlink()
            self.fd=os.open(self.lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        write_json(self.path/"worker.json",{"pid":os.getpid(),"created":psutil.Process().create_time()})
        return self

    def __exit__(self,*args):
        try:
            os.close(self.fd)
            self.lock.unlink(missing_ok=True)
            (self.path/"worker.json").unlink(missing_ok=True)
        finally:
            if self.owns_processing_lock:self.processing_lock.release()
