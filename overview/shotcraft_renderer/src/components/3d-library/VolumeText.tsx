'use client';
import {useMemo,useEffect} from 'react';
import {useLoader} from '@react-three/fiber';
import {Color} from 'three';
import {FontLoader} from 'three/examples/jsm/loaders/FontLoader.js';
import {TextGeometry} from 'three/examples/jsm/geometries/TextGeometry.js';
import {useLibrary} from './runtime';

/** Display typography: deep extrusion, bevel and separate face/side materials. */
export default function VolumeText({text,maxWidth=4.7,maxHeight=.62}:{text:string;maxWidth?:number;maxHeight?:number}){
 const s=useLibrary(),font=useLoader(FontLoader,s.fontUrl);
 const fitted=useMemo(()=>{
  const geometry=new TextGeometry(text||' ',{font,size:1,depth:.42,curveSegments:8,bevelEnabled:true,bevelThickness:.025,bevelSize:.018,bevelSegments:3});
  geometry.computeBoundingBox();const box=geometry.boundingBox!;
  const width=Math.max(.001,box.max.x-box.min.x),height=Math.max(.001,box.max.y-box.min.y);
  if(!box.isEmpty())geometry.translate(-(box.min.x+box.max.x)/2,-(box.min.y+box.max.y)/2,-.21);
  return {geometry,scale:Math.min(.78,maxWidth/width,maxHeight/height)};
 },[font,text,maxWidth,maxHeight]);
 useEffect(()=>()=>fitted.geometry.dispose(),[fitted]);
 const front=new Color(s.color).lerp(new Color(s.theme==='studio'?'#ece5cf':'#d2f4e7'),.55),side=new Color(s.color).multiplyScalar(.48),wire=s.wireframe||s.theme==='wireframe';
 return text?<mesh geometry={fitted.geometry} scale={fitted.scale} castShadow receiveShadow>
  <meshPhysicalMaterial attach="material-0" color={front} roughness={.27} metalness={.42} clearcoat={.85} wireframe={wire}/>
  <meshStandardMaterial attach="material-1" color={side} roughness={.32} metalness={.55} wireframe={wire}/>
 </mesh>:null;
}
