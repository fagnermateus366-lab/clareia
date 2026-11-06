'use client';
import {useMemo,useEffect,useRef} from 'react';
import {Billboard} from '@react-three/drei';
import {useLoader,useFrame} from '@react-three/fiber';
import {Vector3,Vector3Tuple,Quaternion,Group,Mesh} from 'three';
import {FontLoader} from 'three/examples/jsm/loaders/FontLoader.js';
import {TextGeometry} from 'three/examples/jsm/geometries/TextGeometry.js';
import {useLibrary} from './runtime';
import {wrapWords} from './textLayout';
export const colors=['#2696bd','#1ba58e','#a6ba54','#e5a31f','#d65740','#8970ad'];
export function Material({color,metalness=.12}:{color:string;metalness?:number}){
 const s=useLibrary();return <meshStandardMaterial color={color} metalness={metalness} roughness={.34} wireframe={s.wireframe||s.theme==='wireframe'}/>;
}
export function Label({text,position,size=.13,color,face=false,maxWidth=1.7,maxHeight=.30}:{text:string;position:Vector3Tuple;size?:number;color?:string;face?:boolean;maxWidth?:number;maxHeight?:number}){
 const s=useLibrary(),font=useLoader(FontLoader,s.fontUrl);
 const fitted=useMemo(()=>{
  const wrapped=maxWidth/maxHeight<5?wrapWords(text,Math.max(10,Math.floor(maxWidth/maxHeight*5))):text;
  const geometry=new TextGeometry(wrapped,{font,size:1,depth:.018,curveSegments:4,bevelEnabled:false});geometry.computeBoundingBox();
  const box=geometry.boundingBox!,width=Math.max(.001,box.max.x-box.min.x),height=Math.max(.001,box.max.y-box.min.y);
  geometry.translate(-(box.min.x+box.max.x)/2,-(box.min.y+box.max.y)/2,0);
  return {geometry,scale:Math.min(size,maxWidth/width,maxHeight/height)};
 },[font,text,size,maxWidth,maxHeight]);
 useEffect(()=>()=>fitted.geometry.dispose(),[fitted]);
 const mesh=<mesh geometry={fitted.geometry} scale={fitted.scale} renderOrder={100}><meshStandardMaterial color={color||(s.theme==='studio'?'#263240':'#f0f4f5')} roughness={.65} depthTest={false} depthWrite={false}/></mesh>;
 return face?<group position={position}>{mesh}</group>:<Billboard position={position}>{mesh}</Billboard>;
}
// Labels outside a solid move along the camera's screen axes. Their complete
// measured width stays beyond the silhouette rather than behind another mesh.
export function Callout({text,anchor,side=1,radius=1,maxWidth=1.65,vertical=false,color='#566c7e'}:{text:string;anchor:Vector3Tuple;side?:number;radius?:number;maxWidth?:number;vertical?:boolean;color?:string}){
 const root=useRef<Group>(null),label=useRef<Group>(null),line=useRef<Mesh>(null);
 const vectors=useMemo(()=>({origin:new Vector3(),axis:new Vector3(),end:new Vector3(),start:new Vector3(),middle:new Vector3(),direction:new Vector3(),up:new Vector3(0,1,0)}),[]);
 useFrame(({camera})=>{
  if(!root.current||!label.current||!line.current)return;
  root.current.getWorldPosition(vectors.origin);vectors.axis.setFromMatrixColumn(camera.matrixWorld,vertical?1:0).normalize().multiplyScalar(side);
  vectors.end.copy(vectors.origin).addScaledVector(vectors.axis,radius+(vertical?.22:maxWidth/2)+.16);
  root.current.worldToLocal(vectors.end);label.current.position.copy(vectors.end);
  vectors.start.copy(vectors.origin).addScaledVector(vectors.axis,radius*.85);root.current.worldToLocal(vectors.start);
  vectors.middle.copy(vectors.start).add(vectors.end).multiplyScalar(.5);vectors.direction.copy(vectors.end).sub(vectors.start);
  line.current.position.copy(vectors.middle);line.current.scale.set(1,vectors.direction.length(),1);line.current.quaternion.setFromUnitVectors(vectors.up,vectors.direction.normalize());
 });
 return <group position={anchor} ref={root}><mesh ref={line}><cylinderGeometry args={[.009,.009,1,6]}/><Material color={color}/></mesh>
  <group ref={label} position={vertical?[0,side*(radius+.38),0]:[side*(radius+maxWidth/2+.16),0,0]}><Label text={text} position={[0,0,0]} maxWidth={maxWidth} maxHeight={.38} size={.15}/></group></group>;
}
export function Rod({start,end,color='#b4bfca',radius=.022}:{start:Vector3Tuple;end:Vector3Tuple;color?:string;radius?:number}){
 const geometry=useMemo(()=>{const a=new Vector3(...start),b=new Vector3(...end),d=b.clone().sub(a);return {position:a.add(b).multiplyScalar(.5),quaternion:new Quaternion().setFromUnitVectors(new Vector3(0,1,0),d.clone().normalize()),length:d.length()};},[...start,...end]);
 return <mesh position={geometry.position} quaternion={geometry.quaternion} castShadow><cylinderGeometry args={[radius,radius,geometry.length,8]}/><Material color={color}/></mesh>;
}
