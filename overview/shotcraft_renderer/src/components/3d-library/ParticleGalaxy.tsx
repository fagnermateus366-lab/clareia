'use client';
import {useMemo,useRef} from 'react';
import {Points} from 'three';
import {useLibrary,useMotion} from './runtime';
export default function ParticleGalaxy(){
 const s=useLibrary(),ref=useRef<Points>(null),count=s.quality==='alta'?14000:s.quality==='economica'?1800:6000;
 const positions=useMemo(()=>{const data=new Float32Array(count*3);for(let i=0;i<count;i++){const u=(i*.61803398875)%1,v=(i*.754877666)%1,r=.15+Math.sqrt(u)*2.7,angle=r*2.1+(i%4)*Math.PI/2+(v-.5)*.55;data[i*3]=Math.cos(angle)*r;data[i*3+1]=(v-.5)*.24*(1-r/3);data[i*3+2]=Math.sin(angle)*r;}return data;},[count]);
 useMotion((time,state)=>{if(ref.current){ref.current.rotation.y=time*.045+state.pointer.x*.18;ref.current.rotation.x=.30+state.pointer.y*.16;}});
 return <points ref={ref}><bufferGeometry><bufferAttribute attach="attributes-position" args={[positions,3]}/></bufferGeometry><pointsMaterial color={s.color} size={s.quality==='economica'?.035:.022} sizeAttenuation transparent opacity={.92} depthWrite={false}/></points>;
}
