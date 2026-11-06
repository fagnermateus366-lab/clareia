// Optional reference-photo sequence for normal videos. The first photo keeps
// the existing field and framing; empty extra fields preserve the old behavior.
function sceneImageOptions(value=''){
 return opt([['','Não usar'],...(current.imagens||[]).map((name,i)=>[name,'Imagem '+(i+1)+' · '+(current.imagens_meta?.[name]?.nome_original||name)])],value);
}
function refreshSceneImageOptions(el){
 el.querySelectorAll('[data-scene-image-extra]').forEach(select=>{
  const value=select.value;select.innerHTML=sceneImageOptions(value);select.value=value;
  const img=select.closest('label').querySelector('img');img.hidden=!value;
  if(value){img.src='/api/projects/'+current.id+'/images/'+encodeURIComponent(value);img.alt=current.imagens_meta?.[value]?.nome_original||value}
 });
}
function addSceneImageSequence(el,scene){
 const first=el.querySelector('[data-key="imagem"]');
 if(!scene.imagem&&scene.imagens_cena?.length)first.value=scene.imagens_cena[0];
 const box=document.createElement('details');box.className='scene-image-sequence';
 box.innerHTML='<summary>Usar até cinco imagens nesta cena</summary><p class="small">A imagem de referência acima é a primeira. Escolha outras na ordem desejada. O tempo real da narração será dividido igualmente: duas imagens em 20 segundos ficam 10 segundos cada. Uma imagem mantém o comportamento atual.</p><div class="scene-image-slots">'+[1,2,3,4].map(i=>'<label>Imagem '+(i+1)+'<select data-scene-image-extra="'+i+'">'+sceneImageOptions(scene.imagens_cena?.[i]||'')+'</select><img hidden loading="lazy" alt=""></label>').join('')+'</div><label>Troca de imagem dentro da cena<select data-key="transicao_imagens">'+opt([['dissolver','Dissolver suavemente'],['nenhuma','Corte direto']],scene.transicao_imagens||'dissolver')+'</select></label>';
 first.closest('label').insertAdjacentElement('afterend',box);
 const update=()=>{
  const short=document.querySelector('input[name="edit-tipo_video"]:checked')?.value==='shorts';box.hidden=short;
  box.querySelectorAll('select').forEach(select=>select.disabled=first.value==='nenhuma');refreshSceneImageOptions(el);
 };
 box.addEventListener('change',update);first.addEventListener('change',update);
 document.querySelectorAll('input[name="edit-tipo_video"]').forEach(input=>input.addEventListener('change',update));
 if((scene.imagens_cena||[]).length>1)box.open=true;update();
}
function readSceneImageSequence(el,scene){
 if(document.querySelector('input[name="edit-tipo_video"]:checked')?.value==='shorts')return;
 const first=el.querySelector('[data-key="imagem"]').value;
 const extra=Array.from(el.querySelectorAll('[data-scene-image-extra]')).map(e=>e.value).filter(Boolean);
 if(first==='auto'&&extra.length)throw Error('Escolha a primeira imagem de referência antes de montar a sequência da cena.');
 const names=first==='nenhuma'?[]:[...(!['auto','nenhuma'].includes(first)?[first]:[]),...extra];
 if(new Set(names).size!==names.length)throw Error('Escolha imagens diferentes para a sequência da cena.');
 scene.imagens_cena=names.length>1?names:[];
 scene.transicao_imagens=el.querySelector('[data-key="transicao_imagens"]').value;
}
function appendSceneUploadedImages(el,previous,added){
 const names=[...new Set([...(!['auto','nenhuma'].includes(previous)?[previous]:[]),...Array.from(el.querySelectorAll('[data-scene-image-extra]')).map(e=>e.value).filter(Boolean),...added])].slice(0,5);
 el.querySelector('[data-key="imagem"]').value=names[0]||'auto';
 refreshSceneImageOptions(el);
 el.querySelectorAll('[data-scene-image-extra]').forEach((select,i)=>select.value=names[i+1]||'');
 refreshSceneImageOptions(el);el.querySelector('[data-key="imagem"]').dispatchEvent(new Event('change',{bubbles:true}));if(names.length>1)el.querySelector('.scene-image-sequence').open=true;
}
