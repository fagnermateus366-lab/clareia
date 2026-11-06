from typing import Literal
from pydantic import BaseModel,Field,FiniteFloat

class DataPoint(BaseModel):
    x:FiniteFloat
    y:FiniteFloat
    z:FiniteFloat
    label:str=Field('',max_length=80)

class ThreeOptions(BaseModel):
    speed:float=Field(1,ge=0,le=2)
    light:float=Field(1,ge=.3,le=2)
    color:str=Field('#2ba895',pattern=r'^#[0-9a-fA-F]{6}$')
    theme:Literal['dark','studio','wireframe']='studio'
    quality:Literal['economica','equilibrada','alta']='economica'
    wireframe:bool=False
    movement:Literal['padrao','estatico','giro_suave','aproximacao','flutuacao','apresentacao']='padrao'
    dataPoints:list[DataPoint]=Field(default_factory=list,max_length=200)
