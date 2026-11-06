// The sidebar changes the current form/project, including favorite-based creation.
(() => {
 const button=$('local-model-badge');
 let models=[],request=0;
 const busy=()=>!!current&&(current.processando||['fila','agendado','roteirizando','renderizando','importando','preparando_publicacao','enviando_youtube'].includes(current.status?.status));
 const choice=()=>current?{roteiro_provedor:$('edit-roteiro_provedor').value,roteiro_modelo:$('edit-roteiro_modelo').value}:quickModelChoice?{roteiro_provedor:'local',roteiro_modelo:quickModelChoice}:window.favoriteModelForCreate?.()||{roteiro_provedor:$('create-roteiro_provedor').value,roteiro_modelo:$('create-roteiro_modelo').value};
 window.paintQuickModel=()=>{
  const s=choice(),local=s.roteiro_provedor==='local',model=s.roteiro_modelo||defaultLocalModel;
  $('local-model-name').textContent=local?localModelLabel(model):(s.roteiro_modelo||s.roteiro_provedor)+' · '+providerName(s.roteiro_provedor);
  if(local&&$('settings-local-model'))$('settings-local-model').textContent=localModelLabel(model);
  button.disabled=busy();button.title=busy()?'Aguarde o processamento para trocar de modelo':current?'Trocar modelo deste projeto':'Trocar modelo do novo vídeo';
 };
 const menu=document.createElement('div');menu.id='quick-model-menu';menu.className='model-menu quick-model-menu';menu.hidden=true;
 menu.innerHTML='<strong id="quick-model-heading"></strong><p class="small">Modelos locais · Ollama</p><input class="model-search" type="search" placeholder="Buscar modelo" aria-label="Buscar modelo local"><div class="model-options" role="listbox" aria-label="Modelos locais instalados"></div>';
 document.body.append(menu);
 const search=menu.querySelector('input'),options=menu.querySelector('.model-options');
 function position(){
  const rect=button.getBoundingClientRect(),width=Math.min(420,innerWidth-24);
  menu.style.width=width+'px';menu.style.left=Math.min(Math.max(12,rect.left),innerWidth-width-12)+'px';
  const below=innerHeight-rect.bottom-24,above=rect.top-24;
  if(below>=Math.min(280,above)){
   menu.style.top=Math.max(12,rect.bottom+6)+'px';menu.style.bottom='auto';menu.style.maxHeight=Math.max(120,Math.min(490,below))+'px';
  }else{
   menu.style.top='auto';menu.style.bottom=Math.max(12,innerHeight-rect.top+6)+'px';menu.style.maxHeight=Math.max(120,Math.min(490,above))+'px';
  }
 }
 window.positionQuickModel=()=>{if(menu.hidden)return false;const r=button.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return false;position();return true;};
 function draw(){
  const selected=choice(),q=search.value.toLocaleLowerCase('pt-BR');
  options.innerHTML=models.filter(m=>(m.nome+' '+m.id+' '+m.especialidade).toLocaleLowerCase('pt-BR').includes(q)).map(m=>`<button type="button" role="option" aria-selected="${selected.roteiro_provedor==='local'&&(selected.roteiro_modelo||defaultLocalModel)===m.id}" data-quick-model="${esc(m.id)}"><span class="model-check">${selected.roteiro_provedor==='local'&&(selected.roteiro_modelo||defaultLocalModel)===m.id?'✓':''}</span><span><b>${esc(m.nome)}</b><small>${esc(m.especialidade)}</small></span></button>`).join('')||'<p>Nenhum modelo encontrado.</p>';
  options.querySelectorAll('[data-quick-model]').forEach(b=>b.onclick=()=>action(()=>select(b.dataset.quickModel)));
 }
 async function select(model){
  if(busy())throw Error('Aguarde o processamento para trocar de modelo.');
  const prefix=current?'edit':'create',provider=$(prefix+'-roteiro_provedor'),field=$(prefix+'-roteiro_modelo'),previous={provider:provider.value,model:field.value,config:current?.config};
  const projectId=current?.id;
  closeModelPickers();button.disabled=true;
  try{
   provider.value='local';writerCatalog[prefix]=models;
   field.replaceChildren(...models.map(m=>new Option(m.nome,m.id)));field.value=model;
   paintModel(prefix);writerNote(prefix);
   if(projectId){await save();if(current?.id===projectId)toast('Modelo salvo para este projeto: '+localModelLabel(model));}
   else {quickModelChoice=model;toast('Modelo escolhido para o novo vídeo: '+localModelLabel(model));}
  }catch(e){
   if(current?.id===projectId){provider.value=previous.provider;if(!Array.from(field.options).some(o=>o.value===previous.model))field.add(new Option(previous.model,previous.model));field.value=previous.model;if(current)current.config=previous.config;paintModel(prefix);writerNote(prefix);}
   throw e;
  }finally{window.paintQuickModel();button.focus();}
 }
 async function open(keyboard=false){
  if(!menu.hidden){closeModelPickers();return;}
  if(busy())return;
  const revision=++request,projectId=current?.id;
  models=(await api('/api/roteiro/modelos/local')).modelos;
  if(revision!==request||current?.id!==projectId||busy())return;
  closeModelPickers();search.value='';draw();$('quick-model-heading').textContent=current?'Modelo deste projeto':'Modelo do novo vídeo';
  position();
  menu.hidden=false;button.setAttribute('aria-expanded','true');
  if(keyboard)options.querySelector('[role=option]')?.focus();else search.focus();
 }
 button.onclick=()=>action(()=>open());
 button.onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();action(()=>open(true));}};
 search.oninput=draw;
 menu.onkeydown=e=>{
  if(e.key==='Escape'){closeModelPickers();button.focus();}
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();const items=[...options.querySelectorAll('[role=option]')],index=items.indexOf(document.activeElement),next=e.key==='ArrowDown'?index+1:index-1;items[(next+items.length)%items.length]?.focus();}
 };
 window.paintQuickModel();
})();
