function motivationFields(prefix,s={}){
 const presets=typeof studioCatalog!=='undefined'?studioCatalog?.vozes_motivacionais||[]:[];
 return `<fieldset id="${prefix}-motivation-kind" class="video-kind motivation-kind"><legend>Estilo do roteiro</legend><label>Que mensagem vamos criar?<select id="${prefix}-tipo_roteiro"><option value="didatico" ${s.tipo_roteiro!=='motivacional'?'selected':''}>Didático · explicar e ensinar</option><option value="motivacional" ${s.tipo_roteiro==='motivacional'?'selected':''}>Motivacional · inspirar e incentivar</option></select></label><label id="${prefix}-motivation-audience" ${s.tipo_roteiro==='motivacional'?'':'hidden'}>Para quem é esta mensagem? <span class="optional">opcional</span><input id="${prefix}-publico_motivacional" maxlength="250" value="${esc(s.publico_motivacional||'')}" placeholder="Ex.: pessoas desanimadas que querem retomar os estudos"></label><p id="${prefix}-motivation-note" class="small" ${s.tipo_roteiro==='motivacional'?'':'hidden'}>Uma mensagem com identificação, mudança de perspectiva, uma ação possível e fechamento. Funciona em vídeo comum ou Reels / Shorts.</p><div id="${prefix}-motivation-tones" class="motivation-tones" ${s.tipo_roteiro==='motivacional'?'':'hidden'}><div id="${prefix}-motivational-tone-slot"></div><p class="small">O tom orienta a escrita e seleciona a locução correspondente. Você pode ajustar o Modo de locução separadamente depois. Texto enviado como narração pronta conserva suas palavras.</p><details class="motivation-voices"><summary>Experimentar vozes para motivação</summary><label>Combinação de voz e estilo<select id="${prefix}-motivational-voice"><option value="">Escolha uma combinação</option>${presets.map(p=>`<option value="${esc(p.id)}">${esc(p.nome)}</option>`).join('')}</select></label><div class="toolbar"><button type="button" class="secondary" data-motivation-apply="${prefix}">Aplicar voz e estilo</button><button type="button" class="secondary" data-motivation-listen="${prefix}">▷ Ouvir voz selecionada</button></div><p id="${prefix}-motivation-voice-note" class="small" role="status">Combinações das vozes disponíveis com os novos estilos. Para manter sua voz clonada, escolha apenas o tom, sem aplicar uma combinação.</p></details></div></fieldset>`;
}
function motivationConfig(prefix){
 const result={tipo_roteiro:$(prefix+'-tipo_roteiro')?.value||'didatico',publico_motivacional:$(prefix+'-publico_motivacional')?.value.trim()||''};
 if(result.tipo_roteiro==='motivacional'&&$(prefix+'-estilo_locucao')){
  result.tom=$(prefix+'-tom').value;result.estilo_locucao=$(prefix+'-estilo_locucao').value;
 }
 if(motivationalTone($(prefix+'-tom')?.value)){
  result.tom=$(prefix+'-tom').value;result.estilo_locucao=$(prefix+'-estilo_locucao').value;
 }
 if($(prefix+'-motivation-kind')?.dataset.voiceOverride)result.voz_motivacional=result.voz=$(prefix+'-voz').value;
 return result;
}
function motivationalTone(id){return id==='motivacional'||id?.startsWith('motivacional_')}
function paintMotivation(prefix,changed=false){
 const mode=$(prefix+'-tipo_roteiro');if(!mode)return;
 const motivational=mode.value==='motivacional';
 $(prefix+'-motivation-audience').hidden=$(prefix+'-motivation-note').hidden=!motivational;
 const tone=$(prefix+'-tom'),slot=$(prefix+'-motivational-tone-slot'),home=$(prefix+'-tone-home');
 if(tone&&slot&&home)(motivational?slot:home).append(tone.closest('label'));
 if($(prefix+'-motivation-tones'))$(prefix+'-motivation-tones').hidden=!motivational;
 const planning=$(prefix+'-plan-box')?.querySelector('p');
 if(planning)planning.textContent=(motivational?'Planeja público, identificação, mudança de perspectiva, ação e fechamento. ':'Organiza o objetivo, os conceitos, o exemplo e a conclusão antes da escrita do roteiro. ')+'Desmarcado: usa a mesma IA do roteiro.';
 if(changed&&motivational&&$(prefix+'-estilo_locucao')){
  if(!motivationalTone(tone?.value)&&tone)tone.value='motivacional';
  if(!motivationalTone($(prefix+'-estilo_locucao').value))$(prefix+'-estilo_locucao').value=motivationalTone(tone?.value)?tone.value:'motivacional';
  $(prefix+'-estilo_locucao').dispatchEvent(new Event('change'));
 }
 if($(prefix+'-tone-note'))$(prefix+'-tone-note').textContent=studioCatalog?.tons?.find(t=>t.id===tone?.value)?.descricao||'';
 if(prefix!=='create')return;
 const question=motivational?'Em que você quer motivar as pessoas?':'O que você quer explicar?';
 $('topic-question').textContent=question;$('topic').setAttribute('aria-label',question);
 const mic=$('topic').closest('label')?.querySelector('.dictation-mic');
 if(mic){mic.setAttribute('aria-label','Falar para preencher: '+question);mic.title='Falar para preencher: '+question}
 $('topic').placeholder=motivational?'Ex.: incentivar quem perdeu a vontade de estudar a retomar com um pequeno passo por dia.':'Ex.: explique a história do Brasil, destacando como o país se tornou independente.';
 $('source-ai-title').textContent=motivational?'Base e prompt motivacional com IA':'Fonte de informação com IA';
 $('source-ai-generate').textContent=motivational?'✦ Criar base e prompt com IA':'✦ Criar fonte com IA';
 $('source-ai-auto-label').textContent=motivational?'Criar base motivacional com IA automaticamente quando não houver texto de referência':'Criar fonte com IA automaticamente quando não houver texto de referência';
 $('source-ai-process-note').textContent=motivational?'A IA prepara uma base criativa com público, dificuldade, perspectiva e ação possível; depois escreve a mensagem. Você pode editar essa base ou colar uma referência ou um prompt próprio.':'Marcado: primeiro cria o material de estudo e depois o roteiro, inclusive no fluxo agendado. Texto ou documentos já fornecidos são aproveitados. O material criado por IA é editável; revise os fatos antes de produzir.';
 const ready=$('create-roteiro_pronto')?.checked&&document.querySelector('input[name="create-tipo_video"]:checked')?.value==='shorts';
 document.querySelector('.source-topic-help').textContent=ready?'Cole na aba Texto a narração que será usada exatamente como você escreveu. Adicione suas fotos na aba Arquivos.':motivational?'Descreva a mensagem e o público que você quer incentivar. Você pode colar uma referência ou um prompt na aba Texto, ou pedir uma base com IA. O roteiro terá estrutura motivacional.':$('source-ai-auto').checked?'Se não houver texto de referência, a IA escolhida na aba Texto preparará o material de estudo antes de criar o roteiro. Você também pode fornecer suas próprias fontes.':'As fontes abaixo são opcionais. Se informar apenas o assunto, o aplicativo buscará referências sobre o assunto e imagens reutilizáveis na internet antes de escrever.';
}
function bindMotivation(prefix){
 const field=$(prefix+'-tipo_roteiro');if(!field)return;
 field.onchange=()=>paintMotivation(prefix,true);
 const tone=$(prefix+'-tom');if(tone)tone.onchange=()=>{
  if(motivationalTone(tone.value)&&$(prefix+'-estilo_locucao')){
   $(prefix+'-estilo_locucao').value=tone.value;$(prefix+'-estilo_locucao').dispatchEvent(new Event('change'));
  }
  paintMotivation(prefix);
 };
 const apply=document.querySelector(`[data-motivation-apply="${prefix}"]`);
 if(apply)apply.onclick=()=>{
  const preset=studioCatalog.vozes_motivacionais?.find(p=>p.id===$(prefix+'-motivational-voice').value);
  if(!preset){toast('Escolha uma combinação de voz e estilo.');return}
  field.value='motivacional';tone.value=preset.tom;$(prefix+'-voz').value=preset.voz;
  $(prefix+'-estilo_locucao').value=preset.tom;$(prefix+'-motivation-kind').dataset.voiceOverride=preset.voz;
  $(prefix+'-voz').dispatchEvent(new Event('change'));$(prefix+'-estilo_locucao').dispatchEvent(new Event('change'));
  paintMotivation(prefix);$(prefix+'-motivation-voice-note').textContent='Selecionado: '+preset.nome+'. Você pode personalizar o ritmo e o modo de locução.';
 };
 const listen=document.querySelector(`[data-motivation-listen="${prefix}"]`);
 if(listen)listen.onclick=async()=>{
  const label='▷ Ouvir voz selecionada';
  if(audio&&!audio.paused){audio.pause();listen.textContent=label;return}
  const sample=document.querySelector(`[data-sample="${prefix}"]`);if(!sample)return;
  listen.disabled=true;listen.textContent='Preparando amostra…';
  try{
   await sample.onclick();listen.textContent=audio&&!audio.paused?'■ Parar amostra':label;
   audio?.addEventListener('ended',()=>listen.textContent=label,{once:true});
  }finally{listen.disabled=false;if(!audio||audio.paused)listen.textContent=label}
 };
 paintMotivation(prefix);
}
