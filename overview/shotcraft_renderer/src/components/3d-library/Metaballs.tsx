'use client';
import {useEffect,useMemo} from 'react';
import {MeshPhysicalMaterial} from 'three';
import {MarchingCubes} from 'three/examples/jsm/objects/MarchingCubes.js';
import {useLibrary,useMotion} from './runtime';

export default function Metaballs(){
 const s=useLibrary(),uniforms=useMemo(()=>({uTime:{value:0}}),[]);
 const material=useMemo(()=>{const m=new MeshPhysicalMaterial({color:s.color,metalness:.12,roughness:.13,transmission:.8,thickness:.8,ior:1.42,clearcoat:1,envMapIntensity:1.4});
  m.onBeforeCompile=shader=>{shader.uniforms.uTime=uniforms.uTime;shader.vertexShader='uniform float uTime;\n'+shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\n transformed += normalize(normal) * (0.018 * sin(position.x * 11.0 + uTime) * cos(position.y * 9.0 - uTime));`);};
  m.customProgramCacheKey=()=> 'clareia-liquid-pbr-v1';return m;
 },[s.color,uniforms]);
 const volume=useMemo(()=>{const mesh=new MarchingCubes(s.quality==='alta'?40:s.quality==='economica'?20:28,material,false,false,24000);mesh.scale.setScalar(2);mesh.castShadow=true;for(let i=0;i<4;i++)mesh.addBall(.5+Math.sin(i*2.3)*.18,.5+Math.cos(i)*.18,.5+Math.sin(i*1.7)*.16,.42,9);mesh.update();mesh.geometry.computeBoundingBox();return mesh;},[s.quality,material]);
 useEffect(()=>()=>{volume.geometry.dispose();material.dispose();},[volume,material]);
 useMotion(time=>{
  uniforms.uTime.value=time;material.wireframe=s.wireframe||s.theme==='wireframe';volume.reset();
  for(let i=0;i<4;i++)volume.addBall(.5+Math.sin(time*.55+i*2.3)*.18,.5+Math.cos(time*.7+i)*.18,.5+Math.sin(time*.43+i*1.7)*.16,.42,9);
  volume.update();
 });
 return <primitive object={volume} dispose={null} userData={{framingBox:{min:[-1.5,-1.5,-1.5],max:[1.5,1.5,1.5]}}}/>;
}
