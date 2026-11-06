'use client';
import {useMemo,useRef,useLayoutEffect} from 'react';
import {InstancedMesh,Object3D,Vector3Tuple,Color} from 'three';
import {useLibrary} from './runtime';
import {Rod,Label} from './Primitives';
export default function ScatterPlot(){
 const s=useLibrary(),ref=useRef<InstancedMesh>(null);
 const data=useMemo(()=>{
  const points=s.dataPoints?.length?s.dataPoints:Array.from({length:48},(_,i)=>({x:((i*17)%47)/47*3,y:((i*23)%43)/43*2.7,z:((i*29)%41)/41*3,label:`Ponto ${i+1}`}));
  const axes=['x','y','z'] as const,range=axes.map(axis=>{const a=points.map(p=>p[axis]);return {min:Math.min(...a),span:Math.max(...a)-Math.min(...a)||1};});
  return points.map((p,i)=>({position:axes.map((axis,j)=>(p[axis]-range[j].min)/range[j].span*3-1.5) as Vector3Tuple,label:`${p.label||'Ponto '+(i+1)}: X ${p.x.toFixed(2)}, Y ${p.y.toFixed(2)}, Z ${p.z.toFixed(2)}`}));
 },[s.dataPoints]);
 useLayoutEffect(()=>{const dummy=new Object3D();data.forEach((d,i)=>{dummy.position.set(...d.position);dummy.scale.setScalar(.065+(i%4)*.012);dummy.updateMatrix();ref.current?.setMatrixAt(i,dummy.matrix);ref.current?.setColorAt(i,new Color().setHSL(.45+i*.003,.6,.48));});if(ref.current){ref.current.instanceMatrix.needsUpdate=true;if(ref.current.instanceColor)ref.current.instanceColor.needsUpdate=true;}},[data]);
 return <group>
  <Rod start={[-1.7,-1.3,-1.7]} end={[1.8,-1.3,-1.7]} color="#d87069"/><Rod start={[-1.7,-1.3,-1.7]} end={[-1.7,1.8,-1.7]} color="#52af82"/><Rod start={[-1.7,-1.3,-1.7]} end={[-1.7,-1.3,1.8]} color="#579fd5"/>
  <Label text="X" position={[2,-1.3,-1.7]}/><Label text="Y" position={[-1.7,2,-1.7]}/><Label text="Z" position={[-1.7,-1.3,2]}/>
  {data.slice(0,16).map((d,i)=><mesh key={i} position={[d.position[0],(d.position[1]-1.5)/2,d.position[2]]} castShadow><boxGeometry args={[.045,Math.max(.015,d.position[1]+1.5),.045]}/><meshStandardMaterial color={s.color} roughness={.4} metalness={.15} wireframe={s.wireframe||s.theme==='wireframe'}/></mesh>)}
  {!s.dataPoints?.length?<Label text="Amostra ilustrativa" position={[0,-1.75,0]} maxWidth={2} size={.12}/>:null}
  <instancedMesh ref={ref} args={[undefined,undefined,data.length]} castShadow onPointerMove={e=>{e.stopPropagation();const d=data[e.instanceId??0];s.onHover?.(d);}} onPointerOut={()=>s.onHover?.(null)} onClick={e=>{e.stopPropagation();s.onSelect?.(data[e.instanceId??0].label);}}>
   <sphereGeometry args={[1,12,8]}/><meshStandardMaterial roughness={.3} metalness={.2} wireframe={s.wireframe||s.theme==='wireframe'}/>
  </instancedMesh>
 </group>;
}
