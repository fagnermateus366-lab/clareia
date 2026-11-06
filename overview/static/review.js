// Add illustrations and render a single scene without rebuilding the whole video.
(() => {
 let uploading=false,targetScene=null,revision=0,shown=null;
 const imageUrl=(pid,name)=>'/api/projects/'+pid+'/images/'+encodeURIComponent(name);
 const imageName=name=>current?.imagens_meta?.[name]?.nome_original||current?.imagens_meta?.[name]?.identificacao||name;
 function imageOptions(){return opt([['auto','Automática conforme o assunto'],['nenhuma','Sem imagem de referência'],...(current?.imagens||[]).map((name,i)=>[name,'Imagem '+(i+1)+' · '+imageName(name)])],'auto')}
 function drawImage(scene){
  const choice=scene.querySelector('[data-key="imagem"]');const preview=scene.querySelector('.scene-image-preview');
  if(!choice||!preview)return;
  const name=choice.value;preview.replaceChildren();preview.hidden=['auto','nenhuma'].includes(name);
  if(!preview.hidden){const image=document.createElement('img');image.src=imageUrl(current.id,name);image.alt=imageName(name);preview.append(image)}
 }
 function gallery(){
  if(!current)return;
  $('review-image-count').textContent=(current.imagens||[]).length;
  const note=$('review-research-note');if(note){note.textContent=current.pesquisa_imagens?.aviso||'';note.hidden=!note.textContent}
  $('review-image-gallery').innerHTML=(current.imagens||[]).map(name=>`<figure><img loading="lazy" src="${esc(imageUrl(current.id,name))}" alt="${esc(imageName(name))}"><figcaption>${esc(imageName(name))}</figcaption></figure>`).join('')||'<p class="small">Adicione imagens aqui ou no botão de cada cena.</p>';
 }
 window.refreshReviewMedia=()=>{gallery();paintShortPhotos('edit');refreshVideoBackgroundImages()};
 function controls(p,busy){
  const disabled=busy||uploading;
  document.querySelectorAll('[data-scene-preview],[data-scene-image],#review-images-add,#review-image-description').forEach(el=>el.disabled=disabled);
  if(uploading)for(const id of ['save','render','generate','schedule'])$(id).disabled=true;
 }
 function pick(index=null){targetScene=index;$('review-image-files').click()}
 async function upload(files){
  if(!files.length||!current||uploading)return;
  const pid=current.id,index=targetScene;targetScene=null;uploading=true;controls(current,false);
  $('review-media-status').textContent='Adicionando imagens…';
  try{
   await save();
   const data=new FormData();Array.from(files).forEach(f=>data.append('files',f));data.append('descricao',$('review-image-description').value);
   const result=await api('/api/projects/'+pid+'/images',{method:'POST',body:data});
   if(current?.id!==pid){toast('Imagens adicionadas ao projeto.');return}
   current.imagens=result.imagens;current.imagens_meta=result.imagens_meta;
   document.querySelectorAll('[data-scene]').forEach(scene=>{
    const select=scene.querySelector('[data-key="imagem"]');const value=select.value;
    select.innerHTML=imageOptions();select.value=value;
    if(index!==null&&Number(scene.dataset.scene)===index){if(document.querySelector('input[name="edit-tipo_video"]:checked')?.value!=='shorts')appendSceneUploadedImages(scene,value,result.adicionadas);else select.value=result.adicionadas[0]}refreshSceneImageOptions(scene);
    drawImage(scene);
   });
   paintShortPhotos('edit');refreshVideoBackgroundImages();await save();gallery();await refresh();
   $('review-image-description').value='';$('review-media-status').textContent='Imagens adicionadas. '+(index===null?'Escolha em qual cena usar cada uma.':'As imagens foram selecionadas na cena '+(index+1)+'.');
   toast('Imagens adicionadas. Seu roteiro foi preservado.');
  }catch(error){if(current?.id===pid){$('review-media-status').textContent=error.message;await refresh()}throw error;
  }finally{uploading=false;$('review-image-files').value='';if(current)status(current)}
 }
 async function preview(index){
  if(!current)return;
  const pid=current.id,version=++revision;
  await save();
  if(current?.id!==pid||version!==revision)return;
  shown={pid,index};$('scene-preview-title').textContent='Prévia da cena '+(index+1);
  $('scene-preview-video').pause();$('scene-preview-video').removeAttribute('src');$('scene-preview-video').load();$('scene-preview-video').hidden=true;
  $('scene-preview-download').hidden=true;
  $('scene-preview-status').textContent='Preparando a prévia com sua revisão atual…';$('scene-preview-progress').value=0;
  $('scene-preview-again').disabled=true;$('scene-preview-pause').hidden=true;$('scene-preview-cancel').hidden=true;
  if(!$('scene-preview-dialog').open)$('scene-preview-dialog').showModal();
  try{
   let result=await api('/api/projects/'+pid+'/scenes/'+index+'/preview',{method:'POST'});
   if(version!==revision)return;
   shown.key=result.id;await refresh();
   while(version===revision&&$('scene-preview-dialog').open){
    result=await api('/api/projects/'+pid+'/scene-previews/'+result.id);
    if(version!==revision)return;
    $('scene-preview-status').textContent=result.desatualizada?'A cena mudou depois desta prévia. Gere novamente para atualizar.':result.mensagem;
    $('scene-preview-progress').value=result.progresso||0;
    $('scene-preview-pause').hidden=!result.em_execucao;
    $('scene-preview-cancel').hidden=result.tarefa?.status!=='fila';$('scene-preview-cancel').dataset.job=result.tarefa?.id||'';
    if(result.pronta){
     $('scene-preview-video').src=result.url;$('scene-preview-video').hidden=false;
     $('scene-preview-download').href=result.url;$('scene-preview-download').download='cena-'+(index+1)+'.mp4';$('scene-preview-download').hidden=false;
     $('scene-preview-progress').value=1;$('scene-preview-status').textContent='Prévia pronta com voz, imagens, música e transições da cena.'+(result.desatualizada?' A revisão atual tem alterações; gere novamente.':'');
     $('scene-preview-pause').hidden=true;$('scene-preview-cancel').hidden=true;break;
    }
    if(['erro','pausado'].includes(result.status))break;
    await new Promise(resolve=>setTimeout(resolve,700));
   }
  }catch(error){if(version===revision)$('scene-preview-status').textContent=error.message}
  finally{if(version===revision)$('scene-preview-again').disabled=current?.id!==pid}
 }
 async function start(){
  // An older server may still be finishing a render while files are updated.
  // Expose the controls only after the matching backend has been loaded.
  let capabilities;try{capabilities=await api('/api/health')}catch{return}
  if(!capabilities.revisao_imagens||!capabilities.cena_previa)return;
  $('schedule-draft-note').insertAdjacentHTML('afterend',`<section id="review-media" class="review-media"><div class="review-media-head"><h2>Imagens para as cenas <span id="review-image-count">0</span></h2><button id="review-images-add" type="button" class="secondary">＋ Adicionar imagens</button></div><p class="small">Envie PNG, JPG ou WebP mesmo depois de gerar o roteiro. Depois, escolha a imagem na cena. O texto e as fontes atuais são preservados.</p><label>O que aparece na imagem? <span class="optional">opcional</span><input id="review-image-description" maxlength="500" placeholder="Ex.: antena de rádio usada nas primeiras redes"></label><input id="review-image-files" type="file" accept="image/png,image/jpeg,image/webp" multiple hidden><p id="review-media-status" class="small" role="status"></p><p id="review-research-note" class="small" role="status" hidden></p><details><summary>Imagens disponíveis</summary><div id="review-image-gallery"></div></details></section>`);
  document.body.insertAdjacentHTML('beforeend',`<dialog id="scene-preview-dialog" aria-labelledby="scene-preview-title"><div class="dialog-head"><h2 id="scene-preview-title">Prévia da cena</h2><button id="scene-preview-close" type="button" class="secondary" aria-label="Fechar prévia">×</button></div><p class="small">Confira esta cena antes de renderizar o vídeo completo. A passagem da cena anterior é incluída quando estiver configurada.</p><p id="scene-preview-status" role="status"></p><progress id="scene-preview-progress" max="1" value="0"></progress><video id="scene-preview-video" controls preload="metadata" hidden></video><div class="toolbar"><button id="scene-preview-again" class="primary" type="button">Gerar prévia novamente</button><a id="scene-preview-download" class="secondary" hidden>↓ Baixar esta cena</a><button id="scene-preview-pause" class="secondary" type="button" hidden>Pausar prévia</button><button id="scene-preview-cancel" class="secondary" type="button" hidden>Cancelar espera</button></div></dialog>`);
  const paint=paintScenes,previousStatus=status;
  paintScenes=()=>{
   paint();
   document.querySelectorAll('[data-scene]').forEach(scene=>{
    const index=Number(scene.dataset.scene),select=scene.querySelector('[data-key="imagem"]'),value=select.value;
    select.innerHTML=imageOptions();select.value=value;
    select.closest('label').insertAdjacentHTML('afterend','<div class="scene-image-preview" hidden></div>');select.addEventListener('change',()=>drawImage(scene));drawImage(scene);
    scene.insertAdjacentHTML('beforeend',`<div class="scene-review-actions"><button type="button" class="primary" data-scene-preview="${index}">▷ Prévia desta cena</button><button type="button" class="secondary" data-scene-image="${index}">＋ Enviar imagens para esta cena</button></div>`);
    scene.querySelector('[data-scene-preview]').onclick=()=>action(()=>preview(index));scene.querySelector('[data-scene-image]').onclick=()=>pick(index);
   });gallery();
  };
  status=p=>{const busy=previousStatus(p);controls(p,busy);return busy};
  $('review-images-add').onclick=()=>pick();$('review-image-files').onchange=()=>action(()=>upload(Array.from($('review-image-files').files)));
  $('scene-preview-close').onclick=()=>$('scene-preview-dialog').close();
  $('scene-preview-dialog').addEventListener('close',()=>{revision++;$('scene-preview-video').pause()});
  $('scene-preview-again').onclick=()=>action(()=>{if(current?.id!==shown?.pid)throw Error('Abra o projeto desta cena para gerar novamente.');return preview(shown.index)});
  $('scene-preview-pause').onclick=()=>action(async()=>{await api('/api/projects/'+shown.pid+'/pause',{method:'POST'});toast('Pausa solicitada para a prévia.')});
  $('scene-preview-cancel').onclick=()=>action(async()=>{await api('/api/queue/'+$('scene-preview-cancel').dataset.job,{method:'DELETE'});toast('Espera cancelada.')});
  if(current){paintScenes();status(current)}
 }
 if(window.studioReady)start();else window.addEventListener('studio-ready',start,{once:true});
})();
