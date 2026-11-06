'use client';
import {useRef} from 'react';
import {Center,Text3D} from '@react-three/drei';
import {Group} from 'three';
import {useLibrary,useMotion} from './runtime';
import {wrapWords} from './textLayout';
export default function ExtrudedText(){
 const s=useLibrary(),ref=useRef<Group>(null);
 useMotion((time,state)=>{if(ref.current){ref.current.rotation.y=Math.sin(time*.35)*.12+state.pointer.x*.25;ref.current.rotation.x=-state.pointer.y*.16;}});
 return <group ref={ref}><Center><Text3D font={s.fontUrl} size={.55} height={.20} bevelEnabled bevelSegments={3} bevelSize={.018} bevelThickness={.025} curveSegments={8} castShadow>
  {wrapWords(s.text,18)}<meshPhysicalMaterial color={s.color} roughness={.20} metalness={.75} clearcoat={1} wireframe={s.wireframe||s.theme==='wireframe'}/>
 </Text3D></Center></group>;
}
