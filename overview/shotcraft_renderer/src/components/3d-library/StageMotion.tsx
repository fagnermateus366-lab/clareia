'use client';
import {ReactNode,useRef} from 'react';
import {Group} from 'three';
import {useLibrary,useMotion} from './runtime';
import {stagePose} from './motionPose';

export default function StageMotion({children}:{children:ReactNode}){
 const root=useRef<Group>(null),s=useLibrary();
 useMotion(time=>{
  if(!root.current)return;
  const pose=stagePose(s.movement,time);
  root.current.rotation.set(pose.pitch,pose.yaw,0);
  root.current.position.y=pose.y;
  root.current.scale.setScalar(pose.scale);
 });
 return <group ref={root}>{children}</group>;
}
