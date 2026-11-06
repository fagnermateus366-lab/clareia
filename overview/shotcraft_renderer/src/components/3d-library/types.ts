import type {Vector3Tuple} from 'three';
import {variants,VariantId} from './variants/catalog';
import type {PyramidSequence} from './pyramidTiming';

export type ModelId='rigged-viewer'|'metaballs'|'product'|'galaxy'|'text'|'scatter'|
  'pyramid'|'exploded-pyramid'|'ring-funnel'|'columns'|'flow-blocks'|'radial-cubes'|VariantId;
export type Theme='dark'|'studio'|'wireframe';
export type Quality='economica'|'equilibrada'|'alta';
export type Movement='padrao'|'estatico'|'giro_suave'|'aproximacao'|'flutuacao'|'apresentacao';
export const movements:{id:Movement;name:string;description:string}[]=[
 {id:'padrao',name:'Movimento original',description:'Mantém a coreografia própria do modelo.'},
 {id:'estatico',name:'Composição parada',description:'Preserva a posição; o conteúdo continua acompanhando a narração.'},
 {id:'giro_suave',name:'Giro suave',description:'Oscila alguns graus, mantendo as frases voltadas para você.'},
 {id:'aproximacao',name:'Aproximação suave',description:'Aproxima e afasta discretamente, preservando as margens de leitura.'},
 {id:'flutuacao',name:'Flutuação leve',description:'Sobe e desce suavemente, sempre acima do piso.'},
 {id:'apresentacao',name:'Apresentação combinada',description:'Combina giro limitado, aproximação e flutuação discretos.'},
];
export type HoverInfo={label:string;position:Vector3Tuple};
export type DataPoint={x:number;y:number;z:number;label?:string};
export interface LibrarySettings {
  model:ModelId; speed:number; light:number; color:string; theme:Theme; quality:Quality;
  wireframe:boolean; paused:boolean; movement:Movement; labels:string[]; values?:number[];subjects?:string[];dataPoints?:DataPoint[];cardStarts?:number[];layoutAspect?:number;pyramid?:PyramidSequence;
  fixedTime?:number; modelUrl:string; fontUrl:string; text:string; clip:'Idle'|'Walk';
  onHover?:(info:HoverInfo|null)=>void; onSelect?:(label:string)=>void;
}
export const modelCatalog:{id:ModelId;name:string;group:string;description:string}[]=[
  {id:'rigged-viewer',name:'Personagem articulado',group:'Experiências 3D',description:'GLB local com esqueleto e animações Idle e Walk. Controle de velocidade e rotação.'},
  {id:'metaballs',name:'Líquido volumétrico',group:'Experiências 3D',description:'Superfície de metaballs com geometria real, refração PBR e ondulação procedural GLSL.'},
  {id:'product',name:'Produto no pedestal',group:'Experiências 3D',description:'Gadget com materiais físicos. Gire, clique nas partes e escolha uma cor.'},
  {id:'galaxy',name:'Galáxia de partículas',group:'Experiências 3D',description:'Milhares de pontos distribuídos em três dimensões, reagindo ao cursor.'},
  {id:'text',name:'Texto extrudado',group:'Experiências 3D',description:'Letras com espessura, chanfro e reflexos de estúdio. Inclinação pelo cursor.'},
  {id:'scatter',name:'Dispersão espacial',group:'Experiências 3D',description:'Eixos X, Y e Z com pontos volumétricos selecionáveis e leitura de coordenadas.'},
  {id:'pyramid',name:'Pirâmide em camadas',group:'Infográficos 3D',description:'Uma camada por frase: base, meio e topo. A quarta frase inicia uma nova construção.'},
  {id:'exploded-pyramid',name:'Pirâmide expandida',group:'Infográficos 3D',description:'Constrói base, meio e topo com intervalos entre as camadas. Reinicia a cada três frases.'},
  {id:'ring-funnel',name:'Funil de anéis',group:'Infográficos 3D',description:'Anéis sólidos com abertura central, volumes e rótulos alternados.'},
  {id:'columns',name:'Colunas e etapas',group:'Infográficos 3D',description:'Barras volumétricas com formação progressiva. Proporções quantitativas exigem dados.'},
  {id:'flow-blocks',name:'Blocos conectados',group:'Infográficos 3D',description:'Blocos sólidos ligados por setas em um fluxo, como nas apresentações enviadas.'},
  {id:'radial-cubes',name:'Cubos radiais',group:'Infográficos 3D',description:'Quatro sólidos coloridos organizados ao redor de um centro comum.'},
];
modelCatalog.push(...variants);
export const defaultSettings:LibrarySettings={model:'pyramid',speed:1,light:1,color:'#2ba895',theme:'studio',quality:'equilibrada',wireframe:false,paused:false,movement:'padrao',
  labels:['Conhecimento','Prática','Confiança'],modelUrl:'/3d/models/clareia-robot.glb',fontUrl:'/3d/fonts/noto_sans_pt.typeface.json',text:'CLAREIA',clip:'Walk'};
