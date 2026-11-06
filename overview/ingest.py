from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlparse

import pymupdf as fitz
import httpx

URL_HEADERS = {
    "User-Agent": "ClareiaLocal/0.1 (local personal document reader)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def extract_file(path: Path, assets: Path):
    ext = path.suffix.lower()
    blocks = []
    images = []
    if ext == ".pdf":
        with fitz.open(path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text(sort=True).strip()
                if not text:
                    from .ocr import recognize
                    import numpy as np
                    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False,colorspace=fitz.csRGB)
                    text=recognize(np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3))
                if text.strip():
                    blocks.append((f"{path.name} · página {i+1}", text))
                # Capas/páginas originais podem ilustrar as cenas sem geração de IA.
                image = assets / f"{path.stem[:30]}-p{i+1}.png"
                page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(image)
                images.append(image.name)
    elif ext == ".docx":
        from docx import Document
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        text += "\n" + "\n".join(" | ".join(c.text for c in row.cells) for t in doc.tables for row in t.rows)
        blocks.append((path.name, text))
    elif ext == ".pptx":
        from pptx import Presentation
        for i, slide in enumerate(Presentation(path).slides):
            text = "\n".join(s.text for s in slide.shapes if s.has_text_frame)
            blocks.append((f"{path.name} · slide {i+1}", text))
    elif ext in (".txt", ".md"):
        blocks.append((path.name, path.read_text(encoding="utf-8-sig")))
    elif ext in (".png", ".jpg", ".jpeg", ".webp"):
        from PIL import Image, ImageOps
        image = assets / (path.stem + ".png")
        source=ImageOps.exif_transpose(Image.open(path))
        source.convert('RGBA' if 'A' in source.getbands() or 'transparency' in source.info else 'RGB').save(image)
        images.append(image.name)
        from .ocr import recognize
        text=recognize(str(image))
        if text.strip():
            blocks.append((path.name, text))
        meta = identify_image_entity(image)
        if text.strip():
            ocr_tokens = [t for t in re.split(r'[-_.\s\d]+', text.casefold()) if len(t) >= 4][:12]
            meta["palavras_chave"].extend(ocr_tokens)
        from .core import write_json
        write_json(assets / f"{image.name}.meta.json", meta)
        if meta.get("identificacao"):
            blocks.append((f"{path.name} · {meta['identificacao']}", f"Imagem das fontes identificada: {meta['identificacao']}."))
    else:
        raise ValueError(f"Formato não aceito: {ext}")
    return blocks, images


def identify_image_entity(img_path: Path):
    """Extracts semantic keywords and uses Gemini Vision if available to recognize historical figures/topics."""
    meta = {"identificacao": "", "palavras_chave": []}
    stem_tokens = [t for t in re.split(r'[-_.\s\d]+', img_path.stem.casefold()) if len(t) >= 3]
    meta["palavras_chave"].extend(stem_tokens)

    try:
        from .providers import get_key, request
        key = get_key('gemini', required=False)
        if key:
            import base64, io
            from PIL import Image
            with Image.open(img_path) as im:
                thumb = im.copy()
                thumb.thumbnail((512, 512))
                buf = io.BytesIO()
                thumb.convert('RGB').save(buf, format='JPEG', quality=80)
                b64 = base64.b64encode(buf.getvalue()).decode()

            prompt = (
                "Identifique com exatidão quem ou o que aparece nesta imagem em português. "
                "Se for uma pessoa histórica/famosa, forneça seu nome completo (ex: Kurt Gödel). "
                "Se for um conceito, diagrama ou objeto, responda brevemente. "
                "Responda estritamente um JSON: {\"identificacao\": \"Nome da pessoa ou tema\", \"palavras_chave\": [\"termo1\", \"termo2\"]}"
            )
            from .runtime import gemini_only,current_settings
            model=current_settings().roteiro_modelo if gemini_only() else 'gemini-2.5-flash'
            if not re.fullmatch(r'[a-zA-Z0-9_.+-]+',model):raise ValueError('Modelo inválido')
            data = request('POST', f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                           headers={'x-goog-api-key': key},
                           json={'contents': [{'parts': [
                               {'inline_data': {'mime_type': 'image/jpeg', 'data': b64}},
                               {'text': prompt}
                           ]}],
                           'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 150, 'responseMimeType': 'application/json'}})
            candidates = data.get('candidates', [])
            if candidates:
                raw = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                import json
                cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip())
                parsed = json.loads(cleaned)
                if parsed.get('identificacao'):
                    meta['identificacao'] = parsed['identificacao']
                if parsed.get('palavras_chave'):
                    meta['palavras_chave'].extend([str(k).casefold() for k in parsed['palavras_chave']])
    except Exception:
        pass
    return meta


def extract_url(url):
    from trafilatura import extract
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Use um endereço http ou https")
    try:
        # A Wikimedia, entre outros sites, recusa identificadores genéricos
        # como python-httpx. Identifique o leitor sem imitar um navegador.
        with httpx.Client(follow_redirects=True, timeout=40, headers=URL_HEADERS) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > 20_000_000:
                        raise ValueError("Página maior que 20 MB; baixe e importe o documento.")
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        site = parsed.hostname
        if status in (401, 403):
            message = f"O site {site} bloqueou a leitura automática (HTTP {status}). Abra o link no navegador e cole o conteúdo em 'Ou cole um texto', ou envie um PDF da página."
        elif status == 404:
            message = f"A página não foi encontrada em {site} (HTTP 404). Confira o endereço do link."
        elif status == 429:
            message = f"O site {site} recebeu muitas requisições (HTTP 429). Aguarde alguns minutos e tente novamente."
        else:
            message = f"Não foi possível ler a página de {site} (HTTP {status}). Tente novamente mais tarde ou cole o texto da página."
        raise ValueError(message) from exc
    except httpx.TimeoutException as exc:
        raise ValueError(f"O site {parsed.hostname} demorou demais para responder. Tente novamente ou cole o texto da página.") from exc
    except httpx.RequestError as exc:
        raise ValueError(f"Não foi possível conectar a {parsed.hostname}. Confira a conexão e o endereço do link.") from exc
    text = extract(bytes(content), output_format="markdown", include_tables=True)
    if not text:
        raise ValueError("Não foi possível extrair texto desta página. Cole o texto manualmente.")
    return url, text


def ingest(path, files=(), text="", urls=()):
    assets = path / "assets"
    assets.mkdir(exist_ok=True)
    blocks, images = [], []
    for file in files:
        part, pics = extract_file(Path(file), assets)
        blocks.extend(part)
        images.extend(pics)
    if text.strip():
        blocks.append(("Texto enviado", text.strip()))
    for url in urls:
        if url.strip():
            blocks.append(extract_url(url.strip()))
    if not blocks or not any(t.strip() for _, t in blocks):
        if images:
            blocks.append(("Imagens das fontes", f"Coleção de {len(images)} imagem(ns) das fontes para composição e visualização no vídeo."))
        else:
            raise ValueError("Não foi encontrado texto nas fontes. Para imagens sem texto, use também o campo de descrição/texto.")
    sources = [{"id": f"F{i+1}", "origem": name, "texto": re.sub(r"[ \t]+", " ", body).strip()}
               for i, (name, body) in enumerate(blocks)]
    markdown = "\n\n".join(f"## [{s['id']}] {s['origem']}\n\n{s['texto']}" for s in sources)
    (path / "fontes.md").write_text(markdown, encoding="utf-8")
    from .core import write_json, read_json
    imagens_meta = {}
    for img_name in images:
        meta_file = assets / f"{img_name}.meta.json"
        if meta_file.is_file():
            imagens_meta[img_name] = read_json(meta_file, {})
        else:
            tokens = [t for t in re.split(r'[-_.\s\d]+', Path(img_name).stem.casefold()) if len(t) >= 3]
            imagens_meta[img_name] = {"identificacao": "", "palavras_chave": tokens}
    write_json(path / "sources.json", {"fontes": sources, "imagens": images, "imagens_meta": imagens_meta})
    from .ocr import release
    release()
    return sources, images
