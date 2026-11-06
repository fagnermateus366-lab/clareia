'use client';
import {useEffect,useMemo,useRef} from 'react';
import {useGLTF,useAnimations} from '@react-three/drei';
import {Group,Mesh,MeshStandardMaterial} from 'three';
import {clone} from 'three/examples/jsm/utils/SkeletonUtils.js';
import {useLibrary,useMotion} from './runtime';

export default function RiggedViewer(){
 const s=useLibrary(),source=useGLTF(s.modelUrl),root=useRef<Group>(null);
 useEffect(()=>()=>{if(s.modelUrl.startsWith('data:'))useGLTF.clear(s.modelUrl);},[s.modelUrl]);
 const model=useMemo(()=>{const copy=clone(source.scene);copy.traverse(object=>{if(object instanceof Mesh){object.castShadow=true;object.receiveShadow=true;object.material=Array.isArray(object.material)?object.material.map(m=>m.clone()):object.material.clone();}});return copy;},[source.scene]);
 const {actions,mixer}=useAnimations(source.animations,root);
 useEffect(()=>{const action=actions[s.clip]||Object.values(actions)[0];action?.reset().play();return()=>{Object.values(actions).forEach(a=>a?.stop());};},[actions,s.clip]);
 useEffect(()=>()=>model.traverse(object=>{if(object instanceof Mesh)(Array.isArray(object.material)?object.material:[object.material]).forEach(m=>m.dispose());}),[model]);
 useEffect(()=>model.traverse(object=>{if(object instanceof Mesh)(Array.isArray(object.material)?object.material:[object.material]).forEach(m=>{(m as MeshStandardMaterial).wireframe=s.wireframe||s.theme==='wireframe';});}),[model,s.wireframe,s.theme]);
 useMotion(time=>{mixer.setTime(time);});
 return <group ref={root} position={[0,-1.1,0]} onClick={e=>{e.stopPropagation();s.onSelect?.('Personagem articulado · animação Walk');}}><primitive object={model} dispose={null}/></group>;
}
