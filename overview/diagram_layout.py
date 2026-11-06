"""Measured diagram cells reserve space for icons, motion and complete labels."""
from __future__ import annotations

import re
import math

from PIL import Image, ImageDraw

from .visuals import draw_lines, font, wrap

DATE_PATTERN = r'(?:[Aa]nos |[Dd]écada de )?(?:1[0-9]{3}|20[0-9]{2})'
LAYOUT_VERSION = 'measured-layout-v1'


def label_texture(animator, text, width, size):
    """Keep every character, including a long name that needs a word break."""
    width=int(width)
    key=('diagram-label',text,width,size)
    if key not in animator.textures:
        draw=ImageDraw.Draw(Image.new('RGBA',(1,1)))
        for actual in range(size,21,-1):
            face=font(actual,True)
            words=[]
            for word in text.split():
                part=''
                for char in word:
                    if part and draw.textlength(part+char,font=face)>width:
                        words.append(part);part=''
                    part+=char
                if part:words.append(part)
            lines=wrap(draw,' '.join(words),face,width)
            if len(lines)<=3:
                break
        else:
            raise ValueError('Rótulo precisa de mais espaço.')
        texture=Image.new('RGBA',(width,round(actual*1.32*len(lines))+8))
        draw_lines(ImageDraw.Draw(texture),(0,0),lines,face,actual,animator.fg)
        animator.textures[key]=texture
    return animator.textures[key]


def diagram_layout(animator, elements, kind, bounds):
    left, top, right, bottom = bounds
    width, height = right-left, bottom-top
    n = len(elements)
    if not n:
        return []
    compact = animator.portrait or animator.asset is not None
    gap = 24
    cells = []
    if getattr(animator,'mobile',False) and animator.mobile_layout=='equilibrada':
        # Each complete icon and label owns a cell in a compact two-column group.
        cols=min(2,n);rows=math.ceil(n/cols)
        used_h=min(height,430 if rows==1 else 760)
        origin=top+(height-used_h)/2
        order=[(0,0),(1,0),(1,1),(0,1)] if kind=='ciclo' and n==4 else [(i%cols,i//cols) for i in range(n)]
        for index,(col,row) in enumerate(order):
            x=left+col*width/cols
            if n==3 and index==2:x=left+width/4
            cells.append((x+gap/2,origin+row*used_h/rows+gap/2,
                          x+width/cols-gap/2,origin+(row+1)*used_h/rows-gap/2,False,112))
    elif kind == 'conceito' and n > 1 and not compact and animator.style != 'tipografia':
        split = left+width*.48
        cells.append((left, top, split-gap/2, bottom, False, 155))
        step = height/(n-1)
        cells.extend((split+gap/2, top+j*step+gap/2, right,
                      top+(j+1)*step-gap/2, True, 65) for j in range(n-1))
    elif compact and height/n >= 135:
        # Rows also leave the entire image/portrait column untouched.
        step = height/n
        cells = [(left, top+j*step+gap/2, right, top+(j+1)*step-gap/2, True, 56)
                 for j in range(n)]
    elif kind in ('rede', 'ciclo') and n >= 3 and height >= 400:
        # The old diamond placed two full-size nodes on the same central column.
        # Give each icon AND its caption an independent quadrant instead.
        order = [(0, 0), (1, 0), (1, 1), (0, 1)] if kind == 'ciclo' else [(0, 0), (1, 0), (0, 1), (1, 1)]
        for col, row in order[:n]:
            cells.append((left+col*width/2+gap/2, top+row*height/2+gap/2,
                          left+(col+1)*width/2-gap/2, top+(row+1)*height/2-gap/2,
                          True, 100))
    else:
        step = width/n
        cells = [(left+j*step+gap/2, top, left+(j+1)*step-gap/2, bottom,
                  False, 65 if animator.style == 'tipografia' else 110) for j in range(n)]

    nodes = []
    for element, (x1, y1, x2, y2, side, cap) in zip(elements, cells):
        cell_w, cell_h = x2-x1, y2-y1
        label = element['rotulo']
        date = re.fullmatch(DATE_PATTERN, label)
        # Includes pulse, entrance offset, erasing halo, paper tilt, and the
        # thought bubbles extending above the pensador icon.
        above = 1.75 if element['icone'] == 'pensador' and not date else 1.13
        cap=min(cap,int((cell_h-66)/(above+1.13)),int((cell_w-48)/2.30))
        for radius in range(cap, 7, -1):
            iw = radius*2.30+48
            ih = radius*(above+1.13)+66
            label_w = cell_w-iw-18 if side and not date else cell_w-16
            if label_w < 70:
                continue
            size = (38 if side else 36) if getattr(animator,'mobile',False) else 30 if side else 26 if compact or n >= 3 else 34
            try:
                texture = label_texture(animator, label, label_w, size)
            except ValueError:
                continue
            used = texture.getbbox()[2] if texture.getbbox() else texture.width
            if date:
                year = re.search(r'\d{4}', label)[0]
                prefix = label.replace(year, '').strip()
                prefix_tex = animator.text(prefix, cell_w-16, 25, bold=True) if prefix else None
                year_size=min(77 if compact else 100,
                              max(24,int((cell_h-20-(prefix_tex.height+8 if prefix_tex else 0))/1.32)))
                year_tex = animator.text(year, cell_w-16, year_size, animator.accent, True)
                year_w = year_tex.getbbox()[2]
                group_w = max(iw, year_w+12, (prefix_tex.getbbox()[2]+12) if prefix_tex else 0)
                group_h = max(ih, year_tex.height+(prefix_tex.height+8 if prefix_tex else 0)+12)
            else:
                group_w = iw+18+used+12 if side else max(iw, used+12)
                group_h = max(ih, texture.height+12) if side else ih+12+texture.height+12
            if group_w <= cell_w and group_h <= cell_h:
                break
        else:
            raise ValueError('Não há espaço para os ícones e rótulos completos nesta composição.')

        gx = x1+min(24,(cell_w-group_w)/2) if side and not date else x1+(cell_w-group_w)/2
        gy = y1+(cell_h-group_h)/2
        cx = gx+iw/2 if side and not date else (x1+x2)/2
        cy = gy+(group_h-ih)/2+radius*above+24 if side or date else gy+radius*above+24
        if side:
            label_xy = (gx+iw+18+6, gy+(group_h-texture.height)/2)
        else:
            label_xy = (cx-used/2, gy+ih+12+6)
        node = {'center': (cx, cy), 'radius': radius, 'texture': texture,
                'label_xy': label_xy, 'bounds': (gx, gy, gx+group_w, gy+group_h),
                'cell': (x1, y1, x2, y2)}
        if date:
            node.update(year=year_tex, year_xy=(cx-year_w/2, gy+6), prefix=prefix_tex,
                        prefix_xy=(cx-(prefix_tex.getbbox()[2]/2 if prefix_tex else 0), gy+year_tex.height+14))
        nodes.append(node)
    return nodes
