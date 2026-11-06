"""Brazilian Portuguese phrasing for cloned narration, separate from approved text."""
from __future__ import annotations

import re
from num2words import num2words

VERSION = 'cloned-spoken-portuguese-v1'
_LABELS = r'(?:posições|itens|passos|etapas|cenas|capítulos|páginas|pontos|figuras|exemplos|números)'
_PAIR = re.compile(rf'(?P<label>\b{_LABELS}(?:\s+[^\W\d_]+){{0,3}}\s*)'
                   r'\(\s*(?P<a>\d{1,4})\s*[-‐‑‒–—]\s*(?P<b>\d{1,4})\s*\)', re.IGNORECASE)


def number_pairs(text):
    return [(num2words(int(m['a']),lang='pt_BR'),num2words(int(m['b']),lang='pt_BR'))
            for m in _PAIR.finditer(text) if int(m['b'])==int(m['a'])+1]


def check_pairs(text, words):
    from .speech import normalize
    from .speech_alignment import tokens
    from .speech_integrity import IncompleteNarration
    actual=tokens(normalize(' '.join(w['texto'] for w in words)))
    pairs=number_pairs(text)
    for a,b in pairs:
        required=tokens(a+' e '+b)
        if not any(actual[i:i+len(required)]==required for i in range(len(actual)-len(required)+1)):
            raise IncompleteNarration('A voz precisa dizer o par numérico completo: '+a+' e '+b+'. Tente gerar novamente.')
    return len(pairs)


def enabled(settings):
    from .runtime import gemini_only
    voices = [settings.voz]
    if settings.apresentadores == 2:
        voices.append(settings.voz_secundaria)
    return not gemini_only(settings) and any(v.startswith('clone_') for v in voices)


def writing_guide(settings):
    if not enabled(settings):
        return ''
    return ('\nESCRITA PARA NARRAÇÃO COM VOZ CLONADA: escreva como uma pessoa brasileira explicando o assunto em voz alta, '
            'com palavras usuais, voz ativa e uma ideia por período. Preserve os fatos e os termos técnicos necessários, '
            'explicando cada termo com palavras simples. Evite linguagem burocrática, inversões e frases com muitas orações. '
            'Ligue pensamentos relacionados sem uma sucessão de frases telegráficas. Pontue pelo sentido, nunca para encaixar a imagem. '
            'Conecte o convite de revisão à pergunta: "Tente responder com suas palavras: qual é a diferença?" '
            'A pausa para pensar ocorre só depois da pergunta completa. Escreva enumerações como se fala: '
            '"um e dois", "sete e oito"; intervalos maiores como "de um a cinco". Evite pares numéricos entre parênteses, '
            'siglas sem explicação, barras, travessões, reticências e aspas decorativas na narração. '
            'Não coloque SSML, rubricas ou instruções de emoção no texto falado. '
            'Títulos e pontos na tela podem conservar a escrita visual concisa.\n')


def prepare(text):
    # Keep the wording: only typography, optional punctuation and unambiguous
    # consecutive item pairs change in this synthesis-only representation.
    text = re.sub(r'''(?<!\w)['"“‘]([^\W_]+)['"”’](?!\w)''', r'\1', text)
    def enumeration(match):
        a,b = int(match['a']),int(match['b'])
        if b != a+1:
            return match[0]  # Do not invent the meaning of an arbitrary range.
        return match['label']+num2words(a,lang='pt_BR')+' e '+num2words(b,lang='pt_BR')
    text = _PAIR.sub(enumeration,text)
    invitation = re.compile(r'\b((?:Tente responder|Responda com|Pense um pouco|Agora reflita)[^.!?:\n]{0,55})[.:]\s+'
                            r'([^.!?\n]+\?)',re.IGNORECASE)
    def connect(match):
        if len(match[1].split()) > 8:
            return match[0]
        question = match[2]
        # Retain names/acronyms: only lower-case ordinary question openers.
        question = re.sub(r'^(Em|Qual|Quais|Como|Por|O|A|Você)\b',lambda m:m[0].lower(),question)
        return match[1]+': '+question
    text = invitation.sub(connect,text)
    text = re.sub(r'\b(Ao final (?:da|desta|dessa) (?:aula|explicação|história|conversa)|Neste caso|Nesse caso|Agora),\s+',
                  r'\1 ',text)
    return text
