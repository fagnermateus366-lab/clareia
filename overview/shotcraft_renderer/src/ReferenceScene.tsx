import React from 'react';
import {Img} from 'remotion';
import {Shot,Family,ease,sans,serif,fitSize,chooseFamily} from './design';
import {glassClass,glassSurface} from './Finish';

// The photo has one stable place for the whole scene. The selected choreography
// receives its own canvas; phrase changes never remove, crop or restart the photo.
export const referenceLayout=(width:number,height:number)=>height>width?
  {photo:{left:width*.07,top:height*.14,width:width*.86,height:height*.31},
   motion:{left:width*.04,top:height*.46,width:width*.92,height:height*.53}}:
  {photo:{left:width*.055,top:height*.19,width:width*.45,height:height*.70},
   motion:{left:width*.53,top:height*.12,width:width*.45,height:height*.83}};

export const ReferenceScene:React.FC<{shot:Shot;Model:React.FC<Shot>}>=({shot:s,Model})=>{
  const {width:w,height:h,beat:b,palette:p}=s,layout=referenceLayout(w,h),family=chooseFamily(b,'auto');
  const firstIsPhoto=!b.elementos[0]?.figura;
  const elements=firstIsPhoto?b.elementos.slice(1):b.elementos;
  const support:Shot={...s,width:layout.motion.width,height:layout.motion.height,photo:null,
    beat:{...b,elementos:elements,foco:Math.max(0,(b.foco||0)-(firstIsPhoto?1:0))},
    stackCards:s.stackCards.filter(card=>!!card.element.figura)};
  const enter=s.animate?ease(s.timelineTime/.5):1;
  const chrome=family==='interface',retro=family==='retro';
  const float=s.animate&&!s.staticPhoto?Math.sin(s.timelineTime*.28)*h*.006:0;
  const photoBox=layout.photo;
  return <>
    <div data-reference-photo className={glassClass(s)} style={{position:'absolute',...photoBox,
      background:p.surface,border:`1px solid ${p.accent}60`,borderRadius:w*.014,boxShadow:`0 ${h*.025}px ${h*.045}px #0004`,
      ...glassSurface(s),opacity:enter,overflow:'hidden',transform:`translateY(${(1-enter)*h*.025+float}px)`}}>
      {chrome?<div style={{position:'absolute',left:0,top:0,right:0,height:photoBox.height*.075,
        display:'flex',alignItems:'center',gap:w*.006,paddingLeft:w*.016,borderBottom:`1px solid ${p.accent}40`}}>
        {[p.accent,p.second,p.muted].map(color=><span key={color} style={{width:w*.006,height:w*.006,borderRadius:'50%',background:color}}/>)}</div>:null}
      <Img src={s.photo!} style={{position:'absolute',left:'3%',top:'8%',width:'94%',
        height:'77%',objectFit:'contain'}}/>
      {firstIsPhoto?<div style={{position:'absolute',left:'6%',right:'6%',bottom:'4%',height:'12%',
        fontFamily:sans,fontWeight:620,color:p.ink,lineHeight:1.12,
        fontSize:fitSize(b.elementos[0].rotulo,photoBox.width*.88,photoBox.height*.12,w*(h>w?.042:.024),2)}}>{b.elementos[0].rotulo}</div>:null}
      {retro?<div aria-hidden="true" style={{position:'absolute',inset:0,border:`2px solid ${p.accent}70`,borderRadius:'inherit',boxShadow:`inset 0 0 ${w*.022}px ${p.accent}25`}}/>:null}
    </div>
    <div data-reference-motion style={{position:'absolute',...layout.motion,overflow:'hidden'}}>
      {elements.length?<Model {...support}/>:<ReferenceStatement shot={support} family={family}/>}
    </div>
  </>;
};

const ReferenceStatement:React.FC<{shot:Shot;family:Family}>=({shot:s,family})=>{
  const w=s.width,h=s.height,text=s.beat.titulo,font=family==='editorial'?serif:sans;
  const progress=s.animate?ease(s.local/Math.min(1,s.length*.4)):1;
  const title=s.beat.receita==='digitacao'?text.slice(0,Math.ceil(text.length*progress)):text;
  return <div style={{position:'absolute',left:w*.07,top:h*.14,width:w*.86,height:h*.65,display:'flex',alignItems:'center',
    fontFamily:font,fontWeight:740,lineHeight:1.1,letterSpacing:'-.035em',color:s.palette.ink,
    fontSize:fitSize(text,w*.86,h*.65,w*.11,4,font),opacity:progress,transform:`translateY(${(1-progress)*h*.03}px)`}}>
    <span>{title}<span style={{display:'block',width:w*.3,height:3,marginTop:h*.04,background:s.palette.accent}}/></span>
  </div>;
};
