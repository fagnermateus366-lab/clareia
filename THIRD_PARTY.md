# Dependências, modelos e licenças

O código autoral do Clareia usa MIT (`LICENSE`). Isso não relicencia os modelos, executáveis, fontes e bibliotecas de terceiros. Este inventário identifica os componentes principais; metadados das distribuições instaladas em `.venv` são a referência para suas dependências transitivas.

| Componente | Licença / fonte |
|---|---|
| Qwen3 14B | [Apache-2.0, model card oficial](https://huggingface.co/Qwen/Qwen3-14B-GGUF) |
| Qwen 3.5 9B | [Apache-2.0, distribuição no Ollama](https://ollama.com/library/qwen3.5:9b) |
| Kokoro-82M e vozes | [Apache-2.0](https://huggingface.co/hexgrad/Kokoro-82M) |
| Piper (piper-tts 1.8.0) | [GPL-3.0, motor local](https://github.com/OHF-Voice/piper1-gpl) |
| Piper Cadu / Faber / Jeff pt-BR medium | [Model cards individuais CC0](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR); cópias locais em `.models/piper/` |
| kokoro-onnx | [MIT](https://github.com/thewh1teagle/kokoro-onnx) |
| edge-tts 7.3.1 | [LGPL-3.0; srt_composer.py sob MIT](https://github.com/rany2/edge-tts/blob/master/LICENSE). Biblioteca de acesso ao serviço online do Edge; sua licença não licencia o serviço Microsoft. |
| eSpeak NG | [GPL-3.0](https://github.com/espeak-ng/espeak-ng); fonemização local, instalado pelo pacote espeakng-loader |
| ONNX Runtime | [MIT](https://github.com/microsoft/onnxruntime) |
| Whisper small · ditado em português | [MIT, modelo original](https://github.com/openai/whisper); [conversão CTranslate2](https://huggingface.co/Systran/faster-whisper-small) |
| faster-whisper / CTranslate2 | [MIT](https://github.com/SYSTRAN/faster-whisper) / [MIT](https://github.com/OpenNMT/CTranslate2) |
| PyMuPDF/MuPDF | [AGPL-3.0 ou licença comercial](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) |
| RapidOCR e modelos PaddleOCR derivados | [Projeto e informações dos modelos](https://github.com/RapidAI/RapidOCR), Apache-2.0 |
| FFmpeg | [LGPL/GPL conforme configuração do build](https://ffmpeg.org/legal.html); o build local com libx264 requer considerar GPL |
| Ollama | [MIT](https://github.com/ollama/ollama); modelos têm licenças separadas |
| FastAPI, Uvicorn, python-docx, python-pptx, num2words | Projetos gratuitos com licenças indicadas nos respectivos pacotes instalados |
| Pillow | [Licença HPND/Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| Video ShotCraft · modelos e direção visual | [Apache-2.0, copyright 2026 Wei Yihao](https://github.com/Vincentwei1021/video-shotcraft/blob/43bd349a136651865ecfa6ea1cf012f6e957d304/LICENSE). Receitas e componentes selecionados adaptados em React/Remotion; originais, licença, atribuições e hashes em `third_party/video-shotcraft/`. Modificações em `NOTICE.md` e `SHOTCRAFT.md`. Não inclui áudio e capturas de produtos do original. |
| Remotion 4.0.538 / React 19.3.1 | [Licença própria do Remotion](https://www.remotion.dev/license) / [MIT do React](https://github.com/facebook/react/blob/main/LICENSE). Motor opcional isolado em `overview/shotcraft_renderer/`; dependências registradas no lockfile. |
| trafilatura | [Apache-2.0](https://github.com/adbar/trafilatura) |
| Playwright | [Apache-2.0](https://github.com/microsoft/playwright), usado nos testes |
| ReportLab | Biblioteca gratuita usada apenas para criar o PDF de teste |
| Segoe UI | Fonte já instalada no Windows; nenhum arquivo da fonte é redistribuído |

Os executáveis FFmpeg em `tools/` foram copiados da instalação desta máquina para uso local. Modelos e binários ficam fora do Git. Não foi produzido um instalador binário para redistribuição pública. Caso o app seja distribuído, as obrigações dos componentes GPL/AGPL e demais licenças precisam ser atendidas; a licença MIT do código autoral não substitui essas obrigações.

O modo padrão usa a API local do Ollama; as vozes e a montagem são locais. Ao escolher Gemini ou OpenRouter, trechos das fontes e do roteiro são enviados ao provedor selecionado, conforme explicado na interface. A pesquisa externa envia consultas aos buscadores e lê os sites encontrados. URLs são acessadas quando solicitadas e os pesos são baixados na instalação. O aplicativo não usa fontes para treinar modelos.

A imagem transparente da mão com marcador foi gerada com ImageGen para esta implementação, sem copiar um fotograma da referência. O arquivo integra o código em `overview/assets/mao-marcador.png`. Retratos reais vêm do Wikimedia Commons, com licenças e créditos registrados em cada projeto/exportação.

Os personagens articulados e cenários de `overview/cartoon.py` são ilustrações vetoriais autorais do aplicativo, sem reutilizar personagens ou quadros do vídeo de referência.

## Música opcional · Kevin MacLeod

As 32 gravações da biblioteca, incluindo 12 trilhas de terror e suspense, têm autoria de Kevin MacLeod (incompetech.com), licenciadas sob Creative Commons Attribution 4.0: https://creativecommons.org/licenses/by/4.0/. Títulos, ISRC, fontes oficiais, créditos e hashes constam em `overview/assets/music/catalog.json`. Os MP3 originais baixados ficam em `.models/music/tracks`; não são apresentados como obra própria do Clareia. Uso, redistribuição e adaptação exigem atribuição conforme a licença. Modificações nas mixagens: filtros, volume, emendas, fades e ducking; autoria da música continua do compositor. Lista e atribuição em `MUSICAS.md`.

## Clonagem de voz local opcional

Chatterbox Multilingual V3, da Resemble AI (código e pesos MIT), funciona em ambiente Python isolado. O modelo original foi restaurado após a versão especializada em português reduzir a fidelidade percebida pelo usuário. As revisões, licenças e dependências estão registradas em `VOZES-CLONADAS.md` e `.models/voice-cloning/`. O watermark Perth foi preservado. O Qwen3-TTS anteriormente instalado foi removido. O preparo de referências do VoiceStudio foi analisado como comparação; a implementação do Clareia e sua execução são independentes. Amostras pessoais permanecem em `.private/cloned-voices/`, e o motor opera com pesos locais.

## Twemoji · figuras ShotCraft

Twemoji graphics by Twitter, Inc. and other contributors, including jdecked/twemoji contributors. Source: https://github.com/jdecked/twemoji, revision `b6b55fef1e8636b540a6d016a4729ca8cdf2e60b`. Graphics licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Original license at `third_party/twemoji/LICENSE-GRAPHICS`. Selected SVGs are preserved under `overview/assets/shotcraft-figures/`; the manifest records source and hashes. Clareia adds composition, scale, lighting and shadows. Five local SVG drawings are original to Clareia. Exported videos receive `creditos-shotcraft.md` for attribution.
