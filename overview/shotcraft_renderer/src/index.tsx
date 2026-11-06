import React from 'react';
import {AbsoluteFill,Composition,registerRoot,useCurrentFrame} from 'remotion';
import {Film,Shot,StackCard,palettes,chooseFamily,sans} from './design';
import {Kinetic,Spatial,Editorial,Luminous} from './Models';
import {CardLayouts,Glass,Interface,Diagrams,Impact,Retro,TextBanners} from './CatalogModels';
import {Atmosphere,FinishContext,RefractionRules} from './Finish';
import {ReferenceScene} from './ReferenceScene';
import {ThreeShot} from './ThreeShot';
import {figureAt,visualClock} from './continuity';
import {pyramidSequence} from './components/3d-library/pyramidTiming';

const models={tipografia:Kinetic,espacial:Spatial,editorial:Editorial,luminoso:Luminous,
  cartoes:CardLayouts,vidro:Glass,interface:Interface,diagramas:Diagrams,impacto:Impact,retro:Retro,volumetrico:ThreeShot};

const FilmComposition:React.FC<Film>=(props)=>{
  const frame=useCurrentFrame(),seconds=frame/props.fps+(props.timeOffset||0);
  const original=props.moments.find(b=>seconds>=b.inicio&&seconds<b.fim)||props.moments.at(-1)!;
  const active=props.manualFigures?.length?figureAt(props,seconds,original):undefined;
  const beat=active?{...original,elementos:original.elementos.map((e,i)=>i===0?{...e,figura:active}:e)}:original;
  const palette=palettes[props.theme]||palettes.editorial;
  const stackCards:StackCard[]=[];
  if(['janelas_cascata','volume_alt_janelas_cascata'].includes(beat.receita)){
    const current=props.moments.indexOf(original);let first=current;
    while(first>0&&props.moments[first-1].receita===beat.receita)first--;
    let serial=0;
    for(const moment of props.moments.slice(first,current+1)){
      moment.elementos.forEach((element,i)=>{
        const start=moment.inicio+i*Math.min((moment.fim-moment.inicio)*.70,2.2)/moment.elementos.length;
        if(!props.animate||start<=seconds)stackCards.push({element,start,title:moment.titulo,index:serial});
        serial++;
      });
    }
    stackCards.splice(0,Math.floor(Math.max(0,stackCards.length-1)/4)*4);
    if(active&&stackCards.length){const last=stackCards.at(-1)!;last.element={...last.element,figura:active};}
  }
  const shot:Shot={width:props.width,height:props.height,beat,local:Math.max(0,seconds-beat.inicio),length:beat.fim-beat.inicio,
    palette,finish:props.finish||'vidro_avancado',energy:({suave:.8,equilibrada:1,energica:1.18} as Record<string,number>)[props.energy]||1,photo:props.photo,figures:props.figures||{},
    animate:props.animate,camera:props.camera,stackCards,timelineTime:seconds,pyramid:pyramidSequence(props.moments,original,seconds),staticPhoto:props.staticPhoto!==false,threeAssets:props.threeAssets,threeOptions:props.threeOptions,...visualClock(props,original,seconds)};
  const family=chooseFamily(beat,props.family);
  const Model=['faixa_titulo','contorno_preenchido'].includes(beat.receita)?TextBanners:models[family==='auto'?'tipografia':family];
  return <FinishContext.Provider value={shot.finish}><AbsoluteFill style={{background:palette.bg,color:palette.ink,overflow:'hidden'}}>
    {shot.finish==='vidro_avancado'?<><Atmosphere film={props} palette={palette} seconds={seconds}/><RefractionRules/></>:null}
    <div style={{position:'absolute',left:props.width*.07,top:props.height*.045,width:props.width*.86,fontFamily:sans,
      fontSize:props.width*(props.height>props.width? .025:.013),fontWeight:500,letterSpacing:'.07em',textTransform:'uppercase',color:palette.muted,
      whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{props.title}</div>
    <div style={{position:'absolute',left:props.width*.07,right:props.width*.07,top:props.height*.105,height:1,background:palette.muted+'40'}}/>
    {props.photo?<ReferenceScene shot={shot} Model={Model}/>:<Model {...shot}/>}
  </AbsoluteFill></FinishContext.Provider>;
};
const defaults:Film={width:1280,height:720,fps:24,durationInFrames:120,theme:'cinema',energy:'equilibrada',family:'espacial',animate:true,camera:true,title:'Uma ideia em movimento',photo:null,
  moments:[{frase:0,inicio:0,fim:5,titulo:'Novas formas de contar uma história',composicao:'conceito',receita:'pilha_cartoes',foco:0,
    elementos:[{rotulo:'Observe a ideia'},{rotulo:'Explore possibilidades'},{rotulo:'Descubra um caminho'}]}]};
const Root:React.FC=()=> <Composition id="ClareiaShotcraft" component={FilmComposition} defaultProps={defaults} width={1280} height={720} fps={24} durationInFrames={120}
  calculateMetadata={({props})=>({width:props.width,height:props.height,fps:props.fps,durationInFrames:props.durationInFrames})}/>;
registerRoot(Root);
