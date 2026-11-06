'use client';
import React,{Suspense,useEffect,useRef,useState} from 'react';
import {Canvas,useFrame} from '@react-three/fiber';
import {Html,PerspectiveCamera} from '@react-three/drei';
import {LibraryScene} from '@three-library/SceneContent';
import {defaultSettings,modelCatalog,LibrarySettings,ModelId,HoverInfo,Theme,Quality,movements,Movement} from '@three-library/types';
import {subjects} from '@three-library/Subjects';
import {variants} from '@three-library/variants/catalog';

class SceneBoundary extends React.Component<{children:React.ReactNode;resetKey:string},{error:string}>{
 state={error:''};static getDerivedStateFromError(error:Error){return {error:error.message};}
 componentDidUpdate(previous:Readonly<{children:React.ReactNode;resetKey:string}>){if(previous.resetKey!==this.props.resetKey&&this.state.error)this.setState({error:''});}
 render(){return this.state.error?<div role="alert" className="canvas-error">Não foi possível abrir esta cena 3D.<br/>{this.state.error}<p>Experimente a qualidade econômica ou outro modelo.</p></div>:this.props.children;}
}
function Performance({report}:{report:(fps:number,draws:number)=>void}){
 const sample=useRef({time:0,frames:0});useFrame(state=>{const now=state.clock.elapsedTime;sample.current.frames++;if(now-sample.current.time>=1){report(Math.round(sample.current.frames/(now-sample.current.time)),state.gl.info.render.calls);sample.current={time:now,frames:0};}});return null;
}
export default function Gallery(){
 const [settings,setSettings]=useState<LibrarySettings>({...defaultSettings,model:'alt-pilha_cartoes',labels:['Computador','Castelo','Cérebro'],subjects:['computador','castelo','cerebro']}),[embed,setEmbed]=useState(false),[ready,setReady]=useState(false);
 const [hover,setHover]=useState<HoverInfo|null>(null),[selection,setSelection]=useState(''),[performance,setPerformance]=useState({fps:0,draws:0});
 const [enabledApply,setEnabledApply]=useState(false);
 const [modelVersion,setModelVersion]=useState(0);
 const [format,setFormat]=useState<'auto'|'video'|'shorts'>('auto');
 const update=<K extends keyof LibrarySettings>(key:K,value:LibrarySettings[K])=>setSettings(s=>({...s,[key]:value}));
 useEffect(()=>{const query=new URLSearchParams(location.search),model=query.get('model');const motion=movements.find(m=>m.id===query.get('movement'));if(motion)update('movement',motion.id);if(modelCatalog.some(m=>m.id===model))update('model',model as ModelId);setEmbed(query.get('embed')==='1');if(['video','shorts'].includes(query.get('format')||''))setFormat(query.get('format') as 'video'|'shorts');setEnabledApply(window.parent!==window);},[]);
 useEffect(()=>{
  const receive=(event:MessageEvent)=>{
   if(event.source!==window.parent||event.origin!==location.origin||event.data?.type!=='clareia-three-init')return;
   const data=event.data.options||{};
   setSettings(s=>({...s,speed:Number.isFinite(data.speed)?Math.max(0,Math.min(2,data.speed)):s.speed,light:Number.isFinite(data.light)?Math.max(.3,Math.min(2,data.light)):s.light,
    color:/^#[0-9a-f]{6}$/i.test(data.color)?data.color:s.color,theme:['dark','studio','wireframe'].includes(data.theme)?data.theme:s.theme,
    quality:['economica','equilibrada','alta'].includes(data.quality)?data.quality:s.quality,wireframe:!!data.wireframe,movement:movements.some(m=>m.id===data.movement)?data.movement:s.movement,
    dataPoints:Array.isArray(data.dataPoints)?data.dataPoints.slice(0,200).filter((p:{x:number;y:number;z:number})=>[p.x,p.y,p.z].every(Number.isFinite)):s.dataPoints}));
  };
  window.addEventListener('message',receive);if(window.parent!==window)window.parent.postMessage({type:'clareia-three-ready'},location.origin);
  return()=>window.removeEventListener('message',receive);
 },[]);
 useEffect(()=>{setReady(false);setHover(null);setSelection('');},[settings.model]);
 const selected=modelCatalog.find(m=>m.id===settings.model)!;
 const apply=()=>window.parent.postMessage({type:'clareia-three-select',model:settings.model,speed:settings.speed,light:settings.light,color:settings.color,wireframe:settings.wireframe,theme:settings.theme,quality:settings.quality,movement:settings.movement,dataPoints:settings.dataPoints||[]},location.origin);
 const readModel=async(file:File|undefined)=>{if(!file)return;if(file.size>30*1024*1024){setSelection('Escolha um GLB de até 30 MB.');return;}const bytes=new Uint8Array(await file.arrayBuffer());let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));setModelVersion(n=>n+1);setSettings(s=>({...s,model:'rigged-viewer',modelUrl:'data:model/gltf-binary;base64,'+btoa(text)}));};
 return <main className={'gallery '+(embed?'gallery-embed':'')} data-render-ready={ready}>
  {!embed?<aside className="sidebar"><a className="brand" href="/">◒ clareia<span>Biblioteca 3D real</span></a>
   <p className="sidebar-note">Explore o volume. Escolha como contar.</p>
   {['Alternativas 3D','Infográficos 3D','Experiências 3D'].map(group=><section key={group}><h2>{group}</h2><nav aria-label={group}>{modelCatalog.filter(m=>m.group===group).map((m,i)=><button key={m.id} className={'model-button '+(settings.model===m.id?'active':'')} aria-pressed={settings.model===m.id} onClick={()=>{update('model',m.id);if(m.id.startsWith('alt-'))update('labels',['Computador','Castelo','Cérebro']);}}><span className="model-number">{String(i+1).padStart(2,'0')}</span><span>{m.name}</span><span className="model-dot"/></button>)}</nav></section>)}
   <div className="sidebar-footer">Three.js · R3F · PBR<br/>Modelos e fontes locais</div>
  </aside>:null}
  <section className="workspace">
   {!embed?<header><div><p className="eyebrow">ESTÚDIO DE VOLUME E LUZ</p><h1>{selected.name}</h1><p>{selected.description}</p></div><span className="live-badge">● Tempo real</span></header>:null}
   <div className="viewport" aria-label={'Visualização 3D: '+selected.name}>
    <SceneBoundary resetKey={settings.model+settings.quality+modelVersion}><Canvas shadows dpr={settings.quality==='economica'?1:[1,1.5]} camera={{position:[5,3.4,7],fov:42}} gl={{antialias:settings.quality!=='economica',alpha:false,powerPreference:'high-performance'}}>
     <PerspectiveCamera makeDefault position={settings.model.startsWith('alt-')?[0,1,9]:settings.model==='pyramid'||settings.model==='exploded-pyramid'?[5,2.7,7]:[5,3.4,7]} fov={settings.model==='ring-funnel'?46:42}/>
     <LibraryScene settings={{...settings,layoutAspect:format==='shorts'?.827:format==='video'?2.61:undefined,onHover:setHover,onSelect:setSelection}} onReady={()=>setReady(true)}/>
     {hover?<Html position={hover.position} center style={{pointerEvents:'none'}}><div className="tooltip">{hover.label}</div></Html>:null}
     <Performance report={(fps,draws)=>setPerformance({fps,draws})}/>
    </Canvas></SceneBoundary>
    <div className="viewport-tag">{selected.group} <span>WebGL</span></div>
    {!embed?<div className="gesture-hint">Arraste para girar <span>·</span> Role para aproximar <span>·</span> Clique para explorar</div>:null}
    {selection?<div className="selection-message" role="status">{selection}</div>:null}
    {!embed?<div className="stats"><span>{performance.fps||'—'} FPS</span><span>{performance.draws} desenhos/quadro</span><span>{settings.quality}</span></div>:null}
   </div>
   {!embed?<footer><span>{modelCatalog.length} modelos · Seleção manual</span><span>O desempenho é medido neste dispositivo. Ajuste a qualidade se necessário.</span></footer>:null}
  </section>
  {!embed?<aside className="control-panel"><h2>Direção da cena</h2><p className="control-intro">Ajuste o modelo enquanto observa.</p>
   <label>Prévia de composição<select value={format} onChange={e=>setFormat(e.target.value as 'auto'|'video'|'shorts')}><option value="auto">Livre · área da galeria</option><option value="video">Vídeo comum · 16:9</option><option value="shorts">Reels / Shorts · 9:16</option></select></label>
   <label>Ambiente<select value={settings.theme} onChange={e=>update('theme',e.target.value as Theme)}><option value="studio">Estúdio · fundo claro</option><option value="dark">Escuro · luz de recorte</option><option value="wireframe">Malha geométrica</option></select></label>
   <label>Movimento das formas 3D<select aria-describedby="movement-description" value={settings.movement} onChange={e=>update('movement',e.target.value as Movement)}>{movements.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select><small id="movement-description">{movements.find(m=>m.id===settings.movement)?.description}</small></label>
   <label>Velocidade <output>{settings.speed.toFixed(1)}×</output><input aria-label="Velocidade de animação" type="range" min="0" max="2" step=".1" value={settings.speed} onChange={e=>update('speed',+e.target.value)}/></label>
   <label>Intensidade da luz <output>{settings.light.toFixed(1)}</output><input aria-label="Intensidade da luz" type="range" min=".3" max="2" step=".1" value={settings.light} onChange={e=>update('light',+e.target.value)}/></label>
   <label className="color-control">Cor do material<input aria-label="Cor do material" type="color" value={settings.color} onChange={e=>update('color',e.target.value)}/></label>
   <label>Qualidade<select value={settings.quality} onChange={e=>update('quality',e.target.value as Quality)}><option value="economica">Econômica</option><option value="equilibrada">Equilibrada</option><option value="alta">Alta</option></select></label>
   <label className="check"><input type="checkbox" checked={settings.wireframe} onChange={e=>update('wireframe',e.target.checked)}/>Mostrar estrutura da malha</label>
   <button className="secondary-control" onClick={()=>update('paused',!settings.paused)}>{settings.paused?'▶ Retomar animação':'Ⅱ Pausar animação'}</button>
   {settings.model==='rigged-viewer'?<><label>Animação do esqueleto<select value={settings.clip} onChange={e=>update('clip',e.target.value as 'Idle'|'Walk')}><option value="Idle">Idle · repouso</option><option value="Walk">Walk · movimento</option></select></label><label>Seu modelo GLB<input type="file" accept=".glb" onChange={e=>void readModel(e.target.files?.[0])}/><small>Até 30 MB, processado neste navegador. Modelos personalizados são apenas para inspeção nesta galeria.</small></label></>:null}
   {settings.model==='text'?<label>Texto extrudado<input maxLength={80} value={settings.text} onChange={e=>update('text',e.target.value)}/></label>:null}
   {['Infográficos 3D','Alternativas 3D'].includes(selected.group)?<label>Rótulos · um por linha<textarea rows={5} value={settings.labels.join('\n')} onChange={e=>update('labels',e.target.value.split('\n').map(s=>s.trim()).filter(Boolean).slice(0,6))}/><small>Os exemplos são demonstrativos. No vídeo, os rótulos vêm do roteiro.</small></label>:null}
   {variants.find(v=>v.id===settings.model)?.figures?<fieldset><legend>Objetos da demonstração</legend>{[0,1,2].map(i=><label key={i}>Objeto {i+1}<select value={settings.subjects?.[i]} onChange={e=>{const next=[...(settings.subjects||[])];next[i]=e.target.value;update('subjects',next);}}>{subjects.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>)}<small>20 objetos modelados em volume. No roteiro, use o acervo 3D da cena para escolher as figuras.</small></fieldset>:null}
   {settings.model==='scatter'?<><p className="sample-note">{settings.dataPoints?.length?'Dados fornecidos por você. Os eixos são ajustados ao intervalo dos dados.':'Amostra ilustrativa. As coordenadas desta demonstração não representam dados reais.'}</p><label>Importar coordenadas JSON<input type="file" accept=".json,application/json" onChange={async e=>{const file=e.target.files?.[0];if(!file)return;try{if(file.size>100000)throw Error();const data=JSON.parse(await file.text());if(!Array.isArray(data)||!data.length||data.length>200||data.some(p=>!['x','y','z'].every(k=>typeof p[k]==='number'&&Number.isFinite(p[k]))))throw Error();update('dataPoints',data.map(p=>({x:p.x,y:p.y,z:p.z,label:String(p.label||'').slice(0,80)})));}catch{setSelection('Use um JSON com até 200 objetos contendo x, y e z numéricos.');}}}/><small>Formato: [{'{"x":1,"y":2,"z":3,"label":"Ponto A"}'}]. Arquivo processado localmente.</small></label></>:null}
   {enabledApply?<button className="apply-control" disabled={settings.modelUrl.startsWith('data:')} onClick={apply}>Usar este modelo na cena</button>:null}
   <details><summary>Sobre esta biblioteca</summary><p>Objetos com geometria, espessura, iluminação e materiais PBR. As animações anteriores permanecem separadas.</p></details>
  </aside>:null}
 </main>;
}
