// Independent, opt-in text providers. Loading a catalogue never generates text.
const stageAIProviders=[['local','Ollama · modelos instalados'],['gemini','Gemini · sua chave'],['openrouter','OpenRouter · modelos gratuitos'],['groq','GroqCloud · plano gratuito']];
const stageAIControllers=new WeakMap();
function stageAIFields(key,value={},label='Escolher uma IA para esta etapa',description=''){
 const c=value||{};
 return `<fieldset class="stage-ai" id="${key}-box"><label class="check-row stage-ai-toggle"><input type="checkbox" id="${key}-active" ${c.ativa?'checked':''}>${esc(label)}</label><p class="small">${esc(description)} Desmarcado: usa a mesma IA do roteiro.</p><div id="${key}-fields" ${c.ativa?'':'hidden'}><div class="stage-ai-grid"><label>Provedor<select id="${key}-provider">${stageAIProviders.map(([id,name])=>`<option value="${id}" ${id===(c.provedor||'local')?'selected':''}>${esc(name)}</option>`).join('')}</select></label><label>Modelo<select id="${key}-model"><option value="${esc(c.modelo||'')}">${esc(c.modelo||'Escolha um modelo')}</option></select></label></div><button class="secondary" type="button" id="${key}-refresh">Atualizar modelos</button><p class="small" id="${key}-note" role="status"></p></div></fieldset>`;
}
function stageAIRead(key,validate=true){
 const active=$(key+'-active'),provider=$(key+'-provider'),model=$(key+'-model');
 const value={ativa:!!active?.checked,provedor:provider?.value||'local',modelo:model?.value||''};
 if(validate&&value.ativa){
  if($(key+'-box').dataset.loading==='true')throw Error('Aguarde a lista de modelos desta etapa carregar.');
  if(!value.modelo)throw Error('Escolha o modelo da IA específica desta etapa.');
 }
 return value;
}
function stageAIReady(key){try{stageAIRead(key);return true}catch{return false}}
function stageAIKey(value={}){return value?.ativa?JSON.stringify([true,value.provedor,value.modelo||'']):'mesma-ia-do-roteiro'}
function stageAIConfig(prefix){return {planejamento_ia:stageAIRead(prefix+'-plan'),youtube_ia:JSON.parse($(prefix+'-youtube-ia')?.value||'{}')}}
function bindStageAI(key,onChange=()=>{}){
 const box=$(key+'-box');if(!box)return;
 const existing=stageAIControllers.get(box);if(existing)return existing;
 let revision=0;
 function paint(){
  const provider=$(key+'-provider').value;
  $(key+'-fields').hidden=!$(key+'-active').checked;
  $(key+'-note').textContent=provider==='local'?'Processamento desta etapa no computador.':provider==='groq'?'Use chave de uma organização no plano Free da Groq. Há cotas; uma organização paga pode gerar cobrança.':'Usa a chave cadastrada em Configurações. O texto necessário à etapa será enviado ao provedor; há cotas e os preços dependem da conta.';
 }
 async function load(){
  const version=++revision,provider=$(key+'-provider').value,model=$(key+'-model'),previous=model.value;
  box.dataset.loading='true';model.disabled=true;$(key+'-refresh').disabled=true;
  try{
   const data=await api('/api/roteiro/modelos/'+provider);
   if(version!==revision||!box.isConnected)return;
   model.innerHTML='<option value="">Escolha um modelo</option>'+data.modelos.map(m=>`<option value="${esc(m.id)}">${esc(m.nome)}${m.plano_gratuito?' · plano Free':''}</option>`).join('');
   if(data.modelos.some(m=>m.id===previous))model.value=previous;
   else if(provider==='local')model.value=data.modelos.some(m=>m.id===defaultLocalModel)?defaultLocalModel:data.modelos[0]?.id||'';
   if(!data.modelos.length)$(key+'-note').textContent='Nenhum modelo disponível. Confira a chave e atualize a lista.';
  }catch(error){
   if(version===revision&&box.isConnected){$(key+'-note').textContent=error.message;model.replaceChildren(new Option('Confira a chave e atualize os modelos',''))}
  }finally{
   if(version===revision&&box.isConnected){box.dataset.loading='false';model.disabled=false;$(key+'-refresh').disabled=false;onChange()}
  }
 }
 $(key+'-active').onchange=()=>{paint();onChange();if($(key+'-active').checked)load()};
 $(key+'-provider').onchange=()=>{$(key+'-model').replaceChildren(new Option('Escolha um modelo',''));paint();onChange();load()};
 $(key+'-model').onchange=()=>onChange();$(key+'-refresh').onclick=load;
 const controller={set:async(value={})=>{revision++;$(key+'-active').checked=!!value?.ativa;$(key+'-provider').value=value?.provedor||'local';$(key+'-model').replaceChildren(new Option(value?.modelo||'Escolha um modelo',value?.modelo||''));paint();onChange();if(value?.ativa)await load()},setDisabled:disabled=>{box.disabled=disabled}};
 stageAIControllers.set(box,controller);paint();if($(key+'-active').checked)load();return controller;
}
function stageAISet(key,value){return bindStageAI(key).set(value)}
function syncYoutubeAIChoice(project,choice){
 if(current?.id!==project)return;
 current.config.youtube_ia=choice||{};
 if($('edit-youtube-ia'))$('edit-youtube-ia').value=JSON.stringify(choice||{});
}
