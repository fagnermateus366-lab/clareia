'use client';
import {useRef} from 'react';
import {Group,Vector3Tuple} from 'three';
import {useLibrary,useMotion} from './runtime';
import {Material,Label,Callout,colors} from './Primitives';
const places:Vector3Tuple[]=[[0,1.1,0],[1.1,0,0],[0,-1.1,0],[-1.1,0,0]];
export default function RadialCubes(){
 const s=useLibrary(),root=useRef<Group>(null);
 useMotion(time=>{if(root.current)root.current.rotation.y=Math.sin(time*.3)*.10;});
 return <group ref={root}>{s.labels.slice(0,4).map((label,i)=><group key={i} position={places[i]}>
  <mesh rotation={[0,0,Math.PI/4]} castShadow receiveShadow><boxGeometry args={[1.1,1.1,.8]}/><Material color={colors[(i+2)%colors.length]}/></mesh>
  <Label text={String(i+1).padStart(2,'0')} position={[0,0,.421]} color="#ffffff" size={.19} face maxWidth={.65} maxHeight={.4}/>
  <Callout text={label} anchor={[0,0,0]} side={i===2||i===3?-1:1} radius={.85} vertical={i===0||i===2} maxWidth={1.5} color={colors[(i+2)%colors.length]}/>
 </group>)}</group>;
}
