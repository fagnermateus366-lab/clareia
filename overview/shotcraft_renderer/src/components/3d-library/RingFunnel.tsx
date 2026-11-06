'use client';
import {useMemo,useEffect} from 'react';
import {Shape,Path,ExtrudeGeometry} from 'three';
import {useLibrary} from './runtime';
import {Material,Callout,colors} from './Primitives';
function Ring({radius,color}:{radius:number;color:string}){
 const geometry=useMemo(()=>{const shape=new Shape();shape.absarc(0,0,radius,0,Math.PI*2,false);const hole=new Path();hole.absarc(0,0,radius*.56,0,Math.PI*2,true);shape.holes.push(hole);return new ExtrudeGeometry(shape,{depth:.22,bevelEnabled:true,bevelSize:.014,bevelThickness:.012,bevelSegments:2,curveSegments:32});},[radius]);
 useEffect(()=>()=>geometry.dispose(),[geometry]);
 return <mesh geometry={geometry} rotation={[-Math.PI/2,0,0]} castShadow receiveShadow><Material color={color}/></mesh>;
}
export default function RingFunnel(){
 const s=useLibrary(),labels=s.labels.slice(0,6),n=labels.length;
 return <group>{labels.map((text,i)=>{const r=1.4-i*.15,y=1.1-i*.50,side=i%2?-1:1;
  return <group key={i}><group position={[0,y,0]}><Ring radius={r} color={colors[i]}/></group>
   <Callout text={`${String(i+1).padStart(2,'0')}  ${text}`} anchor={[0,y+.13,0]} side={side} radius={r} color={colors[i]}/>
  </group>;
 })}{n===0?null:null}</group>;
}
