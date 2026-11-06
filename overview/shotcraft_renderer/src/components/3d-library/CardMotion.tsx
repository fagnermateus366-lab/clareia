'use client';
import {useRef,useState} from 'react';
import {RoundedBox} from '@react-three/drei';
import {useThree} from '@react-three/fiber';
import {Group} from 'three';
import {Label,Material,Rod} from './Primitives';
import {Subject} from './Subjects';
import {useLibrary,useMotion} from './runtime';
import {cardPositions,framingBox,connectedModes,stackModes} from './layout';
import VolumeText from './VolumeText';

const textModes=new Set(['marker','relay','typing','focus','closing','banner','outline','code','crt','seal']);
const glassModes=new Set(['glass','panel','showcase','browser','cascade','depth']);
const ease=(v:number)=>1-Math.pow(1-Math.max(0,Math.min(1,v)),3);
const pastel=['#d9c0b9','#d8d1bc','#cccac2','#b9cdcb'];

function VolumeCard({label,subject,glass,window=false,small=false,showSubject=true}:{label:string;subject:string;glass:boolean;window?:boolean;small?:boolean;showSubject?:boolean}){
 const s=useLibrary(),w=window&&glass?3.6:small?1.45:1.8,h=window&&glass?1.65:small?1.75:2.18;
 return <group>
  <RoundedBox args={[w,h,.18]} radius={.12} smoothness={3} castShadow receiveShadow>
   {glass?<meshPhysicalMaterial color="#e2dcd0" roughness={.21} metalness={.05} transmission={.38} thickness={.18} transparent opacity={.72} clearcoat={1} wireframe={s.wireframe||s.theme==='wireframe'}/>:<Material color={pastel[(s.subjects||[]).indexOf(subject)%4]||'#d7cec1'}/>}
  </RoundedBox>
  {window?<><Rod start={[-w*.44,h*.37,.1]} end={[w*.44,h*.37,.1]} radius={.005} color="#ddd1c3"/>{[-.73,-.61,-.49].map((x,i)=><mesh key={x} position={[x,h*.43,.11]}><sphereGeometry args={[.022,8,6]}/><Material color={['#ca9b8e','#c7ba9f','#a7b5a4'][i]}/></mesh>)}</>:null}
  {showSubject?<group position={[0,.16,.4]} scale={window&&glass?.65:small?.73:.83}><Subject id={subject}/></group>:null}
  <Label text={label} position={[0,-h*.4,.13]} size={.19} maxWidth={w*.84} maxHeight={.24} color="#3b3937" face/>
 </group>;
}
function TextRow({text,index,mode}:{text:string;index:number;mode:string}){
 const s=useLibrary(),root=useRef<Group>(null),[letters,setLetters]=useState(mode==='typing'?0:text.length),last=useRef(-1);
 useMotion(t=>{
  const p=ease((t-index*.48)/.7);
  if(root.current){root.current.rotation.y=-.19+Math.sin(t*.25+index)*.035;root.current.rotation.x=-.08;root.current.position.x=(1-p)*-.12;
   root.current.scale.setScalar(mode==='relay'?Math.max(.001,p):mode==='focus'&&index===0?1.04:1);}
  if(mode==='typing'&&s.fixedTime===undefined){const count=Math.max(0,Math.min(text.length,Math.floor((t-index*.5)*14)));if(last.current!==count){last.current=count;setLetters(count);}}
 });
 const count=s.speed===0?text.length:s.fixedTime===undefined?letters:Math.max(0,Math.floor((s.fixedTime*s.speed-index*.5)*14));
 return <group ref={root} rotation={[-.08,-.19,0]}><VolumeText text={mode==='typing'?text.slice(0,count):text}/></group>;
}
function TextVolume({mode}:{mode:string}){
 const s=useLibrary(),root=useRef<Group>(null),lines=s.labels.slice(0,4);
 const background=['code','crt','banner','seal'].includes(mode);
 useMotion(t=>{if(!root.current)return;const p=ease(t/.8);root.current.position.set(0,(1-p)*(mode==='zoom'?.7:.2),0);root.current.scale.setScalar(mode==='focus'?.9+.1*p:mode==='closing'?1-.02*ease(t/3):.95+.05*p);});
 return <group ref={root} userData={{framingBox:{min:[-2.85,-lines.length*.45-.12,-.5],max:[2.85,lines.length*.45+.12,.7]}}}>
  {background?<RoundedBox args={[5.6,Math.max(2,lines.length*.88+.5),.3]} position={[0,0,-.35]} radius={mode==='crt'?.25:.09} smoothness={3} castShadow receiveShadow><Material color={mode==='crt'?'#263a34':mode==='seal'?'#c9b49d':'#d9d4c9'}/></RoundedBox>:null}
  {lines.map((line,i)=><group key={i} position={[0,(lines.length-1)*.45-i*.9,.2]}>
   <TextRow text={line} index={i} mode={mode}/>
   {mode==='marker'?<Rod start={[-2,-.4,-.03]} end={[2,-.4,-.03]} radius={.035} color={s.color}/>:null}
   {mode==='outline'?<RoundedBox args={[5,.75,.2]} radius={.04} smoothness={2} position={[0,0,-.22]}><meshStandardMaterial color={s.color} wireframe/></RoundedBox>:null}
  </group>)}
 </group>;
}
/** Shared real-mesh construction; each wrapper selects its own choreography. */
export default function CardMotion({mode}:{mode:string}){
 const s=useLibrary(),canvasAspect=useThree(state=>state.size.width/state.size.height),aspect=s.layoutAspect||canvasAspect,root=useRef<Group>(null),cards=useRef<(Group|null)[]>([]);
 const textOnly=textModes.has(mode),glass=glassModes.has(mode),stack=stackModes.has(mode);
 const labels=(s.labels.length?s.labels:['']).slice(0,4),n=labels.length,connected=connectedModes.has(mode),points=cardPositions(mode,n,aspect);
 useMotion((t,state)=>{
  if(root.current){root.current.rotation.y=mode==='dolly'?Math.sin(t*.18)*.06:0;root.current.position.y=mode==='glass'?Math.sin(t*.5)*.035:0;}
  cards.current.forEach((g,i)=>{if(!g)return;const target=points[i],p=ease((t-(s.cardStarts?.[i]??i*(mode==='impact'?.1:.16)))/.75),scale=mode==='reveal'?Math.max(.001,p):1;
   g.position.set(target[0]+(1-p)*(mode==='deal'?-4:0),target[1]+(1-p)*(mode==='steps'?-.6:.18),target[2]+(1-p)*(mode==='zoom'?2:.16));
   g.rotation.set((1-p)*.06,mode==='fan'?(i-(n-1)/2)*.08*(1-p):mode==='carousel'?Math.sin(t*.35-i*.7)*.12:mode==='browser'?(1-p)*-.3:0,mode==='deal'?(1-p)*-.45:0);
   if(mode==='carousel'){g.position.z+=Math.cos(t*.35-i*.7)*.18;g.position.x+=Math.sin(t*.35-i*.7)*.14;}
   if(mode==='vertical')g.position.y+=Math.sin(t*.3-i)*.035;
   if(mode==='ramp')g.position.x+=Math.sin(t*.24-i*.8)*.12;
   g.scale.setScalar(scale*(mode==='hero'&&i===0?1.08:mode==='mosaic'&&i===1?.92:1));
  });
 });
 if(textOnly)return <TextVolume mode={mode}/>;
 return <group ref={root} userData={{framingBox:framingBox(mode,points)}}>
  {connected&&points.slice(1).map((p,i)=><Rod key={i} start={points[i]} end={p} radius={.035} color="#a3b5b6"/>)}
  {mode==='spotlight'?<spotLight position={[-2,3,3]} angle={.6} intensity={5} penumbra={.7} color="#f0c5a2"/>:null}
  {labels.map((label,i)=><group key={i} position={points[i]} ref={node=>{cards.current[i]=node;}}>
   <VolumeCard label={label} subject={s.subjects?.[i]||s.subjects?.[0]||''} glass={glass} window={['browser','cascade'].includes(mode)} small={connected} showSubject={!stack||i===n-1}/>
  </group>)}
 </group>;
}
