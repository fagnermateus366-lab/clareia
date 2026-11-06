'use client';
import {createContext,useContext,useRef} from 'react';
import {useFrame,RootState} from '@react-three/fiber';
import {defaultSettings,LibrarySettings} from './types';
export const LibraryContext=createContext<LibrarySettings>(defaultSettings);
export const useLibrary=()=>useContext(LibraryContext);
export function useMotion(callback:(time:number,state:RootState,delta:number)=>void){
  const settings=useLibrary(),elapsed=useRef(settings.paused||settings.speed===0?6:0);
  useFrame((state,delta)=>{
    if(!settings.paused)elapsed.current+=Math.min(.05,delta)*settings.speed;
    callback(settings.speed===0||settings.movement==='estatico'?6:settings.fixedTime===undefined?elapsed.current:settings.fixedTime*settings.speed,state,delta);
  });
}
