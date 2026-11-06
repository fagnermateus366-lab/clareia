'use client';
import {useRef,useState} from 'react';
import {Group} from 'three';
import {useLibrary,useMotion} from './runtime';
import {Material,Label,colors} from './Primitives';
import {pyramidDemoCycle,tierProgress} from './pyramidTiming';
export default function PyramidLayers({exploded=false}:{exploded?:boolean}){
 const s=useLibrary(),root=useRef<Group>(null),tiers=useRef<(Group|null)[]>([]);
 const sequence=s.pyramid,source=s.labels.slice(0,6),[demoFirst,setDemoFirst]=useState(0),lastDemo=useRef(0);
 const labels=sequence?.labels||source.slice(demoFirst,demoFirst+3);
 const n=sequence?.capacity||3,step=.48+(exploded ? .16 : .025);
 useMotion(time=>{
  if(root.current)root.current.rotation.y=s.movement==='padrao'?Math.sin(time*.23)*.06:0;
  const demo=pyramidDemoCycle(time,source.length),clock=sequence?sequence.time:demo.time;
  if(!sequence&&lastDemo.current!==demo.first){lastDemo.current=demo.first;setDemoFirst(demo.first);}
  tiers.current.forEach((tier,i)=>{
   if(!tier)return;const start=sequence?sequence.starts[i]:i*2.5;
   const p=start===undefined?0:tierProgress(clock,start,s.speed);
   tier.visible=i<labels.length&&start!==undefined&&clock>=start;
   tier.position.y=-1.2+i*step+(1-p)*.32;
   tier.scale.y=.85+p*.15;
  });
 });
 // Include future tiers in the bounds: adding a phrase must not zoom the
 // camera or change the floor. Partial final cycles retain true tier sizes.
 return <group ref={root} position={[-.5,0,0]} userData={{framingBox:{min:[-2.15,-1.5,-1.65],max:[2.6,-.8+(n-1)*step,1.65]}}}>{Array.from({length:n},(_,i)=>{
  const bottom=1.6*(1-i/n),top=1.6*(1-(i+1)/n);
  return <group key={i} ref={node=>{tiers.current[i]=node;}} position={[0,-1.2+i*step,0]} visible={i<labels.length}>
   <mesh castShadow receiveShadow rotation={[0,Math.PI/4,0]}><cylinderGeometry args={[top,bottom,.45,4,1,false]}/><Material color={colors[i%colors.length]}/></mesh>
   <mesh position={[1.85,.08,0]} castShadow><boxGeometry args={[2.2,.28,.13]}/><Material color={colors[i%colors.length]}/></mesh>
   <Label text={labels[i]||''} position={[1.85,.08,.09]} color="#ffffff" size={.14} face maxWidth={2.0} maxHeight={.20}/>
  </group>;
 })}</group>;
}
