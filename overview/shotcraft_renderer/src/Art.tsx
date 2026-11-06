import React, {useContext} from 'react';
import {Img} from 'remotion';
import {Palette} from './design';
import {FinishContext} from './Finish';

// New material studies, not the legacy Clareia icon library. These are
// decorative abstract forms, never fabricated scientific diagrams or metrics.
export const Material:React.FC<{palette:Palette;variant:number;photo?:string|null;figure?:string}>=({palette:p,variant,photo,figure})=>{
  const glass=useContext(FinishContext)==='vidro_avancado';
  if(photo)return <Img src={photo} style={{width:'100%',height:'100%',objectFit:'contain',background:p.surface}}/>;
  if(figure)return <div style={{position:'relative',width:'100%',height:'100%',background:`radial-gradient(ellipse at 50% 65%,${p.second}28,transparent 70%)`}}>
    <div style={{position:'absolute',left:'22%',top:'79%',width:'56%',height:'9%',borderRadius:'50%',background:'#0004',filter:'blur(8px)'}}/>
    <Img src={figure} style={{position:'absolute',left:'16%',top:'8%',width:'68%',height:'77%',objectFit:'contain',filter:glass?`drop-shadow(0 8px 7px #0005) drop-shadow(0 -1px 1px ${p.accent}38)`:'drop-shadow(0 6px 4px #0004)'}}/>
    {glass?<div aria-hidden="true" style={{position:'absolute',left:'16%',top:'8%',width:'68%',height:'77%',
      maskImage:`url("${figure}")`,maskSize:'contain',maskPosition:'center',maskRepeat:'no-repeat',
      background:'linear-gradient(125deg,transparent 15%,#ffffff42 31%,transparent 44%,#ffffff08 62%,#00000018 85%)',mixBlendMode:'soft-light'}}/>:null}
  </div>;
  // Without a safe subject match, keep a quiet decorative surface. Never
  // label a random planet, ribbon or document as a specific narrated object.
  return <div style={{width:'100%',height:'100%',background:`linear-gradient(135deg,${p.second}18,${p.surface},${p.accent}12)`}}/>;
};

// Material study retained as an explicitly decorative asset, not a fallback
// for unknown subject nouns. It is not used by semantic figure selection.
export const AbstractMaterial:React.FC<{palette:Palette;variant:number}>=({palette:p,variant})=>{
  const id=`mat-${variant}`;
  return <svg viewBox="0 0 600 440" width="100%" height="100%" aria-hidden="true">
    <defs>
      <radialGradient id={id+'-bg'}><stop stopColor={p.second} stopOpacity=".35"/><stop offset="1" stopColor={p.bg}/></radialGradient>
      <radialGradient id={id+'-orb'} cx="32%" cy="24%" r="80%"><stop stopColor="#fff"/><stop offset=".25" stopColor={p.accent}/><stop offset=".67" stopColor={p.second}/><stop offset="1" stopColor={p.bg}/></radialGradient>
      <linearGradient id={id+'-ribbon'} x1="0" y1="0" x2="1" y2="1"><stop stopColor={p.accent}/><stop offset=".48" stopColor="#fff"/><stop offset=".65" stopColor={p.second}/><stop offset="1" stopColor={p.bg}/></linearGradient>
      <radialGradient id={id+'-shadow'}><stop stopColor="#000" stopOpacity=".5"/><stop offset="1" stopColor="#000" stopOpacity="0"/></radialGradient>
    </defs>
    <rect width="600" height="440" fill={`url(#${id}-bg)`}/>
    <ellipse cx="310" cy="367" rx="205" ry="38" fill={`url(#${id}-shadow)`}/>
    {variant%3===0?<>
      <circle cx="304" cy="202" r="139" fill={`url(#${id}-orb)`}/>
      <ellipse cx="304" cy="202" rx="192" ry="60" fill="none" stroke={p.accent} strokeWidth="9" transform="rotate(-24 304 202)"/>
      <ellipse cx="304" cy="202" rx="164" ry="44" fill="none" stroke="#fff" strokeOpacity=".55" strokeWidth="2" transform="rotate(38 304 202)"/>
    </>:variant%3===1?<>
      {[0,1,2,3].map(i=><g key={i} transform={`translate(${145+i*45} ${92+i*36}) rotate(-22 120 80)`}>
        <rect width="235" height="140" rx="23" fill={i===3?p.accent:p.second} fillOpacity={.25+i*.15} stroke="#fff" strokeOpacity=".5"/>
        <path d="M24 40 H130 M24 65 H190 M24 90 H162" stroke={p.bg} strokeWidth="7" strokeLinecap="round" opacity=".4"/>
      </g>)}
    </>:<>
      {[0,1,2].map(i=><ellipse key={i} cx="300" cy="215" rx={170-i*32} ry={100-i*16} fill="none" stroke={`url(#${id}-ribbon)`} strokeWidth="30" transform={`rotate(${-40+i*42} 300 215)`}/>)}
      <circle cx="328" cy="186" r="34" fill={`url(#${id}-orb)`}/>
    </>}
  </svg>;
};
