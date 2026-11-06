"""Articulated painted sprites. Texture transforms preserve fabric and anatomy."""
from functools import lru_cache
import math
from PIL import Image,ImageChops,ImageDraw
from .core import ROOT

FOLDER=ROOT/'overview/assets/illustrated'


@lru_cache(maxsize=5)
def rig(role):
    source=Image.open(FOLDER/f'corpo-{role}.png').convert('RGBA')
    def mask_for(points,arm=False):
        mask=Image.new('L',source.size);ImageDraw.Draw(mask).polygon(points,fill=255)
        if role=='menina' and arm:
            import numpy as np
            rgb=np.asarray(source)[:,:,:3].astype('float32')
            cape=(rgb[:,:,0]>rgb[:,:,1]*1.55)&(rgb[:,:,0]>rgb[:,:,2]*1.65)
            alpha=np.asarray(mask).copy();alpha[cape]=0;mask=Image.fromarray(alpha)
        return mask
    def region(mask):
        tile=source.copy();tile.putalpha(ImageChops.multiply(source.getchannel('A'),mask))
        box=tile.getbbox();return tile.crop(box),box[:2]
    def mirror(points):return [(500-x,y) for x,y in points]
    upper=[(151,202),(151,270),(139,350),(125,474),(0,474),(0,202)]
    fore=[(125,450),(104,655),(0,655),(0,450)]
    upper_leg=[(0,520),(250,520),(250,823),(0,823)]
    lower_leg=[(0,820 if role=='menina' else 774),(250,820 if role=='menina' else 774),(250,1060),(0,1060)]
    masks={'upper_left':mask_for(upper,True),'fore_left':mask_for(fore,True),
           'upper_right':mask_for(mirror(upper),True),'fore_right':mask_for(mirror(fore),True),
           'shin_left':mask_for(lower_leg),'shin_right':mask_for(mirror(lower_leg))}
    if role!='menina':masks.update(thigh_left=mask_for(upper_leg),thigh_right=mask_for(mirror(upper_leg)))
    # Partition the complete painted silhouette. Unassigned fabric remains in
    # the torso, instead of being lost at arbitrary rectangular boundaries.
    body_mask=Image.new('L',source.size,255);ImageDraw.Draw(body_mask).rectangle((0,0,500,182),fill=0)
    for mask in masks.values():body_mask=ImageChops.subtract(body_mask,mask)
    result={name:region(mask) for name,mask in masks.items()}
    result['body']=region(body_mask)
    if role=='menina':result.update(thigh_left=None,thigh_right=None)
    return result


def bone(canvas,part,source_a,source_b,target_a,target_b):
    if part is None:return
    tile,(ox,oy)=part
    old_dx=source_b[0]-source_a[0];old_dy=source_b[1]-source_a[1]
    dx=target_b[0]-target_a[0];dy=target_b[1]-target_a[1]
    scale=math.hypot(dx,dy)/math.hypot(old_dx,old_dy)
    resized=tile.resize((max(1,round(tile.width*scale)),max(1,round(tile.height*scale))),Image.Resampling.BICUBIC)
    angle=math.atan2(old_dy,old_dx)-math.atan2(dy,dx)
    rotated=resized.rotate(math.degrees(angle),Image.Resampling.BICUBIC,expand=True)
    ax=(source_a[0]-ox)*scale-resized.width/2;ay=(source_a[1]-oy)*scale-resized.height/2
    anchor_x=ax*math.cos(angle)+ay*math.sin(angle)+rotated.width/2
    anchor_y=-ax*math.sin(angle)+ay*math.cos(angle)+rotated.height/2
    canvas.alpha_composite(rotated,(round(target_a[0]-anchor_x),round(target_a[1]-anchor_y)))


def painted_body(role,action,t,previous_action=None,blend=1):
    parts=rig(role);canvas=Image.new('RGBA',(500,1060))
    front=Image.new('RGBA',canvas.size)
    walking=action in ('andar','correr');phase=t*(6 if action=='correr' else 3.2)
    previous_action=previous_action or action
    old_walking=previous_action in ('andar','correr')
    old_swing=math.sin(t*(6 if previous_action=='correr' else 3.2)) if old_walking else 0
    swing=old_swing*(1-blend)+(math.sin(phase) if walking else 0)*blend
    bob=abs(math.sin(phase))*4 if walking else math.sin(t*1.4)*1.8
    for side in [-1,1]:
        word='left' if side==-1 else 'right'
        hip=(250+side*42,535);knee=(250+side*53,800);ankle=(250+side*81,1000)
        target_hip=(hip[0],hip[1]+bob);target_knee=(knee[0]+side*swing*20,knee[1])
        target_ankle=(ankle[0]+side*swing*48,ankle[1]-(max(0,side*math.cos(phase))*22 if walking else 0))
        bone(canvas,parts['thigh_'+word],hip,knee,target_hip,target_knee)
        bone(canvas,parts['shin_'+word],knee,ankle,target_knee,target_ankle)
    def arm(side):
        word='left' if side==-1 else 'right'
        shoulder=(250+side*100,235);elbow=(250+side*142,450);wrist=(250+side*166,610)
        target_shoulder=(shoulder[0],shoulder[1]+bob)
        target_elbow=(elbow[0]+side*swing*9,elbow[1]+bob)
        target_wrist=(wrist[0]-side*swing*30,wrist[1]+bob)
        def pose(what):
            if side==1 and what=='pensar':return (377,384+bob),(310,210+bob)
            if side==1 and what in ('gesticular','conversar','apontar'):return (420,428+bob),(450+5*math.sin(t*1.5),550+8*math.sin(t*1.5))
            if what=='ler':return (250+side*131,406+bob),(250+side*46,430+bob)
            return target_elbow,target_wrist
        old_e,old_w=pose(previous_action);new_e,new_w=pose(action)
        target_elbow=tuple(x*(1-blend)+y*blend for x,y in zip(old_e,new_e))
        target_wrist=tuple(x*(1-blend)+y*blend for x,y in zip(old_w,new_w))
        bone(canvas,parts['upper_'+word],shoulder,elbow,target_shoulder,target_elbow)
        if side==1 and (action=='pensar' or previous_action=='pensar'):bone(front,parts['fore_'+word],elbow,wrist,target_elbow,target_wrist)
        else:bone(canvas,parts['fore_'+word],elbow,wrist,target_elbow,target_wrist)
    arm(-1)
    tile,origin=parts['body'];canvas.alpha_composite(tile,(origin[0],origin[1]+round(bob)))
    arm(1)
    return canvas,bob,front
