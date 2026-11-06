export type Point3=[number,number,number];
export const stackModes=new Set(['cascade','depth']);
export const connectedModes=new Set(['network','diagram','path','mindmap','timeline']);
export function cardSize(mode:string):Point3{return mode==='browser'||mode==='cascade'?[3.6,1.65,.18]:connectedModes.has(mode)?[1.45,1.75,.18]:[1.8,2.18,.18];}
export function cardPositions(mode:string,n:number,aspect:number):Point3[]{
 const cols=aspect<1.1?2:3;
 return Array.from({length:n},(_,i)=>{
  if(stackModes.has(mode))return [(i-(n-1)/2)*.14,(i-(n-1))*.34,(i-(n-1))*.32];
  if(mode==='browser')return [0,(n-1)*.98-i*1.96,0];
  if(aspect>=1.1&&['showcase','hero','dolly','spotlight'].includes(mode))return [(i-(n-1)/2)*2.12,0,0];
  if(mode==='vertical'||mode==='steps')return [i%2===0?-1.06:1.06,(n-1)*.66-i*1.32,0];
  if(mode==='mindmap'||mode==='network'){const a=i/n*Math.PI*2;return [Math.cos(a)*1.9,Math.sin(a)*1.2,0];}
  if(mode==='timeline'||mode==='path')return [(i-(n-1)/2)*1.85,Math.sin(i*1.1)*.3,0];
  const rows=Math.ceil(n/cols),row=Math.floor(i/cols),count=Math.min(cols,n-row*cols);
  return [(i%cols-(count-1)/2)*2.12,((rows-1)/2-row)*2.55,0];
 });
}
export function framingBox(mode:string,points:Point3[]){
 const [w,h]=cardSize(mode),scale=mode==='hero'?1.08:1;
 return {min:[Math.min(...points.map(p=>p[0]))-w*.5*scale-.08,Math.min(...points.map(p=>p[1]))-h*.5*scale-.08,Math.min(...points.map(p=>p[2]))-.12] as Point3,
  max:[Math.max(...points.map(p=>p[0]))+w*.5*scale+.08,Math.max(...points.map(p=>p[1]))+h*.5*scale+.08,Math.max(...points.map(p=>p[2]))+1.1] as Point3};
}
export const floorBelow=(lowest:number)=>lowest-.8;
