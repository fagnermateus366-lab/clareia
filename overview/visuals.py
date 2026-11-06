from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .core import digest

from .video_palettes import PALETTES


def font(size, bold=False):
    paths = ([Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("segoeuib.ttf" if bold else "segoeui.ttf")]
             if os.name == "nt" else [Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")])
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def wrap(draw, text, face, width):
    lines = []
    line = ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if draw.textlength(candidate, font=face) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + ([line] if line else [])


def fit(draw, text, width, max_lines, size, bold=False):
    while size > 22:
        face = font(size, bold)
        lines = wrap(draw, text, face, width)
        if len(lines) <= max_lines:
            return face, lines, size
        size -= 2
    raise ValueError("Texto demais para o slide. Encurte os pontos na revisão do roteiro.")


def draw_lines(draw, xy, lines, face, size, color):
    x,y = xy
    for line in lines:
        draw.text((x,y), line, font=face, fill=color)
        y += int(size*1.32)
    return y


import re


def match_contextual_image(scene, images, path, modo_visual="auto", index=0):
    """Context-aware image selection: images only appear when directly relevant to scene."""
    if scene.get("usar_imagem") is False:return None
    selected = scene.get("imagem")
    if selected:
        return selected
    if not images:
        return None

    use_explicit = (scene.get("tipo_visual") == "imagem_do_usuario" or modo_visual == "imagem_do_usuario")

    sources_meta = {}
    research_data = {}
    if path:
        from .core import read_json
        sources_data = read_json(path / "sources.json", {})
        sources_meta = sources_data.get("imagens_meta", {})
        research_data = read_json(path / "pesquisa.json", {})

    import unicodedata

    def strip_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFKD', str(s).casefold()) if not unicodedata.combining(c))

    raw_corpus = (
        (scene.get("titulo") or "") + " " +
        (scene.get("narracao_ptbr") or "") + " " +
        " ".join(scene.get("texto_na_tela") or [])
    )
    text_corpus = strip_accents(raw_corpus)

    STOP_WORDS = {
        "imagem", "image", "foto", "photo", "figura", "fig", "screenshot", "print",
        "slide", "pagina", "page", "doc", "arquivo", "img", "originais", "fonte",
        "fontes", "novo", "video", "download", "documento", "texto", "tela",
        "png", "jpg", "jpeg", "webp", "pdf", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    }

    best_match = None
    best_score = 0

    for img in images:
        score = 0
        stem = strip_accents(Path(img).stem)
        tokens = [t for t in re.split(r'[-_.\s\d]+', stem) if len(t) >= 3 and t not in STOP_WORDS]
        for token in tokens:
            if token in text_corpus:
                score += 4

        meta = sources_meta.get(img, {})
        ident = strip_accents(meta.get("identificacao") or "")
        if ident:
            ident_words = [w for w in re.split(r'[-_.\s\d]+', ident) if len(w) >= 3 and w not in STOP_WORDS]
            for w in ident_words:
                if w in text_corpus:
                    score += 6

        for kw in meta.get("palavras_chave", []):
            kw_clean = strip_accents(kw)
            if kw_clean and len(kw_clean) >= 3 and kw_clean not in STOP_WORDS:
                if kw_clean in text_corpus:
                    score += 5

        for r in research_data.get("retratos", []):
            if r.get("arquivo") == img:
                person = strip_accents(r.get("pessoa") or "")
                if person and person in text_corpus:
                    score += 10

        if score > best_score:
            best_score = score
            best_match = img

    if best_score > 0:
        return best_match

    if use_explicit:
        return images[index % len(images)]

    return None


def slide(scene, settings, path, index, total, images):
    from .video_backgrounds import selection,identity as background_identity,canvas as background_canvas
    selected_image = match_contextual_image(scene, images, path, settings.modo_visual, index)
    if (scene["tipo_visual"] == "imagem_do_usuario" or settings.modo_visual == "imagem_do_usuario") and not images:
        raise ValueError("Este modo precisa de uma imagem ou página de PDF na fonte. Selecione Slides para fontes só de texto.")
    asset_hash = ""
    if selected_image:
        target = (path / "assets" / selected_image).resolve()
        if target.parent != (path / "assets").resolve() or not target.is_file():
            raise ValueError("Imagem não pertence ao projeto")
        asset_hash = digest(target.read_bytes().hex())
    key = digest("slide-v4", scene["titulo"], scene["texto_na_tela"], scene["tipo_visual"], settings.estilo,
                 settings.formato, index, total, selected_image, asset_hash, scene.get("fontes"))
    background_key=background_identity(scene,settings,path)
    if background_key:key=digest(key,'video-background-v1',background_key)
    out = path / "cache/visuais" / (key + ".png")
    if out.exists():
        return out, key
    out.parent.mkdir(parents=True, exist_ok=True)
    w,h = (1920,1080) if settings.formato == "16:9" else (1080,1920)
    bg, card, fg, accent, muted = PALETTES[selection(scene,settings)[0]]
    image = background_canvas(scene,settings,path,(w,h),bg)
    draw = ImageDraw.Draw(image)
    margin = 100 if w>h else 72
    draw.rounded_rectangle((margin,70,margin+40,110), radius=12, fill=accent)
    draw.text((margin+58,70), "CLAREIA  /  ESTÚDIO LOCAL", font=font(27,True), fill=muted)
    draw.text((w-margin-160,70), f"{index+1:02} / {total:02}", font=font(27), fill=muted)
    face, lines, size = fit(draw, scene["titulo"], w-margin*2, 2 if w>h else 4, 76 if w>h else 70, True)
    title_end = draw_lines(draw, (margin,175 if w>h else 210), lines, face, size, fg)
    content_top = max(390 if w>h else 620, title_end+45)
    bottom = h-255
    points = scene["texto_na_tela"]
    is_diagram = scene["tipo_visual"] == "diagrama" and not selected_image
    if is_diagram and w>h:
        n=len(points)
        gap=30
        cw=(w-2*margin-gap*(n-1))/n
        for i, point in enumerate(points):
            x=margin+i*(cw+gap)
            draw.rounded_rectangle((x,content_top,x+cw,bottom),28,fill=card)
            draw.text((x+30,content_top+25), f"0{i+1}",font=font(43,True),fill=accent)
            face, lines, size = fit(draw,point,cw-60,5,42)
            draw_lines(draw,(x+30,content_top+105),lines,face,size,fg)
            if i<n-1:
                draw.text((x+cw+3,(content_top+bottom)/2-20),"›",font=font(40),fill=accent)
    else:
        right_image = selected_image and w>h
        content_w = (w-2*margin)*.51 if right_image else w-2*margin
        gap=22
        ch=(bottom-content_top-gap*(len(points)-1))/len(points)
        for i, point in enumerate(points):
            y=content_top+i*(ch+gap)
            draw.rounded_rectangle((margin,y,margin+content_w,y+ch),22,fill=card)
            text_x=margin+65
            if is_diagram:
                draw.text((margin+24,y+28),f"{i+1:02}",font=font(31,True),fill=accent)
                text_x=margin+90
                if i<len(points)-1:
                    draw.text((margin+content_w/2,y+ch-5),"↓",font=font(30),fill=accent)
            else:
                draw.ellipse((margin+24,y+30,margin+40,y+46),fill=accent)
            face, lines, size = fit(draw,point,content_w-(text_x-margin)-35,3,39 if w>h else 45)
            draw_lines(draw,(text_x,y+22),lines,face,size,fg)
        if right_image:
            pic=Image.open(target).convert("RGB")
            box=(int(w*.57),content_top,w-margin,bottom)
            pw,ph=box[2]-box[0],int(box[3]-box[1])
            pic=ImageOps.contain(pic,(pw,ph))
            image.paste(pic,(box[0]+(pw-pic.width)//2,int(box[1])+(ph-pic.height)//2))
        elif selected_image:
            # No retrato, a imagem ocupa um fundo leve; texto mantém área reservada.
            pic=ImageOps.contain(Image.open(target).convert("RGB"),(250,250))
            image.paste(pic,(w-margin-pic.width,330))
    refs="FONTES  " + " · ".join(scene.get("fontes",[]))
    draw.text((margin,h-190),refs,font=font(22),fill=muted)
    draw.rounded_rectangle((margin,h-145,w-margin,h-139),radius=3,fill=card)
    draw.rounded_rectangle((margin,h-145,margin+(w-2*margin)*(index+1)/total,h-139),radius=3,fill=accent)
    image.save(out)
    return out,key
