export interface PyramidSequence {labels:string[];starts:number[];capacity:number;time:number}
interface PyramidMoment {receita:string;inicio:number;fim:number;titulo:string;elementos:{rotulo:string}[]}
export const pyramidRecipes=new Set(['volume_piramide','volume_piramide_expandida']);

// Each spoken phrase adds one tier. A partial final cycle keeps the geometry
// of a three-tier pyramid rather than stretching the base into a whole cone.
export function pyramidSequence(moments:PyramidMoment[],current:PyramidMoment,time:number):PyramidSequence|undefined{
 if(!pyramidRecipes.has(current.receita))return undefined;
 const index=moments.indexOf(current);if(index<0)return undefined;
 let first=index;while(first>0&&moments[first-1].receita===current.receita)first--;
 const capacity=3,start=first+Math.floor((index-first)/capacity)*capacity;
 const group=moments.slice(start,index+1);
 return {capacity,time,labels:group.map(m=>m.elementos[0]?.rotulo||m.titulo),starts:group.map(m=>m.inicio)};
}

export function tierProgress(time:number,start:number,speed=1){
 if(time<start)return 0;
 if(speed===0)return 1;
 const t=Math.max(0,Math.min(1,(time-start)*speed/.65));
 return 1-Math.pow(1-t,3);
}

export function pyramidDemoTime(time:number,capacity:number){
 const period=Math.max(1,capacity)*2.5;
 return ((time%period)+period)%period;
}

export function pyramidDemoCycle(time:number,count:number){
 const clock=pyramidDemoTime(time,count),first=Math.floor(clock/7.5)*3;
 return {first,time:clock-first*2.5};
}
