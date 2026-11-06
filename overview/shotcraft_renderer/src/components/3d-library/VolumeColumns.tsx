'use client';
import {useRef} from 'react';
import {Group} from 'three';
import {useLibrary,useMotion} from './runtime';
import {Material,Label,colors} from './Primitives';
export default function VolumeColumns(){
 const s=useLibrary(),root=useRef<Group>(null),labels=s.labels.slice(0,6);
 const max=Math.max(1,...(s.values||[]));
 useMotion(time=>{if(root.current)root.current.children.forEach((child,i)=>{child.scale.y=Math.min(1,Math.max(.015,(time-i*.18)*1.5));});});
 return <group ref={root} position={[0,-1.2,0]}>{labels.map((text,i)=>{const height=s.values?.length===labels.length ? .4+(s.values[i]/max)*2.1 : .7+i*.38,x=(i-(labels.length-1)/2)*.88;
  return <group key={i} position={[x,0,0]}><mesh position={[0,height/2,0]} castShadow receiveShadow><boxGeometry args={[.70,height,.78]}/><Material color={colors[i]}/></mesh>
   <Label text={text} position={[0,height+.28,0]} size={.11}/>
   {s.values?.length===labels.length?<Label text={String(s.values[i])} position={[0,height*.55,.43]} color="#ffffff" size={.16}/>:null}
  </group>;
 })}</group>;
}
