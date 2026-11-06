import type {LibrarySettings} from './components/3d-library/types';
import type {PyramidSequence} from './components/3d-library/pyramidTiming';
// Choreography adapted from Video ShotCraft, copyright 2026 Wei Yihao,
// Apache-2.0. See third_party/video-shotcraft/NOTICE.md and original sources.
export type Family = 'auto' | 'tipografia' | 'espacial' | 'editorial' | 'luminoso' |
  'cartoes' | 'vidro' | 'interface' | 'diagramas' | 'impacto' | 'retro' | 'volumetrico';
export type Element = {rotulo: string; icone?: string; figura?:string};
export type StackCard = {element:Element; start:number; title:string; index:number};
export type Moment = {frase: number; inicio: number; fim: number; titulo: string;
  composicao: string; elementos: Element[]; receita: string; linguagem?: Family; foco?: number};
export type Film = {width: number; height: number; fps: number; durationInFrames: number;
  theme: string; finish?: 'vidro_avancado'|'original'; energy: string; family: Family; animate: boolean; camera: boolean;
  title: string; moments: Moment[]; photo: string | null; staticPhoto?:boolean; figures?:Record<string,string>; timeOffset?:number; threeAssets?:{model:string;font:string};threeOptions?:Partial<LibrarySettings>;manualFigures?:string[]};
export type Shot = {beat: Moment; width: number; height: number; local: number;
  length: number; palette: Palette; finish: 'vidro_avancado'|'original'; energy: number; photo: string | null; figures:Record<string,string>; animate: boolean; camera: boolean;
  stackCards:StackCard[]; timelineTime:number; pyramid?:PyramidSequence; staticPhoto?:boolean; threeAssets?:{model:string;font:string};threeOptions?:Partial<LibrarySettings>;manualFigures?:string[];visualLocal?:number;textOpacity?:number};
export type Palette = {bg: string; surface: string; ink: string; accent: string; second: string; muted: string};
export const palettes: Record<string, Palette> = {
  editorial: {bg:'#f3efe7',surface:'#fffdf8',ink:'#24232b',accent:'#c45239',second:'#c4b293',muted:'#78726b'},
  cinema: {bg:'#101216',surface:'#24262b',ink:'#fff8e9',accent:'#e5bd77',second:'#9ea1aa',muted:'#a4a4ab'},
  tecnologia: {bg:'#071a29',surface:'#123343',ink:'#effbff',accent:'#61e2d6',second:'#5695ec',muted:'#9dbccf'},
  vibrante: {bg:'#281946',surface:'#453061',ink:'#fff7f0',accent:'#ffb18e',second:'#a89aff',muted:'#cbbcdf'},
};
export const clamp=(v:number)=>Math.max(0,Math.min(1,v));
export const ease=(v:number)=>1-Math.pow(1-clamp(v),3);
export const mix=(a:number,b:number,t:number)=>a+(b-a)*t;
export const ramp=(t:number,start:number,duration:number)=>ease((t-start)/Math.max(.02,duration));
export const sans='"Segoe UI", Arial, sans-serif';
export const serif='Georgia, "Times New Roman", serif';

// Cached local Canvas measurement; no web fonts, random values or frame state.
const measurements=new Map<string,number>();
export function measure(text:string,size:number,weight:number,family=sans):number {
  const key=[text,size,weight,family].join('|');const hit=measurements.get(key);if(hit!==undefined)return hit;
  const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d')!;
  ctx.font=`${weight} ${size}px ${family}`;const result=ctx.measureText(text).width;measurements.set(key,result);return result;
}
export function fitSize(text:string,width:number,height:number,max:number,lines=3,family=sans,weight=750):number {
  for(let size=max;size>=14;size-=2){
    let rows=1,line='';for(const word of text.split(/\s+/)){
      const candidate=line?line+' '+word:word;
      if(measure(candidate,size,weight,family)>width&&line){rows++;line=word}else line=candidate;
    }
    if(rows<=lines&&rows*size*1.12<=height&&text.split(/\s+/).every(w=>measure(w,size,weight,family)<=width))return size;
  }return 14;
}
export const choreography=(s:Shot)=>Math.min(3,Math.max(.12,s.length*.58))/Math.max(.85,s.energy);
export const settled=(s:Shot)=>s.animate?s.local:Math.max(4,s.length*.85);
// Center incomplete rows: a third card below a pair never sticks to one side.
export const rowLeft=(i:number,n:number,cols:number,left:number,width:number,gap:number)=>{
  const count=Math.min(cols,n-Math.floor(i/cols)*cols),cell=(width-gap*(cols-1))/cols;
  return left+(width-(count*cell+gap*(count-1)))/2+(i%cols)*(cell+gap);
};
export const chooseFamily=(b:Moment,chosen:Family):Family=>b.linguagem&&b.linguagem!=='auto'?b.linguagem:
  b.receita.startsWith('volume_')?'volumetrico':
  ['baralho_distribuido','carrossel_horizontal','carrossel_vertical','grade_mosaico'].includes(b.receita)?'cartoes':
  ['vidro_flutuante','paineis_desfocados','vidro_vitrine'].includes(b.receita)?'vidro':
  ['navegador_zoom','janelas_cascata','codigo_foco'].includes(b.receita)?'interface':
  ['cascata_diagrama','conectores_etapas','mapa_mental'].includes(b.receita)?'diagramas':
  ['zoom_impacto','ritmo_acelerado','grade_impacto'].includes(b.receita)?'impacto':
  ['monitor_crt','selo_carimbado'].includes(b.receita)?'retro':
  ['faixa_titulo','contorno_preenchido'].includes(b.receita)?'tipografia':
  ['titulo_marcado','palavras_encadeadas','digitacao','titulo_foco','conclusao_limpa'].includes(b.receita)?'tipografia':
  ['rede_conexoes','traco_progressivo'].includes(b.receita)?'luminoso':
  ['camadas_profundidade','camera_suave','pilha_cartoes','destaque_icone','foco_luz'].includes(b.receita)?'espacial':
  ['grade_paineis','comparacao_revelada','lista_progressiva','linha_tempo'].includes(b.receita)?'editorial':chosen!=='auto'?chosen:'tipografia';
