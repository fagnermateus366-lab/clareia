// Reuse a finished video's settings while writing new content for a new subject.
(() => {
 let favorites=[],controlSlots=[],activeFavorite='',manualMusic=null,musicEdited=false;
 const json=body=>({headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const selected=()=>favorites.find(f=>f.id===$('favorite-select').value);
 const useFavorite=()=>$('use-favorite').checked;
 function placeControls(enabled){
  if(enabled&&!controlSlots.length){
   const nodes=[$('create-roteiro_provedor').closest('label'),$('create-model-trigger').closest('.model-field'),
    $('create-plan-box'),$('create-provider-note'),$('create-gemini-test-area'),$('create-gemini-project'),$('create-musica_fundo').closest('.music-settings')];
   controlSlots=nodes.map(node=>{const marker=document.createComment('favorite-control');node.before(marker);$('favorite-overrides').append(node);return {node,marker}});
  }else if(!enabled&&controlSlots.length){
   for(const {node,marker} of controlSlots){marker.replaceWith(node)}controlSlots=[];
  }
  $('favorite-overrides').hidden=!enabled;
 }
 function setMusic(s){
  $('create-musica_fundo').innerHTML=musicOptions(s.musica_fundo||'');
  setMusicVolume('create',musicVolumePercent(s.volume_musica_db??-20));
  // Keep the original dB value exact until the user edits the volume.
  $('create-volume_musica_db').value=s.volume_musica_db??-20;
  $('create-reduzir_musica_na_fala').checked=s.reduzir_musica_na_fala!==false;
  paintMusicNote('create');
 }
 function summary(f){
  const voice=f.config.gemini_projeto_completo?'Gemini '+f.config.gemini_voz:studioCatalog.vozes.find(v=>v.id===f.config.voz)?.nome||f.config.voz;
  const animation=studioCatalog.animacoes.find(a=>a.id===f.config.animacao)?.nome||f.config.animacao;
  return voice+' · '+animation+' · '+f.quantidade_cenas+' cenas de referência';
 }
 async function load(){
  const previous=$('favorite-select').value;
  favorites=await api('/api/favorites');
  $('favorite-select').innerHTML=favorites.length?favorites.map(f=>`<option value="${esc(f.id)}" ${f.id===previous?'selected':''}>${esc(f.nome)}</option>`).join(''):'<option value="">Favorite a configuração de um vídeo concluído</option>';
  $('use-favorite').disabled=!favorites.length;
  if(!favorites.length)$('use-favorite').checked=false;
  mode();paintButton(current);
 }
 function mode(){
  const enabled=useFavorite(),favorite=selected();
  $('favorite-choice').hidden=!enabled;
  $('create-config').hidden=enabled;
  placeControls(enabled);
  if(enabled&&favorite){
   if(!activeFavorite){manualMusic=musicConfig('create');musicEdited=false}
   if(activeFavorite!==favorite.id&&!musicEdited)setMusic(favorite.config);
   activeFavorite=favorite.id;
  }else if(activeFavorite){
   if(!musicEdited&&manualMusic)setMusic(manualMusic);
   activeFavorite='';manualMusic=null;musicEdited=false;
  }
  document.querySelector('[data-create-step="3"]').hidden=enabled;
  if(enabled&&$('create-form').dataset.step==='3')creationStep(2);
  $('favorite-summary').textContent=favorite?summary(favorite)+'. Você pode escolher outra música e outra IA abaixo.':'';
  if(window.paintQuickModel)window.paintQuickModel();
 }
 function prepareCreation(){
  quickModelChoice=null;
  $('creation-purpose').innerHTML=motivationFields('create',{});bindMotivation('create');
  activeFavorite='';manualMusic=null;musicEdited=false;
  // Duration is shared; writer and music controls remain editable in favorite mode.
  const duration=$('create-minutos')?.closest('label');
  if(duration)$('creation-duration').replaceChildren(duration);const kind=$('create-video-kind');if(kind)$('creation-video-kind').replaceChildren(kind);
  $('title').value='';$('topic').value='';$('create-mode').value='revisao';
  mode();creationMode();
 }
 function creationMode(){
  const scheduled=$('create-mode').value==='agendar';
  $('create-button').textContent=scheduled?'Continuar para agendar':'Criar roteiro';
  document.querySelector('.config-panel .tip').textContent=scheduled?'No horário escolhido, o aplicativo criará o roteiro, produzirá o vídeo e publicará no canal selecionado.':'Primeiro, você recebe um roteiro editável. A renderização começa quando você escolher.';
 }
 function paintButton(p){
  const button=$('favorite-project');if(!button)return;
  const item=favorites.find(f=>f.projeto===p?.id);
  button.textContent=item?'★ Configuração favorita':'☆ Favoritar configuração';
  button.disabled=!p?.exportado||p.processando||['fila','agendado','renderizando','enviando_youtube'].includes(p?.status?.status);
  button.dataset.favorite=item?.id||'';
 }
 async function showLibrary(){
  await load();
  $('favorite-items').innerHTML=favorites.length?favorites.map(f=>`<article class="favorite-item"><label>Nome da configuração<input value="${esc(f.nome)}" maxlength="150" data-favorite-name="${esc(f.id)}"></label><p class="small">${esc(summary(f))}</p><div class="toolbar"><button type="button" class="primary" data-use-favorite="${esc(f.id)}">Usar em novo vídeo</button><button type="button" class="secondary" data-rename-favorite="${esc(f.id)}">Salvar nome</button><button type="button" class="secondary" data-remove-favorite="${esc(f.id)}">Remover dos favoritos</button></div></article>`).join(''):'<p>Abra um vídeo concluído e marque ☆ Favoritar configuração para começar.</p>';
  document.querySelectorAll('[data-use-favorite]').forEach(b=>b.onclick=()=>{reset();$('favorite-select').value=b.dataset.useFavorite;$('use-favorite').checked=true;mode();$('favorites-dialog').close();$('topic').focus()});
  document.querySelectorAll('[data-rename-favorite]').forEach(b=>b.onclick=()=>action(async()=>{await api('/api/favorites/'+b.dataset.renameFavorite,{method:'PUT',...json({nome:document.querySelector('[data-favorite-name="'+b.dataset.renameFavorite+'"]').value})});await showLibrary();toast('Nome salvo.')}));
  document.querySelectorAll('[data-remove-favorite]').forEach(b=>b.onclick=()=>action(async()=>{await api('/api/favorites/'+b.dataset.removeFavorite,{method:'DELETE'});await showLibrary();toast('Configuração removida da lista. Os projetos que já a usam foram preservados.')}));
  if(!$('favorites-dialog').open)$('favorites-dialog').showModal();
 }
 function start(){
  $('new-project').insertAdjacentHTML('afterend','<button id="favorites-open" class="favorite-library" type="button">★ Configurações favoritas</button>');
  document.querySelector('.workspace-top .toolbar').insertAdjacentHTML('afterbegin','<button id="favorite-project" class="secondary" type="button" disabled>☆ Favoritar configuração</button>');
  $('favorites-open').onclick=()=>action(showLibrary);
  $('favorite-close').onclick=()=>$('favorites-dialog').close();
  $('favorite-project').onclick=()=>action(async()=>{
   const id=$('favorite-project').dataset.favorite;
   if(id)await api('/api/favorites/'+id,{method:'DELETE'});
   else await api('/api/projects/'+current.id+'/favorite',{method:'POST'});
   await load();toast(id?'Configuração removida dos favoritos.':'Configuração completa salva nos favoritos.');
  });
  window.favoriteModelForCreate=()=>useFavorite()?{roteiro_provedor:$('create-roteiro_provedor').value,roteiro_modelo:$('create-roteiro_modelo').value}:null;
  window.favoritePreviewConfig=prefix=>prefix==='create'&&useFavorite()&&selected()?{...selected().config,...geminiProjectConfig('create'),...shortVideoConfig('create')}:null;
  $('use-favorite').onchange=$('favorite-select').onchange=mode;
  const musicChanged=e=>{if(useFavorite()&&['create-musica_fundo','create-volume_musica','create-volume_musica_percent','create-reduzir_musica_na_fala'].includes(e.target.id))musicEdited=true};
  document.addEventListener('change',musicChanged,true);document.addEventListener('input',musicChanged,true);
  $('create-mode').onchange=creationMode;
  const oldReset=reset;reset=()=>{
   closeModelPickers();placeControls(false);
   document.querySelectorAll('#create-model-menu').forEach(menu=>{if(menu.parentElement===document.body)menu.remove()});
   $('creation-duration').replaceChildren();$('creation-video-kind').replaceChildren();oldReset();prepareCreation();
  };
  $('new-project').onclick=$('back').onclick=reset;
  const oldStatus=status;status=p=>{
   const busy=oldStatus(p);paintButton(p);
   $('edit-topic-box').hidden=!!p.cenas.length||!p.assunto?.assunto;
   $('edit-topic').disabled=busy;
   if($('edit-topic').dataset.project!==p.id){$('edit-topic').dataset.project=p.id;$('edit-topic').dataset.dirty='false';$('edit-topic').value=p.assunto?.assunto||''}
   else if($('edit-topic').dataset.dirty!=='true'&&document.activeElement!==$('edit-topic'))$('edit-topic').value=p.assunto?.assunto||'';
   return busy;
  };
  window.editTopicForSave=()=>$('edit-topic-box').hidden?undefined:$('edit-topic').value;
  $('edit-topic').oninput=()=>{$('edit-topic').dataset.dirty='true'};
  const priorSave=save;save=async()=>{await priorSave();if(!$('edit-topic-box').hidden){current.assunto={...current.assunto,assunto:$('edit-topic').value};$('edit-topic').dataset.dirty='false'}};
  $('source-next').onclick=()=>{
   if(!$('topic').value.trim()&&!$('source-text').value.trim()&&!$('urls').value.trim()&&!window.filePool.length&&!$('files').files.length){toast('Informe o assunto ou adicione uma fonte para continuar.',true);return}
   creationStep(2);
  };
  $('create-form').onsubmit=e=>{e.preventDefault();action(async()=>{
   if(window.sourceAIBusy)throw Error('Aguarde a fonte com IA terminar antes de criar o projeto.');
   const files=window.filePool.length?window.filePool:Array.from($('files').files||[]),topic=$('topic').value.trim();
   if(!topic&&!files.length&&!$('source-text').value.trim()&&!$('urls').value.trim())throw Error('Informe o assunto ou adicione uma fonte.');
   const favorite=useFavorite()?selected():null;
   if(useFavorite()&&!favorite)throw Error('Escolha uma configuração favorita.');
   const minutes=Number($('create-minutos').value);
   if(!(minutes>0))throw Error('Informe uma duração maior que zero.');
   const settings={...(favorite?{minutos:minutes,...musicConfig('create'),...geminiProjectConfig('create')}:config('create')),...window.sourceAIConfig?.('create'),...stageAIConfig('create'),...shortVideoConfig('create')};
   const data=new FormData();data.append('titulo',$('title').value.trim());data.append('assunto',topic);
   data.append('texto',$('source-text').value);data.append('urls',$('urls').value);data.append('config',JSON.stringify(settings));
   data.append('clipes_youtube',JSON.stringify(window.youtubeClipSelection?.()||[]));
   if(favorite)data.append('favorito',favorite.id);
   if(quickModelChoice)data.append('modelo_local',quickModelChoice);
   for(const file of files)data.append('files',file);
   const scheduled=$('create-mode').value==='agendar';$('create-button').disabled=true;
   try{
    const project=await api('/api/projects',{method:'POST',body:data});clearAllSources();
    await openProject(project.id);
    if(scheduled){$('schedule').click();toast('Escolha o horário para pesquisar, criar o roteiro e publicar o vídeo automaticamente.')}
    else{await api('/api/projects/'+project.id+'/script',{method:'POST'});await refresh()}
   }finally{$('create-button').disabled=false}
  })};
  prepareCreation();load().catch(e=>toast(e.message,true));
 }
 if(window.studioReady)start();else window.addEventListener('studio-ready',start,{once:true});
})();
