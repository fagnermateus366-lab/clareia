'use client';
import {RoundedBox} from '@react-three/drei';
import {useRef} from 'react';
import {Group} from 'three';
import {useLibrary,useMotion} from './runtime';
import {Material,Label} from './Primitives';
export default function ProductCard(){
 const s=useLibrary(),product=useRef<Group>(null);
 useMotion((time,state)=>{if(product.current){product.current.rotation.y=Math.sin(time*.22)*.22+state.pointer.x*.18;product.current.position.y=.25+Math.sin(time*.6)*.04;}});
 return <group><mesh position={[0,-1.0,0]} receiveShadow castShadow><cylinderGeometry args={[1.5,1.6,.30,48]}/><Material color={s.theme==='studio'?'#e3e7e9':'#29313c'}/></mesh>
  <group ref={product} onClick={e=>{e.stopPropagation();s.onSelect?.('Gadget · cor editável no painel');}}>
   <RoundedBox args={[1.35,2.1,.3]} radius={.13} smoothness={4} castShadow><Material color={s.color} metalness={.6}/></RoundedBox>
   <RoundedBox args={[1.15,1.75,.03]} radius={.075} position={[0,.02,.17]}><meshPhysicalMaterial color="#091a24" roughness={.12} metalness={.45} clearcoat={1} wireframe={s.wireframe}/></RoundedBox>
   {[0,1,2].map(i=><mesh key={i} position={[-.25+i*.25,.68,.197]} castShadow><circleGeometry args={[.075,24]}/><Material color="#529cbb" metalness={.8}/></mesh>)}
  </group><Label text="Explore cada detalhe" position={[0,-1.6,0]} size={.15}/>
 </group>;
}
