from __future__ import annotations

import math
import json
import os
from pathlib import Path
import subprocess
import time
import soundfile as sf

from .core import CREATE_FLAGS, Scene, Settings, binary, digest, read_json, run, set_status, write_json
from . import speech
from .storyboard import plan, timed
from .motion import Animator
from .runtime import using_settings

FPS = 24


class Paused(Exception):
    pass


def verify_duration(path, expected):
    """Check both encoded streams before a clip/export is marked complete."""
    result = json.loads(run([binary('ffprobe'), '-v', 'error', '-show_entries',
                             'stream=codec_type,duration', '-of', 'json', path], timeout=30))
    durations = {s['codec_type']: float(s.get('duration', 0)) for s in result['streams']
                 if s['codec_type'] in ('audio', 'video')}
    if any(not math.isfinite(durations.get(kind, 0)) or durations.get(kind, 0) < expected-2/FPS
           for kind in ('audio', 'video')):
        raise ValueError('O arquivo de vídeo não preservou toda a duração da narração. '
                         'A exportação incompleta não será marcada como concluída.')
    return durations


def timestamp(seconds, ass=False):
    n = round(seconds*(100 if ass else 1000))
    scale=100 if ass else 1000
    h,n=divmod(n,3600*scale)
    m,n=divmod(n,60*scale)
    s,f=divmod(n,scale)
    return f"{h}:{m:02}:{s:02}.{f:02}" if ass else f"{h:02}:{m:02}:{s:02},{f:03}"


def subtitle_files(cues, srt, ass, portrait=False, *, words=None, caption_style='amarelo',caption_effect='destaque',caption_position='inferior',caption_preset='impacto',footer_background='escuro',footer_text='#FFFFFF',footer_color='#000000'):
    if words is not None:
        from .short_captions import write
        return write(words,srt,ass,caption_style,effect=caption_effect,position=caption_position,preset=caption_preset)
    srt.write_text("\n\n".join(f"{i+1}\n{timestamp(c['inicio'])} --> {timestamp(c['fim'])}\n{c['texto']}" for i,c in enumerate(cues))+"\n",encoding="utf-8")
    w,h=(1080,1920) if portrait else (1920,1080)
    def ass_color(value,alpha='00'):
        return '&H'+alpha+value[5:7]+value[3:5]+value[1:3]
    color=ass_color(footer_text);border=3;outline='1';back='&H80000000';edge='&H00151616'
    if footer_background=='transparente':border=1;outline='1.5';back='&HFF000000'
    elif footer_background=='claro':back='&H20F5F5F5';edge='&H00F5F5F5';color='&H00222222' if footer_text=='#FFFFFF' else color
    elif footer_background=='personalizado':back=ass_color(footer_color,'40');edge=ass_color(footer_color)
    header=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Segoe UI,38,{color},{color},{edge},{back},0,0,0,0,100,100,0,0,{border},{outline},0,2,85,85,30,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[]
    for c in cues:
        safe=c["texto"].replace("\\","/").replace("{","(").replace("}",")").replace("\n"," ")
        lines.append(f"Dialogue: 0,{timestamp(c['inicio'],True)},{timestamp(c['fim'],True)},Default,,0,0,0,,{safe}")
    ass.write_text(header+"\n".join(lines),encoding="utf-8-sig")


def ffmpeg_filter_path(path):
    # Caminhos absolutos ficam nos argumentos; filtros usam arquivos relativos simples.
    return str(path).replace("\\","/").replace(":","\\:").replace("'","\\'")


def encode_options(codec):
    if codec=="h264_amf":
        return ["-c:v",codec,"-quality","speed","-rc","cqp","-qp_i","23","-qp_p","25"]
    return ["-c:v","libx264","-preset","veryfast","-crf","23","-threads","6"]


def choose_encoder():
    forced=os.environ.get("CLAREIA_ENCODER","auto")
    if forced=="libx264":
        return "libx264"
    if forced not in ("auto","h264_amf"):
        raise ValueError("CLAREIA_ENCODER deve ser auto, h264_amf ou libx264")
    if os.name=="nt":
        try:
            run([binary("ffmpeg"),"-v","error","-f","lavfi","-i","color=s=320x180:r=24:d=0.2",*encode_options("h264_amf"),"-f","null","-"],timeout=25)
            return "h264_amf"
        except RuntimeError:
            pass
    return "libx264"


def execute(args, cwd, cancel):
    with open(cwd / "ffmpeg.log","w",encoding="utf-8") as log:
        proc=subprocess.Popen([str(x) for x in args],cwd=cwd,stdout=subprocess.DEVNULL,stderr=log,creationflags=CREATE_FLAGS)
        try:
            while proc.poll() is None:
                if cancel.exists():
                    proc.terminate()
                    proc.wait(timeout=10)
                    raise Paused("Renderização pausada; cenas prontas preservadas.")
                time.sleep(.3)
            if proc.returncode:
                raise RuntimeError((cwd / "ffmpeg.log").read_text(encoding="utf-8",errors="replace")[-4000:])
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def animate(args, cwd, cancel, animator, duration, progress=None):
    """Bounded-memory frame pipe with the same cancellation/error contract as execute."""
    with open(cwd/'ffmpeg.log','w',encoding='utf-8') as log:
        proc=subprocess.Popen([str(x) for x in args],cwd=cwd,stdin=subprocess.PIPE,
                              stdout=subprocess.DEVNULL,stderr=log,creationflags=CREATE_FLAGS)
        try:
            for frame in range(round(duration*FPS)):
                if cancel.exists():
                    raise Paused()
                proc.stdin.write(animator.frame(frame/FPS).tobytes())
                if progress and frame%(FPS*3)==0:
                    progress(frame/FPS)
            proc.stdin.close()
            while proc.poll() is None:
                if cancel.exists():
                    raise Paused()
                time.sleep(.1)
            if proc.returncode:
                raise RuntimeError((cwd/'ffmpeg.log').read_text(encoding='utf-8',errors='replace')[-4000:])
        except BrokenPipeError:
            raise RuntimeError((cwd/'ffmpeg.log').read_text(encoding='utf-8',errors='replace')[-4000:])
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            if not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except BrokenPipeError:
                    pass


@using_settings
def render_project(path, settings: Settings, callback=None, pause_after=None, *, only_scene=None, pause_file=None):
    start=time.monotonic()
    from .production_time import begin_render,finish_render
    begin_render(path)
    if settings.musica_fundo:
        from .music import ensure_track
        ensure_track(settings.musica_fundo)
    scenes=[Scene.model_validate(s).model_dump() for s in read_json(path/"script.json")]
    from .video_backgrounds import validate as validate_backgrounds
    validate_backgrounds(scenes,settings,path)
    from .short_video import animator_for,is_short
    all_scenes=scenes
    original_total=len(scenes)
    if only_scene is not None and not 0<=only_scene<len(scenes):raise ValueError('Cena não encontrada.')
    if settings.pesquisa_externa:
        research=read_json(path/'pesquisa.json')
        if not research:raise ValueError('Gere o roteiro com a checagem externa ativada antes de renderizar.')
        research['desatualizada']=research.get('roteiro_hash')!=digest([s['narracao_ptbr'] for s in scenes])
        from .research import write_report
        write_report(path,research)
    if only_scene is not None:scenes=[all_scenes[only_scene]]
    images=read_json(path/"sources.json")["imagens"]
    photos=is_short(settings) and settings.modo_shorts in ('fotos','clipes')
    media_playback=None
    if photos:
        from .short_photos import gallery_board
        from .reels_media import validate
        validate(settings,path,all_scenes)
        from .reels_media import MediaPlayback
        media_playback=MediaPlayback()
    cache=path/"cache/video"
    cache.mkdir(parents=True,exist_ok=True)
    cancel=pause_file or path/"pause.request"
    cancel.unlink(missing_ok=True)
    encoder=choose_encoder()
    completed=[]
    offset=0
    cues=[]
    all_words=[]
    reused=0
    visual_timeline=[]
    speech.release()
    from .llm import unload
    animator=None
    review_index=None;review_scene=None
    try:
        boards=[]
        for i,scene in enumerate(scenes):
            if cancel.exists():
                raise Paused()
            review_index=only_scene if only_scene is not None else i;review_scene=scene
            set_status(path,'renderizando',f'Planejando ilustrações da cena {review_index+1}/{original_total}',.05*i/len(scenes),cena=review_index+1,total=original_total)
            selected=scene.get('animacao','herdar')
            effective=settings.animacao if selected=='herdar' else selected
            board=gallery_board(scene) if photos else plan(scene,path,story=effective in ('historia','historia_ilustrada'),collage=effective=='colagem_documental')[0]
            boards.append(board)
        from .shotcraft_figures import apply as apply_art
        from .shotcraft import enabled as shotcraft_enabled
        from .speech import phrases
        art_history=[]
        for i,(scene,board) in enumerate(zip(scenes,boards)):
            review_index=only_scene if only_scene is not None else i;review_scene=scene
            if not photos and shotcraft_enabled(scene,settings):
                apply_art(board,phrases(scene['narracao_ptbr']),scene,settings=settings,strict=True,history=art_history,
                          photo=bool((scene.get('imagem') or scene.get('imagens_cena')) and scene.get('usar_imagem',True)))
            from .scene_diagnostics import clear as clear_review
            clear_review(path,{review_index})
        unload()
        context=None
        if only_scene is not None and only_scene>0:
            previous=all_scenes[only_scene-1]
            review_index=only_scene-1;review_scene=previous
            selected=previous.get('animacao','herdar');effective=settings.animacao if selected=='herdar' else selected
            previous_board=gallery_board(previous) if photos else plan(previous,path,story=effective in ('historia','historia_ilustrada'),collage=effective=='colagem_documental')[0]
            context=(previous,previous_board)
        from .collage_assets import prepare_project
        if not photos:prepare_project(path,([context[0]] if context else [])+scenes,([context[1]] if context else [])+boards,settings,cancel)
        with speech.TTS_LOCK:
            previous_visual=None;previous_collage=None
            if photos and settings.continuar_clipes and only_scene is not None and only_scene>1:
                # A scene preview must seek to the same clip position as a full
                # render. Reuse cached narration; only the preceding timing is
                # prepared here, without rendering earlier frames.
                from .timeline import synchronize
                for j,prior in enumerate(all_scenes[:only_scene-1]):
                    set_status(path,'renderizando',f'Preparando continuidade das mídias · cena {j+1}/{only_scene}',.02)
                    if cancel.exists():raise Paused()
                    prior_audio,prior_meta=speech.scene_audio(prior,settings,path)
                    prior_audio,_,prior_beats=synchronize(prior,settings,path,gallery_board(prior),prior_audio,prior_meta,False)
                    prior_beats[-1]['fim']=math.ceil(sf.info(prior_audio).duration*FPS)/FPS
                    prior_animator=animator_for(prior,settings,j,original_total,prior_beats,path,images,playback=media_playback)
                    prior_animator.close()
            if context:
                from .timeline import synchronize
                previous,previous_board=context
                context_audio,context_meta=speech.scene_audio(previous,settings,path)
                _,context_meta,context_beats=synchronize(previous,settings,path,previous_board,context_audio,context_meta,not photos and only_scene>1)
                context_duration=math.ceil(context_meta['duracao']*FPS)/FPS
                context_beats[-1]['fim']=context_duration
                context_animator=animator_for(previous,settings,only_scene-1,original_total,context_beats,path,images,playback=media_playback)
                try:
                    previous_visual=context_animator._frame_raw(context_duration-.001)
                    if context_animator.style=='colagem_documental':previous_collage=context_animator.story.snapshot(context_duration-.001,len(context_beats)-1)
                finally:
                    if hasattr(context_animator,'close'):context_animator.close()
            for i,scene in enumerate(scenes):
                if cancel.exists():
                    raise Paused()
                review_index=only_scene if only_scene is not None else i;review_scene=scene
                def update(message,within=0):
                    elapsed=time.monotonic()-start
                    progress=.05+.9*(i+within)/len(scenes)
                    set_status(path,"renderizando",message,progress,cena=i+1,total=len(scenes),
                               decorrido_s=round(elapsed,1),eta_s=round(elapsed/progress*(1-progress)) if i or within else None)
                    if callback:
                        callback(message,progress)
                update(f"Cena {i+1}/{len(scenes)} · narração")
                audio,meta=speech.scene_audio(scene,settings,path)
                from .timeline import synchronize
                audio,meta,beats=synchronize(scene,settings,path,boards[i],audio,meta,not photos and previous_visual is not None)
                # The waveform, rather than a target length or stale metadata,
                # determines how long the encoded scene must remain on screen.
                duration=math.ceil(sf.info(audio).duration*FPS)/FPS
                beats[-1]['fim']=duration
                animator=animator_for(scene,settings,only_scene if only_scene is not None else i,original_total,beats,path,images,playback=media_playback)
                words=None
                from .caption_presentation import large_enabled
                if is_short(settings) and large_enabled(settings):
                    update(f'Cena {i+1}/{len(scenes)} · sincronizando legendas grandes',.1)
                    from .short_captions import timed_words
                    words=timed_words(scene,path,audio,meta)
                if previous_visual is not None:animator.set_previous(previous_visual,previous_collage)
                visual_key=animator.key
                visual_timeline.append({'cena':i+1,'inicio':offset,'momentos':beats})
                if getattr(animator,'image_cues',None):visual_timeline[-1]['imagens']=animator.image_cues
                if photos:
                    visual_timeline[-1]['midias']=[{'arquivo':cue.arquivo,'inicio':start,'posicao_reproducao_s':animator.playheads[j],
                        'enquadramento':settings.enquadramento_reels if cue.ajuste=='herdar' else cue.ajuste}
                        for j,(start,cue) in enumerate(animator.slots)]
                key=digest("video-motion-v1",visual_key,meta["hash"],settings.formato,encoder)
                from .caption_presentation import identity as caption_identity,files as caption_files
                if caption_identity(settings):key=digest(key,'caption-controls-v1',caption_identity(settings))
                if words is not None:
                    from .short_captions import VERSION as CAPTIONS_VERSION
                    key=digest(key,CAPTIONS_VERSION,words,settings.legenda_shorts,settings.efeito_legenda,settings.posicao_legenda,settings.modelo_legenda)
                clip=cache/(key+".mp4")
                marker=cache/(key+".json")
                saved = read_json(marker, {})
                reusable = (clip.exists() and saved.get('bytes') == clip.stat().st_size
                            and abs(saved.get('duracao', 0)-duration) < 1/FPS)
                if reusable:
                    try:
                        verify_duration(clip, duration)
                    except (ValueError, RuntimeError):
                        reusable = False
                if reusable:
                    reused+=1
                else:
                    update(f"Cena {i+1}/{len(scenes)} · ilustrações e legendas",.15)
                    caption_paths=caption_files(meta['legendas'],words,settings,cache/(key+'.srt'),cache/(key+'.ass'))
                    w,h=(1920,1080) if settings.formato=="16:9" else (1080,1920)
                    filters=','.join([*(f'ass={p.name}' for p in caption_paths),'format=yuv420p'])
                    temp=cache/(key+".partial.mp4")
                    args=[binary("ffmpeg"),"-y","-v","warning","-filter_threads","2","-f","rawvideo","-pixel_format","rgb24",
                          "-video_size",f'{w}x{h}',"-framerate",FPS,"-i","pipe:0",
                          "-i",audio,"-vf",filters,"-af",f"apad,atrim=duration={duration:.6f}","-t",f"{duration:.6f}",
                          *encode_options(encoder),"-pix_fmt","yuv420p","-r",FPS,"-c:a","aac","-b:a","160k","-ar","48000",
                          "-video_track_timescale","24000","-movflags","+faststart",temp]
                    try:
                        animate(args,cache,cancel,animator,duration,
                                lambda seconds:update(f'Cena {i+1}/{len(scenes)} · ilustrações animadas · {seconds:.0f}/{duration:.0f} s',.15+.85*min(1,seconds/duration)))
                    except RuntimeError:
                        if encoder=="libx264":
                            raise
                        args2=args[:]
                        idx=args2.index("-c:v")
                        end=args2.index("-pix_fmt",idx)
                        args2[idx:end]=encode_options("libx264")
                        animate(args2,cache,cancel,animator,duration)
                    verify_duration(temp, duration)
                    os.replace(temp,clip)
                    write_json(marker,{"duracao":duration,"bytes":clip.stat().st_size,"visual":visual_key,"audio":meta["hash"]})
                completed.append(clip)
                previous_visual=animator._frame_raw(duration-.001)
                previous_collage=animator.story.snapshot(duration-.001,len(beats)-1) if animator.style=='colagem_documental' else None
                if hasattr(animator,'close'):animator.close()
                for cue in meta["legendas"]:
                    cues.append({**cue,"inicio":cue["inicio"]+offset,"fim":cue["fim"]+offset})
                if words is not None:
                    all_words.extend({**word,'inicio':word['inicio']+offset,'fim':word['fim']+offset} for word in words)
                offset+=duration
                write_json(path/"checkpoint.json",{"concluidas":i+1,"total":len(scenes),"segundos":offset,
                           "clipes":[x.name for x in completed],"cache_reutilizado":reused})
                update(f"Cena {i+1}/{len(scenes)} concluída",1)
                if pause_after and i+1>=pause_after:
                    raise Paused("Pausa de teste após checkpoint")
        speech.release()
        set_status(path,"renderizando","Montando MP4 final",.98)
        export=path/"export"
        export.mkdir(exist_ok=True)
        listing=cache/"concat.txt"
        listing.write_text("\n".join("file '"+p.name+"'" for p in completed),encoding="utf-8")
        temporary=export/"video.partial.mp4"
        execute([binary("ffmpeg"),"-y","-v","warning","-f","concat","-safe","0","-i",listing,"-c","copy","-movflags","+faststart",temporary],cache,cancel)
        music_report=None
        if settings.musica_fundo:
            from .music import mix_video,credit_text
            set_status(path,'renderizando','Equilibrando música de fundo e narração',.99)
            mixed=export/'video.music.partial.mp4'
            music_report=mix_video(temporary,mixed,settings,cache,cancel)
            os.replace(mixed,temporary)
            (export/'creditos-musica.md').write_text('# Créditos da música\n\nCopie os créditos abaixo para a descrição ou créditos públicos do vídeo.\n\n'+credit_text(settings.musica_fundo),encoding='utf-8')
        else:(export/'creditos-musica.md').unlink(missing_ok=True)
        verified_streams = verify_duration(temporary, offset)
        os.replace(temporary,export/"video.mp4")
        from .caption_presentation import files as caption_files
        caption_files(cues,all_words if is_short(settings) else None,settings,export/'legendas.srt',export/'legendas.ass')
        write_json(export/'storyboard.json',visual_timeline)
        from .shotcraft_figures import credits as shotcraft_credits
        art_credits=shotcraft_credits([b for b in boards if any('receita' in m for m in b['momentos'])])
        if art_credits:(export/'creditos-shotcraft.md').write_text(art_credits,encoding='utf-8')
        else:(export/'creditos-shotcraft.md').unlink(missing_ok=True)
        markdown="# "+read_json(path/"project.json")["titulo"]+"\n\n"
        for i,scene in enumerate(scenes):
            markdown+=f"## Cena {(only_scene if only_scene is not None else i)+1} · {scene['titulo']}\n\n{scene['narracao_ptbr']}\n\nTela: " + " · ".join(scene["texto_na_tela"]) + "\n\nFontes: " + ", ".join(scene["fontes"])+"\n\n"
        (export/"roteiro.md").write_text(markdown,encoding="utf-8")
        result={"duracao_s":offset,"tempo_render_s":round(time.monotonic()-start,2),"cenas":len(scenes),
                'tipo_video':settings.tipo_video,'formato':settings.formato,
                "momentos_visuais":sum(len(b['momentos']) for b in boards),"animacao":"narrativa-v1",
                "cenas_reutilizadas":reused,"encoder_solicitado":encoder,"bytes":(export/"video.mp4").stat().st_size,
                "duracoes_verificadas": verified_streams}
        from .runtime import local_model
        timing=read_json(path/'script-timing.json',{})
        teaching_record=read_json(path/('plano-motivacional.json' if settings.tipo_roteiro=='motivacional' else 'plano-didatico.json'),{}) or {}
        result.update(modelo_roteiro=timing.get('modelo') or teaching_record.get('modelo') or (local_model(settings) if settings.roteiro_provedor=='local' else settings.roteiro_modelo),
                      provedor_roteiro=timing.get('provedor') or teaching_record.get('provedor') or settings.roteiro_provedor,
                      concluido_em=time.time())
        result['tempos']=finish_render(path)
        if is_short(settings):
            from .short_video import verify_export
            try:result['shorts']=verify_export(path,settings)
            except ValueError as exc:result['aviso_shorts']=str(exc)
        if music_report:result['musica']=music_report
        write_json(path/"render-report.json",result)
        label='Shorts pronto' if is_short(settings) and not result.get('aviso_shorts') else 'Vídeo pronto'
        set_status(path,"concluido",f"{label} · {offset/60:.1f} minutos"+(f" · {result['aviso_shorts']}" if result.get('aviso_shorts') else ''),1,**result)
        return result
    except Paused:
        set_status(path,"pausado","Pausado. Clique em retomar para aproveitar as cenas prontas.",len(completed)/len(scenes))
        return {"pausado":True,"cenas":len(completed)}
    except Exception as exc:
        from .shotcraft_figures import ArtDirectionError
        if isinstance(exc,ArtDirectionError) and review_scene is not None:
            from .scene_diagnostics import record
            record(path,review_index,review_scene,settings,exc)
            exc.args=(f'Cena {review_index+1} · {review_scene["titulo"]}: {exc}',)
        set_status(path,"erro",str(exc)[-800:])
        raise
    finally:
        if animator is not None and hasattr(animator,'close'):animator.close()
        speech.release()
        unload()
