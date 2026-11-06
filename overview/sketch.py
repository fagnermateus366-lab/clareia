"""Trace the actual vector paths progressively; the marker follows their endpoints."""
import math
from PIL import ImageDraw


class SketchPen:
    def __init__(self):self.paths=[]
    def line(self,points,fill=None,width=3,joint=None):
        self.paths.append((list(points),max(2,width)))
    def ellipse(self,box,fill=None,outline=None,width=3):
        x1,y1,x2,y2=box;cx=(x1+x2)/2;cy=(y1+y2)/2
        self.line([(cx+(x2-x1)/2*math.cos(i*math.tau/64),cy+(y2-y1)/2*math.sin(i*math.tau/64)) for i in range(65)],width=width)
    def arc(self,box,start,end,fill=None,width=3):
        x1,y1,x2,y2=box;cx=(x1+x2)/2;cy=(y1+y2)/2
        self.line([(cx+(x2-x1)/2*math.cos(math.radians(start+(end-start)*i/48)),
                    cy+(y2-y1)/2*math.sin(math.radians(start+(end-start)*i/48))) for i in range(49)],width=width)
    def rounded_rectangle(self,box,radius=8,fill=None,outline=None,width=3):
        x1,y1,x2,y2=box;r=min(radius,(x2-x1)/2,(y2-y1)/2);points=[]
        for cx,cy,start in [(x2-r,y1+r,-90),(x2-r,y2-r,0),(x1+r,y2-r,90),(x1+r,y1+r,180)]:
            points += [(cx+r*math.cos(math.radians(start+i*90/12)),cy+r*math.sin(math.radians(start+i*90/12))) for i in range(13)]
        self.line(points+[points[0]],width=width)
    def polygon(self,points,fill=None,outline=None,width=3):self.line(list(points)+[points[0]],width=width)
    def render(self,canvas,progress,color):
        progress=max(0,min(1,progress));segments=[];total=0
        for points,width in self.paths:
            for a,b in zip(points,points[1:]):
                length=math.dist(a,b);segments.append((a,b,width,length));total+=length
        left=total*progress;d=ImageDraw.Draw(canvas);tip=None
        for a,b,width,length in segments:
            if left<=0:break
            ratio=min(1,left/max(length,.001));end=(a[0]+(b[0]-a[0])*ratio,a[1]+(b[1]-a[1])*ratio)
            d.line((a,end),fill=color,width=round(width));tip=end;left-=length
        return tip
