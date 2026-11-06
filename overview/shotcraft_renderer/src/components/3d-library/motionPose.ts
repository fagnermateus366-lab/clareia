// Conservative bounds preserve front-facing labels and the camera's fit margin.
export type StageMovement='padrao'|'estatico'|'giro_suave'|'aproximacao'|'flutuacao'|'apresentacao';
export function stagePose(movement:StageMovement,time:number){
 const wave=Math.sin(time*.42),rise=(1-Math.cos(time*.55))/2;
 const rotate=movement==='giro_suave'||movement==='apresentacao';
 const zoom=movement==='aproximacao'||movement==='apresentacao';
 const float=movement==='flutuacao'||movement==='apresentacao';
 return {yaw:rotate?wave*.12:0,pitch:rotate?Math.sin(time*.27)*.025:0,
         y:float?rise*.09:0,scale:zoom?1+(1-Math.cos(time*.32))*.0175:1};
}
