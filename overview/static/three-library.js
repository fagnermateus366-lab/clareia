// The same local R3F components are used by this gallery and the video renderer.
function threeOptionsField(prefix,settings={}){
 return `<input type="hidden" id="${prefix}-three-options" value="${esc(JSON.stringify(settings.three_options||{}))}"><button type="button" class="secondary" data-three-gallery="${prefix}">◇ Galeria 3D interativa · ${studioCatalog.shotcraft.receitas.filter(r=>r.modelo3d).length} modelos</button>`;
}
function readThreeOptions(prefix){return JSON.parse($(prefix+'-three-options')?.value||'{}')}
function bindThreeLibrary(prefix){document.querySelectorAll(`[data-three-gallery="${prefix}"]`).forEach(b=>b.onclick=()=>openThreeGallery(prefix))}
function addThreeSceneControl(el,scene){
 const box=el.querySelector('[data-shotcraft-scene]');
 box.insertAdjacentHTML('beforeend',`<input type="hidden" data-three-options value="${esc(JSON.stringify(scene.three_options||null))}"><button type="button" class="secondary" data-scene-three>◇ Galeria 3D desta cena</button>`);
 box.querySelector('[data-scene-three]').onclick=()=>openThreeGallery('edit',el);
}
let threeGalleryTarget=null;
function openThreeGallery(prefix,scene=null){
 let dialog=$('three-library-dialog');
 if(!dialog){
  dialog=document.createElement('dialog');dialog.id='three-library-dialog';dialog.setAttribute('aria-label','Biblioteca interativa de modelos 3D');
  dialog.innerHTML='<button type="button" class="secondary three-close" aria-label="Fechar galeria 3D">×</button><iframe title="Galeria de modelos 3D reais" src="about:blank"></iframe>';
  document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{dialog.querySelector('iframe').src='about:blank';threeGalleryTarget=null});
 }
 threeGalleryTarget={prefix,scene,pid:current?.id};
 const value=scene?.querySelector('[data-key="shotcraft_receita"]').value||$(prefix+'-shotcraft_receita').value;
 const recipe=studioCatalog.shotcraft.receitas.find(r=>r.id===value),model=recipe?.modelo3d||'pyramid';
 const format=document.querySelector(`input[name="${prefix}-tipo_video"]:checked`)?.value||'video';
 dialog.querySelector('iframe').src='/3d/?model='+encodeURIComponent(model)+'&format='+encodeURIComponent(format);dialog.showModal();
}
window.addEventListener('message',event=>{
 const dialog=$('three-library-dialog'),target=threeGalleryTarget;
 if(!target||!dialog?.open||event.origin!==location.origin||event.source!==dialog.querySelector('iframe').contentWindow)return;
 if(event.data?.type==='clareia-three-ready'){
  const saved=target.scene?JSON.parse(target.scene.querySelector('[data-three-options]').value||'null')||readThreeOptions(target.prefix):readThreeOptions(target.prefix);
  event.source.postMessage({type:'clareia-three-init',options:saved},location.origin);return;
 }
 if(event.data?.type!=='clareia-three-select')return;
 const recipe=studioCatalog.shotcraft.receitas.find(r=>r.modelo3d===event.data.model);if(!recipe)return;
 if(target.prefix==='edit'&&target.pid!==current?.id)return;
 const data=event.data,options={speed:Math.max(0,Math.min(2,Number(data.speed)||0)),light:Math.max(.3,Math.min(2,Number(data.light)||1)),
  color:/^#[0-9a-f]{6}$/i.test(data.color)?data.color:'#2ba895',theme:['studio','dark','wireframe'].includes(data.theme)?data.theme:'studio',
  quality:['economica','equilibrada','alta'].includes(data.quality)?data.quality:'economica',wireframe:!!data.wireframe,
  movement:['padrao','estatico','giro_suave','aproximacao','flutuacao','apresentacao'].includes(data.movement)?data.movement:'padrao'};
 options.dataPoints=Array.isArray(data.dataPoints)?data.dataPoints.slice(0,200).filter(p=>['x','y','z'].every(k=>Number.isFinite(p[k]))).map(p=>({x:p.x,y:p.y,z:p.z,label:String(p.label||'').slice(0,80)})):[];
 if(target.scene?.isConnected){
  target.scene.querySelector('[data-key="animacao"]').value='shotcraft';target.scene.querySelector('[data-key="shotcraft_receita"]').value=recipe.id;
  target.scene.querySelector('[data-three-options]').value=JSON.stringify(options);updateShotcraft('edit');
 }else if(!target.scene){
  $(target.prefix+'-animacao').value='shotcraft';$(target.prefix+'-shotcraft_modelo').value='volumetrico';updateShotcraftRecipes(target.prefix);
  $(target.prefix+'-shotcraft_receita').value=recipe.id;$(target.prefix+'-three-options').value=JSON.stringify(options);
  $(target.prefix+'-animacao').dispatchEvent(new Event('change'));
 }
 dialog.close();toast('Modelo 3D escolhido. Salve a revisão ou gere uma prévia para aplicar.');
});
