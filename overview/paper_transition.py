"""Textured notebook sheet, lit folds, photographic paper ball and fresh sheet."""
from functools import lru_cache
from pathlib import Path
import math
import hashlib

import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFilter

VERSION='notebook-crumple-v1'
ASSET=Path(__file__).parent/'assets/paper/crumpled-notebook.png'


@lru_cache(maxsize=1)
def fingerprint():
    return hashlib.sha256(VERSION.encode()+ASSET.read_bytes()+ASSET.with_name('flattened-notebook.png').read_bytes()).hexdigest()


def smooth(value):
    value=max(0.,min(1.,value))
    return value*value*(3-2*value)


@lru_cache(maxsize=3)
def material(size):
    w,h=size
    rng=np.random.default_rng(1047)
    noise=rng.normal(0,1.05,(h,w,1))
    paper=np.clip(np.array([249,247,239])+noise,0,255).astype('uint8')
    page=Image.fromarray(paper);d=ImageDraw.Draw(page)
    spacing=max(12,round(h/19))
    for y in range(spacing*2,h,spacing):d.line((0,y,w,y),fill='#c5d5dc',width=max(1,w//1100))
    d.line((w*.112,0,w*.112,h),fill='#e2aaa5',width=max(1,w//750))
    # Small binding holes retain an illuminated paper rim.
    r=max(2,round(w*.004))
    for y in np.linspace(h*.12,h*.88,6):
        d.ellipse((w*.035-r-1,y-r-1,w*.035+r+1,y+r+1),fill='#fffdf6')
        d.ellipse((w*.035-r,y-r,w*.035+r,y+r),fill='#b5b2aa')
    desktop=np.clip(np.array([218,215,207])+rng.normal(0,.65,(h,w,1)),0,255).astype('uint8')
    # Stable irregular triangulation makes folds follow the printed content.
    cols,rows=(29,19) if w>=h else (19,29)
    uv=np.array([(x/(cols-1),y/(rows-1)) for y in range(rows) for x in range(cols)],dtype='float64')
    jitter=rng.uniform(-.28,.28,uv.shape)/np.array([cols-1,rows-1])
    inside=(uv[:,0]>0)&(uv[:,0]<1)&(uv[:,1]>0)&(uv[:,1]<1)
    uv[inside]+=jitter[inside]
    faces=[]
    for y in range(rows-1):
        for x in range(cols-1):
            a=y*cols+x;b=a+1;c=a+cols;d=c+1
            faces.extend([(a,b,d),(a,d,c)] if (x+y)%2 else [(a,b,c),(b,d,c)])
    ball=Image.open(ASSET).convert('RGBA')
    ball=ball.crop(ball.getbbox())
    creases=Image.open(ASSET.with_name('flattened-notebook.png')).convert('L').resize(size,Image.Resampling.LANCZOS).convert('RGB')
    return page,Image.fromarray(desktop),uv,np.array(faces),ball,creases


def printed(content,page):
    pixels=np.asarray(content,dtype='float32')
    w,h=content.size
    background=np.median(pixels[::max(1,h//30),::max(1,w//30)].reshape(-1,3),axis=0)
    coverage=np.clip(np.max(np.abs(pixels-background),axis=2)/38,0,1)[...,None]
    if background.mean()<130:
        # Bright lettering on dark themes becomes ink on the notebook page.
        pixels=255-pixels
    texture=np.asarray(page,dtype='float32')
    ink=np.minimum(pixels,texture)
    return Image.fromarray(np.clip(texture*(1-coverage)+ink*coverage,0,255).astype('uint8'))


def folded(texture,uv,faces,amount):
    w,h=texture.size;short=min(w,h)
    u,v=uv.T
    c=smooth(amount)
    theta=(u-.5)*math.pi*.97+.12*np.sin(v*8+u*9)
    phi=math.pi*(.07+.86*v)+.15*np.sin(u*11+v*5)
    radius=short*.145*(.88+.12*np.sin(u*43+v*19)+.08*np.cos(v*47-u*17))
    sphere=np.column_stack((radius*np.sin(phi)*np.sin(theta),-radius*np.cos(phi),radius*np.sin(phi)*np.cos(theta)))
    flat=np.column_stack(((u-.5)*w,(v-.5)*h,np.zeros_like(u)))
    xyz=flat*(1-c)+sphere*c
    ridge=(np.sin(u*37+v*9)+.65*np.cos(v*35-u*13))
    xyz[:,2]+=short*.075*math.sin(math.pi*c)*ridge
    xyz[:,0]+=short*.025*math.sin(math.pi*c)*np.sin(v*29+u*5)
    xyz[:,1]+=short*.025*math.sin(math.pi*c)*np.cos(u*27-v*8)
    angle=-.23*c
    x=xyz[:,0]*math.cos(angle)-xyz[:,1]*math.sin(angle)
    y=xyz[:,0]*math.sin(angle)+xyz[:,1]*math.cos(angle)
    perspective=3*max(w,h)/(3*max(w,h)-xyz[:,2])
    screen=np.column_stack((w*.5+x*perspective,h*.48+y*perspective))
    vertices=xyz[faces]
    normals=np.cross(vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-8)
    vertex_normals=np.zeros_like(xyz)
    for corner in range(3):np.add.at(vertex_normals,faces[:,corner],normals)
    vertex_normals/=np.maximum(np.linalg.norm(vertex_normals,axis=1)[:,None],1e-8)
    light=np.array([-.35,-.42,.84]);light/=np.linalg.norm(light)
    # Two-sided paper with directional illumination and fold self-occlusion.
    vertex_light=.62+.42*np.abs(vertex_normals@light)
    depth=vertices[:,:,2].mean(axis=1)
    occlusion=1-.17*c*(depth.max()-depth)/(np.ptp(depth)+1)
    pixels=np.asarray(texture)
    out=np.zeros((h,w,4),dtype='uint8')
    for index in np.argsort(depth):
        face=faces[index];triangle=screen[face]
        x0=max(0,math.floor(triangle[:,0].min())-1);x1=min(w,math.ceil(triangle[:,0].max())+1)
        y0=max(0,math.floor(triangle[:,1].min())-1);y1=min(h,math.ceil(triangle[:,1].max())+1)
        if x1<=x0 or y1<=y0:continue
        a,b,d=triangle
        determinant=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
        if abs(determinant)<.05:continue
        yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
        first=((b[1]-d[1])*(xx-d[0])+(d[0]-b[0])*(yy-d[1]))/determinant
        second=((d[1]-a[1])*(xx-d[0])+(a[0]-d[0])*(yy-d[1]))/determinant
        third=1-first-second
        mask=(first>=-.008)&(second>=-.008)&(third>=-.008)
        if not mask.any():continue
        source=uv[face]
        sx=np.clip((first*source[0,0]+second*source[1,0]+third*source[2,0])*(w-1),0,w-1)
        sy=np.clip((first*source[0,1]+second*source[1,1]+third*source[2,1])*(h-1),0,h-1)
        ix=sx.astype('int32');iy=sy.astype('int32')
        fx=(sx-ix)[...,None];fy=(sy-iy)[...,None]
        ix2=np.minimum(ix+1,w-1);iy2=np.minimum(iy+1,h-1)
        color=(pixels[iy,ix]*(1-fx)+pixels[iy,ix2]*fx)*(1-fy)+(pixels[iy2,ix]*(1-fx)+pixels[iy2,ix2]*fx)*fy
        target=out[y0:y1,x0:x1]
        lighting=(first*vertex_light[face[0]]+second*vertex_light[face[1]]+third*vertex_light[face[2]])*occlusion[index]
        target[mask,:3]=np.clip(color[mask]*lighting[mask,None],0,255).astype('uint8')
        target[mask,3]=255
    return Image.fromarray(out)


def with_shadow(canvas,tile,xy,opacity=1.,blur=8):
    if opacity<=0:return
    alpha=tile.getchannel('A')
    if opacity<1:
        alpha=alpha.point(lambda value:round(value*opacity))
        tile=tile.copy();tile.putalpha(alpha)
    shadow=Image.new('RGBA',canvas.size)
    shade=alpha.point(lambda value:round(value*.24))
    shadow.paste((39,32,22), (xy[0]+7,xy[1]+12,xy[0]+7+tile.width,xy[1]+12+tile.height),shade)
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(tile,xy)


def crumple(old,new,progress):
    original_size=new.size
    # Bound mesh work while preserving the full-resolution endpoints.
    scale=min(1,1152/max(original_size))
    size=tuple(max(1,round(value*scale)) for value in original_size)
    page,desk,uv,faces,ball,creases=material(size)
    w,h=size
    p=progress
    canvas=desk.convert('RGBA')
    if p<.70:
        content=printed(old.resize(size,Image.Resampling.BICUBIC),page)
        content=Image.blend(content,ImageChops.multiply(content,creases),smooth(p/.32)*.95)
        sheet=folded(content,uv,faces,max(0,(p-.025)/.615))
        fade=smooth((p-.46)/.18)
        with_shadow(canvas,sheet,(0,0),1-fade,5+round(8*p))
    if p>.46 and p<.94:
        appearance=smooth((p-.46)/.18)
        throw=smooth((p-.68)/.23)
        diameter=round(min(w,h)*(.30-.065*throw))
        sprite=ball.copy();sprite.thumbnail((diameter,diameter),Image.Resampling.LANCZOS)
        sprite=sprite.rotate(-13+115*throw,Image.Resampling.BICUBIC,expand=True)
        x=w*.5+w*.76*throw;y=h*.48+h*(.68*throw*throw-.12*math.sin(throw*math.pi))
        with_shadow(canvas,sprite,(round(x-sprite.width/2),round(y-sprite.height/2)),appearance,10)
    if p>.70:
        arrival=smooth((p-.70)/.27)
        fresh=printed(new.resize(size,Image.Resampling.BICUBIC),page).convert('RGBA')
        angle=-5*(1-arrival)
        fresh=fresh.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        with_shadow(canvas,fresh,(round((w-fresh.width)/2+w*(1-arrival)),round((h-fresh.height)/2+h*.08*(1-arrival))),1,10)
    result=canvas.convert('RGB').resize(original_size,Image.Resampling.BICUBIC)
    if p<.035:return Image.blend(old,result,smooth(p/.035))
    if p>.96:return Image.blend(result,new,smooth((p-.96)/.04))
    return result
