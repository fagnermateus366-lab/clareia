import type {Film,Moment} from './design';
export function figureAt(film:Film,time:number,moment:Moment){
 const duration=Math.max(...film.moments.map(b=>b.fim)),manual=film.manualFigures||[];
 return manual.length?manual[Math.min(manual.length-1,Math.max(0,Math.floor(time/(duration/manual.length))))]:moment.elementos[0]?.figura||'';
}
export function visualClock(film:Film,moment:Moment,time:number){
 const current=film.moments.indexOf(moment),key=figureAt(film,time,moment);let first=current;
 while(first>0){const prior=film.moments[first-1];if(prior.receita!==moment.receita||figureAt(film,Math.max(prior.inicio,prior.fim-.001),prior)!==key)break;first--;}
 let start=film.moments[first].inicio;
 if(film.manualFigures?.length){const duration=Math.max(...film.moments.map(b=>b.fim)),slot=duration/film.manualFigures.length;
  for(let i=1;i<film.manualFigures.length;i++)if(i*slot<=time&&film.manualFigures[i]!==film.manualFigures[i-1])start=Math.max(start,i*slot);
 }
 const next=film.moments[current+1],continues=next&&next.receita===moment.receita&&figureAt(film,next.inicio,next)===key;
 const local=Math.max(0,time-moment.inicio),fade=film.animate?Math.min(1,local/.24,continues?Math.max(0,(moment.fim-time)/.18):1):1;
 return {visualLocal:Math.max(0,time-start),textOpacity:fade};
}
