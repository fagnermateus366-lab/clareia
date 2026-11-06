// Extend the editor with animation choices, local voices and recoverable projects.
let deletePending=null,previewPrefix='create',previewStyle='ilustracoes';
const handSpeeds=[[.5,'Bem calma · 0,5×'],[.75,'Suave · 0,75×'],[1,'Natural · 1×'],[1.25,'Ágil · 1,25×']];
let previewRevision=0;
let voiceSampleURL=null;
let voiceSampleRevision=0;
function clearVoicePreview(){
 previewRevision++;$('animation-video').pause();$('animation-video').removeAttribute('src');$('animation-video').load();
 $('animation-video').hidden=true;$('animation-poster').hidden=false;$('animation-poster').src='/static/previews/'+previewStyle+'.png'+(previewStyle==='historia_ilustrada'?'':'?v=layout-transitions-1');
 if(previewStyle==='shotcraft'&&!studioCatalog.shotcraft.receitas.find(r=>r.id===$(previewPrefix+'-shotcraft_receita')?.value)?.modelo3d)$('animation-poster').src=shotcraftPreviewURL(previewPrefix,$(previewPrefix+'-shotcraft_receita').value==='auto'?'titulo_marcado':$(previewPrefix+'-shotcraft_receita').value);
 let three=$('animation-three');if(!three){three=document.createElement('iframe');three.id='animation-three';three.title='Demonstração do modelo 3D';three.style.cssText='width:100%;height:340px;border:0;border-radius:8px';$('animation-poster').after(three);}
 const recipe=studioCatalog.shotcraft.receitas.find(r=>r.id===$(previewPrefix+'-shotcraft_receita')?.value),isThree=previewStyle==='shotcraft'&&recipe?.modelo3d;
 three.hidden=!isThree;three.src=isThree?'/3d/?embed=1&model='+encodeURIComponent(recipe.modelo3d)+'&format='+(document.querySelector(`input[name="${previewPrefix}-tipo_video"]:checked`)?.value||'video')+'&movement='+encodeURIComponent(readThreeOptions(previewPrefix).movement||'padrao'):'about:blank';if(isThree)$('animation-poster').hidden=true;
 if(previewStyle==='colagem_documental')$('animation-poster').src='/static/previews/colagem_documental.gif?v=vox-density-3';
 $('animation-test-status').textContent='Teste um trecho com a voz e o ritmo escolhidos. A preparação é local e fica em cache.';
}
async function testVoicePreview(){
 const revision=previewRevision,b=$('animation-test');b.disabled=true;
 try{
  $('animation-test-status').textContent='Preparando animação com a voz escolhida…';
  const settings={...videoBackgroundConfig(previewPrefix),...shotcraftConfig(previewPrefix),...geminiProjectConfig(previewPrefix),...shortVideoConfig(previewPrefix),voz:$('animation-voice').value,estilo_locucao:$('animation-delivery').value,velocidade:Number($('animation-pace').value),animacao:previewStyle,velocidade_mao:Number($('animation-hand-speed').value),formato:$(previewPrefix+'-formato').value,estilo:$(previewPrefix+'-estilo').value,destaques_animados:$(previewPrefix+'-destaques_animados').checked,camera_dinamica:$('animation-camera').checked,animar_elementos:$(previewPrefix+'-animar_elementos').checked,imagem_estatica:$(previewPrefix+'-imagem_estatica').checked,transicao:$(previewPrefix+'-transicao').value,duracao_transicao:Number($(previewPrefix+'-duracao_transicao').value),aplicar_transicao:$(previewPrefix+'-aplicar_transicao').value,movimento_figuras:$('animation-figure-motion').value};
  const job=await api('/api/animation-previews'+(previewPrefix==='edit'?'?projeto='+encodeURIComponent(current.id):''),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings)});
  for(;;){
   const state=await api('/api/animation-previews/'+job.id);
   if(revision!==previewRevision)return;
   if(['erro','pausado'].includes(state.status))throw Error(state.mensagem);
   if(state.url){$('animation-poster').hidden=true;$('animation-video').hidden=false;$('animation-video').src=state.url;$('animation-test-status').textContent='Prévia pronta com '+(settings.gemini_projeto_completo?'Gemini '+settings.gemini_voz:studioCatalog.vozes.find(v=>v.id===settings.voz).nome)+'. Clique em reproduzir.';return}
   $('animation-test-status').textContent=state.mensagem;await new Promise(resolve=>setTimeout(resolve,700));
  }
 }finally{b.disabled=false}
}
const opt=(items,value)=>items.map(([v,n,disabled])=>`<option value="${esc(v)}" ${String(v)===String(value)?'selected':''} ${disabled?'disabled':''}>${esc(n)}</option>`).join('');
function transitionFields(prefix,s={}){
 const transitions=(studioCatalog.transicoes||[]).map(t=>[t.id,t.nome]);
 return `<fieldset class="transition-settings"><legend>Transições e imagens</legend><div class="config-fields">
 <label>Efeito de transição<select id="${prefix}-transicao">${opt(transitions,s.transicao??'padrao')}</select></label>
 <label>Duração da transição<select id="${prefix}-duracao_transicao">${opt([[.3,'Rápida · 0,3 s'],[.6,'Suave · 0,6 s'],[1,'Calma · 1 s'],[1.5,'Longa · 1,5 s'],[2,'Muito longa · 2 s']],s.duracao_transicao??.6)}</select></label>
 <label>Aplicar transições<select id="${prefix}-aplicar_transicao"><option value="cenas">Somente entre cenas</option></select></label></div>
 <p class="small">Estes efeitos são usados na mudança de cena, como da introdução para a explicação. Em Reels com fotos ou clipes, as passagens dentro da narração são escolhidas em Transição na troca de mídia, sem pausar a voz.</p><label class="check-row"><input type="checkbox" id="${prefix}-animar_elementos" ${s.animar_elementos!==false?'checked':''}>Animar os elementos · desmarque para usar apenas as transições</label>
 <label class="check-row"><input type="checkbox" id="${prefix}-imagem_estatica" ${s.imagem_estatica!==false?'checked':''}>Manter a imagem de referência parada durante a explicação</label>
 <button type="button" class="secondary" data-transition-preview="${prefix}">▷ Ver efeito de transição</button>
 <div id="${prefix}-transition-demo" class="transition-demo" hidden><img alt="Demonstração da transição entre dois contextos"><p class="small"></p></div>
 </fieldset>`;
}
function bindTransitionControls(prefix){
 const update=()=>{
  const id=$(prefix+'-transicao').value,entry=studioCatalog.transicoes?.find(t=>t.id===id);
  const demo=$(prefix+'-transition-demo');
  if(!demo.hidden){demo.querySelector('img').src='/api/transitions/'+encodeURIComponent(id)+'/preview';demo.querySelector('p').textContent=entry?.descricao||''}
 };
 $(prefix+'-transicao').onchange=()=>{
  if($(prefix+'-transicao').value==='papel_amassado'&&Number($(prefix+'-duracao_transicao').value)<1.5)$(prefix+'-duracao_transicao').value='2';
  update();
 };
 document.querySelector(`[data-transition-preview="${prefix}"]`).onclick=()=>{const demo=$(prefix+'-transition-demo');demo.hidden=!demo.hidden;update()};
}
function drawAnimationPreview(){
 if(!studioCatalog.animacoes.some(a=>a.id===previewStyle))previewStyle='shotcraft';
 const selected=studioCatalog.animacoes.find(a=>a.id===previewStyle);
 $('animation-choices').innerHTML=studioCatalog.animacoes.map(a=>`<button type="button" class="animation-choice ${a.id===previewStyle?'selected':''}" data-animation-choice="${a.id}" aria-pressed="${a.id===previewStyle}"><b>${esc(a.nome)}</b><small>${esc(a.descricao)}</small></button>`).join('');
 document.querySelectorAll('[data-animation-choice]').forEach(b=>b.onclick=()=>{previewStyle=b.dataset.animationChoice;drawAnimationPreview()});
 $('animation-caption').textContent=selected?.descricao||'';
 const library=$('animation-library'),recipe=studioCatalog.shotcraft.receitas.find(r=>r.id===$(previewPrefix+'-shotcraft_receita')?.value);library.hidden=previewStyle!=='colagem_documental'&&!(previewStyle==='shotcraft'&&recipe?.figuras);library.textContent=previewStyle==='shotcraft'?(recipe?.acervo3d?'Ver objetos do acervo 3D':'Ver figuras do ShotCraft'):'Ver figuras do Vox';
 $('animation-hand-options').hidden=previewStyle!=='mao';$('animation-camera-options').hidden=!['historia_ilustrada','colagem_documental'].includes(previewStyle);$('animation-figure-options').hidden=previewStyle!=='colagem_documental';clearVoicePreview();
}
let trashItems=[];
function chosenAnimation(prefix){
 const choice=$(prefix+'-animacao');if(choice.selectedOptions[0]?.disabled)throw Error('Este modelo foi removido. Escolha outra animação.');return choice.value;
}
function animationOptions(value,inherit=false){
 const items=[...(inherit?[['herdar','Usar a do projeto']]:[]),...studioCatalog.animacoes.map(a=>[a.id,a.nome])];
 if(['historia','historia_ilustrada'].includes(value))items.unshift([value,'Modelo removido · escolha outra animação',true]);
 return opt(items,value);
}
function videoClock(value){
 if(value===null||value===undefined||!Number.isFinite(Number(value))||Number(value)<0)return 'Não registrado';
 const seconds=Math.round(Number(value)),hours=Math.floor(seconds/3600),minutes=Math.floor(seconds/60)%60,rest=seconds%60;
 return (hours?hours+':'+String(minutes).padStart(2,'0'):String(minutes))+':'+String(rest).padStart(2,'0');
}
function completedCard(p){
 const d=p.conclusao||{},name=d.modelo_nome||d.modelo||'Modelo não registrado';
 const scheduledBadge=d.fluxo_agendado?'<span class="completed-scheduled-badge" role="img" aria-label="Fluxo agendado concluído automaticamente" title="Fluxo agendado concluído automaticamente"><svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m4 8 2.5 2.5L12 5"/></svg></span>':'';
 const timing=`<span class="completed-time completed-script-time" title="Do pedido de geração do roteiro ao início da renderização. Inclui estudo, narração, espera e revisão entre as etapas."><span>Roteiro</span><b>${videoClock(d.tempo_roteiro_s)}</b></span><span class="completed-time completed-render-time" title="Do início da renderização até o vídeo ficar pronto."><span>Renderização</span><b>${videoClock(d.tempo_render_s)}</b></span><span class="completed-time completed-total-time" title="Soma de Roteiro e Renderização. O envio ao YouTube não faz parte deste tempo."><span class="completed-total-label">Total${scheduledBadge}</span><b>${videoClock(d.tempo_producao_s)}</b></span>`;
 return `<span class="completed-poster"><span class="completed-poster-fallback" aria-hidden="true">▶</span>${d.miniatura?`<img src="${esc(d.miniatura)}" loading="lazy" decoding="async" alt="Prévia de ${esc(p.titulo)}" onerror="this.hidden=true">`:''}<span class="completed-video-length" aria-label="Duração do vídeo">${videoClock(d.duracao_s)}</span></span><strong title="${esc(p.titulo)}">${esc(p.titulo)}</strong><span class="completed-model" title="${esc(d.modelo||name)}">IA · ${esc(name)}</span>${timing}`;
}
async function showTrash(){
 const items=await api('/api/trash');
 trashItems=items;
 $('trash-empty').disabled=!items.length;
 $('trash-confirm-box').hidden=true;
 $('trash-summary').textContent=items.length?`${items.length} ${items.length===1?'projeto':'projetos'} · ${formatBytes(items.reduce((n,p)=>n+(p.tamanho_bytes||0),0))} em arquivos`:'A lixeira está vazia.';
 $('trash-list').innerHTML=items.length?items.map(p=>`<div class="trash-row"><div><span>${esc(p.titulo)}</span><small>${formatBytes(p.tamanho_bytes||0)}${p.remocao_incompleta?' · Remoção interrompida. Esvazie novamente para concluir.':''}</small></div><button class="secondary" data-restore="${esc(p.id)}" ${p.remocao_incompleta?'disabled':''}>Restaurar</button></div>`).join(''):'<p class="small">Os projetos que você excluir aparecerão aqui até serem restaurados ou removidos definitivamente.</p>';
 document.querySelectorAll('[data-restore]').forEach(b=>b.onclick=()=>action(async()=>{await api('/api/trash/'+b.dataset.restore+'/restore',{method:'POST'});await list();await showTrash();toast('Projeto restaurado.')}));
 if(!$('trash-dialog').open)$('trash-dialog').showModal();
}
function creationStep(step){
 $('create-form').dataset.step=step;
 document.querySelectorAll('[data-create-step]').forEach(b=>{if(b.dataset.createStep===String(step))b.setAttribute('aria-current','step');else b.removeAttribute('aria-current')});
 if($('create-advanced'))$('create-advanced').open=String(step)==='3';
}
function sourceTab(mode){
 $('create-form').dataset.sourceMode=mode;
 for(const [key,id] of [['arquivos','files'],['texto','source-text'],['links','urls']])$(id).closest('label').hidden=mode!==key;
 if($('file-queue'))$('file-queue').hidden=mode!=='arquivos'||!(window.filePool?.length);
 if($('source-ai-panel'))$('source-ai-panel').hidden=mode!=='texto';
 document.querySelectorAll('[data-source-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sourceTab===mode)));
}
document.addEventListener('DOMContentLoaded',()=>action(async()=>{
 const bootNavigation=navigationRevision;
 studioCatalog=await api('/api/options');
 await loadMusicCatalog();
 const originalFields=fields,originalConfig=config,originalBind=configBind,originalStatus=status,originalPaint=paintScenes,originalSave=save,originalReset=reset;
 fields=(prefix,s={})=>{
  let html=originalFields(prefix,s);
  const voices=studioCatalog.vozes.map(v=>[v.id,v.nome+' · '+v.motor+(v.instalada?'':' · não instalada'),!v.instalada]);
  for(const voice of [s.voz,s.voz_secundaria])if(voice?.startsWith('clone_')&&!voices.some(v=>v[0]===voice))voices.push([voice,'Voz apagada · escolha outra voz',true]);
  html=html.replace(new RegExp('(<select id="'+prefix+'-voz">)[\\s\\S]*?(</select>)'),(_,a,b)=>a+opt(voices,s.voz??'pf_dora')+b);
  html=html.replace('Voz · Kokoro local','Voz');
  html=html.replace('Estilo visual','Cores');
  const split=html.indexOf('<div class="writer-settings">');
  const basic=document.createElement('div');basic.innerHTML=html.slice(0,split);let secondary='';
  basic.querySelector('#'+prefix+'-estilo').innerHTML=videoPaletteOptions(s.estilo||'oceano');
  const tone=basic.querySelector('#'+prefix+'-tom'),tones=studioCatalog.tons||[];
  if(tones.length)tone.innerHTML=['Explicação','Motivacional'].map(group=>`<optgroup label="${group}">${opt(tones.filter(t=>t.grupo===group).map(t=>[t.id,t.nome]),s.tom??'didático')}</optgroup>`).join('');
  tone.closest('label').insertAdjacentHTML('beforeend',`<small id="${prefix}-tone-note"></small>`);
  for(const key of ['tom','apresentadores','modo_visual','estilo']){const label=basic.querySelector('#'+prefix+'-'+key).closest('label');secondary+=key==='tom'?`<div id="${prefix}-tone-home" class="script-tone-home">${label.outerHTML}</div>`:label.outerHTML+(key==='estilo'?videoBackgroundFields(prefix,s):'');label.remove()}
 const select=(key,label,items,value)=>`<label>${label}<select id="${prefix}-${key}" ${key==='estilo_locucao'?`aria-label="${esc(label)}" aria-describedby="${prefix}-delivery-note"`:''}>${opt(items,value)}</select>${key==='estilo_locucao'?`<small id="${prefix}-delivery-note"></small>`:''}</label>`;
  basic.querySelector('.config-fields').insertAdjacentHTML('beforeend',`
   ${select('estilo_locucao','Modo de locução',studioCatalog.locucoes.map(d=>[d.id,d.nome]),s.estilo_locucao??'natural')}
   <label>Animação<select id="${prefix}-animacao">${animationOptions(s.animacao??'ilustracoes')}</select></label>
   <label class="hand-speed" id="${prefix}-hand-options" ${s.animacao==='mao'?'':'hidden'}>Velocidade da mão<select id="${prefix}-velocidade_mao">${opt(handSpeeds,s.velocidade_mao??.75)}</select><small>Acompanha a fala e reserva tempo para observar o desenho.</small></label>
   <label id="${prefix}-second-voice" ${s.apresentadores===2?'':'hidden'}>Segunda voz<select id="${prefix}-voz_secundaria">${opt(voices,s.voz_secundaria??'pm_alex')}</select></label>
  `);
  return shortVideoFields(prefix,s)+basic.innerHTML+musicFields(prefix,s)+transitionFields(prefix,s)+shotcraftFields(prefix,s)+`<fieldset id="${prefix}-collage-options" ${s.animacao==='colagem_documental'?'':'hidden'}><legend>Figuras da colagem documental</legend><p class="small collage-comfort-note">O papel permanece fixo. Com imagem principal, até dois apoios; sem imagem, até três na horizontal. Recortes e legendas entram suavemente. A transição escolhida ocorre só entre cenas.</p><label>Movimento das figuras<select id="${prefix}-movimento_figuras">${opt([['tematico','Movimentos discretos por objeto'],['suave','Balanço suave de adesivos'],['nenhum','Figuras paradas']],s.movimento_figuras??'tematico')}</select></label><p class="small">96 recortes locais em 8 áreas. Os movimentos de rotação, pulsação, respiração e sinais foram suavizados. <button type="button" class="secondary" data-collage-library>Ver figuras</button> Você também pode usar imagens das fontes e indicar figuras em cada cena.</p><label class="check-row"><input type="checkbox" id="${prefix}-colagem_buscar_figuras" ${s.colagem_buscar_figuras?'checked':''}>Ampliar o acervo com busca de figuras no Wikimedia Commons</label><p class="small">Opcional. Envia somente os termos visuais da busca, salva as imagens e os créditos no computador. Sem correspondência, a informação permanece em texto. Fotos encontradas precisam de revisão no contexto da cena.</p></fieldset><div class="animation-line"><button type="button" class="secondary" data-preview="${prefix}">▷ Ver animações</button><label class="check-row"><input type="checkbox" id="${prefix}-destaques_animados" ${s.destaques_animados!==false?'checked':''}>Palavras grandes animadas</label><label class="check-row" id="${prefix}-camera-options" ${['historia_ilustrada','colagem_documental'].includes(s.animacao)?'':'hidden'}><input type="checkbox" id="${prefix}-camera_dinamica" ${s.camera_dinamica!==false?'checked':''}>Aproximações e deslocamentos suaves de câmera</label></div><p class="small voice-note" id="${prefix}-voice-note"></p>
  <details class="advanced-settings" id="${prefix}-advanced"><summary>Roteiro, modelos de IA e opções avançadas</summary><div class="config-fields">${secondary}</div>${html.slice(split)}</details>`;
 };
 config=prefix=>({...originalConfig(prefix),...videoBackgroundConfig(prefix),...shotcraftConfig(prefix),...shortVideoConfig(prefix),...geminiProjectConfig(prefix),...musicConfig(prefix),animacao:chosenAnimation(prefix),colagem_buscar_figuras:$(prefix+'-colagem_buscar_figuras').checked,movimento_figuras:$(prefix+'-movimento_figuras').value,velocidade_mao:Number($(prefix+'-velocidade_mao').value),estilo_locucao:$(prefix+'-estilo_locucao').value,voz_secundaria:$(prefix+'-voz_secundaria').value,destaques_animados:$(prefix+'-destaques_animados').checked,camera_dinamica:$(prefix+'-camera_dinamica').checked,animar_elementos:$(prefix+'-animar_elementos').checked,imagem_estatica:$(prefix+'-imagem_estatica').checked,transicao:$(prefix+'-transicao').value,duracao_transicao:Number($(prefix+'-duracao_transicao').value),aplicar_transicao:$(prefix+'-aplicar_transicao').value});
 configBind=()=>{
  originalBind();
  for(const prefix of ['create','edit'])if($(prefix+'-voice-note')){
   const note=()=>{voiceSampleRevision++;if(audio)audio.pause();const d=studioCatalog.locucoes.find(d=>d.id===$(prefix+'-estilo_locucao').value);$(prefix+'-delivery-note').textContent=d?.descricao||'';updateGeminiProject(prefix)};
   bindShortVideo(prefix);bindShotcraft(prefix);bindVideoBackgrounds(prefix);note();$(prefix+'-voz').onchange=note;$(prefix+'-voz_secundaria').onchange=note;$(prefix+'-estilo_locucao').addEventListener('change',note);bindTransitionControls(prefix);bindMusicControls(prefix);
   $(prefix+'-animacao').onchange=()=>{const style=$(prefix+'-animacao').value;$(prefix+'-hand-options').hidden=style!=='mao';$(prefix+'-camera-options').hidden=!['historia_ilustrada','colagem_documental'].includes(style);$(prefix+'-collage-options').hidden=style!=='colagem_documental';updateShotcraft(prefix)};
   $(prefix+'-apresentadores').onchange=()=>updateGeminiProject(prefix);updateGeminiProject(prefix);
  }
  document.querySelectorAll('[data-sample]').forEach(b=>b.onclick=()=>action(async()=>{
   if(audio)audio.pause();b.disabled=true;const label=b.textContent,revision=++voiceSampleRevision;b.textContent='Preparando…';
   try{
    const response=await fetch('/api/samples/'+encodeURIComponent($(b.dataset.sample+'-voz').value)+'?estilo='+encodeURIComponent($(b.dataset.sample+'-estilo_locucao').value));
    if(!response.ok){const error=await response.json().catch(()=>({}));throw Error(error.detail||'Não foi possível ouvir esta voz agora.')}
    const blob=await response.blob();if(revision!==voiceSampleRevision)return;
    if(voiceSampleURL)URL.revokeObjectURL(voiceSampleURL);voiceSampleURL=URL.createObjectURL(blob);audio=new Audio(voiceSampleURL);await audio.play();
   }finally{b.disabled=false;b.textContent=label}
  }));
  document.querySelectorAll('[data-preview]').forEach(b=>b.onclick=()=>{previewPrefix=b.dataset.preview;previewStyle=$(previewPrefix+'-animacao').value;for(const [dialogKey,field] of [['hand-speed','velocidade_mao'],['voice','voz'],['delivery','estilo_locucao'],['pace','velocidade']])$('animation-'+dialogKey).value=$(previewPrefix+'-'+field).value;$('animation-camera').checked=$(previewPrefix+'-camera_dinamica').checked;$('animation-figure-motion').value=$(previewPrefix+'-movimento_figuras').value;drawAnimationPreview();$('animation-voice').disabled=geminiEnabled(previewPrefix);if(geminiEnabled(previewPrefix))$('animation-test-status').textContent='A prévia usará a voz Gemini '+$(previewPrefix+'-gemini_voz').value+' e consumirá a API. O MP4 é montado neste computador.';$('animation-dialog').showModal()});
 };
 list=async()=>{
  const items=await api('/api/projects');
  const groups={ativos:[],concluidos:[],agendamentos:[]};
  for(const p of items)(groups[p.grupo||(['concluido','enviado_youtube'].includes(p.status.status)?'concluidos':'ativos')]||groups.ativos).push(p);
  groups.ativos.sort((a,b)=>Number(b.em_execucao)-Number(a.em_execucao));
  groups.agendamentos.sort((a,b)=>(a.tarefa_fila?.scheduled||Date.parse(a.agendamento?.horario)/1000||Infinity)-(b.tarefa_fila?.scheduled||Date.parse(b.agendamento?.horario)/1000||Infinity));
  for(const [group,id] of [['ativos','projects'],['concluidos','completed-projects'],['agendamentos','scheduled-projects']]){
   $('count-'+group).textContent=groups[group].length;
   $(id).innerHTML=groups[group].length?groups[group].map(p=>{
    const percent=Math.round((p.progresso_total||0)*100);
    const moment=p.tarefa_fila?.scheduled||Date.parse(p.agendamento?.horario)/1000;
    const note=p.agendamento_em_edicao?'Em edição · agendamento suspenso':group==='agendamentos'&&!p.em_execucao&&moment?'Agendado: '+new Date(moment*1000).toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'}):p.status.mensagem?.slice(0,80)||'Fontes prontas';
    const canEdit=group==='agendamentos'&&!p.em_execucao;
    return `<div class="project-row ${group==='concluidos'?'completed-project-row':''}" data-project-row="${esc(p.id)}"><button class="project-link ${current?.id===p.id?'selected':''}" data-id="${esc(p.id)}">${group==='concluidos'?completedCard(p):`<strong>${esc(p.tarefa_fila?.publication?.titulo||p.titulo)}</strong>`}<small class="project-status-note" title="${esc(note)}">${esc(note)}</small>${p.em_execucao?`<span class="sidebar-progress-label">Processando <b>${percent}%</b></span><progress class="sidebar-progress" max="100" value="${percent}" aria-label="Progresso de ${esc(p.titulo)}: ${percent}%"></progress>`:''}</button><div class="project-row-actions">${canEdit?`<button type="button" class="schedule-edit" data-edit-schedule="${esc(p.id)}" title="Editar vídeo e agendamento" aria-label="Editar agendamento de ${esc(p.titulo)}">✎</button>`:''}<button class="project-delete" data-delete="${esc(p.id)}" data-title="${esc(p.titulo)}" aria-label="Excluir projeto ${esc(p.titulo)}" title="Excluir projeto">×</button></div></div>`;
   }).join(''):`<p class="drawer-empty">${group==='ativos'?'Nenhum projeto em edição ou processamento.':group==='concluidos'?'Os projetos finalizados aparecerão aqui.':'Seus vídeos agendados aparecerão aqui.'}</p>`;
  }
  document.querySelectorAll('[data-id]').forEach(b=>b.onclick=()=>action(()=>openProject(b.dataset.id)));
  document.querySelectorAll('[data-edit-schedule]').forEach(b=>b.onclick=()=>action(()=>window.editScheduledProject(b.dataset.editSchedule)));
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>{deletePending=b.dataset.delete;$('delete-name').textContent=b.dataset.title;$('delete-dialog').showModal()});
 };
 status=p=>{
  const busy=originalStatus(p);$('exports').classList.toggle('short-export',p.config.tipo_video==='shorts');if(!busy&&p.config.tipo_video==='shorts')$('edit-formato').disabled=true;updateGeminiProject('edit');$('download-music').hidden=!p.creditos_musica;$('download-music').href='/api/projects/'+p.id+'/download/creditos-musica.md';$('download-shotcraft').hidden=!p.creditos_shotcraft;$('download-shotcraft').href='/api/projects/'+p.id+'/download/creditos-shotcraft.md';$('download-collage').hidden=!p.creditos_colagem;$('download-collage').href='/api/projects/'+p.id+'/download/creditos-colagem.md';$('edit-project').disabled=busy;$('resume').disabled=busy;
  $('resume').hidden=!(['pausado','pausado_youtube'].includes(p.status.status)||(p.tarefa?.tipo==='render_youtube'&&['erro','erro_youtube'].includes(p.status.status)));$('resume').textContent=p.tarefa?.tipo==='render_youtube'?'Retomar criação e publicação':p.tarefa?.tipo==='youtube'?'Retomar envio ao YouTube':p.tarefa?.tipo?.startsWith('scene_preview:')?'Retomar prévia da cena':p.tarefa?.tipo==='roteiro'?'Salvar e retomar roteiro':p.tarefa?.tipo?.startsWith('cena:')?'Salvar e retomar cena':'Salvar e retomar vídeo';
  $('render').disabled=busy||!p.cenas.length;$('preview-empty').hidden=!!p.exportado;if(window.updateQueueControls)window.updateQueueControls(p,busy);return busy;
 };
 paintScenes=()=>{
  originalPaint();$('reports-panel').hidden=!(current.didatica||current.checagem);
  document.querySelectorAll('[data-scene]').forEach(el=>{const s=current.cenas[Number(el.dataset.scene)];const label=document.createElement('label');label.innerHTML='Animação desta cena<select data-key="animacao">'+animationOptions(s.animacao??'herdar',true)+'</select>';el.querySelector('.scene-body>div:last-child').append(label);
   const movement=document.createElement('label');movement.innerHTML='Movimento desta cena<select data-key="animar_elementos">'+opt([['herdar','Usar o do projeto'],['sim','Elementos animados + transições'],['nao','Quadro parado + transições']],s.animar_elementos==null?'herdar':s.animar_elementos?'sim':'nao')+'</select>';el.querySelector('.scene-body>div:last-child').append(movement);
   const figures=document.createElement('label');figures.innerHTML='Figuras desejadas na colagem (opcional)<input data-key="figuras_colagem" maxlength="1000" placeholder="avião comercial; antena parabólica; microscópio" value="'+esc(s.figuras_colagem||'')+'"><small>Separe por ponto e vírgula, na ordem dos elementos e dos trechos narrados. Vazio: escolha automática por assunto.</small>';el.querySelector('.scene-body>div:last-child').append(figures);const fm=document.createElement('label');fm.innerHTML='Movimento das figuras nesta cena<select data-key="movimento_figuras">'+opt([['herdar','Usar o do projeto'],['tematico','Conforme o objeto'],['suave','Adesivos suaves'],['nenhum','Figuras paradas']],s.movimento_figuras??'herdar')+'</select>';el.querySelector('.scene-body>div:last-child').append(fm);figures.insertAdjacentHTML('beforeend','<button type="button" class="secondary" data-collage-library>Escolher figuras do acervo</button>');
   figures.dataset.sceneVox='';fm.dataset.sceneVox='';
   const effect=document.createElement('label');effect.innerHTML='Transição desta cena<select data-key="transicao">'+opt([['herdar','Usar a do projeto'],...(studioCatalog.transicoes||[]).map(t=>[t.id,t.nome])],s.transicao??'herdar')+'</select>';el.querySelector('.scene-body>div:last-child').append(effect);
   const duration=document.createElement('label');duration.innerHTML='Duração da transição desta cena<select data-key="duracao_transicao">'+opt([['herdar','Usar a do projeto'],[.3,'0,3 s'],[.6,'0,6 s'],[1,'1 s'],[1.5,'1,5 s'],[2,'2 s']],s.duracao_transicao??'herdar')+'</select>';el.querySelector('.scene-body>div:last-child').append(duration);
   effect.querySelector('select').onchange=()=>{const control=duration.querySelector('select');if(effect.querySelector('select').value==='papel_amassado'&&(control.value==='herdar'||Number(control.value)<1.5))control.value='2'};
   const image=document.createElement('label');image.innerHTML='Imagem de referência desta cena<select data-key="imagem">'+opt([['auto','Automática conforme o assunto'],['nenhuma','Sem imagem de referência'],...(current.imagens||[]).map((name,i)=>[name,'Imagem '+(i+1)+' · '+name])],s.usar_imagem===false?'nenhuma':s.imagem??'auto')+'</select>';el.querySelector('.scene-body>div:last-child').append(image);addSceneBackground(el,s);addSceneImageSequence(el,s);addShotcraftSceneControl(el,s)});updateShotcraft('edit');
 };
 save=async()=>{document.querySelectorAll('[data-scene]').forEach(el=>{
  const scene=current.cenas[Number(el.dataset.scene)];
  scene.animacao=el.querySelector('[data-key="animacao"]').value;if(['historia','historia_ilustrada'].includes(scene.animacao))throw Error('Escolha outra animação na cena '+(Number(el.dataset.scene)+1)+'. Este modelo foi removido do catálogo.');scene.shotcraft_receita=el.querySelector('[data-key="shotcraft_receita"]').value;scene.shotcraft_figuras=el.querySelector('[data-key="shotcraft_figuras"]').value.trim();scene.distribuicao_figuras=el.querySelector('[data-key="distribuicao_figuras"]').value;scene.three_options=JSON.parse(el.querySelector('[data-three-options]').value||'null');
  scene.figuras_colagem=el.querySelector('[data-key="figuras_colagem"]').value.trim();scene.movimento_figuras=el.querySelector('[data-key="movimento_figuras"]').value;
  scene.transicao=el.querySelector('[data-key="transicao"]').value;
  const movement=el.querySelector('[data-key="animar_elementos"]').value;scene.animar_elementos=movement==='herdar'?null:movement==='sim';
  const duration=el.querySelector('[data-key="duracao_transicao"]').value;scene.duracao_transicao=duration==='herdar'?null:Number(duration);
  const image=el.querySelector('[data-key="imagem"]').value;scene.usar_imagem=image!=='nenhuma';scene.imagem=['auto','nenhuma'].includes(image)?null:image;readSceneImageSequence(el,scene);readSceneBackground(el,scene);
 });await originalSave();current.frases_midias=(await api('/api/projects/'+current.id)).frases_midias;paintReelsCues('edit')};
 refresh=async()=>{
  if(!current)return;const p=await api('/api/projects/'+current.id),previous=current.status.status;current.status=p.status;current.tarefa=p.tarefa;current.processando=p.processando;current.exportado=p.exportado;current.agendamento=p.agendamento;current.agendamento_em_edicao=p.agendamento_em_edicao;current.assunto=p.assunto;current.pesquisa_imagens=p.pesquisa_imagens;current.titulo=p.titulo;$('project-title').textContent=p.titulo;
  if(JSON.stringify(current.imagens)!==JSON.stringify(p.imagens)){current.imagens=p.imagens;current.imagens_meta=p.imagens_meta;window.refreshReviewMedia?.()}
  if(p.checagem?.desatualizada){current.checagem=p.checagem;paintResearch()}
  if(p.didatica?.desatualizado){current.didatica=p.didatica;paintTeaching()}
  const busy=status(p);if(!busy&&(['roteirizando','fila','renderizando','preparando_publicacao','enviando_youtube'].includes(previous)||current.cenas.length!==p.cenas.length)){current.cenas=p.cenas;current.frases_midias=p.frases_midias;current.videos=p.videos;current.videos_meta=p.videos_meta;current.imagens=p.imagens;current.imagens_meta=p.imagens_meta;current.fontes=p.fontes;current.didatica=p.didatica;current.checagem=p.checagem;paintScenes();paintReelsCues('edit');$('source-summary').textContent=p.fontes.map(s=>`[${s.id}] ${s.origem} · ${s.caracteres} caracteres`).join('\n')}
  if(previous!==p.status.status)list().catch(()=>{});
 };
 $('edit-project').onclick=()=>{$('project-options').open=true;$('project-options').scrollIntoView({behavior:'smooth',block:'start'});$('edit-minutos').focus()};
 $('resume').onclick=()=>action(async()=>{await save();await api('/api/projects/'+current.id+'/resume',{method:'POST'});await refresh()});
 $('pause').onclick=()=>action(async()=>{await api('/api/projects/'+current.id+'/pause',{method:'POST'});toast('Aguarde a pausa concluir. Depois use Voltar à edição ou Retomar.')} );
 $('delete-cancel').onclick=()=>$('delete-dialog').close();
 $('delete-confirm').onclick=()=>action(async()=>{await api('/api/projects/'+deletePending,{method:'DELETE'});$('delete-dialog').close();if(current?.id===deletePending)reset();await list();toast('Projeto movido para a lixeira. Você pode restaurá-lo.');deletePending=null});
 $('trash-open').onclick=()=>action(showTrash);$('trash-close').onclick=()=>$('trash-dialog').close();
 $('trash-empty').onclick=()=>{
  $('trash-confirm-text').textContent=`Excluir definitivamente ${trashItems.length} ${trashItems.length===1?'projeto':'projetos'}? Os arquivos, vídeos e caches desses projetos serão apagados e não poderão ser restaurados.`;
  $('trash-confirm-box').hidden=false;$('trash-empty-cancel').focus();
 };
 $('trash-empty-cancel').onclick=()=>{$('trash-confirm-box').hidden=true;$('trash-empty').focus()};
 $('trash-empty-confirm').onclick=()=>action(async()=>{
  const button=$('trash-empty-confirm');button.disabled=true;$('trash-empty').disabled=true;
  try{
   const result=await api('/api/trash',{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({projetos:trashItems.map(p=>p.id)})});
   await showTrash();await list();
   $('trash-result').textContent=`${result.removidos} ${result.removidos===1?'projeto removido':'projetos removidos'} definitivamente · ${formatBytes(result.bytes_removidos)} em arquivos apagados.`+(result.erros.length?' Alguns arquivos não puderam ser removidos. Feche arquivos abertos e tente novamente.':'');
  }catch(e){await showTrash();throw e}
  finally{button.disabled=false;$('trash-empty').disabled=!trashItems.length}
 });
 $('animation-close').onclick=()=>$('animation-dialog').close();$('animation-dialog').addEventListener('close',()=>{previewRevision++;$('animation-video').pause();if($('animation-three'))$('animation-three').src='about:blank'});
 $('animation-hand-speed').innerHTML=opt(handSpeeds,.75);
 $('animation-voice').innerHTML=opt(studioCatalog.vozes.map(v=>[v.id,v.nome,!v.instalada]),'pf_dora');
 $('animation-delivery').innerHTML=opt(studioCatalog.locucoes.map(v=>[v.id,v.nome]),'natural');
 for(const name of ['hand-speed','voice','delivery','pace'])$('animation-'+name).onchange=clearVoicePreview;
 $('animation-camera').onchange=clearVoicePreview;$('animation-figure-motion').onchange=clearVoicePreview;
 $('animation-test').onclick=()=>action(testVoicePreview);
 $('animation-library').onclick=()=>previewStyle==='shotcraft'?openShotcraftFigures(null,previewPrefix):window.openCollageLibrary?.();
 $('animation-apply').onclick=()=>{for(const [field,dialogKey] of [['velocidade_mao','hand-speed'],['voz','voice'],['estilo_locucao','delivery'],['velocidade','pace']])$(previewPrefix+'-'+field).value=$('animation-'+dialogKey).value;$(previewPrefix+'-animacao').value=previewStyle;$(previewPrefix+'-movimento_figuras').value=$('animation-figure-motion').value;$(previewPrefix+'-camera_dinamica').checked=$('animation-camera').checked;$(previewPrefix+'-animacao').dispatchEvent(new Event('change'));$(previewPrefix+'-voz').dispatchEvent(new Event('change'));$('animation-dialog').close();toast('Voz e animação selecionadas. Renderize para aplicar.')};
 if($('projects-toggle'))$('projects-toggle').onclick=()=>document.querySelector('aside').classList.toggle('projects-open');
 reset=()=>{originalReset();creationStep(1);sourceTab('arquivos');document.querySelector('aside').classList.remove('projects-open')};
 $('new-project').onclick=$('back').onclick=reset;
 document.querySelectorAll('[data-create-step]').forEach(b=>b.onclick=()=>creationStep(b.dataset.createStep));
 document.querySelectorAll('[data-source-tab]').forEach(b=>b.onclick=()=>sourceTab(b.dataset.sourceTab));
 $('source-next').onclick=()=>{const count=(window.filePool?.length||0)||$('files').files.length;if(!count&&!$('source-text').value.trim()&&!$('urls').value.trim()){toast('Adicione um arquivo, imagem, texto ou link para continuar.',true);return}creationStep(2)};
 $('config-back').onclick=()=>creationStep(1);
 const pid=current?.id||(navigationRevision===bootNavigation?(initial||new URLSearchParams(location.search).get('projeto')):null);
 reset();const restoreRevision=navigationRevision;await list();if(pid&&navigationRevision===restoreRevision)await openProject(pid);
 setupThemeAndSidebar();
 window.studioReady=true;window.dispatchEvent(new Event('studio-ready'));
}));

function setupThemeAndSidebar(){
 const drawers=document.querySelector('#app-aside .project-drawers');
 const fitDrawers=()=>{
  if(!drawers)return;
  const sections=[...drawers.querySelectorAll('.project-drawer')];
  const open=sections.filter(d=>d.open).length;
  const headers=sections.reduce((height,d)=>height+d.querySelector('summary').getBoundingClientRect().height+(parseFloat(getComputedStyle(d).marginBottom)||0),0);
  drawers.style.setProperty('--drawer-list-height',Math.max(24,Math.floor((drawers.clientHeight-headers)/Math.max(1,open)))+'px');
 };
 if(drawers){const resize=new ResizeObserver(fitDrawers);resize.observe(drawers);drawers.querySelectorAll('summary').forEach(d=>resize.observe(d));requestAnimationFrame(fitDrawers)}
 for(const id of ['drawer-active','drawer-completed','drawer-scheduled']){
  const drawer=$(id);if(!drawer)continue;
  try{const saved=localStorage.getItem('clareia-'+id);if(saved!==null)drawer.open=saved==='true'}catch(e){}
  drawer.addEventListener('toggle',()=>{try{localStorage.setItem('clareia-'+id,String(drawer.open))}catch(e){}requestAnimationFrame(fitDrawers)});
 }
 const toggleBtn=$('sidebar-toggle'),collapseBtn=$('aside-collapse');
 const applySidebarState=collapsed=>{
  document.body.classList.toggle('sidebar-collapsed',collapsed);
  if(toggleBtn)toggleBtn.setAttribute('aria-expanded',String(!collapsed));
  try{localStorage.setItem('clareia-sidebar-collapsed',String(collapsed))}catch(e){}
 };
 const isCollapsed=localStorage.getItem('clareia-sidebar-collapsed')==='true';
 applySidebarState(isCollapsed);
 if(toggleBtn)toggleBtn.onclick=()=>applySidebarState(!document.body.classList.contains('sidebar-collapsed'));
 if(collapseBtn)collapseBtn.onclick=()=>applySidebarState(true);

 const drawerToggle=$('projects-drawer-toggle');
 const projectsList=$('projects');
 const drawerArrow=$('projects-drawer-arrow');
 if(drawerToggle&&projectsList){
  const applyDrawer=collapsed=>{
   projectsList.classList.toggle('drawer-collapsed',collapsed);
   drawerToggle.classList.toggle('is-collapsed',collapsed);
   drawerToggle.setAttribute('aria-expanded',String(!collapsed));
   if(drawerArrow)drawerArrow.textContent=collapsed?'▸':'▾';
   try{localStorage.setItem('clareia-projects-collapsed',String(collapsed))}catch(e){}
  };
  const savedDrawer=localStorage.getItem('clareia-projects-collapsed')==='true';
  applyDrawer(savedDrawer);
  drawerToggle.onclick=()=>{
   const now=!projectsList.classList.contains('drawer-collapsed');
   applyDrawer(now);
  };
  drawerToggle.onkeydown=e=>{
   if(e.key==='Enter'||e.key===' '){
    e.preventDefault();
    drawerToggle.click();
   }
  };
 }

 api('/api/health').then(h=>{
  if(h&&h.modelo){
   defaultLocalModel=h.modelo;
   updateGeminiProject(current?'edit':'create');
  }
 }).catch(()=>{});

 const themeDialog=$('theme-dialog');
 if($('theme-open')&&themeDialog){
  $('theme-open').onclick=()=>themeDialog.showModal();
  if($('theme-close'))$('theme-close').onclick=()=>themeDialog.close();
 }

 const applyTheme=theme=>{
  document.documentElement.dataset.theme=theme;
  try{localStorage.setItem('clareia-theme',theme)}catch(e){}
  document.querySelectorAll('.theme-opt').forEach(b=>b.classList.toggle('active',b.dataset.theme===theme));
 };
 document.querySelectorAll('.theme-opt').forEach(b=>{b.onclick=()=>applyTheme(b.dataset.theme)});
 const savedTheme=localStorage.getItem('clareia-theme')||'cyber';
 applyTheme(savedTheme);

 const applyBg=bg=>{
  document.body.dataset.bg=bg;
  try{localStorage.setItem('clareia-bg',bg)}catch(e){}
  if(bg!=='custom'){document.body.style.backgroundImage='';try{localStorage.removeItem('clareia-custom-bg')}catch(e){}}
  document.querySelectorAll('.bg-opt').forEach(b=>b.classList.toggle('active',b.dataset.bg===bg));
 };
 document.querySelectorAll('.bg-opt').forEach(b=>{b.onclick=()=>applyBg(b.dataset.bg)});
 if($('custom-bg-apply')){
  $('custom-bg-apply').onclick=()=>{
   const url=($('custom-bg-input').value||'').trim();
   if(!url)return;
   document.body.dataset.bg='custom';
   document.body.style.backgroundImage=`url("${url}")`;
   document.body.style.backgroundSize='cover';
   document.body.style.backgroundPosition='center';
   document.body.style.backgroundAttachment='fixed';
   try{localStorage.setItem('clareia-bg','custom');localStorage.setItem('clareia-custom-bg',url)}catch(e){}
   document.querySelectorAll('.bg-opt').forEach(b=>b.classList.remove('active'));
   toast('Papel de parede personalizado aplicado!');
  };
 }
 const savedCustomBg=localStorage.getItem('clareia-custom-bg');
 const savedBg=localStorage.getItem('clareia-bg')||'aurora';
 if(savedBg==='custom'&&savedCustomBg){
  document.body.dataset.bg='custom';
  document.body.style.backgroundImage=`url("${savedCustomBg}")`;
  document.body.style.backgroundSize='cover';
  document.body.style.backgroundPosition='center';
  document.body.style.backgroundAttachment='fixed';
  if($('custom-bg-input'))$('custom-bg-input').value=savedCustomBg;
 }else{
  applyBg(savedBg);
 }

 const applyFont=font=>{
  document.documentElement.style.setProperty('--font-sans',`"${font}", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`);
  try{localStorage.setItem('clareia-font',font)}catch(e){}
  document.querySelectorAll('.font-opt').forEach(b=>b.classList.toggle('active',b.dataset.font===font));
 };
 document.querySelectorAll('.font-opt').forEach(b=>{b.onclick=()=>applyFont(b.dataset.font)});
 const savedFont=localStorage.getItem('clareia-font')||'Outfit';
 applyFont(savedFont);

 const blurSlider=$('glass-blur-range');
 if(blurSlider){
  const applyBlur=val=>{
   document.documentElement.style.setProperty('--glass-blur',val+'px');
   try{localStorage.setItem('clareia-glass-blur',val)}catch(e){}
   blurSlider.value=val;
  };
  blurSlider.oninput=()=>applyBlur(blurSlider.value);
  const savedBlur=localStorage.getItem('clareia-glass-blur')||'20';
  applyBlur(savedBlur);
 }
}
