import React from 'react';
import {Shot,ease,clamp,sans,fitSize} from './design';
import {glassClass,glassSurface} from './Finish';
import {Material} from './Art';

// A single chronological deck, not a fresh set of windows for every phrase.
// Up to four cards remain behind the new one, then the next deck starts.
export const StackedWindows:React.FC<Shot>=(s)=>{
  const {width:w,height:h,palette:p}=s,portrait=h>w,n=s.stackCards.length;
  const cw=w*(portrait? .68:.58),ch=h*(portrait? .43:.49),stepX=w*.026,stepY=h*.022;
  return <div style={{position:'absolute',inset:0,perspective:w*1.6}}>
    {s.stackCards.map((card,i)=>{
      const entry=s.animate?ease((s.timelineTime-card.start)/Math.min(.55,Math.max(.18,s.length*.22))):1;
      const depth=n-1-i,x=(w-cw)/2+depth*stepX-stepX*(n-1)/2,y=h*.36+depth*stepY;
      return <div key={card.index} className={glassClass(s)} style={{position:'absolute',left:x,top:y,width:cw,height:ch,
        background:p.surface,border:`1px solid ${p.accent}65`,borderRadius:w*.014,overflow:'hidden',
        boxShadow:`0 ${h*.024}px ${h*.045}px #0004`,...glassSurface(s),
        opacity:clamp(entry),transformOrigin:'50% 75%',
        transform:`translateY(${(1-entry)*h*.17}px) rotateX(${(1-entry)*9}deg) rotateZ(${(1-entry)*-3}deg)`}}>
        <div style={{height:ch*.10,display:'flex',alignItems:'center',gap:w*.008,paddingLeft:w*.02,
          borderBottom:`1px solid ${p.accent}35`,background:s.finish==='original'?p.bg:'#ffffff09'}}>
          {[p.accent,p.second,p.muted].map((color,j)=><span key={j} style={{width:w*.007,height:w*.007,borderRadius:'50%',background:color}}/>)}
          <span style={{fontFamily:sans,fontSize:w*(portrait? .019:.012),color:p.muted,marginLeft:w*.012}}>Clareia · {String(card.index+1).padStart(2,'0')}</span>
        </div>
        {s.figures[card.element.figura||'']?<div style={{position:'absolute',left:'7%',top:'14%',width:'86%',height:'47%'}}>
          <Material palette={p} variant={i} figure={s.figures[card.element.figura||'']}/></div>:null}
        <div style={{position:'absolute',left:'9%',top:s.figures[card.element.figura||'']?'66%':'24%',width:'82%',height:s.figures[card.element.figura||'']?'28%':'60%',
          borderTop:`1px solid ${p.accent}35`,paddingTop:ch*.045,fontFamily:sans,color:p.ink,fontWeight:680,
          fontSize:fitSize(card.element.rotulo,cw*.82,ch*(s.figures[card.element.figura||'']? .23:.51),w*(portrait? .052:.037),3),lineHeight:1.13}}>{card.element.rotulo}</div>
      </div>;
    })}
  </div>;
};
