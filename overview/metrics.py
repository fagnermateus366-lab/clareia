import os
import threading
import time

import httpx
import psutil

from .core import OLLAMA_URL, write_json,read_json


class Metrics:
    def __init__(self,path):
        self.path=path
        self.stop=threading.Event()
        self.started=time.monotonic()
        self.peak_rss=0
        self.peak_system=0
        self.peak_vram=0
        self.gpu_details=[]
        cfg=read_json(path.parent/'project.json',{}).get('config',{})
        self.cloud_only=cfg.get('roteiro_provedor')=='gemini' and cfg.get('gemini_projeto_completo',False)

    def sample(self):
        process=psutil.Process(os.getpid())
        while not self.stop.is_set():
            processes=[process]+process.children(recursive=True)
            rss=0
            for p in processes:
                try:
                    rss+=p.memory_info().rss
                except psutil.Error:
                    pass
            self.peak_rss=max(self.peak_rss,rss)
            self.peak_system=max(self.peak_system,psutil.virtual_memory().used)
            try:
                if self.cloud_only:
                    self.stop.wait(1)
                    continue
                models=httpx.get(OLLAMA_URL+"/api/ps",timeout=2).json().get("models",[])
                self.peak_vram=max(self.peak_vram,sum(x.get("size_vram",0) for x in models))
                if models:
                    self.gpu_details=models
            except (httpx.HTTPError,ValueError):
                pass
            self.stop.wait(1)

    def __enter__(self):
        self.thread=threading.Thread(target=self.sample,daemon=True)
        self.thread.start()
        return self

    def __exit__(self,*args):
        self.stop.set()
        self.thread.join(timeout=4)
        write_json(self.path,{"tempo_total_s":round(time.monotonic()-self.started,2),
                  "pico_rss_app_e_filhos_mb":round(self.peak_rss/2**20,1),
                  "pico_ram_sistema_mb":round(self.peak_system/2**20,1),
                  "pico_vram_alocada_ollama_mb":round(self.peak_vram/2**20,1),
                  "ollama_ps":self.gpu_details,
                  "metodo":"Amostras a cada 1 s. RSS inclui app e FFmpeg; Ollama é serviço separado. RAM do sistema inclui outros programas. VRAM corresponde à alocação informada por Ollama, não ao pico total da GPU."})
