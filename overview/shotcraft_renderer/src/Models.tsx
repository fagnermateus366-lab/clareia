/*
 * ShotCraft-derived motion models: copyright 2026 Wei Yihao, Apache-2.0.
 * Native Clareia adaptations of CardStack, LeadWordZoomAssemble,
 * WordRelayFilmstrip, MultiplaneReal and TimelineTravel. Original files and
 * attribution are in third_party/video-shotcraft/. Text/art/data are replaced
 * with this project's approved headings, elements and optional source photo.
 */
import React from 'react';
import {Img,spring} from 'remotion';
import {Material} from './Art';
import {glassSurface,glassClass} from './Finish';
import {Shot,clamp,ease,mix,ramp,sans,serif,fitSize,measure,choreography,settled,rowLeft} from './design';

export const Kinetic:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w;
  const size=fitSize(b.titulo,w*.86,h*.47,portrait?w*.13:w*.105,3);
  const words=b.titulo.split(/\s+/),lead=words[0],rest=words.slice(1).join(' ');
  const leadScale=mix(1.7,1,ramp(t,span*.14,span*.38)),assemble=ramp(t,span*.25,span*.4);
  const start=ramp(t,0,span*.14),marked=ramp(t,span*.62,span*.18);
  const typing=b.receita==='digitacao',relay=b.receita==='palavras_encadeadas';
  const visible=typing?b.titulo.slice(0,Math.ceil(b.titulo.length*clamp(t/(span*.65)))):b.titulo;
  return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
    <div style={{position:'absolute',width:w*.64,height:w*.64,borderRadius:'50%',left:w*.58,top:-w*.25,
      background:`radial-gradient(circle,${p.accent}25,transparent 65%)`,transform:`scale(${1+.04*ease(t/span)})`}}/>
    <div style={{position:'absolute',left:w*.07,top:h*.22,width:w*.86,height:h*.48,display:'flex',alignItems:'center'}}>
      <div style={{fontFamily:b.receita==='conclusao_limpa'?serif:sans,fontWeight:780,fontSize:size,lineHeight:1.05,letterSpacing:'-.055em',color:p.ink,
        opacity:start,transform:`translateY(${(1-start)*h*.035}px)`,overflowWrap:'anywhere'}}>
        {typing?visible:relay?words.map((word,i)=>{const entry=ramp(t,i*span*.42/words.length,span*.22);return <React.Fragment key={i}><span style={{display:'inline-block',opacity:entry,color:i===0?p.accent:p.ink,
          transform:`translateY(${(1-entry)*size*.5}px) rotateX(${(1-entry)*65}deg)`,filter:`blur(${(1-entry)*4}px)`}}>{word}</span>{' '}</React.Fragment>}):<><span style={{display:'inline-block',transformOrigin:'left center',transform:`scale(${b.receita==='titulo_foco'?leadScale:1})`}}>{lead}</span>{' '}
          <span style={{opacity:assemble,filter:`blur(${(1-assemble)*5}px)`,position:'relative',left:(1-assemble)*w*.08}}>{rest}</span></>}
        {typing?<span style={{display:'inline-block',height:size*.85,width:Math.max(2,size*.035),background:p.accent,marginLeft:8,verticalAlign:'baseline',opacity:t<span?1:0}}/>:null}
      </div>
    </div>
    {b.receita==='titulo_marcado'?<div style={{position:'absolute',left:w*.07,top:h*.70,height:Math.max(3,h*.008),width:w*.54*marked,background:p.accent,transform:'rotate(-1deg)',borderRadius:'70% 30% 50% 40%'}}/>:null}
    <div style={{position:'absolute',left:w*.075,top:h*.78,width:w*.85,display:'flex',gap:w*.025,flexWrap:'wrap'}}>
      {b.elementos.map((e,i)=>{const enter=ramp(t,span*.45+i*span*.09,span*.25)*(b.receita==='conclusao_limpa'?1-ramp(t,s.length*.70,s.length*.18):1);return <div key={i} style={{fontFamily:serif,fontStyle:'italic',fontSize:portrait?w*.038:w*.026,color:i===0?p.accent:p.muted,
        borderBottom:`1px solid ${p.accent}70`,paddingBottom:h*.012,opacity:enter,transform:`translateY(${(1-enter)*18}px)`}}>{e.rotulo}</div>})}
    </div>
  </div>;
};

export const Spatial:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w;
  const n=b.elementos.length,cols=portrait?Math.min(2,n):n,rows=Math.ceil(n/cols);
  const cw=(w*.86-(cols-1)*w*.035)/cols,ch=Math.min(h*(portrait? .29:.48),(h*.65-(rows-1)*h*.025)/rows);
  const top=h*(portrait? .31:.34),fan=ramp(t,span*.33,span*.44);
  const titleSize=fitSize(b.titulo,w*.86,h*.18,portrait?w*.075:w*.049,2);
  return <div style={{position:'absolute',inset:0,perspective:w*1.3,overflow:'hidden'}}>
    <div style={{position:'absolute',left:w*.07,top:h*.14,width:w*.86,fontFamily:sans,fontSize:titleSize,fontWeight:760,lineHeight:1.08,color:p.ink,letterSpacing:'-.045em'}}>{b.titulo}</div>
    <div style={{position:'absolute',left:w*.08,top:h*.79,width:w*.84,height:h*.1,borderRadius:'50%',background:'#0003',filter:`blur(${h*.025}px)`,opacity:.4}}/>
    <div style={{position:'absolute',inset:0,transform:s.camera&&b.receita==='camera_suave'?`scale(${mix(1.055,1,ramp(t,0,span))})`:'none',transformOrigin:`50% ${h*.6}px`,transformStyle:'preserve-3d'}}>
    {b.elementos.map((e,i)=>{
      const row=Math.floor(i/cols),endX=rowLeft(i,n,cols,w*.07,w*.86,w*.035),endY=top+row*(ch+h*.025);
      const delay=i*span*.055,entry=s.animate?spring({fps:24,frame:Math.max(0,(t-delay)*24/(Math.max(.2,span*.35))),config:{damping:20,stiffness:95,mass:1}}):1;
      const startX=w/2-cw/2,startY=top+h*.12;
      const parallax=b.receita==='camadas_profundidade',slide=ramp(t,0,span*.8);
      const x=parallax?endX+(1-slide)*w*.15*(.6+i*.35):mix(startX,endX,fan),y=parallax?endY+(1-entry)*h*.03:mix(startY,endY,fan)+(1-entry)*h*.65;
      const theta=mix((i-(n-1)/2)*7,portrait?0:(i-(n-1)/2)*2,fan);
      const focus=i===(b.foco||0),lift=focus?ramp(t,span*.70,span*.22):0;
      const spotlight=b.receita==='foco_luz',hero=b.receita==='destaque_icone';
      return <div key={i} className={glassClass(s)} style={{position:'absolute',left:x,top:y,width:cw,height:ch,transformOrigin:'50% 120%',
        transform:`translateZ(${12+i*(parallax?12:2)+lift*(hero?26:15)}px) rotateX(${mix(8,0,fan)}deg) rotateY(${mix(-14,0,fan)}deg) rotate(${theta}deg) scale(${hero&&focus?1+lift*.035:1})`,
        background:p.surface,borderRadius:Math.max(8,w*.009),overflow:'hidden',border:`1px solid ${focus?p.accent+'80':p.ink+'18'}`,
        boxShadow:`${w*.005}px ${h*.018+lift*4}px ${h*.04}px #0003, 0 2px 3px #0002${spotlight&&focus?`,0 0 ${w*.025}px ${p.accent}35`:''}`,opacity:clamp(entry)*(spotlight&&!focus? .38:1),...glassSurface(s)}}>
        <div style={{position:'absolute',left:0,top:0,width:'100%',height:'68%'}}><Material palette={p} variant={i} photo={i===0?s.photo:null} figure={s.figures[e.figura||'']}/></div>
        <div style={{position:'absolute',left:'8%',top:'75%',width:'84%',color:p.ink,fontFamily:sans,fontWeight:650,
          fontSize:fitSize(e.rotulo,cw*.84,ch*.19,portrait?w*.036:w*.022,2),lineHeight:1.12}}>{e.rotulo}</div>
        <div style={{position:'absolute',left:0,top:0,width:'100%',height:'100%',background:'linear-gradient(135deg,#ffffff18,transparent 38%,#00000010)',pointerEvents:'none'}}/>
      </div>;
    })}
    </div>
  </div>;
};

export const Editorial:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w;
  const enter=ramp(t,0,span*.4),comparison=b.receita==='comparacao_revelada'&&b.elementos.length===2;
  const titleSize=fitSize(b.titulo,w*.85,h*.20,portrait?w*.09:w*.06,2,serif,600);
  if(b.receita==='linha_tempo'){
    const n=b.elementos.length,cols=portrait?2:n,rows=Math.ceil(n/cols),gap=w*.025,cw=(w*.86-gap*(cols-1))/cols;
    const ch=h*(portrait? .225:.30),start=h*.40,advance=ramp(t,span*.1,span*.75);
    return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
      <div style={{position:'absolute',left:w*.07,top:h*.14,width:w*.86,fontFamily:serif,fontSize:titleSize,lineHeight:1.06,color:p.ink}}>{b.titulo}</div>
      <svg width={w} height={h} style={{position:'absolute',inset:0}} aria-hidden="true">
        {Array.from({length:rows},(_,row)=><line key={row} x1={w*.07} y1={start+row*(ch+h*.06)+ch*.82} x2={w*.07+w*.86*advance} y2={start+row*(ch+h*.06)+ch*.82} stroke={p.accent} strokeWidth={Math.max(2,w*.002)}/>)}
      </svg>
      {b.elementos.map((e,i)=>{const entry=ramp(t,i*span*.14,span*.3),x=rowLeft(i,n,cols,w*.07,w*.86,gap),y=start+Math.floor(i/cols)*(ch+h*.06);return <div key={i} style={{position:'absolute',left:x,top:y,width:cw,height:ch,opacity:entry,transform:`translateY(${(1-entry)*h*.045}px)`}}>
        <div className={glassClass(s)} style={{position:'absolute',inset:'0 0 25%',border:`1px solid ${p.accent}60`,borderRadius:12,background:p.surface,boxShadow:`0 8px 20px #0002`,padding:'9%',fontFamily:sans,fontWeight:600,
          color:p.ink,fontSize:fitSize(e.rotulo,cw*.82,ch*.50,portrait?w*.04:w*.026,3),lineHeight:1.1,...glassSurface(s)}}>{e.rotulo}</div>
        <div style={{position:'absolute',left:'48%',top:'78%',width:Math.max(8,w*.009),height:Math.max(8,w*.009),borderRadius:'50%',background:p.accent,boxShadow:`0 0 18px ${p.accent}60`}}/>
      </div>})}
    </div>;
  }
  return <div style={{position:'absolute',inset:0,perspective:w*1.2,overflow:'hidden'}}>
    <div style={{position:'absolute',left:w*.07,top:h*.135,width:w*.86,fontFamily:serif,fontSize:titleSize,lineHeight:1.04,fontWeight:550,color:p.ink,letterSpacing:'-.04em'}}>{b.titulo}</div>
    <div style={{position:'absolute',left:w*.07,top:h*.38,width:w*.86,height:h*.51,display:'grid',gap:w*.025,
      gridTemplateColumns:comparison?'1fr 1fr':portrait?'1fr':'1.25fr 1fr',transform:`rotateX(${(1-enter)*10}deg) translateY(${(1-enter)*h*.07}px)`,opacity:enter}}>
      <div className={glassClass(s)} style={{position:'relative',overflow:'hidden',borderRadius:w*.008,background:p.surface,boxShadow:`0 ${h*.012}px ${h*.025}px #0002`,...glassSurface(s)}}>
        <div style={{position:'absolute',inset:0}}><Material palette={p} variant={2} photo={s.photo} figure={s.figures[b.elementos[0]?.figura||'']}/></div>
        <div style={{position:'absolute',inset:0,background:`linear-gradient(transparent 42%,${p.bg}f0)`}}/>
        <div style={{position:'absolute',left:'7%',bottom:'8%',width:'86%',fontFamily:serif,fontStyle:'italic',fontSize:portrait?w*.055:w*.037,color:p.ink}}>{b.elementos[0]?.rotulo}</div>
      </div>
      {portrait&&!comparison?null:<div style={{display:'flex',flexDirection:'column',justifyContent:'center',gap:h*.025}}>
        {b.elementos.slice(comparison?1:0).map((e,i)=>{const entry=ramp(t,span*.25+i*span*.10,span*.3);return <div key={i} style={{borderTop:`1px solid ${p.accent}80`,paddingTop:h*.012,
          color:p.ink,fontFamily:sans,fontWeight:540,fontSize:fitSize(e.rotulo,w*.35,h*.10,w*.029,2),lineHeight:1.13,
          opacity:entry,transform:`translateX(${(1-entry)*w*.04}px)`}}>{b.receita==='lista_progressiva'?<span style={{fontFamily:serif,fontStyle:'italic',color:p.accent,marginRight:w*.014}}>{i+1}.</span>:null}{e.rotulo}</div>})}
      </div>}
    </div>
    {portrait&&!comparison?<div style={{position:'absolute',left:w*.07,top:h*.81,width:w*.86,display:'flex',gap:w*.025,flexWrap:'wrap'}}>
      {b.elementos.slice(1).map((e,i)=><span key={i} style={{fontFamily:sans,fontSize:w*.032,color:p.ink,background:p.surface,padding:'8px 12px',borderRadius:8}}>{e.rotulo}</span>)}
    </div>:null}
  </div>;
};

export const Luminous:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w;
  const n=b.elementos.length,cols=portrait?2:n,rows=Math.ceil(n/cols),left=w*.08,top=h*.42;
  const positions=b.elementos.map((_,i)=>({x:rowLeft(i,n,cols,left,w*.84,0)+w*.42/cols,y:top+(Math.floor(i/cols)+.4)*h*.46/rows}));
  const titleSize=fitSize(b.titulo,w*.85,h*.22,portrait?w*.08:w*.06,2);
  const connect=['rede','processo','linha_do_tempo','ciclo'].includes(b.composicao);
  return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:`radial-gradient(ellipse at 50% 65%,${p.second}20,transparent 70%)`}}/>
    <div style={{position:'absolute',left:w*.075,top:h*.14,width:w*.85,fontFamily:sans,fontSize:titleSize,lineHeight:1.07,fontWeight:730,color:p.ink,letterSpacing:'-.04em'}}>{b.titulo}</div>
    <svg width={w} height={h} style={{position:'absolute',inset:0}} aria-hidden="true">
      {connect?positions.slice(1).map((end,i)=>{const start=positions[b.composicao==='rede'?0:i],entry=ramp(t,span*.25+i*span*.1,span*.5),mid=(start.x+end.x)/2;return <path key={i}
        d={`M${start.x},${start.y} C${mid},${start.y-h*.09} ${mid},${end.y+h*.09} ${end.x},${end.y}`} fill="none" stroke={p.accent} strokeWidth={Math.max(2,w*.002)} pathLength={1} strokeDasharray={1} strokeDashoffset={1-entry}/> }):null}
    </svg>
    {positions.map((pos,i)=>{const entry=ramp(t,i*span*.08,span*.5),r=Math.min(w*.11,w*.26/cols),size=r*2;
      return <div key={i} style={{position:'absolute',left:pos.x-r,top:pos.y-r,width:size,height:size,opacity:entry,transform:`scale(${mix(.72,1,entry)})`}}>
        {s.figures[b.elementos[i].figura||'']?<div style={{position:'absolute',inset:0,clipPath:b.receita==='traco_progressivo'?`circle(${entry*74}% at 50% 50%)`:'none'}}><Material palette={p} variant={i} figure={s.figures[b.elementos[i].figura||'']}/></div>:
          <div style={{position:'absolute',inset:'12%',borderRadius:w*.02,border:`1px solid ${p.accent}60`,background:p.surface}}/>}
        <div style={{position:'absolute',left:-r*.5,top:size+size*.16,width:size+r,color:p.ink,textAlign:'center',fontFamily:sans,fontWeight:550,
          fontSize:fitSize(b.elementos[i].rotulo,size+r,h*.1,portrait?w*.035:w*.025,2),lineHeight:1.1}}>{b.elementos[i].rotulo}</div>
      </div>;
    })}
  </div>;
};
