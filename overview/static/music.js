// One soundtrack spans the complete video. Voice/visual timing remains independent.
let musicCatalog=[],musicTarget='create',musicPreviewRevision=0;
const musicNorm=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
async function loadMusicCatalog(){
 musicCatalog=await api('/api/music');
 const control=$('music-category');if(control){const selected=control.value;control.innerHTML='<option value="">Todos os estilos</option>'+[...new Set(musicCatalog.map(t=>t.categoria))].map(category=>`<option value="${esc(category)}">${esc(category)}</option>`).join('');control.value=[...control.options].some(o=>o.value===selected)?selected:''}
}
function musicOptions(selected=''){
 const groups=[...new Set(musicCatalog.map(t=>t.categoria))];
 return '<option value="">Sem música de fundo</option>'+groups.map(g=>`<optgroup label="${esc(g)}">${musicCatalog.filter(t=>t.categoria===g).map(t=>`<option value="${esc(t.id)}" ${t.id===selected?'selected':''}>${esc(t.nome)}${t.recomendada?' · recomendada':''}</option>`).join('')}</optgroup>`).join('');
}
function musicVolumePercent(db){return db<=-60?0:Math.round(Math.min(100,100*10**((db+14)/20)))}
function setMusicVolume(prefix,value){
 const percent=Math.max(0,Math.min(100,Math.round(Number(value))));if(!Number.isFinite(percent))return;
 $(prefix+'-volume_musica').value=percent;$(prefix+'-volume_musica_percent').value=percent;
 $(prefix+'-volume_musica_db').value=percent===0?-60:-14+20*Math.log10(percent/100);
 const player=$(prefix+'-music-audio');
 if(player.dataset.kind==='music'&&!player.hidden){musicPreviewRevision++;player.volume=.7*percent/100}
 else{stopMusic();player.hidden=true;$(prefix+'-music-status').textContent='Volume alterado. Clique em Testar com a voz escolhida para ouvir a nova mixagem.'}
}
function musicFields(prefix,s){return `<fieldset class="music-settings"><legend>Música de fundo</legend><p class="small">Trilha contínua e discreta, com a narração em primeiro plano. Ouça antes de renderizar.</p><label>Trilha do vídeo<select id="${prefix}-musica_fundo">${musicOptions(s.musica_fundo||'')}</select></label><div class="config-fields"><label class="music-volume-label" for="${prefix}-volume_musica">Volume da música</label><div class="music-volume-row"><input type="range" id="${prefix}-volume_musica" min="0" max="100" step="1" value="${musicVolumePercent(s.volume_musica_db??-20)}" aria-label="Volume da música" aria-describedby="${prefix}-volume-help"><span class="music-volume-number"><input type="number" id="${prefix}-volume_musica_percent" min="0" max="100" step="1" value="${musicVolumePercent(s.volume_musica_db??-20)}" aria-label="Volume da música em porcentagem">%</span></div><input type="hidden" id="${prefix}-volume_musica_db" value="${s.volume_musica_db??-20}"><p class="small" id="${prefix}-volume-help">0% deixa a música muda. Comece em 50% e teste com a narração. Este controle também vale para o vídeo exportado.</p><label class="check-row"><input type="checkbox" id="${prefix}-reduzir_musica_na_fala" ${s.reduzir_musica_na_fala!==false?'checked':''}>Reduzir a música durante a fala</label></div><div class="music-actions"><button class="secondary" type="button" data-music-library="${prefix}">♫ Explorar músicas e importar</button><button class="secondary" type="button" data-music-listen="${prefix}">▷ Ouvir música</button><button class="secondary" type="button" data-music-voice="${prefix}">▷ Testar com a voz escolhida</button></div><p class="small music-track-note" id="${prefix}-music-note"></p><audio id="${prefix}-music-audio" controls preload="none" hidden></audio><p class="small" id="${prefix}-music-status" role="status"></p></fieldset>`}
function musicConfig(prefix){return {musica_fundo:$(prefix+'-musica_fundo').value,volume_musica_db:Number($(prefix+'-volume_musica_db').value),reduzir_musica_na_fala:$(prefix+'-reduzir_musica_na_fala').checked}}
function stopMusic(){musicPreviewRevision++;document.querySelectorAll('.music-settings audio,#music-library audio').forEach(a=>a.pause());window.stopYouTubeMusic?.()}
function paintMusicNote(prefix){const t=musicCatalog.find(t=>t.id===$(prefix+'-musica_fundo').value);$(prefix+'-music-note').textContent=t?`${t.uso} ${t.autor} · ${t.licenca}. Os créditos ficam disponíveis junto ao vídeo.`:`Opcional. Escolha entre ${musicCatalog.length} faixas da biblioteca ou importe sua própria música.`;for(const name of ['listen','voice'])document.querySelector(`[data-music-${name}="${prefix}"]`).disabled=!t}
async function playMusic(prefix,voice=false){
 stopMusic();if(audio)audio.pause();const rev=musicPreviewRevision,settings=musicConfig(prefix),player=$(prefix+'-music-audio'),statusBox=$(prefix+'-music-status');
 if(!settings.musica_fundo)throw Error('Escolha uma música primeiro.');
 statusBox.textContent=voice?'Preparando uma amostra com a voz, o ritmo e a intensidade escolhidos…':'Carregando a faixa…';
 try{
  let url='/api/music/tracks/'+encodeURIComponent(settings.musica_fundo);
  if(voice){const preset=window.favoritePreviewConfig?.(prefix),result=await api('/api/music/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...settings,...geminiProjectConfig(prefix),voz:preset?.voz??$(prefix+'-voz').value,estilo_locucao:preset?.estilo_locucao??$(prefix+'-estilo_locucao').value,velocidade:preset?.velocidade??Number($(prefix+'-velocidade').value)})});url=result.url}
  if(rev!==musicPreviewRevision)return;
  player.src=url;player.dataset.kind=voice?'voice':'music';player.volume=voice?1:.7*Number($(prefix+'-volume_musica').value)/100;player.hidden=false;await player.play();
  statusBox.textContent=voice?'Amostra da mixagem: a mesma configuração será usada no vídeo.':'Música isolada para escolher a faixa. Use o teste com voz para conferir o equilíbrio.';
 }catch(e){if(rev===musicPreviewRevision)statusBox.textContent='Não foi possível preparar a amostra.';throw e}
}
function bindMusicControls(prefix){
 paintMusicNote(prefix);
 $(prefix+'-volume_musica').oninput=e=>setMusicVolume(prefix,e.target.value);
 $(prefix+'-volume_musica_percent').oninput=e=>{if(e.target.value!=='')setMusicVolume(prefix,e.target.value)};
 $(prefix+'-volume_musica_percent').onchange=e=>setMusicVolume(prefix,e.target.value||0);
 for(const k of ['voz','velocidade','estilo_locucao'])$(prefix+'-'+k).addEventListener('change',()=>{stopMusic();$(prefix+'-music-audio').hidden=true;$(prefix+'-music-status').textContent=''});
 for(const k of ['musica_fundo','volume_musica_db','reduzir_musica_na_fala'])$(prefix+'-'+k).onchange=()=>{stopMusic();$(prefix+'-music-audio').hidden=true;$(prefix+'-music-status').textContent='';paintMusicNote(prefix)};
 document.querySelector(`[data-music-listen="${prefix}"]`).onclick=()=>action(()=>playMusic(prefix));
 document.querySelector(`[data-music-voice="${prefix}"]`).onclick=()=>action(()=>playMusic(prefix,true));
 document.querySelector(`[data-music-library="${prefix}"]`).onclick=()=>{musicTarget=prefix;drawMusicLibrary();$('music-library').showModal()};
}
function drawMusicLibrary(){
 const query=musicNorm($('music-search').value),category=$('music-category').value;
 const tracks=musicCatalog.filter(t=>(!category||category===t.categoria)&&musicNorm([t.nome,t.uso,t.categoria,t.instrumentos,t.autor].join(' ')).includes(query));
 $('music-count').textContent=tracks.length+' faixas · consulte a licença de cada faixa; o acervo inicial CC BY exige créditos';
 $('music-grid').innerHTML=tracks.map(t=>`<article class="music-card"><div><h3>${esc(t.nome)}</h3>${t.recomendada?'<span class="music-badge">Recomendada para narração</span>':''}<p>${esc(t.uso)}</p><small>${esc(t.categoria)} · ${Math.floor(t.duracao_s/60)}:${String(Math.floor(t.duracao_s%60)).padStart(2,'0')} · ${esc(t.autor)}</small><p class="small">${esc(t.licenca)}</p></div><div class="music-actions"><button type="button" class="secondary" data-library-listen="${esc(t.id)}">▷ Ouvir</button><button type="button" class="primary" data-use-music="${esc(t.id)}">Usar esta música</button>${t.fonte?`<a href="${esc(t.fonte)}" target="_blank" rel="noreferrer">Fonte e licença ↗</a>`:''}</div></article>`).join('')||'<p>Nenhuma faixa corresponde à busca.</p>';
 document.querySelectorAll('[data-library-listen]').forEach(b=>b.onclick=()=>action(async()=>{stopMusic();if(audio)audio.pause();const player=$('music-library-audio');player.src='/api/music/tracks/'+encodeURIComponent(b.dataset.libraryListen);player.volume=.35;player.hidden=false;await player.play()}));
 document.querySelectorAll('[data-use-music]').forEach(b=>b.onclick=()=>{const control=$(musicTarget+'-musica_fundo');control.innerHTML=musicOptions(b.dataset.useMusic);control.dispatchEvent(new Event('change'));$('music-library').close();toast('Música selecionada. Teste com a voz antes de renderizar.')});
}
document.addEventListener('DOMContentLoaded',()=>{
 const dialog=document.createElement('dialog');dialog.id='music-library';dialog.setAttribute('aria-labelledby','music-library-title');
 dialog.innerHTML=`<div class="dialog-head"><h2 id="music-library-title">Músicas para seus vídeos</h2><button type="button" class="secondary" id="music-close" aria-label="Fechar músicas">×</button></div><p class="small">Trilhas instrumentais para aulas, documentários, histórias de terror e suspense. Nas categorias de terror, comece pelas recomendadas para narração; as intensas têm sons mais marcantes. Acervo Kevin MacLeod · CC BY 4.0, com crédito público obrigatório na descrição ou no próprio vídeo.</p><div class="config-fields"><label>Buscar música<input type="search" id="music-search" placeholder="Terror, suspense, piano, calma…"></label><label>Estilo<select id="music-category"><option value="">Todos os estilos</option></select></label></div><audio controls id="music-library-audio" hidden preload="none"></audio><p class="small" id="music-count" role="status"></p><div id="music-grid"></div><details class="music-import"><summary>Importar minha música</summary><p class="small">Importe uma faixa própria ou licenciada para o seu uso. O arquivo fica neste computador. MP3, WAV, FLAC, OGG ou M4A · até 120 MB e 30 minutos.</p><label>Arquivo de áudio<input type="file" id="music-file" accept=".mp3,.wav,.flac,.ogg,.m4a,.aac"></label><label>Nome da música<input id="music-title" maxlength="100" placeholder="Opcional · usa o nome do arquivo"></label><label>Créditos da faixa<textarea id="music-credit" rows="2" maxlength="2000" placeholder="Autor, fonte e licença, conforme os termos da sua faixa"></textarea></label><button type="button" class="secondary" id="music-import">Importar música</button><p class="small" id="music-import-status" role="status"></p></details><details><summary>Faixa do canal que você indicou</summary><p class="small">A descrição de <a href="https://www.youtube.com/watch?v=pSZKl8dvdcc" target="_blank" rel="noreferrer">Education Background Music</a> permite uso gratuito sem monetização, com reivindicação de Content ID; monetizar exige licença do canal. Ela não integra o acervo CC BY. Use o download e a licença oficiais do autor, depois importe seu arquivo acima.</p><a href="https://www.youtube.com/@backgroundmusicforvideoedits" target="_blank" rel="noreferrer">Explorar o canal de referência ↗</a></details>`;
 document.body.append(dialog);$('music-close').onclick=()=>dialog.close();dialog.addEventListener('close',stopMusic);
 $('music-search').oninput=$('music-category').onchange=drawMusicLibrary;
 $('music-import').onclick=()=>action(async()=>{
  const file=$('music-file').files[0];if(!file)throw Error('Escolha um arquivo de música.');
  const button=$('music-import');button.disabled=true;$('music-import-status').textContent='Importando áudio…';
  try{const form=new FormData();form.append('file',file);form.append('titulo',$('music-title').value);form.append('creditos',$('music-credit').value);const track=await api('/api/music/import',{method:'POST',body:form});await loadMusicCatalog();for(const prefix of ['create','edit'])if($(prefix+'-musica_fundo')){const old=$(prefix+'-musica_fundo').value;$(prefix+'-musica_fundo').innerHTML=musicOptions(prefix===musicTarget?track.id:old);paintMusicNote(prefix)}$('music-file').value='';$('music-title').value='';$('music-credit').value='';$('music-import-status').textContent='Música importada e selecionada para este vídeo.';drawMusicLibrary()}
  catch(e){$('music-import-status').textContent='A importação não foi concluída.';throw e}finally{button.disabled=false}
 });
 const credits=document.createElement('a');credits.id='download-music';credits.className='secondary';credits.hidden=true;credits.textContent='↓ Créditos da música';$('download-collage').insertAdjacentElement('afterend',credits);
});
