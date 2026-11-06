// Reusable silent footage; narration and music remain independent choices.
document.addEventListener('DOMContentLoaded',()=>{
 let pending=[],target='create',targetPid=null,results=[],library=[],jobId=null,importing=false,pollRevision=0;
 const dialog=document.createElement('dialog');dialog.id='youtube-clips-dialog';dialog.setAttribute('aria-labelledby','youtube-clips-title');
 dialog.innerHTML=`<div class="dialog-head"><h2 id="youtube-clips-title">Clipes do YouTube para seus Reels</h2><button type="button" class="secondary" id="youtube-clips-close" aria-label="Fechar clipes">×</button></div><p class="small">Pesquise pelo nome ou cole o link de um vídeo. Os clipes são salvos sem o áudio original e ficam disponíveis para outros projetos. No vídeo final, use a sua narração e a música escolhida no Clareia.</p><p class="small youtube-music-license">Use clipes próprios ou com autorização para reutilizar. O download não concede direitos sobre as imagens.</p><form id="youtube-clips-search"><label>Nome ou link do vídeo<input id="youtube-clips-query" type="search" required minlength="2" maxlength="200" placeholder="Paisagens de montanha, clipe de natureza ou link do YouTube"></label><label>Qualidade máxima<select id="youtube-clips-quality"><option value="720">720p · arquivo menor</option><option value="1080">1080p · mais detalhes</option></select></label><button class="primary" type="submit" id="youtube-clips-search-button">Buscar clipes</button></form><p class="small" id="youtube-clips-status" role="status"></p><div id="youtube-clips-preview" hidden></div><div class="youtube-import-progress" id="youtube-clips-import" hidden><strong id="youtube-clips-import-name"></strong><p id="youtube-clips-import-status" role="status"></p><progress id="youtube-clips-progress" max="1" value="0"></progress><button type="button" class="secondary" id="youtube-clips-cancel">Cancelar download</button></div><h3 id="youtube-clips-results-heading" hidden>Resultados da busca</h3><div id="youtube-clips-results" class="youtube-music-results"></div><h3>Clipes salvos no computador</h3><div id="youtube-clips-library" class="youtube-music-results"></div><p class="small">Até 30 minutos e 200 MB por clipe. Depois de adicionar ao projeto, escolha a frase de entrada, os cortes e as transições em Escolher onde cada mídia aparece no roteiro.</p>`;
 document.body.append(dialog);
 const preview=$('youtube-clips-preview');
 const stop=()=>{preview.querySelectorAll('video,audio').forEach(p=>p.pause());preview.replaceChildren();preview.hidden=true};
 function paintPending(){
  const pool=$('create-youtube-clips-pending');if(!pool)return;
  pool.innerHTML=pending.length?'<p class="small">Clipes que entrarão no novo projeto:</p>'+pending.map(c=>`<div class="pending-youtube-clip"><img src="/api/youtube-clips/library/${c.id}/poster" alt=""><span>${esc(c.nome)} · sem áudio</span><button type="button" class="secondary" data-remove-youtube-clip="${c.id}" aria-label="Remover clipe selecionado">×</button></div>`).join(''):'';
  pool.querySelectorAll('[data-remove-youtube-clip]').forEach(b=>b.onclick=()=>{pending=pending.filter(c=>c.id!==b.dataset.removeYoutubeClip);paintPending()});
 }
 window.youtubeClipSelection=()=>pending.map(c=>c.id);
 window.clearYouTubeClipSelection=()=>{pending=[];paintPending()};
 function playOriginal(c,muted=false){
  stop();stopMusic();preview.hidden=false;
  preview.innerHTML=`<strong>${muted?'Original sem áudio':'Original com áudio'} · ${esc(c.nome)}</strong><iframe title="Prévia ${muted?'sem':'com'} áudio de ${esc(c.nome)}" src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(c.youtube_id)}?autoplay=1&amp;mute=${muted?1:0}&amp;controls=1&amp;playsinline=1&amp;rel=0&amp;origin=${encodeURIComponent(location.origin)}" allow="autoplay; encrypted-media; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe><p class="small">Esta é a reprodução do original no YouTube. Você pode ouvir o som e avaliar o clipe antes de escolher Baixar sem áudio. Se necessário, inicie a reprodução ou ative o alto-falante no player.</p><a href="${esc(c.fonte)}" target="_blank" rel="noopener noreferrer">Abrir original com áudio no YouTube ↗</a><button type="button" class="secondary" data-stop-clip-preview>Fechar prévia</button>`;
  preview.querySelector('[data-stop-clip-preview]').onclick=stop;preview.scrollIntoView({behavior:'smooth',block:'nearest'});
 }
 async function useClip(id){
  const record=library.find(c=>c.id===id);if(!record)throw Error('Atualize a biblioteca de clipes antes de usar.');
  if(target==='edit'&&current?.id!==targetPid)throw Error('O projeto mudou. Abra a biblioteca a partir do projeto desejado.');
  const radio=document.querySelector(`input[name="${target}-tipo_video"][value="shorts"]`);radio.checked=true;radio.dispatchEvent(new Event('change',{bubbles:true}));
  $(target+'-modo_shorts').value='clipes';$(target+'-modo_shorts').dispatchEvent(new Event('change',{bubbles:true}));
  if(target==='create'){
   if(!pending.some(c=>c.id===id)){if(pending.length>=12)throw Error('Selecione até 12 clipes para o novo projeto.');pending.push(record)}
   paintPending();dialog.close();toast('Clipe selecionado. Informe o assunto ou a narração e crie o roteiro.');return;
  }
  await save();
  const added=await api('/api/projects/'+targetPid+'/reels/youtube-clips',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clipes:[id]})});
  if(current?.id!==targetPid)return;
  Object.assign(current,added);paintShortPhotos('edit');
  document.querySelectorAll('#edit-photo-order [data-short-photo]').forEach(el=>{if(added.adicionadas.includes(el.dataset.shortPhoto))el.querySelector('input').checked=true});
  paintReelsCues('edit');await save();await refresh();dialog.close();toast('Clipe adicionado sem áudio. Agora escolha onde ele aparece no roteiro.');
 }
 function paint(){
  $('youtube-clips-results-heading').hidden=!results.length;
  $('youtube-clips-results').innerHTML=results.map(c=>{
   const saved=library.filter(t=>t.youtube_id===c.youtube_id),best=saved.find(t=>t.qualidade===Number($('youtube-clips-quality').value));
   return `<article class="youtube-music-card"><img loading="lazy" src="${esc(c.miniatura)}" alt=""><div><h4>${esc(c.nome)}</h4><p>${esc(c.autor)}</p><small>${videoClock(c.duracao_s)}</small><div class="music-actions"><button class="secondary" type="button" data-clip-preview="${c.id}">▶ Prévia com áudio</button><button class="secondary" type="button" data-clip-preview="${c.id}" data-preview-muted>▷ Prévia sem áudio</button>${best?`<button class="primary" type="button" data-clip-use="${best.id}">Usar este clipe</button>`:`<button class="primary" type="button" data-clip-download="${c.id}" ${importing?'disabled':''}>↓ Baixar sem áudio</button>`}<a href="${esc(c.fonte)}" target="_blank" rel="noopener noreferrer">Abrir no YouTube ↗</a></div></div></article>`;
  }).join('');
  $('youtube-clips-library').innerHTML=library.map(c=>`<article class="youtube-music-card"><img loading="lazy" src="/api/youtube-clips/library/${c.id}/poster" alt=""><div><h4>${esc(c.nome)}</h4><p>${esc(c.autor)}</p><small>${videoClock(c.duracao_s)} · ${c.largura} × ${c.altura} · arquivo sem áudio</small><div class="music-actions"><button type="button" class="secondary" data-clip-original="${c.id}">▶ Original com áudio</button><button type="button" class="secondary" data-saved-clip-preview="${c.id}">▷ Arquivo sem áudio</button><button type="button" class="primary" data-clip-use="${c.id}">Usar este clipe</button></div></div></article>`).join('')||'<p class="small">Os clipes que você baixar aparecerão aqui e poderão ser usados em outros vídeos.</p>';
  dialog.querySelectorAll('[data-clip-use]').forEach(b=>b.onclick=()=>action(()=>useClip(b.dataset.clipUse)));
  dialog.querySelectorAll('[data-clip-preview]').forEach(b=>b.onclick=()=>playOriginal(results.find(c=>c.id===b.dataset.clipPreview),b.hasAttribute('data-preview-muted')));
  dialog.querySelectorAll('[data-clip-original]').forEach(b=>b.onclick=()=>playOriginal(library.find(c=>c.id===b.dataset.clipOriginal)));
  dialog.querySelectorAll('[data-saved-clip-preview]').forEach(b=>b.onclick=()=>{
   stop();stopMusic();preview.hidden=false;preview.innerHTML=`<video controls autoplay muted playsinline src="/api/youtube-clips/library/${b.dataset.savedClipPreview}/video"></video><button type="button" class="secondary" data-stop-clip-preview>Fechar prévia</button>`;
   preview.querySelector('[data-stop-clip-preview]').onclick=stop;preview.scrollIntoView({behavior:'smooth',block:'nearest'});
  });
  dialog.querySelectorAll('[data-clip-download]').forEach(b=>b.onclick=()=>action(async()=>{
   if(importing)return;importing=true;paint();
   try{
    const job=await api('/api/youtube-clips/imports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resultado:b.dataset.clipDownload,qualidade:Number($('youtube-clips-quality').value)})});
    jobId=job.id||null;await watch(job);
   }catch(e){importing=false;paint();$('youtube-clips-status').textContent=e.message;throw e}
  }));
 }
 function showJob(job){
  $('youtube-clips-import').hidden=false;$('youtube-clips-import-name').textContent=job.video?.nome||job.clipe?.nome||'Importação do clipe';
  $('youtube-clips-import-status').textContent=job.mensagem||'';$('youtube-clips-progress').value=job.progresso||0;
  $('youtube-clips-cancel').hidden=!['aguardando','baixando','convertendo'].includes(job.estado);
 }
 async function watch(job){
  const revision=++pollRevision;showJob(job);
  while(revision===pollRevision){
   importing=['aguardando','baixando','convertendo'].includes(job.estado);paint();
   if(!importing){
    if(job.estado==='concluido'){library=await api('/api/youtube-clips/library');paint();$('youtube-clips-status').textContent='Clipe salvo sem áudio. Clique em Usar este clipe para adicionar ao projeto.'}
    return;
   }
   await new Promise(resolve=>setTimeout(resolve,800));if(revision!==pollRevision)return;
   job=await api('/api/youtube-clips/imports/'+job.id);showJob(job);
  }
 }
 window.bindYouTubeClips=prefix=>{
  const button=document.querySelector('[data-youtube-clips="'+prefix+'"]');if(!button)return;
  button.onclick=()=>action(async()=>{
   target=prefix;targetPid=current?.id||null;library=await api('/api/youtube-clips/library');paint();dialog.showModal();
   const active=await api('/api/youtube-clips/imports/active');
   if(active.importacao){jobId=active.importacao.id;watch(active.importacao).catch(e=>{$('youtube-clips-status').textContent=e.message})}
   else if(jobId)watch(await api('/api/youtube-clips/imports/'+jobId)).catch(e=>{$('youtube-clips-status').textContent=e.message});
  });paintPending();
 };
 $('youtube-clips-search').onsubmit=e=>{e.preventDefault();action(async()=>{
  const button=$('youtube-clips-search-button');button.disabled=true;$('youtube-clips-status').textContent='Buscando vídeos no YouTube…';
  try{const found=await api('/api/youtube-clips/search?q='+encodeURIComponent($('youtube-clips-query').value.trim()));results=found.videos;paint();$('youtube-clips-status').textContent=results.length?(results.length===1?'1 vídeo encontrado':results.length+' vídeos encontrados')+'. Confira o canal e a duração antes de baixar.':'Nenhum clipe de até 30 minutos foi encontrado. Tente outro nome ou o link do vídeo.'}
  catch(e){$('youtube-clips-status').textContent=e.message;throw e}finally{button.disabled=false}
 })};
 $('youtube-clips-quality').onchange=paint;
 $('youtube-clips-cancel').onclick=()=>action(async()=>{if(jobId){await api('/api/youtube-clips/imports/'+jobId+'/cancel',{method:'POST'});$('youtube-clips-import-status').textContent='Cancelando…'}});
 $('youtube-clips-close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{stop();pollRevision++});
});
