import React from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useDelayRender} from 'remotion';
import {useState} from 'react';
import {Shot,sans,fitSize} from './design';
import {LibraryScene} from './components/3d-library/SceneContent';
import {defaultSettings,ModelId} from './components/3d-library/types';
import {variants} from './components/3d-library/variants/catalog';

export const modelByRecipe:Record<string,ModelId>={volume_piramide:'pyramid',volume_piramide_expandida:'exploded-pyramid',volume_funil:'ring-funnel',
 volume_colunas:'columns',volume_blocos:'flow-blocks',volume_radial:'radial-cubes',volume_personagem:'rigged-viewer',volume_fluido:'metaballs',
 volume_produto:'product',volume_particulas:'galaxy',volume_texto:'text',volume_dispersao:'scatter',...Object.fromEntries(variants.map(v=>[v.recipe,v.id]))};
export const ThreeShot:React.FC<Shot>=s=>{
 const {delayRender,continueRender}=useDelayRender();
 const [readyHandle]=useState(()=>delayRender('Preparando geometria e fontes 3D locais'));
 const w=Math.round(s.width),h=Math.round(s.height),model=modelByRecipe[s.beat.receita]||'pyramid';
 const dark=s.palette.bg!=='#f3efe7';
 const stack=model==='alt-janelas_cascata'&&s.stackCards.length?s.stackCards:null;
 const settings={...defaultSettings,theme:dark?'dark' as const:'studio' as const,...s.threeOptions,model,
  speed:s.animate?s.threeOptions?.speed??1:1,fixedTime:s.animate?(stack||s.pyramid?s.timelineTime:s.visualLocal??s.local):stack?s.timelineTime+6:6,quality:s.threeOptions?.quality||'economica' as const,labels:stack?stack.map(c=>c.element.rotulo):s.beat.elementos.map(e=>e.rotulo),subjects:stack?stack.map(c=>c.element.figura||''):s.beat.elementos.map(e=>e.figura||''),cardStarts:stack?.map(c=>c.start),text:s.beat.titulo,
  pyramid:s.pyramid?{...s.pyramid,time:s.pyramid.time+(s.animate?0:6)}:undefined,
  modelUrl:s.threeAssets?.model||defaultSettings.modelUrl,fontUrl:s.threeAssets?.font||defaultSettings.fontUrl};
 if(s.pyramid)settings.labels=s.pyramid.labels;
 return <div style={{position:'absolute',inset:0}}>
  <div style={{position:'absolute',left:w*.06,top:h*.13,width:w*.88,fontFamily:sans,color:s.palette.ink,fontWeight:740,lineHeight:1.1,
   fontSize:fitSize(s.beat.titulo,w*.88,h*.15,w*(h>w?.075:.045),2)}}>{s.beat.titulo}</div>
  <ThreeCanvas width={w} height={Math.round(h*.68)} style={{position:'absolute',top:h*.31}} shadows dpr={1}
   camera={{position:model.startsWith('alt-')?[0,1,9]:[5,3.4,7],fov:h>w?52:42}} gl={{antialias:true,alpha:false,preserveDrawingBuffer:true}}>
   <LibraryScene settings={settings} interactive={false} onReady={()=>continueRender(readyHandle)}/>
  </ThreeCanvas>
 </div>;
};
