"""Large phone captions, highlighting the spoken word on its audio clock."""
from __future__ import annotations

import re
from pathlib import Path
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont

from .core import digest,read_json,write_json
from .short_video import CAPTION_BOX,caption_box
from .visuals import font,wrap

VERSION='phone-word-captions-v3-templates'
COLORS={'amarelo':'&H4AE1FF&','ciano':'&HF5E631&','branca':'&HFFFFFF&'}


def _units(text):
    from .speech_alignment import tokens
    result=[]
    for word in text.split():
        if tokens(word):result.append(word)
        elif result:result[-1]+=' '+word
    return result


def timed_words(scene,path,audio,meta):
    from .speech_alignment import align
    from .speech_integrity import check_audio,fingerprint
    from .speech import normalize
    spoken=' '.join(c['texto'] for c in meta['legendas'])
    checksum=fingerprint(audio)
    target=path/'cache/audio'/('short-captions-'+digest(VERSION,checksum,spoken)+'.json')
    saved=read_json(target)
    if saved:return saved['palavras']
    words=meta.get('palavras')
    origin='Microsoft · tempos por palavra'
    if not words:
        origin='Alinhamento local da narração'
        glossary=read_json(path/'pronuncia.json',{})
        words,_=check_audio(audio,normalize(scene['narracao_ptbr'],glossary),path/'cache/audio/verificacao')
    units=_units(spoken)
    duration=sf.info(audio).duration
    try:
        aligned,coverage=align(units,words,duration)
    except ValueError:
        # Recognizers sometimes merge a short word with its neighbour. Anchor
        # pairs to real speech, then split only that small acoustic interval.
        groups=[' '.join(units[i:i+2]) for i in range(0,len(units),2)]
        pairs,coverage=align(groups,words,duration)
        aligned=[]
        for pair in pairs:
            parts=pair['texto'].split();weights=[max(1,len(re.sub(r'\W','',w))) for w in parts]
            start=pair['inicio'];length=pair['fim']-start;total=sum(weights)
            for word,weight in zip(parts,weights):
                end=start+length*weight/total
                aligned.append({'texto':word,'inicio':start,'fim':end});start=end
    # Do not light the first word during a silent scene transition, or the last
    # word over a long trailing silence. Native/ASR bounds are the outer anchors.
    if aligned and words:
        aligned[0]['inicio']=max(aligned[0]['inicio'],float(words[0]['inicio']))
        aligned[-1]['fim']=min(aligned[-1]['fim'],float(words[-1]['fim']))
    write_json(target,{'versao':VERSION,'sha256':checksum,'origem':origin,'cobertura':coverage,'palavras':aligned})
    return aligned


def groups(words,preset='impacto'):
    """Stable two-line blocks of at most four words, sized before highlighting."""
    from .reels_styles import PRESETS
    template=PRESETS[preset]
    draw=ImageDraw.Draw(Image.new('RGB',(1,1)))
    result=[];current=[]
    width=CAPTION_BOX[2]-CAPTION_BOX[0]-36
    def layout(items):
        text=' '.join(w['texto'].upper() if template['upper'] else w['texto'] for w in items)
        for size in range(template['size'],35,-2):
            try:face=ImageFont.truetype('C:/Windows/Fonts/'+template['file'],size)
            except OSError:face=font(size,True)
            lines=wrap(draw,text,face,width*.90)
            if len(lines)<=2 and all(draw.textlength(line,font=face)<=width*.90 for line in lines):
                return size,lines
        raise ValueError('Uma palavra da legenda é longa demais. Ajuste sua escrita antes de renderizar o Shorts.')
    for word in words:
        if word['fim']<=word['inicio']:continue
        if current and (len(current)>=4 or word['fim']-current[0]['inicio']>1.9
                        or word['inicio']-current[-1]['fim']>.55):
            size,lines=layout(current);result.append({'palavras':current,'fonte':size,'linhas':lines});current=[]
        current.append(dict(word))
        if re.search(r'[.!?]$',word['texto']):
            size,lines=layout(current);result.append({'palavras':current,'fonte':size,'linhas':lines});current=[]
    if current:
        size,lines=layout(current);result.append({'palavras':current,'fonte':size,'linhas':lines})
    return result


def write(words,srt,ass,style='amarelo',*,effect='destaque',position='inferior',preset='impacto'):
    from .render import timestamp
    from .reels_styles import PRESETS,caption_colors,ass_color
    template=PRESETS[preset]
    primary,accent=caption_colors(preset,style)
    blocks=groups(words,preset)
    srt.write_text('\n\n'.join(f"{i+1}\n{timestamp(b['palavras'][0]['inicio'])} --> {timestamp(b['palavras'][-1]['fim'])}\n"+
                               '\n'.join(b['linhas']) for i,b in enumerate(blocks))+'\n',encoding='utf-8')
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,64,144,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    outline=ass_color(template.get('background','101010'))
    if template.get('neon'):outline=accent
    ass_style=f"Style: Default,{template['font']},{template['size']},{primary},{primary},{outline},&H80000000,-1,0,0,0,100,100,0,0,{3 if template.get('box') else 1},{template['outline']},{template['shadow']},5,64,144,0,1"
    header=re.sub(r'Style: Default,[^\n]+',lambda _:ass_style,header)
    lines=[]
    for block_index,block in enumerate(blocks):
        box=caption_box(position,block_index)
        cx=(box[0]+box[2])//2;cy=(box[1]+box[3])//2
        items=block['palavras']
        # Preserve line breaks when changing color; no glyph changes position.
        breaks=[];count=0
        for line in block['linhas'][:-1]:count+=len(line.split());breaks.append(count)
        for active,item in enumerate(items):
            end=items[active+1]['inicio'] if active+1<len(items) else item['fim']
            if end<=item['inicio']:continue
            safe_word=(item['texto'].upper() if template['upper'] else item['texto']).replace('\\','/').replace('{','(').replace('}',')')
            # Hidden suffixes reserve the final glyph layout, avoiding jumps as
            # a phrase grows. Each block clears before the next phrase begins.
            steps=min(len(safe_word),max(1,int((item['fim']-item['inicio'])*24))) if effect=='maquina' else 1
            for step in range(steps):
                start=item['inicio']+(item['fim']-item['inicio'])*step/steps
                finish=end if step==steps-1 else item['inicio']+(item['fim']-item['inicio'])*(step+1)/steps
                visible=max(1,round(len(safe_word)*(step+1)/steps))
                text=''
                for index,word in enumerate(items):
                    if index:text+='\\N' if index in breaks else ' '
                    safe=(word['texto'].upper() if template['upper'] else word['texto']).replace('\\','/').replace('{','(').replace('}',')')
                    color=accent if index==active else primary
                    hidden=effect!='destaque' and index>active
                    text+='{\\alpha'+('&HFF&' if hidden else '&H00&')+'\\1c'+color+'}'
                    if effect=='maquina' and index==active:
                        text+=safe[:visible]+'{\\alpha&HFF&}'+safe[visible:]
                    else:text+=safe
                tags=f'{{\\an5\\pos({cx},{cy})\\fs{block["fonte"]}}}'
                if finish>start:
                    lines.append(f"Dialogue: 0,{timestamp(start,True)},{timestamp(finish,True)},Default,,0,0,0,,{tags}{text}")
    ass.write_text(header+'\n'.join(lines),encoding='utf-8-sig')
