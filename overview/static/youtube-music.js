// Discover songs online; only an explicit download adds audio to the local catalog.
document.addEventListener('DOMContentLoaded',()=>{
 const dialog=$('music-library');if(!dialog)return;
 const head=dialog.querySelector('.dialog-head'),local=document.createElement('section');local.id='music-local-panel';
 [...dialog.children].filter(el=>el!==head).forEach(el=>local.append(el));dialog.append(local);
 head.insertAdjacentHTML('afterend',`<div class="music-sources" role="group" aria-label="Onde buscar músicas"><button type="button" class="secondary" id="music-source-local" aria-pressed="true">Minha biblioteca</button><button type="button" class="secondary" id="music-source-youtube" aria-pressed="false">Buscar no YouTube Music</button></div>`);
 dialog.insertAdjacentHTML('beforeend',`<section id="music-youtube-panel" hidden><h3>Músicas e trilhas do YouTube Music</h3><p class="small">Busque pelo nome da faixa ou do artista. Os resultados são filtrados como músicas; vídeos comuns, filmes, podcasts e playlists ficam fora da lista.</p><form id="music-youtube-search"><label>Nome da música ou artista<input type="search" id="music-youtube-query" required minlength="2" maxlength="200" placeholder="Ex.: Carefree Kevin MacLeod"></label><button type="submit" class="primary" id="music-youtube-search-button">Buscar músicas</button></form>
 <p class="small youtube-music-license">Ouvir ou baixar uma música não concede autorização para colocá-la no seu vídeo. Use uma faixa própria ou com licença adequada; ela pode gerar uma reivindicação de direitos autorais no YouTube.</p>
 <p id="music-youtube-status" class="small" role="status"></p><div id="music-youtube-preview" hidden></div>
 <details class="youtube-credit"><summary>Créditos e licença para guardar com a próxima faixa</summary><label>Créditos ou autorização de uso<textarea id="music-youtube-credit" rows="3" maxlength="2000" placeholder="Opcional · autor, licença e link fornecidos pelo titular da música"></textarea></label></details>
 <div id="music-youtube-import" class="youtube-import-progress" hidden><strong id="music-youtube-import-name"></strong><p id="music-youtube-import-status" role="status"></p><progress id="music-youtube-progress" max="1" value="0"></progress><button id="music-youtube-cancel" type="button" class="secondary">Cancelar importação</button></div>
 <div id="music-youtube-results" class="youtube-music-results"></div><p class="small">Integração comunitária, sem chave de API e sem acesso à sua conta Google. A busca e a reprodução precisam de internet; depois de salva, a faixa fica disponível no computador para vídeos e Reels. Até 30 minutos e 120 MB por faixa.</p></section>`);
 let results=[],searchRevision=0,pollRevision=0,jobId=null,importing=false;
 const preview=$('music-youtube-preview');
 window.stopYouTubeMusic=()=>{preview.querySelectorAll('audio,video').forEach(p=>p.pause());preview.replaceChildren();preview.hidden=true};
 function choose(trackId){
  const control=$(musicTarget+'-musica_fundo');if(!control)throw Error('Abra as músicas a partir das configurações do vídeo.');
  control.innerHTML=musicOptions(trackId);control.dispatchEvent(new Event('change'));dialog.close();toast('Música selecionada para este vídeo.');
 }
 function paint(){
  $('music-youtube-results').innerHTML=results.map(t=>`<article class="youtube-music-card"><img loading="lazy" src="${esc(t.miniatura)}" alt=""><div><h4>${esc(t.nome)}</h4><p>${esc(t.autor)}</p><small>${Math.floor(t.duracao_s/60)}:${String(Math.floor(t.duracao_s%60)).padStart(2,'0')}${t.album?' · '+esc(t.album):''}</small><div class="music-actions"><button type="button" class="secondary" data-youtube-listen="${esc(t.id)}">▷ Ouvir</button>${t.salva_id?`<button type="button" class="primary" data-youtube-use="${esc(t.salva_id)}">Usar esta música</button><small>Salva no computador</small>`:`<button type="button" class="primary" data-youtube-download="${esc(t.id)}" ${importing?'disabled':''}>↓ Baixar para a biblioteca</button>`}<a href="${esc(t.fonte)}" target="_blank" rel="noopener noreferrer">Abrir no YouTube Music ↗</a></div></div></article>`).join('');
  document.querySelectorAll('[data-youtube-listen]').forEach(b=>b.onclick=()=>{
   const t=results.find(t=>t.id===b.dataset.youtubeListen);stopMusic();if(audio)audio.pause();
   preview.hidden=false;preview.innerHTML=`<div class="youtube-preview-title"><strong>Ouvindo: ${esc(t.nome)} · ${esc(t.autor)}</strong><button type="button" class="secondary" id="music-youtube-stop">Fechar reprodução</button></div>`+(t.salva_id?`<audio controls autoplay src="/api/music/tracks/${encodeURIComponent(t.salva_id)}"></audio>`:`<iframe title="Reprodução de ${esc(t.nome)} no YouTube" src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(t.youtube_id)}?autoplay=1&amp;origin=${encodeURIComponent(location.origin)}" allow="autoplay; encrypted-media; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe><p class="small">Player do YouTube. Se a faixa não permitir reprodução incorporada, use Abrir no YouTube Music.</p>`);
   $('music-youtube-stop').onclick=window.stopYouTubeMusic;preview.scrollIntoView({behavior:'smooth',block:'nearest'});
  });
  document.querySelectorAll('[data-youtube-use]').forEach(b=>b.onclick=()=>action(async()=>{await loadMusicCatalog();choose(b.dataset.youtubeUse)}));
  document.querySelectorAll('[data-youtube-download]').forEach(b=>b.onclick=()=>action(async()=>{
   if(importing)return;importing=true;paint();
   try{
    const job=await api('/api/music/youtube/imports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resultado:b.dataset.youtubeDownload,creditos:$('music-youtube-credit').value})});
    jobId=job.id||null;await watch(job);
   }catch(e){importing=false;paint();$('music-youtube-status').textContent=e.message;throw e}
  }));
 }
 async function refreshCatalog(){
  await loadMusicCatalog();
  for(const prefix of ['create','edit'])if($(prefix+'-musica_fundo')){
   const control=$(prefix+'-musica_fundo'),value=control.value;control.innerHTML=musicOptions(value);paintMusicNote(prefix);
  }
  drawMusicLibrary();
 }
 function showJob(job){
  $('music-youtube-import').hidden=false;$('music-youtube-import-name').textContent=job.musica?.nome||job.faixa?.nome||'Importação da música';
  let note=job.mensagem||'';if(job.estado==='baixando'&&job.baixados_bytes)note+=' '+formatBytes(job.baixados_bytes)+(job.total_bytes?' / '+formatBytes(job.total_bytes):'');
  $('music-youtube-import-status').textContent=note;$('music-youtube-progress').value=job.progresso||0;
  $('music-youtube-cancel').hidden=!['aguardando','baixando','convertendo'].includes(job.estado);
 }
 async function watch(job){
  const version=++pollRevision;showJob(job);
  while(version===pollRevision){
   importing=['aguardando','baixando','convertendo'].includes(job.estado);paint();
   if(!importing){
    if(job.estado==='concluido'){
     await refreshCatalog();for(const t of results)if(t.youtube_id===job.faixa.youtube_id)t.salva_id=job.faixa.id;paint();
     $('music-youtube-status').textContent='Música salva. Ela também estará na biblioteca dos seus próximos vídeos.';
    }
    return;
   }
   await new Promise(resolve=>setTimeout(resolve,800));if(version!==pollRevision)return;
   job=await api('/api/music/youtube/imports/'+job.id);showJob(job);
  }
 }
 $('music-youtube-search').onsubmit=e=>{e.preventDefault();action(async()=>{
  const version=++searchRevision,button=$('music-youtube-search-button');button.disabled=true;$('music-youtube-status').textContent='Buscando músicas no YouTube Music…';
  try{
   const found=await api('/api/music/youtube/search?q='+encodeURIComponent($('music-youtube-query').value.trim()));
   if(version!==searchRevision)return;results=found.faixas;paint();$('music-youtube-status').textContent=results.length?results.length+' músicas encontradas. Confira o artista e ouça antes de baixar.':'Nenhuma música encontrada. Tente o nome da faixa com o artista.';
  }catch(e){if(version===searchRevision)$('music-youtube-status').textContent=e.message;throw e}finally{if(version===searchRevision)button.disabled=false}
 })};
 $('music-youtube-cancel').onclick=()=>action(async()=>{if(jobId){await api('/api/music/youtube/imports/'+jobId+'/cancel',{method:'POST'});$('music-youtube-import-status').textContent='Cancelando a importação…'}});
 async function surface(youtube){
  stopMusic();local.hidden=youtube;$('music-youtube-panel').hidden=!youtube;
  $('music-source-local').setAttribute('aria-pressed',String(!youtube));$('music-source-youtube').setAttribute('aria-pressed',String(youtube));
  if(youtube){
   const active=await api('/api/music/youtube/imports/active');
   if(active.importacao){jobId=active.importacao.id;watch(active.importacao).catch(e=>{$('music-youtube-status').textContent=e.message})}
   else if(jobId)watch(await api('/api/music/youtube/imports/'+jobId)).catch(e=>{$('music-youtube-status').textContent=e.message});
   $('music-youtube-query').focus();
  }
 }
 $('music-source-local').onclick=()=>action(()=>surface(false));$('music-source-youtube').onclick=()=>action(()=>surface(true));
 dialog.addEventListener('close',()=>{window.stopYouTubeMusic();pollRevision++});
 dialog.addEventListener('toggle',e=>{if(e.newState==='open'&&!$('music-youtube-panel').hidden)action(()=>surface(true))});
});
