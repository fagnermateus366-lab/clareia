"""Extractive on-screen quotations: recipe instructions are never narration."""
import re
import unicodedata

STOP={'a','o','as','os','de','da','do','das','dos','e','em','na','no','nas','nos','que','se','um','uma','para','por','com','ao','ou','sua','seu','voce','isso','esse','essa'}
def tokens(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',str(text).casefold()) if not unicodedata.combining(c))
    return re.findall(r'\w+',text)

def contained(label,phrase):
    value=tokens(label);source=tokens(phrase)
    return bool(value) and any(source[i:i+len(value)]==value for i in range(len(source)-len(value)+1))

def excerpts(phrase,limit=32):
    words=list(re.finditer(r'[\w]+(?:[’\x27-][\w]+)*',phrase));candidates=[]
    for i in range(len(words)):
        for j in range(i,min(len(words),i+6)):
            text=phrase[words[i].start():words[j].end()]
            if len(text)>limit:break
            content=[w for w in tokens(text) if w not in STOP]
            if not content or tokens(text)[-1] in STOP:continue
            score=len(content)*4+len(tokens(text))*.35-(tokens(text)[0] in STOP)*3
            candidates.append((-score,i,text))
    return [text for _,_,text in sorted(candidates)] or [phrase.strip()[:limit]]

def constrain_labels(board,units):
    for beat in board['momentos']:
        if not 0<=beat['frase']<len(units):continue
        phrase=units[beat['frase']];choices=excerpts(phrase);used=set()
        for element in beat['elementos']:
            label=element['rotulo']
            if not contained(label,phrase):
                replacement=next((c for c in choices if c.casefold() not in used),choices[0])
                element['rotulo']=replacement
                # A recipe-specific query such as "monitor CRT curvo" must
                # not survive after its unsupported caption was removed.
                for key in ('consulta_figura','intencao_visual','justificativa_visual','figura'):
                    element[key]=''
            used.add(element['rotulo'].casefold())
    return board
