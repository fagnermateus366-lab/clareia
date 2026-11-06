/* Clareia's manual catalog. Choreography inspired by the pinned ShotCraft
 * recipes in third_party/video-shotcraft; no upstream product data or audio.
 * All geometry is calculated from the frame: seekable, deterministic, bounded.
 */
import React from 'react';
import {Img} from 'remotion';
import {Material} from './Art';
import {glassSurface,glassClass} from './Finish';
import {StackedWindows} from './StackedWindows';
import {Shot,clamp,ease,mix,ramp,sans,serif,fitSize,choreography,settled,rowLeft} from './design';

const Heading:React.FC<{s:Shot}>=({s})=>{
  const {width:w,height:h,beat:b,palette:p}=s;
  return <div style={{position:'absolute',left:w*.075,top:h*.145,width:w*.85,height:h*.16,fontFamily:sans,
    fontSize:fitSize(b.titulo,w*.85,h*.16,w*(h>w? .078:.052),2),fontWeight:760,lineHeight:1.07,letterSpacing:'-.035em',color:p.ink}}>{b.titulo}</div>;
};
const Label:React.FC<{text:string;width:number;height:number;max:number;color:string}>=({text,width,height,max,color})=>
  <div style={{fontFamily:sans,fontSize:fitSize(text,width,height,max,3),fontWeight:650,lineHeight:1.13,color,overflowWrap:'anywhere'}}>{text}</div>;

export const CardLayouts:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w,n=b.elementos.length;
  const horizontal=b.receita==='carrossel_horizontal',vertical=b.receita==='carrossel_vertical',mosaic=b.receita==='grade_mosaico';
  // Travel ends with a hold on the final item. No modulo/reset at a scene edge.
  const travel=s.animate?clamp((t-span*.12)/Math.max(1,s.length*.7)):0;
  const cursor=travel*(n-1),cols=portrait?2:Math.min(3,n),rows=Math.ceil(n/cols);
  const cw=horizontal?w*(portrait? .60:.40):vertical?w*(portrait? .73:.60):(w*.85-w*.025*(cols-1))/cols;
  const ch=horizontal?h*.43:vertical?h*.25:Math.min(h*.51/rows,h*.42);
  return <div style={{position:'absolute',inset:0,overflow:'hidden',perspective:w*1.4}}><Heading s={s}/>
    <div style={{position:'absolute',left:w*.04,top:h*.35,width:w*.92,height:h*.57,overflow:'hidden',maskImage:horizontal?'linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)':vertical?'linear-gradient(transparent,#000 8%,#000 92%,transparent)':'none'}}>
    {b.elementos.map((e,i)=>{
      const entry=ramp(t,i*span*.10,span*.30),distance=i-cursor,focus=clamp(1-Math.abs(distance)*.5);
      let x=rowLeft(i,n,cols,w*.035,w*.85,w*.025),y=Math.floor(i/cols)*(ch+h*.025),rotate=0,scale=1;
      if(horizontal){x=w*.46-cw/2+distance*(cw+w*.035);y=h*.055+Math.abs(distance)*h*.025;rotate=-distance*7;scale=.9+focus*.1}
      else if(vertical){x=w*.46-cw/2+Math.abs(distance)*w*.025;y=h*.14+distance*(ch+h*.025);scale=.9+focus*.1}
      else if(!mosaic){x=mix(-cw,x,entry);y=mix(h*.43,y,entry);rotate=mix(-28,0,entry)}
      let mw=cw,mh=ch;
      if(mosaic){
        mw=w*(i===0? .49:.33);mh=i===0?h*.51:(h*.51-(n-2)*h*.02)/(n-1);
        x=w*(i===0? .035:.55);y=i===0?0:(i-1)*(mh+h*.02);
      }
      return <div key={i} className={glassClass(s)} style={{position:'absolute',left:x,top:y,width:mw,height:mh,background:p.surface,border:`1px solid ${p.accent}60`,borderRadius:w*.015,
        opacity:(horizontal||vertical)?clamp(1-Math.max(0,Math.abs(distance)-1)*.7):entry,
        transform:`rotateY(${horizontal?rotate:0}deg) rotate(${horizontal?0:rotate}deg) scale(${scale})`,boxShadow:`0 ${h*.018}px ${h*.03}px #0004`,overflow:'hidden',...glassSurface(s)}}>
        <div style={{height:'65%'}}><Material palette={p} variant={i+1} photo={i===0?s.photo:null} figure={s.figures[e.figura||'']}/></div>
        <div style={{position:'absolute',left:'8%',right:'8%',top:'72%'}}><Label text={e.rotulo} width={mw*.84} height={mh*.22} max={w*(portrait? .042:.027)} color={p.ink}/></div>
        {mosaic?<div style={{position:'absolute',left:0,top:0,width:entry*100+'%',height:5,background:p.accent}}/>:null}
      </div>;
    })}</div>
  </div>;
};

export const Glass:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=s.animate?(s.visualLocal??s.local):Math.max(4,s.length),span=choreography(s),portrait=h>w,n=b.elementos.length;
  const panel=b.receita==='paineis_desfocados',showcase=b.receita==='vidro_vitrine',entry=ramp(t,0,span*.6);
  const cols=portrait?2:n,cw=(w*.82-w*.025*(cols-1))/cols,ch=h*(portrait? .22:.42);
  const surface={background:panel?'#ffffff20':'linear-gradient(135deg,#ffffff35,#ffffff09)',backdropFilter:`blur(${w*.018}px)`,
    border:'1px solid #ffffff60',boxShadow:`0 ${h*.025}px ${h*.05}px #0004,inset 0 1px 0 #ffffff70`,borderRadius:w*.025,...glassSurface(s)};
  return <div style={{position:'absolute',inset:0,overflow:'hidden',perspective:w*1.5}}>
    {[0,1,2].map(i=><div key={i} style={{position:'absolute',left:w*(-.1+i*.38),top:h*(.30+i*.12),width:w*.5,height:w*.5,borderRadius:'50%',
      background:`radial-gradient(circle,${i%2?p.second:p.accent}b0,transparent 68%)`,filter:`blur(${w*.035}px)`,transform:`translateY(${s.animate?Math.sin(s.timelineTime*.5+i)*h*.025:0}px)`}}/>)}
    <div style={{position:'absolute',inset:0,opacity:s.textOpacity??1}}><Heading s={s}/></div>
    {showcase?<div className={glassClass(s)} style={{position:'absolute',left:w*.10,top:h*.36,width:w*.80,height:h*.52,...surface,overflow:'hidden',opacity:entry,
      transform:`rotateY(${mix(-18,-4,entry)}deg) rotateX(${mix(12,3,entry)}deg) translateY(${(1-entry)*h*.12}px)`}}>
      <div style={{position:'absolute',left:'4%',top:'6%',width:portrait?'92%':'48%',height:portrait?'48%':'88%',borderRadius:w*.015,overflow:'hidden'}}><Material palette={p} variant={2} photo={s.photo} figure={s.figures[b.elementos[0]?.figura||'']}/></div>
      <div style={{position:'absolute',left:portrait?'7%':'57%',top:portrait?'60%':'12%',width:portrait?'86%':'36%',height:portrait?'34%':'76%',display:'flex',flexDirection:'column',justifyContent:'space-around'}}>
        {b.elementos.map((e,i)=><div key={i} style={{opacity:s.textOpacity??1,borderLeft:`3px solid ${p.accent}`,paddingLeft:w*.016}}><Label text={e.rotulo} width={w*(portrait? .64:.25)} height={h*.075} max={w*(portrait? .042:.025)} color={p.ink}/></div>)}
      </div></div>:panel?<div className={glassClass(s)} style={{position:'absolute',left:w*.09,top:h*.37,width:w*.82,height:h*.51,...surface,padding:w*.04,boxSizing:'border-box',clipPath:`inset(0 ${100*(1-entry)}% 0 0 round ${w*.025}px)`}}>
      {b.elementos.map((e,i)=><div key={i} style={{display:'flex',alignItems:'center',height:100/n+'%',gap:w*.04,borderBottom:i<n-1?'1px solid #ffffff40':'none',opacity:s.textOpacity??1}}>
        <span style={{fontFamily:serif,fontSize:w*(portrait? .09:.05),color:p.accent}}>{String(i+1).padStart(2,'0')}</span><Label text={e.rotulo} width={w*.6} height={h*.35/n} max={w*(portrait? .049:.032)} color={p.ink}/>
      </div>)}</div>:b.elementos.map((e,i)=>{const ent=ramp(t,i*span*.1,span*.4),x=rowLeft(i,n,cols,w*.09,w*.82,w*.025),y=h*.37+Math.floor(i/cols)*(ch+h*.025);
      return <div key={i} className={glassClass(s)} style={{position:'absolute',left:x,top:y,width:cw,height:ch,...surface,opacity:ent,transform:`translateY(${(1-ent)*h*.16}px) rotateY(${(1-ent)*-20}deg)`,overflow:'hidden'}}>
        <div style={{position:'absolute',left:'10%',top:'15%',width:'80%',height:'40%',borderRadius:'50%',background:`radial-gradient(ellipse,${p.accent}90,transparent 70%)`}}/>
        {s.figures[e.figura||'']?<div style={{position:'absolute',left:'5%',top:0,width:'90%',height:'60%'}}><Material palette={p} variant={i} figure={s.figures[e.figura||'']}/></div>:null}
        <div style={{position:'absolute',left:'10%',right:'10%',top:'62%',opacity:s.textOpacity??1}}><Label text={e.rotulo} width={cw*.8} height={ch*.28} max={w*(portrait? .04:.028)} color={p.ink}/></div>
      </div>})}
  </div>;
};

export const Interface:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w;
  if(b.receita==='janelas_cascata')return <><Heading s={s}/><StackedWindows {...s}/></>;
  const code=b.receita==='codigo_foco',cascade=b.receita==='janelas_cascata',entry=ramp(t,0,span*.6),n=b.elementos.length;
  const wx=w*.10,wy=h*.36,ww=w*.80,wh=h*.51;
  return <div style={{position:'absolute',inset:0,perspective:w*1.6,overflow:'hidden'}}><Heading s={s}/>
    <div style={{position:'absolute',left:w*.05,top:h*.31,width:w*.9,height:h*.6,background:`radial-gradient(ellipse,${p.second}40,transparent 70%)`}}/>
    {(cascade?b.elementos:[b.elementos[0]]).map((_,i)=>{
      const ent=ramp(t,i*span*.14,span*.4),back=cascade?n-i-1:0,small=cascade? .82:1;
      return <div key={i} className={glassClass(s)} style={{position:'absolute',left:wx+back*w*.032,top:wy+back*h*.033,width:ww*small,height:wh*small,
        background:code?'#111a23':p.surface,border:`1px solid ${p.accent}80`,borderRadius:w*.012,overflow:'hidden',boxShadow:`0 ${h*.03}px ${h*.05}px #0005`,opacity:ent,
        transformOrigin:'50% 50%',transform:`translateY(${(1-ent)*h*.25}px) rotateY(${mix(-12,0,entry)}deg) scale(${mix(.93,1,entry)})`,...glassSurface(s,code?'#111a23':p.surface)}}>
        <div style={{height:wh*.10,display:'flex',alignItems:'center',gap:w*.008,paddingLeft:w*.018,background:code?'#26313e':p.bg,borderBottom:`1px solid ${p.accent}50`}}>
          {[0,1,2].map(j=><span key={j} style={{width:w*.007,height:w*.007,borderRadius:'50%',background:[p.accent,p.second,p.muted][j]}}/>)}
          <span style={{fontFamily:sans,fontSize:w*(portrait? .021:.012),color:code?'#c9d6e2':p.muted,marginLeft:w*.015}}>Maquete ilustrativa · {code?'texto aprovado':'Clareia'}</span>
        </div>
        {code?<div style={{padding:w*.03,fontFamily:'Consolas,monospace'}}>
          {b.elementos.map((e,j)=>{const reveal=ramp(t,span*.2+j*span*.12,span*.25),focus=j===Math.min(n-1,Math.floor(clamp(t/Math.max(1,s.length*.8))*n));return <div key={j} style={{position:'relative',display:'flex',gap:w*.025,padding:`${h*.017}px ${w*.016}px`,background:focus?p.accent+'20':'transparent',borderLeft:`3px solid ${focus?p.accent:'transparent'}`,opacity:reveal}}>
            <span style={{color:'#718399',fontSize:w*(portrait? .033:.020)}}>{j+1}</span><span style={{color:j%2?'#d6e3ee':p.accent,fontSize:fitSize(e.rotulo,ww*.72,wh*.12,w*(portrait? .042:.028),2,'Consolas,monospace',500),whiteSpace:'pre-wrap'}}>{e.rotulo}</span>
          </div>})}</div>:s.photo?<Img src={s.photo} style={{position:'absolute',left:'3%',top:'16%',width:'94%',height:'79%',objectFit:'contain'}}/>:
          <div style={{padding:w*.035}}>
            <div style={{height:wh*.15,width:'65%',borderRadius:8,background:p.accent+'30',marginBottom:wh*.07}}/>
            {(cascade?[b.elementos[i]]:b.elementos).map((e,j)=><div key={j} style={{display:'flex',alignItems:'center',borderTop:`1px solid ${p.accent}30`,padding:`${h*.015}px 0`,opacity:ramp(t,span*.3+j*span*.08,span*.2)}}>
              <Label text={e.rotulo} width={ww*.8} height={wh*.13} max={w*(portrait? .039:.026)} color={p.ink}/>
            </div>)}
          </div>}
      </div>;
    })}
  </div>;
};

export const Diagrams:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w,n=b.elementos.length;
  const mind=b.receita==='mapa_mental',steps=b.receita==='conectores_etapas';
  const cw=w*(portrait? .35:.23),ch=h*(portrait? .14:.19),cx=w*.5,cy=h*.61;
  const positions=b.elementos.map((_,i)=>{
    if(mind){
      if(portrait){
        if(i===0)return {x:cx,y:h*.60};
        if(n===2)return {x:cx,y:h*.81};
        if(n===3)return {x:w*(i===1? .24:.76),y:h*.81};
        return i===1?{x:cx,y:h*.39}:{x:w*(i===2? .24:.76),y:h*.81};
      }
      if(i===0)return {x:cx,y:cy};const angle=(-90+(i-1)*360/Math.max(1,n-1))*Math.PI/180;
      return {x:cx+Math.cos(angle)*w*.28,y:cy+Math.sin(angle)*h*.21};
    }
    if(steps)return {x:portrait?w*(.28+i%2*.44):w*(.16+i*.68/Math.max(1,n-1)),y:portrait?h*(.41+Math.floor(i/2)*.28):h*(.52+i%2*.20)};
    if(portrait){
      if(i===0)return {x:cx,y:h*.43};
      if(n===2)return {x:cx,y:h*.75};
      if(n===3)return {x:w*(i===1? .25:.75),y:h*.75};
      return i===3?{x:cx,y:h*.87}:{x:w*(i===1? .25:.75),y:h*.68};
    }
    return i===0?{x:cx,y:h*.43}:{x:w*(.17+(i-1)*.66/Math.max(1,n-2)),y:h*.74};
  });
  const supported=['processo','rede','ciclo','linha_do_tempo'].includes(b.composicao);
  return <div style={{position:'absolute',inset:0,overflow:'hidden'}}><Heading s={s}/>
    <div style={{position:'absolute',inset:0,opacity:.09,backgroundImage:`radial-gradient(${p.ink} 1px,transparent 1px)`,backgroundSize:`${w*.025}px ${w*.025}px`}}/>
    <svg width={w} height={h} style={{position:'absolute',inset:0}} aria-hidden="true">
      {supported?positions.slice(1).map((end,i)=>{const start=positions[steps?i:0],mid=(start.y+end.y)/2,entry=ramp(t,span*.25+i*span*.14,span*.4);
        return <path key={i} d={`M${start.x},${start.y} C${start.x},${mid} ${end.x},${mid} ${end.x},${end.y}`} fill="none" stroke={p.accent} strokeWidth={Math.max(2,w*.003)} pathLength={1} strokeDasharray={1} strokeDashoffset={1-entry}/> }):null}
    </svg>
    {positions.map((pos,i)=>{const entry=ramp(t,i*span*.12,span*.35),main=mind&&i===0;return <div key={i} className={glassClass(s)} style={{position:'absolute',left:pos.x-cw/2,top:pos.y-ch/2,width:cw,height:ch,
      background:main?p.accent:p.surface,color:main?p.bg:p.ink,border:`${Math.max(1,w*.0015)}px solid ${p.accent}`,borderRadius:main?ch*.45:w*.016,
      boxShadow:`0 ${h*.012}px ${h*.025}px #0002`,display:'flex',alignItems:'center',justifyContent:'center',padding:w*.018,boxSizing:'border-box',opacity:entry,transform:`translateY(${(1-entry)*h*.07}px) scale(${mix(.90,1,entry)})`,...(!main?glassSurface(s):{})}}>
      {s.figures[b.elementos[i].figura||'']?<Img src={s.figures[b.elementos[i].figura||'']} style={{width:'27%',height:'70%',objectFit:'contain',marginRight:w*.012,flexShrink:0}}/>:null}
      <Label text={b.elementos[i].rotulo} width={(cw-w*.036)*(s.figures[b.elementos[i].figura||'']? .65:1)} height={ch*.65} max={w*(portrait? .04:.028)} color={main?p.bg:p.ink}/>
    </div>})}
  </div>;
};

export const Impact:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w,n=b.elementos.length;
  const grid=b.receita==='grade_impacto',speed=b.receita==='ritmo_acelerado';
  if(speed){
    // Nonlinear visual time only: arrive rapidly, hold, ease into the next item.
    const phase=clamp(t/Math.max(.3,s.length*.85)),chunk=phase*(n-1),index=Math.floor(chunk),u=chunk-index;
    const cursor=index+(u<.60?0:ease((u-.60)/.40)),cw=w*.69,ch=h*.39;
    return <div style={{position:'absolute',inset:0,overflow:'hidden'}}><Heading s={s}/>
      <div style={{position:'absolute',left:w*.04,top:h*.38,width:w*.92,height:h*.50,overflow:'hidden'}}>
        {b.elementos.map((e,i)=>{const d=i-cursor;return <div key={i} className={glassClass(s)} style={{position:'absolute',left:w*.46-cw/2+d*(cw+w*.045),top:h*.035,width:cw,height:ch,background:p.surface,
          border:`2px solid ${p.accent}`,borderRadius:w*.02,boxShadow:`0 ${h*.02}px ${h*.04}px #0004`,padding:w*.045,boxSizing:'border-box',display:'flex',alignItems:'center',transform:`scale(${1-Math.min(1,Math.abs(d))*.07})`,...glassSurface(s)}}>
          <Label text={e.rotulo} width={cw-w*.09} height={ch*.7} max={w*(portrait? .08:.06)} color={p.ink}/>
          <svg viewBox="0 0 600 300" style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:Math.max(0,1-Math.abs(d)*3)}}><ellipse cx="300" cy="150" rx="276" ry="127" fill="none" stroke={p.accent} strokeWidth="3" strokeDasharray="12 8"/></svg>
        </div>})}</div></div>;
  }
  const arrival=ramp(t,span*.08,span*.18),recoil=ramp(t,span*.26,span*.25),scale=t<span*.26?mix(2.7,1.05,arrival):mix(1.05,1,recoil);
  const cols=portrait?2:n,cw=(w*.86-(cols-1)*w*.02)/cols,ch=h*(portrait? .24:.40);
  return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:`linear-gradient(125deg,${p.accent}15,transparent 60%)`}}/>
    {grid?<><Heading s={s}/>{b.elementos.map((e,i)=>{const ent=ramp(t,i*span*.12,span*.18);return <div key={i} className={glassClass(s)} style={{position:'absolute',left:rowLeft(i,n,cols,w*.07,w*.86,w*.02),top:h*.36+Math.floor(i/cols)*(ch+h*.025),width:cw,height:ch,
      background:i%2?p.surface:p.accent,borderRadius:w*.009,opacity:ent,transform:`translate(${(1-ent)*w*.4*(i%2?-1:1)}px,${(1-ent)*h*.5}px) scale(${mix(1.35,1,ent)})`,padding:w*.025,boxSizing:'border-box',display:'flex',alignItems:'center',...glassSurface(s)}}>
      <Label text={e.rotulo} width={cw-w*.05} height={ch*.75} max={w*(portrait? .063:.046)} color={s.finish!=='original'||i%2?p.ink:p.bg}/>
    </div>})}</>:<div style={{position:'absolute',left:w*.075,top:h*.26,width:w*.85,height:h*.61,transform:`scale(${s.animate?scale:1})`,opacity:ramp(t,0,span*.12)}}>
      <div className={glassClass(s)} style={{position:'absolute',inset:0,border:`2px solid ${p.accent}`,borderRadius:w*.02,background:p.surface,boxShadow:`0 0 ${w*.08}px ${p.accent}35`,...glassSurface(s)}}/>
      <div style={{position:'absolute',left:'7%',top:'14%',width:'86%'}}><Label text={b.titulo} width={w*.73} height={h*.32} max={w*(portrait? .12:.085)} color={p.ink}/></div>
      <div style={{position:'absolute',left:'7%',bottom:'12%',width:'86%',display:'flex',gap:w*.02,flexWrap:'wrap',fontFamily:sans,fontSize:w*(portrait? .036:.022),color:p.accent}}>{b.elementos.map((e,i)=><span key={i}>{e.rotulo}</span>)}</div>
    </div>}
  </div>;
};

export const Retro:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w;
  const stamp=b.receita==='selo_carimbado',entry=ramp(t,0,span*.40),accent=stamp?p.accent:'#a6edba';
  if(stamp)return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
    <div className={glassClass(s)} style={{position:'absolute',left:w*.09,top:h*.16,width:w*.82,height:h*.72,background:p.surface,boxShadow:`0 ${h*.025}px ${h*.05}px #0004`,transform:'rotate(-2deg)',borderRadius:3,...glassSurface(s)}}/>
    <div style={{position:'absolute',left:w*.17,top:h*.31,width:w*.66,height:h*.39,border:`${w*.006}px double ${accent}`,borderRadius:w*.025,
      transform:`rotate(-7deg) scale(${s.animate?mix(1.65,1,entry):1})`,opacity:entry,color:accent,display:'flex',alignItems:'center',justifyContent:'center',padding:w*.04,boxSizing:'border-box'}}>
      <Label text={b.titulo.toLocaleUpperCase('pt-BR')} width={w*.56} height={h*.30} max={w*(portrait? .10:.07)} color={accent}/>
    </div>
    <div style={{position:'absolute',left:w*.16,top:h*.77,width:w*.68,display:'flex',gap:w*.02,flexWrap:'wrap',fontFamily:serif,fontSize:w*(portrait? .031:.023),color:p.ink}}>{b.elementos.map((e,i)=><span key={i} style={{borderBottom:`1px solid ${accent}`,paddingBottom:4,opacity:ramp(t,span*.4+i*span*.12,span*.22)}}>{e.rotulo}</span>)}</div>
  </div>;
  const ww=w*.84,wh=h*.68;
  return <div style={{position:'absolute',inset:0,overflow:'hidden',background:s.finish==='original'?'#101a17':'transparent'}}>
    <div style={{position:'absolute',left:w*.07,top:h*.17,width:w*.86,height:h*.73,borderRadius:w*.05,background:'linear-gradient(135deg,#687066,#202b26)',boxShadow:`inset 0 0 ${w*.02}px #000,0 ${h*.02}px ${h*.04}px #0008`}}/>
    <div style={{position:'absolute',left:w*.08,top:h*.18,width:ww,height:wh,borderRadius:w*.045,background:'#06140e',boxShadow:`inset 0 0 ${w*.05}px #000`,overflow:'hidden'}}>
      <div style={{position:'absolute',left:'8%',top:'10%',width:'84%',height:'80%',clipPath:`inset(0 0 ${(1-entry)*100}% 0)`}}>
        <div style={{fontFamily:'Consolas,monospace',fontSize:fitSize(b.titulo,ww*.84,wh*.28,w*(portrait? .07:.045),3,'Consolas,monospace',600),fontWeight:600,lineHeight:1.14,color:accent,textShadow:`0 0 ${w*.008}px #5fd48f80`}}>{b.titulo}</div>
        <div style={{marginTop:wh*.09}}>{b.elementos.map((e,i)=><div key={i} style={{fontFamily:'Consolas,monospace',fontSize:fitSize(e.rotulo,ww*.8,wh*.10,w*(portrait? .037:.026),2),lineHeight:1.15,color:accent,padding:`${wh*.018}px 0`,opacity:ramp(t,span*.2+i*span*.1,span*.25)}}>› {e.rotulo}</div>)}</div>
      </div>
      <div style={{position:'absolute',inset:0,pointerEvents:'none',opacity:.13,background:'repeating-linear-gradient(0deg,#000 0px,#000 1px,transparent 1px,transparent 4px)'}}/>
      <div style={{position:'absolute',left:0,top:wh*entry,width:'100%',height:2,opacity:entry<1? .4:0,background:accent,boxShadow:`0 0 18px ${accent}`}}/>
    </div>
    <div style={{position:'absolute',left:w*.14,top:h*.875,fontFamily:sans,fontSize:w*(portrait? .019:.011),letterSpacing:'.2em',color:'#aebbb0'}}>CLAREIA / ARQUIVO VISUAL</div>
  </div>;
};

export const TextBanners:React.FC<Shot>=(s)=>{
  const {width:w,height:h,beat:b,palette:p}=s,t=settled(s),span=choreography(s),portrait=h>w,entry=ramp(t,0,span*.5),outline=b.receita==='contorno_preenchido';
  const size=fitSize(b.titulo,w*.78,h*.37,w*(portrait? .14:.105),3);
  return <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
    {s.photo?<Img src={s.photo} style={{position:'absolute',left:w*.07,top:h*.16,width:w*.86,height:h*.71,objectFit:'contain',opacity:.2}}/>:null}
    {outline?<div style={{position:'absolute',left:w*.08,top:h*.29,width:w*.84,height:h*.45,fontFamily:sans,fontWeight:850,fontSize:size,lineHeight:1.06,letterSpacing:'-.05em'}}>
      <div style={{position:'absolute',inset:0,color:'transparent',WebkitTextStroke:`${Math.max(1,w*.0018)}px ${p.ink}`}}>{b.titulo}</div>
      <div style={{position:'absolute',inset:0,color:p.accent,clipPath:`inset(0 ${100*(1-entry)}% 0 0)`}}>{b.titulo}</div>
    </div>:<div style={{position:'absolute',left:w*.07,top:h*.33,width:w*.86,height:h*.37,background:p.accent,clipPath:`inset(0 ${100*(1-entry)}% 0 0)`,transform:`skewY(-2deg)`,boxShadow:`0 ${h*.02}px ${h*.04}px #0003`}}>
      <div style={{padding:`${h*.035}px ${w*.04}px`,transform:'skewY(2deg)',opacity:ramp(t,span*.25,span*.3)}}><Label text={b.titulo} width={w*.78} height={h*.29} max={size} color={p.bg}/></div>
    </div>}
    <div style={{position:'absolute',left:w*.09,top:h*.79,width:w*.82,display:'flex',gap:w*.025,flexWrap:'wrap',fontFamily:sans,fontSize:w*(portrait? .035:.026),color:p.ink}}>{b.elementos.map((e,i)=><span key={i} style={{opacity:ramp(t,span*.4+i*span*.12,span*.25)}}>{e.rotulo}</span>)}</div>
  </div>;
};
