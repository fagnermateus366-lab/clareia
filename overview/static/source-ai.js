// Build study material first, then let the selected writer turn it into a script.
(() => {
 let revision=0,sourceRevision=0;
 window.sourceAIBusy=false;
 window.sourceAIConfig=(prefix='create')=>{
  if(prefix==='edit'){
   const c=current?.config||{};
   return {fonte_ia_automatica:c.fonte_ia_automatica??false,fonte_ia_provedor:c.fonte_ia_provedor||'roteiro',fonte_ia_modelo:c.fonte_ia_modelo||''};
  }
  return {fonte_ia_automatica:$('source-ai-auto').checked,fonte_ia_provedor:$('source-ai-provider').value,fonte_ia_modelo:$('source-ai-model').value};
 };
 function note(){
  const provider=$('source-ai-provider').value;
  $('source-ai-model-field').hidden=provider==='roteiro';
  $('source-ai-models').hidden=provider==='roteiro';
  $('source-ai-provider-note').textContent=provider==='roteiro'?'Usa a mesma IA escolhida para o roteiro deste vídeo.':provider==='local'?'Usa um modelo instalado no Ollama deste computador.':provider==='groq'?'Envia o assunto ao GroqCloud. Modelos do plano Free têm cotas; use chave de uma organização Free. Uma organização paga pode gerar cobrança.':'Envia o assunto à API escolhida, usando sua chave cadastrada. Há consumo da cota; no Gemini, o preço depende da sua conta.';
 }
 async function models(){
  const provider=$('source-ai-provider').value,version=++revision;
  note();if(provider==='roteiro')return;
  const select=$('source-ai-model'),previous=select.value;
  $('source-ai-models').disabled=true;select.disabled=true;
  try{
   const data=await api('/api/roteiro/modelos/'+provider);
   if(version!==revision)return;
   select.innerHTML='<option value="">Escolha um modelo</option>'+data.modelos.map(m=>`<option value="${esc(m.id)}">${esc(m.nome)}</option>`).join('');
   if(data.modelos.some(m=>m.id===previous))select.value=previous;
   else if(provider==='local')select.value=data.modelos.some(m=>m.id===$('create-roteiro_modelo').value)?$('create-roteiro_modelo').value:defaultLocalModel;
  }finally{if(version===revision){$('source-ai-models').disabled=false;select.disabled=false}}
 }
 function start(){
  const oldConfig=config;
  config=prefix=>({...oldConfig(prefix),...window.sourceAIConfig(prefix)});
  const oldClear=clearAllSources;
  clearAllSources=()=>{sourceRevision++;oldClear();$('source-ai-status').textContent=''};
  $('source-ai-provider').onchange=()=>{revision++;$('source-ai-model').innerHTML='<option value="">Escolha um modelo</option>';action(models)};
  $('source-ai-models').onclick=()=>action(models);
  const sourceHelp=document.querySelector('.source-topic-help'),originalHelp=sourceHelp.textContent;
  $('source-ai-auto').onchange=()=>paintMotivation('create');
  $('source-ai-generate').onclick=()=>action(async()=>{
   const topic=$('topic').value.trim();if(!topic)throw Error('Descreva o assunto ou o que você quer motivar antes de criar a base.');
   const settings={...motivationConfig('create'),roteiro_provedor:$('create-roteiro_provedor').value,roteiro_modelo:$('create-roteiro_modelo').value,...window.sourceAIConfig()};
   const requestedRevision=sourceRevision;
   window.sourceAIBusy=true;
   $('source-ai-generate').disabled=true;$('create-button').disabled=true;
   $('source-ai-status').textContent=settings.tipo_roteiro==='motivacional'?'Planejando público, identificação, perspectiva, ação e briefing. Pode levar alguns minutos.':'Criando material detalhado: contexto, conceitos, passo a passo, exemplos e limites. Pode levar alguns minutos.';
   try{
    const result=await api('/api/sources/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({assunto:topic,config:settings})});
    if(requestedRevision!==sourceRevision){toast('A fonte foi criada e salva. Informe o mesmo assunto para recuperar o material.');return}
    if($('topic').value.trim()!==topic||$('welcome').hidden){$('source-ai-status').textContent='Fonte criada para o assunto anterior. Informe novamente esse assunto e use Criar fonte para recuperar o material salvo.';return}
    const previous=$('source-text').value.trim();
    if(!previous.includes(result.texto))$('source-text').value=previous?previous+'\n\n'+result.texto:result.texto;
    $('source-text').dispatchEvent(new Event('input',{bubbles:true}));
    $('source-ai-status').textContent=`Fonte pronta · ${result.secoes} seções · ${result.provedor} / ${result.modelo}. O texto está disponível acima para você revisar e editar.`;
    $('source-text').focus();$('source-text').setSelectionRange(0,0);$('source-text').scrollTop=0;toast('Fonte criada com IA e adicionada ao texto.');
   }catch(e){$('source-ai-status').textContent='Não foi possível concluir a fonte. '+e.message;throw e}
   finally{window.sourceAIBusy=false;$('source-ai-generate').disabled=false;$('create-button').disabled=false}
  });
  note();
 }
 if(window.studioReady)start();else window.addEventListener('studio-ready',start,{once:true});
})();
