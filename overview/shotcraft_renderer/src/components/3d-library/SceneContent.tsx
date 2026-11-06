'use client';
import {Suspense,useEffect,useRef,useState,RefObject} from 'react';
import {Environment,Lightformer,Html,OrbitControls,Bounds,useBounds} from '@react-three/drei';
import {useThree} from '@react-three/fiber';
import {Box3,Group,PerspectiveCamera,Vector3} from 'three';
import {floorBelow} from './layout';
import {LibraryContext} from './runtime';
import {LibrarySettings} from './types';
import RiggedViewer from './RiggedViewer';import Metaballs from './Metaballs';import ProductCard from './ProductCard';
import ParticleGalaxy from './ParticleGalaxy';import ExtrudedText from './ExtrudedText';import ScatterPlot from './ScatterPlot';
import PyramidLayers from './PyramidLayers';import ExplodedPyramid from './ExplodedPyramid';import RingFunnel from './RingFunnel';
import VolumeColumns from './VolumeColumns';import FlowBlocks from './FlowBlocks';import RadialCubes from './RadialCubes';
import {variantComponents} from './variants';
import StageMotion from './StageMotion';

const models={'rigged-viewer':RiggedViewer,metaballs:Metaballs,product:ProductCard,galaxy:ParticleGalaxy,text:ExtrudedText,scatter:ScatterPlot,
 pyramid:PyramidLayers,'exploded-pyramid':ExplodedPyramid,'ring-funnel':RingFunnel,columns:VolumeColumns,'flow-blocks':FlowBlocks,'radial-cubes':RadialCubes,...variantComponents};
function Ready({onReady,onFloor,modelRoot}:{onReady?:()=>void;onFloor:(y:number)=>void;modelRoot:RefObject<Group|null>}){
 const bounds=useBounds(),{camera,size,controls,advance,gl,scene}=useThree();
 useEffect(()=>{
  let framing:Box3|undefined;
  scene.traverse(o=>{const b=o.userData.framingBox;if(b)framing=new Box3(new Vector3(...b.min),new Vector3(...b.max));});
  if(!framing&&modelRoot.current)framing=new Box3().setFromObject(modelRoot.current,true);
  const {box,center}=bounds.refresh(framing).getSize(),cam=camera as PerspectiveCamera;
  const direction=cam.position.clone().sub(center).normalize(),right=new Vector3().crossVectors(cam.up,direction).normalize(),up=new Vector3().crossVectors(direction,right).normalize();
  const tan=Math.tan(cam.fov*Math.PI/360),aspect=size.width/size.height;let distance=1;
  for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
   const p=new Vector3(x,y,z).sub(center);distance=Math.max(distance,p.dot(direction)+Math.max(Math.abs(p.dot(right))/(tan*aspect),Math.abs(p.dot(up))/tan));
  }
  cam.position.copy(center).addScaledVector(direction,distance*1.16);cam.lookAt(center);cam.near=.01;cam.far=Math.max(100,distance*20);cam.updateProjectionMatrix();
  const orbit=controls as unknown as {target?:Vector3;update?:()=>void};orbit?.target?.copy(center);orbit?.update?.();
  if(Number.isFinite(box.min.y))onFloor(floorBelow(box.min.y));
  // Fit after asynchronous geometry/fonts resolve and on a viewport resize.
 },[bounds,camera,size.width,size.height]);
 useEffect(()=>{
  let first=0,second=0;
  first=requestAnimationFrame(()=>{second=requestAnimationFrame(()=>{advance(performance.now());gl.render(scene,camera);onReady?.();});});
  return()=>{cancelAnimationFrame(first);cancelAnimationFrame(second);};
 },[advance]);
 return null;
}
export function LibraryScene({settings,onReady,interactive=true}:{settings:LibrarySettings;onReady?:()=>void;interactive?:boolean}){
 const Model=models[settings.model];
 const [loading,setLoading]=useState(true);
 const fitKey=[settings.model,settings.layoutAspect||0,settings.labels.join('|'),settings.text].join('|');
 const [floor,setFloor]=useState({key:'',y:-8});
 const modelRoot=useRef<Group>(null);
 useEffect(()=>setLoading(true),[settings.model]);
 const content=<><Environment resolution={64} frames={1}><Lightformer intensity={4} position={[0,4,-4]} rotation={[Math.PI/4,0,0]} scale={[8,4,1]}/><Lightformer intensity={2} position={[-4,1,2]} rotation={[0,Math.PI/2,0]} scale={[4,5,1]}/></Environment><Bounds><group key={settings.model} ref={modelRoot}><StageMotion><Model/></StageMotion></group><Ready key={fitKey} modelRoot={modelRoot} onFloor={y=>setFloor({key:fitKey,y})} onReady={()=>{setLoading(false);onReady?.();}}/></Bounds></>;
 return <LibraryContext.Provider value={settings}>
  <color attach="background" args={[settings.theme==='studio'?'#edf0f2':'#111722']}/>
  <fog attach="fog" args={[settings.theme==='studio'?'#edf0f2':'#111722',12,45]}/>
  <ambientLight intensity={.6*settings.light}/><directionalLight position={[4,6,5]} intensity={2.4*settings.light} castShadow
   shadow-mapSize={settings.quality==='alta'?2048:settings.quality==='economica'?512:1024} shadow-camera-left={-5} shadow-camera-right={5} shadow-camera-top={5} shadow-camera-bottom={-5} shadow-bias={-.0005}/>
  <directionalLight position={[-4,2,-2]} intensity={.6*settings.light} color="#b8d8f5"/>
  {interactive?<><Suspense fallback={null}>{content}</Suspense><Html center style={{pointerEvents:'none'}}><div hidden={!loading} role="status" style={{color:'#79bfbc',background:'#17202d',padding:14,borderRadius:10,whiteSpace:'nowrap'}}>Preparando modelo 3D…</div></Html></>:content}
  {settings.model==='galaxy'||floor.key!==fitKey?null:<mesh rotation={[-Math.PI/2,0,0]} position={[0,floor.y,0]} receiveShadow><planeGeometry args={[200,200]}/><meshStandardMaterial color={settings.theme==='studio'?'#e5e9ed':'#151e2b'} roughness={.85}/></mesh>}
  {interactive?<OrbitControls makeDefault enableDamping dampingFactor={.08} minDistance={3} maxDistance={18} minPolarAngle={.25} maxPolarAngle={Math.PI*.49}
   minAzimuthAngle={settings.model.startsWith('alt-')||['pyramid','exploded-pyramid','flow-blocks','radial-cubes'].includes(settings.model)?-.8:-Infinity}
   maxAzimuthAngle={settings.model.startsWith('alt-')||['pyramid','exploded-pyramid','flow-blocks','radial-cubes'].includes(settings.model)?.8:Infinity} enablePan={false}/>:null}
 </LibraryContext.Provider>;
}
