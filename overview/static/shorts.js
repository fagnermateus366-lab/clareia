// Phone composition choices are shared by creation, favorites and review.
function shortVideoFields(prefix,s={}){
 const select=(key,label,items,value)=>`<label>${label}<select id="${prefix}-${key}">${opt(items,value)}</select></label>`;
 return captionDisplayFields(prefix,s)+(prefix==='edit'?motivationFields(prefix,s):'')+`<fieldset id="${prefix}-video-kind" class="video-kind"><legend>Que vídeo vamos criar?</legend>
 <div class="video-kind-choices" role="group" aria-label="Tipo de vídeo">
 ${[['video','Vídeo comum','Formato livre · YouTube'],['shorts','Reels / Shorts','Vertical · 9:16 · até 3 minutos']].map(([v,n,d])=>`<label class="video-kind-card"><input type="radio" name="${prefix}-tipo_video" value="${v}" ${(s.tipo_video||'video')===v?'checked':''}><span><b>${n}</b><small>${d}</small></span></label>`).join('')}</div>
 <div id="${prefix}-short-options" class="short-options" ${s.tipo_video==='shorts'?'':'hidden'}>
 <div class="config-fields">
 ${select('modo_shorts','Conteúdo na tela',[['animacoes','Animações para celular'],['fotos','Fotos em sequência'],['clipes','Fotos e clipes com narração']],s.modo_shorts||'animacoes')}
 ${select('composicao_shorts','Organização das figuras',[['equilibrada','Equilibrada · figuras lado a lado'],['coluna','Em coluna · uma abaixo da outra']],s.composicao_shorts||'equilibrada')}
 ${select('filtro_reels','Filtro da imagem ou clipe',[['original','Original'],['pb','Preto e branco'],['pb_contraste','Preto e branco · contraste'],['sepia','Sépia'],['quente','Quente'],['frio','Frio'],['cinema','Cinema'],['suave','Suave']],s.filtro_reels||'original')}
 ${select('legenda_shorts','Cor da palavra falada',[['amarelo','Amarelo'],['ciano','Ciano'],['branca','Branco'],['vermelho','Vermelho'],['verde','Verde'],['roxo','Roxo']],s.legenda_shorts||'amarelo')}
 ${select('efeito_legenda','Como a legenda aparece',[['destaque','Frase com palavra destacada'],['montagem','Montar a frase por palavras'],['maquina','Máquina de escrever']],s.efeito_legenda||'destaque')}
 ${select('posicao_legenda','Posição das legendas',[['inferior','Embaixo · área protegida'],['superior','Em cima'],['centro','Centro · sobre a mídia'],['alternada','Alternar posições · sobre a mídia']],s.posicao_legenda||'inferior')}
 </div><p class="small">O filtro afeta o visual. As legendas conservam suas próprias cores.</p>
 <details class="caption-library"><summary>Biblioteca de estilos de legenda · 8 modelos</summary><div class="caption-style-grid" role="group" aria-label="Estilo de legenda">
 ${[['impacto','Impacto','Grandes, com contorno forte'],['faixa_branca','Faixa branca','Texto escuro sobre branco'],['caixa_escura','Caixa escura','Fundo escuro de alto contraste'],['minimalista','Minimalista','Limpa, com caixa normal'],['documental','Documental','Serifada, leitura sóbria'],['neon','Neon','Contorno com cor'],['editorial','Editorial','Citação sobre papel claro'],['compacta','Compacta','Letras altas e condensadas']].map(([id,name,note])=>`<label class="caption-style-card"><input type="radio" name="${prefix}-modelo_legenda" value="${id}" ${(s.modelo_legenda||'impacto')===id?'checked':''}><span class="caption-template caption-${id}">Dê o <strong>primeiro</strong> passo</span><b>${name}</b><small>${note}</small></label>`).join('')}</div></details>
 <p class="short-caption-sample" aria-hidden="true"><span>UM PASSO</span> <strong>DE CADA VEZ</strong></p>
 <p class="small">Letras grandes com contorno, sincronizadas com a narração. As frases aparecem em blocos curtos e dão lugar à próxima. A composição Equilibrada agrupa figuras lado a lado e usa uma segunda linha quando necessário, com espaço próprio para as legendas.</p>
 <label class="check-row"><input id="${prefix}-roteiro_pronto" type="checkbox" ${s.roteiro_pronto?'checked':''}>Usar o texto enviado como narração pronta, sem reescrever com IA</label>
 <p class="small">Cole a narração completa na aba Texto ao criar o projeto. Você poderá editá-la por cena. Para fotos em sequência, adicione suas imagens na aba Arquivos; depois escolha a ordem abaixo. Música e voz são escolhidas nas configurações do vídeo. O modo Motivacional fica em Modo de locução.</p>
 ${reelsMediaFields(prefix,s)}
 <p class="small short-limit" role="status">O arquivo final precisa ter até 3 minutos para ser um Shorts no YouTube. A fala é preservada: se passar do limite, o Clareia avisa antes do envio.</p>
 </div></fieldset>`;
}
function shortVideoConfig(prefix){
 const root=$(prefix+'-video-kind');if(!root)return {};
 const type=root.querySelector('input[name="'+prefix+'-tipo_video"]:checked')?.value||'video';
 const result={tipo_video:type,formato:$(prefix+'-formato').value,...motivationConfig(prefix),...captionDisplayConfig(prefix)};
 for(const k of ['modo_shorts','composicao_shorts','legenda_shorts','efeito_legenda','posicao_legenda','filtro_reels','transicao_midias_shorts'])result[k]=$(prefix+'-'+k).value;
 result.modelo_legenda=root.querySelector('input[name="'+prefix+'-modelo_legenda"]:checked')?.value||'impacto';
 result.duracao_transicao_midias=Number($(prefix+'-duracao_transicao_midias').value);result.trechos_reels=readReelsCues(prefix);
 result.enquadramento_reels=$(prefix+'-enquadramento_reels').value;result.posicao_recorte_reels=$(prefix+'-posicao_recorte_reels').value;
 result.continuar_clipes=$(prefix+'-continuar_clipes').checked;
 result.roteiro_pronto=type==='shorts'&&$(prefix+'-roteiro_pronto').checked;
 if(type==='shorts'){
  result.formato='9:16';
  if(Number($(prefix+'-minutos').value)>3)throw Error('Para Reels / Shorts, escolha uma duração alvo de até 3 minutos. O texto não será cortado.');
  if(result.legendas_grandes&&result.modo_shorts==='animacoes'&&['centro','alternada'].includes(result.posicao_legenda))result.posicao_legenda='inferior';
 }
 const pool=$(prefix+'-photo-order'),photos=[...pool.querySelectorAll('[data-short-photo]')];
 const chosen=photos.filter(el=>el.querySelector('input').checked).map(el=>el.dataset.shortPhoto);
 result.midias_reels=result.modo_shorts==='clipes'?chosen:[];result.fotos_shorts=chosen.filter(n=>!(current?.videos||[]).includes(n));
 if(type==='shorts'&&result.modo_shorts!=='animacoes'&&photos.length&&!chosen.length)throw Error('Marque pelo menos uma mídia para a sequência.');
 return result;
}
function paintShortPhotos(prefix){
 const pool=$(prefix+'-photo-order');if(!pool||prefix!=='edit'||!current)return;
 const existing=[...pool.querySelectorAll('[data-short-photo]')];
 const saved=existing.length?existing.filter(el=>el.querySelector('input').checked).map(el=>el.dataset.shortPhoto):JSON.parse(pool.dataset.selected||'[]');
 const images=mediaNames(prefix);
 const order=[...existing.map(el=>el.dataset.shortPhoto),...saved,...images].filter((n,i,a)=>images.includes(n)&&a.indexOf(n)===i);
 pool.innerHTML=order.map((name,i)=>{const video=current.videos_meta?.[name],src='/api/projects/'+encodeURIComponent(current.id)+(video?'/media/'+encodeURIComponent(video.miniatura):'/images/'+encodeURIComponent(name));return `<div class="short-photo-row" data-short-photo="${esc(name)}"><label><input type="checkbox" ${saved.includes(name)||!existing.length&&!saved.length?'checked':''}><img loading="lazy" src="${src}" alt=""><span>${esc(mediaLabel(name))}${video?' · Clipe · '+Number(video.duracao_s).toFixed(1)+' s':''}</span></label><button type="button" class="secondary" data-photo-up aria-label="Mover mídia para cima" ${i===0?'disabled':''}>↑</button><button type="button" class="secondary" data-photo-down aria-label="Mover mídia para baixo" ${i===order.length-1?'disabled':''}>↓</button></div>`}).join('')||'<p class="small">Adicione fotos ou clipes para montar a sequência.</p>';
 const buttons=()=>{[...pool.children].filter(el=>el.matches('[data-short-photo]')).forEach((el,i)=>{el.querySelector('[data-photo-up]').disabled=i===0;el.querySelector('[data-photo-down]').disabled=i===pool.children.length-1})};
 pool.querySelectorAll('[data-photo-up],[data-photo-down]').forEach(b=>b.onclick=()=>{const row=b.closest('[data-short-photo]');if(b.hasAttribute('data-photo-up')&&row.previousElementSibling)row.previousElementSibling.before(row);else if(row.nextElementSibling)row.nextElementSibling.after(row);buttons()});
 paintReelsFraming(prefix);
}
function bindShortVideo(prefix){
 const root=$(prefix+'-video-kind');if(!root)return;
 const update=e=>{
  const short=root.querySelector('input[name="'+prefix+'-tipo_video"]:checked').value==='shorts',photos=$(prefix+'-modo_shorts').value!=='animacoes';
  $(prefix+'-short-options').hidden=!short;$(prefix+'-short-photos').hidden=!photos;
  $(prefix+'-composicao_shorts').closest('label').hidden=photos;
  const format=$(prefix+'-formato');format.disabled=short;
  if(short)format.value='9:16';else if(e?.target?.name===prefix+'-tipo_video')format.value='16:9';
  $(prefix+'-minutos').max=short?'3':'';
  const position=$(prefix+'-posicao_legenda');
  for(const option of position.options)option.disabled=!photos&&['centro','alternada'].includes(option.value);
  if(!photos&&['centro','alternada'].includes(position.value))position.value='inferior';
  const large=$(prefix+'-legendas_grandes').checked;root.querySelector('.caption-library').hidden=!large;root.querySelector('.short-caption-sample').hidden=!large;root.dataset.captionColor=$(prefix+'-legenda_shorts').value;
  root.dataset.captionPreset=root.querySelector('input[name="'+prefix+'-modelo_legenda"]:checked')?.value||'impacto';
  const animationButton=document.querySelector('[data-preview="'+prefix+'"]');if(animationButton)animationButton.hidden=photos&&short;
  if(e?.target?.id===prefix+'-modo_shorts'){paintShortPhotos(prefix);paintReelsCues(prefix,readReelsCues(prefix).filter(c=>mediaNames(prefix).includes(c.arquivo)))}
  paintMotivation(prefix);
 };
 bindCaptionDisplay(prefix);root.addEventListener('change',update);bindMotivation(prefix);update();paintShortPhotos(prefix);bindReelsMedia(prefix);
}
