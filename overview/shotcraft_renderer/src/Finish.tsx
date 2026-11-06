import React, {createContext} from 'react';
import {Film,Palette,Shot} from './design';

export const FinishContext=createContext<'vidro_avancado'|'original'>('vidro_avancado');
export const glassClass=(s:Shot)=>s.finish==='vidro_avancado'?'shot-surface':undefined;

// Tint stays between 44% and 72%; the rim is a separate masked light layer.
// Native CSS blur, no external texture, shader, network or per-frame simulation.
export function glassSurface(s:Shot,tint=s.palette.surface):React.CSSProperties {
  if(s.finish!=='vidro_avancado')return {};
  return {background:`linear-gradient(145deg,${tint}b8,${tint}70)`,
    backdropFilter:`blur(${Math.max(8,s.width*.016)}px) saturate(125%)`,
    border:'1px solid #ffffff30',
    boxShadow:`0 ${s.height*.018}px ${s.height*.045}px #00000038,0 2px 8px #00000020,inset 0 1px 0 #ffffff60,inset 0 -1px 0 ${s.palette.second}28`};
}

const lights:Record<string,[string,string,string]>={
  cinema:['#178caa','#7452b8','#d4a05a'],tecnologia:['#12bda8','#1c70b5','#9e7bb5'],
  vibrante:['#7451bd','#ca5f83','#4797b0'],editorial:['#bb906c','#8eaca8','#baacc9'],
};
export const Atmosphere:React.FC<{film:Film;palette:Palette;seconds:number}>=({film,palette:p,seconds})=>{
  const colors=lights[film.theme]||lights.editorial,t=film.animate?seconds:0,w=film.width,h=film.height;
  return <div aria-hidden="true" style={{position:'absolute',inset:0,overflow:'hidden',pointerEvents:'none',
    background:`linear-gradient(145deg,${p.bg},${p.surface} 48%,${p.bg})`}}>
    {colors.map((color,i)=><div key={color} style={{position:'absolute',
      left:w*([-.22,.38,.20][i]+Math.sin(t*.19+i*2)*.065),
      top:h*([.06,.42,.73][i]+Math.cos(t*.16+i*1.7)*.045),
      width:w*1.08,height:Math.max(w*.8,h*.67),borderRadius:'50%',
      background:`radial-gradient(ellipse,${color}${film.theme==='editorial'?'44':'80'} 0%,${color}18 43%,transparent 71%)`,
      filter:`blur(${w*.035}px)`,transform:`rotate(${i*51+Math.sin(t*.13)*7}deg)`}}/>)}
    <div style={{position:'absolute',inset:0,background:`radial-gradient(ellipse at 50% 42%,transparent 28%,${p.bg}8c 100%)`}}/>
  </div>;
};

export const RefractionRules:React.FC=()=> <style>{`
  .shot-surface::after {content:"";position:absolute;inset:0;z-index:8;border-radius:inherit;padding:1px;
    background:linear-gradient(135deg,#ffffffa8 0%,#ffffff20 35%,#ffffff08 52%,#ffffff50 76%,#ffffff18 100%);
    -webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);
    -webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;}
`}</style>;
