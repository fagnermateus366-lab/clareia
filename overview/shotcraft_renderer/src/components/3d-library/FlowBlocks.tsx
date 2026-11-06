'use client';
import {Vector3Tuple} from 'three';
import {useLibrary} from './runtime';
import {Material,Label,Rod,colors} from './Primitives';
const positions:Vector3Tuple[]=[[0,-1.0,0],[-1.4,.1,0],[1.4,.1,0],[0,1.2,0]];
export default function FlowBlocks(){
 const s=useLibrary(),labels=s.labels.slice(0,4);
 return <group>{labels.map((label,i)=><group key={i} position={positions[i]}>
  <mesh castShadow receiveShadow><boxGeometry args={[1.28,.63,.55]}/><Material color={colors[i]}/></mesh>
  <Label text={label} position={[0,0,.292]} size={.14} color="#ffffff" face maxWidth={1.1} maxHeight={.4}/>
 </group>)}
 {labels.slice(1).map((_,i)=><Rod key={i} start={positions[Math.max(0,i-1)]} end={positions[i+1]} color={s.theme==='studio'?'#697787':'#e4e8ed'} radius={.04}/>)}
 </group>;
}
