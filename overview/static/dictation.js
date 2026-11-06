// One microphone session at a time. Recognition happens only on the local server.
(() => {
 'use strict';
 const entries=new Map();
 const excluded=new Set(['urls','custom-bg-input','channel-id']);
 const mic='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3m-4 0h8"/></svg>';
 let active=null,scheduled=false;

 function editable(el){return el.isConnected&&!el.disabled&&!el.readOnly}
 function visible(el){return !!el.getClientRects().length&&!el.closest('[hidden],dialog:not([open])')}
 function name(el){
  const label=el.closest('label');
  return el.getAttribute('aria-label')||Array.from(label?.childNodes||[]).filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ').trim()||el.placeholder||'texto';
 }
 function message(entry,text,error=false){
  entry.status.textContent=text;entry.status.hidden=!text;entry.status.classList.toggle('dictation-error',error);
 }
 function sync(){
  for(const [el,entry] of entries){
   if(!el.isConnected){entries.delete(el);continue}
   const selected=active?.entry===entry;
   const disabled=!editable(el)||!!active&&(!selected||active.phase!=='recording');
   if(entry.button.disabled!==disabled)entry.button.disabled=disabled;
  }
  if(active&&(!editable(active.entry.el)||!visible(active.entry.el)))cancel('Ditado encerrado porque este campo deixou de estar disponível.');
 }
 function decorate(el){
  if(entries.has(el)||excluded.has(el.id)||el.dataset.dictation==='off'||el.closest('[data-dictation="off"]'))return;
  const fieldName=name(el);
  // Keep the field's accessible name independent of the new controls/status.
  if(!el.hasAttribute('aria-label')&&!el.hasAttribute('aria-labelledby'))el.setAttribute('aria-label',fieldName);
  const wrap=document.createElement('div');wrap.className='dictation-field';
  el.before(wrap);wrap.append(el);
  const controls=document.createElement('div');controls.className='dictation-controls';
  const button=document.createElement('button');button.type='button';button.className='dictation-mic';button.innerHTML=mic;
  const label='Falar para preencher: '+fieldName;button.title=label;button.setAttribute('aria-label',label);button.setAttribute('aria-pressed','false');
  const cancelButton=document.createElement('button');cancelButton.type='button';cancelButton.className='dictation-cancel';cancelButton.textContent='×';cancelButton.title='Cancelar ditado';cancelButton.setAttribute('aria-label','Cancelar ditado');cancelButton.hidden=true;
  const status=document.createElement('span');status.className='dictation-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.hidden=true;
  controls.append(button,cancelButton);wrap.append(controls,status);
  const entry={el,wrap,button,cancelButton,status,label};entries.set(el,entry);
  // Keep the field's cursor/selection when its microphone is clicked.
  button.addEventListener('mousedown',e=>e.preventDefault());
  button.addEventListener('click',e=>{e.preventDefault();if(active?.entry===entry){if(active.phase==='recording')stop(active);return}start(entry)});
  cancelButton.addEventListener('click',e=>{e.preventDefault();cancel()});
 }
 function scan(){
  document.querySelectorAll('textarea,input:not([type]),input[type="text"]').forEach(decorate);sync();
 }
 function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(()=>{scheduled=false;scan()})}}
 function stopTracks(session){session.stream?.getTracks().forEach(track=>track.stop());clearInterval(session.timer)}
 function release(session){
  stopTracks(session);session.chunks=[];
  const {entry}=session;entry.wrap.classList.remove('dictation-active');entry.button.innerHTML=mic;entry.button.title=entry.label;entry.button.setAttribute('aria-label',entry.label);entry.button.setAttribute('aria-pressed','false');entry.cancelButton.hidden=true;
  if(active===session)active=null;sync();
 }
 function cancel(text='Ditado cancelado. O texto foi preservado.'){
  const session=active;if(!session)return;
  active=null;session.controller.abort();
  if(session.recorder?.state==='recording')session.recorder.stop();
  release(session);message(session.entry,text);
 }
 function fail(session,error){
  if(active!==session)return;
  const messages={NotAllowedError:'Permita o microfone nas configurações deste site e tente novamente.',NotFoundError:'Nenhum microfone foi encontrado. Conecte um microfone e tente novamente.',NotReadableError:'Não consegui acessar o microfone. Confira se outro aplicativo está usando o dispositivo.',SecurityError:'Este navegador bloqueou o microfone. Abra o estúdio em localhost no Chrome ou Edge.',AbortError:'A transcrição demorou demais. Tente ditar um trecho menor.'};
  const text=messages[error.name]||error.message||'Não foi possível iniciar o microfone.';
  if(session.recorder?.state==='recording'){active=null;session.recorder.stop()}
  release(session);message(session.entry,text,true);
 }
 function clock(seconds){return String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0')}

 async function start(entry){
  if(active||!editable(entry.el))return;
  const el=entry.el;
  const session={entry,phase:'requesting',base:el.value,start:el.selectionStart??el.value.length,end:el.selectionEnd??el.value.length,chunks:[],bytes:0,controller:new AbortController()};
  active=session;sync();message(entry,'Preparando microfone…');entry.cancelButton.hidden=false;
  try{
   if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw Error('Este navegador não permite gravar aqui. Abra http://127.0.0.1:7860 no Chrome ou Edge e permita o microfone.');
   const response=await fetch('/api/dictation',{signal:session.controller.signal});
   if(!response.ok)throw Error('Não foi possível conferir o ditado. Verifique se o estúdio está aberto.');
   const config=await response.json();if(active!==session)return;
   if(!config.pronto)throw Error('O ditado local precisa ser instalado. Execute instalar-ditado.bat na pasta do aplicativo e tente novamente.');
   message(entry,'Permita o uso do microfone quando o navegador solicitar.');
   session.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
   if(active!==session){stopTracks(session);return}
   const mime=['audio/webm;codecs=opus','audio/mp4','audio/ogg;codecs=opus'].find(type=>MediaRecorder.isTypeSupported(type));
   const recorder=session.recorder=new MediaRecorder(session.stream,mime?{mimeType:mime}:{});
   recorder.ondataavailable=e=>{
    if(active!==session||!e.data.size)return;
    session.chunks.push(e.data);session.bytes+=e.data.size;
    if(session.bytes>config.max_bytes)fail(session,Error('A gravação ficou muito grande. Grave um trecho menor.'));
   };
   recorder.onerror=()=>fail(session,Error('A gravação foi interrompida. Confira o microfone e tente novamente.'));
   recorder.onstop=()=>{if(active===session)transcribe(session)};
   recorder.start(1000);session.phase='recording';session.started=Date.now();
   entry.wrap.classList.add('dictation-active');entry.button.innerHTML='<span aria-hidden="true">■</span>';entry.button.title='Parar e inserir texto';entry.button.setAttribute('aria-label','Parar e inserir texto');entry.button.setAttribute('aria-pressed','true');
   const tick=()=>{
    const seconds=Math.floor((Date.now()-session.started)/1000);
    message(entry,'Ouvindo · '+clock(seconds)+' · clique em ■ para inserir o texto. Áudio local.');
    // Leave one second for the container's encoder tail.
    if(seconds>=config.max_segundos-1)stop(session);
   };
   tick();session.timer=setInterval(tick,1000);
   session.stream.getAudioTracks().forEach(track=>track.addEventListener('ended',()=>{if(active===session&&session.phase==='recording')stop(session)}));
  }catch(error){fail(session,error)}
 }

 function stop(session){
  if(active!==session||session.phase!=='recording')return;
  session.phase='transcribing';message(session.entry,'Transcrevendo sua fala neste computador…');
  session.entry.button.disabled=true;session.recorder.stop();stopTracks(session);
 }
 function insert(session,text){
  const el=session.entry.el;
  // If the user typed during recording, append instead of overwriting that edit.
  const unchanged=el.value===session.base;
  const start=unchanged?session.start:el.value.length,end=unchanged?session.end:el.value.length;
  const before=el.value.slice(0,start),after=el.value.slice(end);
  text=text.trim();
  const left=before&&!/\s$/.test(before)&&! /^[,.;:!?]/.test(text)?' ':'';
  const right=after&&!/^\s|^[,.;:!?]/.test(after)?' ':'';
  const limit=el.maxLength<0?Infinity:Math.max(0,el.maxLength-before.length-after.length);
  let addition=left+text+right;
  const shortened=addition.length>limit;
  if(shortened)addition=addition.slice(0,limit).trimEnd();
  if(!addition.trim())return 'O campo chegou ao limite de caracteres. O texto existente foi preservado.';
  el.value=before+addition+after;
  el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));
  el.focus({preventScroll:true});el.setSelectionRange(before.length+addition.length,before.length+addition.length);
  return shortened?'Texto inserido até o limite do campo. Revise antes de continuar.':'Texto inserido. Você pode revisar ou ditar mais.';
 }
 async function transcribe(session){
  if(active!==session)return;
  stopTracks(session);session.phase='transcribing';session.entry.button.disabled=true;
  message(session.entry,'Transcrevendo sua fala neste computador…');
  const timeout=setTimeout(()=>session.controller.abort(),180000);
  try{
   const blob=new Blob(session.chunks,{type:session.recorder.mimeType||session.chunks[0]?.type||'audio/webm'});session.chunks=[];
   if(!blob.size)throw Error('Não recebi áudio do microfone. Grave novamente.');
   const data=new FormData();data.append('audio',blob,'ditado');
   const response=await fetch('/api/dictation/transcribe',{method:'POST',body:data,signal:session.controller.signal});
   const result=await response.json();
   if(active!==session)return;
   if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:'Não foi possível transcrever a gravação.');
   if(!editable(session.entry.el)||!visible(session.entry.el)){cancel();return}
   if(!result.texto?.trim())throw Error('Não consegui reconhecer a fala. Grave novamente.');
   const text=insert(session,result.texto);release(session);message(session.entry,text);
  }catch(error){fail(session,error)}finally{clearTimeout(timeout)}
 }

 // Do not let a late response write into another project, closed dialog or submitted form.
 document.addEventListener('submit',()=>{if(active)cancel()},true);
 document.addEventListener('click',e=>{
  if(active&&!active.entry.wrap.contains(e.target)&&e.target.closest('button,a,input,textarea,select'))cancel();
 },true);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&active){e.preventDefault();e.stopImmediatePropagation();cancel()}},true);
 document.addEventListener('close',e=>{if(active&&e.target.contains(active.entry.el))cancel()},true);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel()});
 window.addEventListener('pagehide',()=>cancel());
 new MutationObserver(schedule).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['disabled','readonly','hidden','open','class','data-step']});
 scan();
})();
