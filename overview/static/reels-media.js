// Explicit cuts follow the saved narration's actual phrase segmentation.
function reelsMediaFields(prefix,s){
 const transitions=[['nenhuma','Corte direto'],['dissolver','Dissolver'],['escurecer','Pelo preto'],['clarear','Pelo branco'],['deslizar_esquerda','Deslizar'],['zoom','Aproximar'],['revelar','Revelar']];
 return `<div id="${prefix}-short-photos" ${['fotos','clipes'].includes(s.modo_shorts)?'':'hidden'}><h4>Biblioteca de fotos e clipes</h4><p class="small">Marque e ordene as mídias. Na sequência de clipes, a reprodução continua entre as cenas e só volta ao início quando a lista termina. O áudio original fica desligado no vídeo final: a voz e a música vêm das configurações do projeto.</p><div class="config-fields"><label>Enquadramento das fotos e clipes<select id="${prefix}-enquadramento_reels">${opt([['inteira','Imagem inteira · fundo suave'],['preencher','Recortar para preencher · sem deformar'],['esticar','Redimensionar para a tela · pode deformar']],s.enquadramento_reels||'inteira')}</select></label><label>Posição do recorte<select id="${prefix}-posicao_recorte_reels">${opt([['centro','Centro'],['esquerda','Manter o lado esquerdo'],['direita','Manter o lado direito'],['superior','Manter a parte de cima'],['inferior','Manter a parte de baixo']],s.posicao_recorte_reels||'centro')}</select></label></div><p class="small">Imagem inteira conserva o formato original. Recortar preenche o celular preservando as proporções; redimensionar ocupa toda a tela alterando as proporções. Os trechos manuais podem usar outro enquadramento.</p><label class="check-row"><input type="checkbox" id="${prefix}-continuar_clipes" ${s.continuar_clipes!==false?'checked':''}>Continuar os clipes entre as cenas</label><p class="small">Com um clipe, ele continua de onde parou. Com vários clipes, a sequência automática reproduz cada um até o fim antes de passar ao próximo. Desmarcado: cada cena começa o clipe novamente. Em trechos manuais ou com fotos intercaladas, o aplicativo guarda a posição de cada clipe.</p>${prefix==='edit'?`<details class="reels-fit-preview"><summary>Ver enquadramento antes de renderizar</summary><label>Mídia da prévia<select id="${prefix}-framing-media"></select></label><div class="reels-phone-preview" id="${prefix}-framing-preview"><img class="reels-fit-background" alt=""><img class="reels-fit-foreground" alt="Prévia do enquadramento"></div><p class="small">Mostra o enquadramento geral. As legendas e os cortes específicos são aplicados na renderização.</p></details>`:''}<button type="button" class="secondary" data-youtube-clips="${prefix}">▶ Buscar e baixar clipes do YouTube</button><div id="${prefix}-youtube-clips-pending"></div>
 ${prefix==='edit'?`<button type="button" class="secondary" id="${prefix}-media-add">＋ Adicionar fotos e clipes</button><input type="file" id="${prefix}-media-files" accept="image/png,image/jpeg,image/webp,.mp4,.mov,.m4v,.webm,.mkv" multiple hidden><p class="small" id="${prefix}-media-status" role="status"></p>`:'<p class="small">Adicione as mídias na aba Arquivos. Depois de criar o roteiro, você poderá ajustar a ordem e os cortes. Até 20 MB por foto e 200 MB por clipe.</p>'}
 <div id="${prefix}-photo-order" class="short-photo-order" data-selected="${esc(JSON.stringify(s.modo_shorts==='clipes'?s.midias_reels||[]:s.fotos_shorts||[]))}"></div>
 <div class="config-fields"><label>Transição na troca de mídia<select id="${prefix}-transicao_midias_shorts">${opt(transitions,s.transicao_midias_shorts||'dissolver')}</select></label><label>Duração da troca<select id="${prefix}-duracao_transicao_midias">${opt([[.3,'0,3 s'],[.6,'0,6 s'],[1,'1 s'],[1.5,'1,5 s'],[2,'2 s']],s.duracao_transicao_midias??.6)}</select></label></div><p class="small">Estas passagens trocam fotos e clipes dentro da fala. A transição entre cenas continua sendo escolhida separadamente.</p>
 ${prefix==='edit'?`<details class="reels-cue-panel"><summary>Escolher onde cada mídia aparece no roteiro</summary><p class="small">Adicione trechos e escolha a cena e a frase em que cada um começa. Ele continua até o próximo trecho ou até o fim da cena. A primeira mídia de cada cena deve começar na primeira frase; cenas sem trechos usam a sequência automática. Salve alterações do roteiro para atualizar a lista de frases.</p><div id="${prefix}-media-cues" data-cues="${esc(JSON.stringify(s.trechos_reels||[]))}"></div><button type="button" class="secondary" id="${prefix}-cue-add">＋ Posicionar mídia no roteiro</button></details>`:''}</div>`;
}
function mediaNames(prefix){
 if(!current||prefix!=='edit')return [];
 return [...(current.imagens||[]),...($(prefix+'-modo_shorts').value==='clipes'?current.videos||[]:[])];
}
function mediaLabel(name){return current.videos_meta?.[name]?.nome_original||current.imagens_meta?.[name]?.nome_original||name}
function readReelsCues(prefix){
 const pool=$(prefix+'-media-cues');if(!pool)return [];
 return [...pool.querySelectorAll('[data-media-cue]')].map(el=>{
  const v=k=>el.querySelector('[data-cue-key="'+k+'"]').value;
  return {arquivo:v('arquivo'),cena:Number(v('cena')),frase:Number(v('frase')),entrada_s:Number(v('entrada_s')||0),saida_s:v('saida_s')===''?null:Number(v('saida_s')),ajuste:v('ajuste'),posicao_recorte:v('posicao_recorte'),reiniciar:v('reiniciar')==='true',fim:v('fim'),transicao:v('transicao')};
 });
}
function paintReelsCues(prefix,cues){
 const pool=$(prefix+'-media-cues');if(!pool||!current)return;
 cues=cues??(pool.dataset.ready?readReelsCues(prefix):JSON.parse(pool.dataset.cues||'[]'));pool.dataset.ready='1';
 const names=mediaNames(prefix),select=(key,label,items,value)=>`<label>${label}<select data-cue-key="${key}">${opt(items,value)}</select></label>`;
 pool.innerHTML=cues.map((cue,i)=>`<fieldset class="reels-cue" data-media-cue><legend>Trecho ${i+1}</legend><div class="config-fields">
 ${select('arquivo','Foto ou clipe',names.map(n=>[n,mediaLabel(n)]),cue.arquivo)}
 ${select('cena','Cena',(current.cenas||[]).map((s,j)=>[j,(j+1)+' · '+s.titulo]),cue.cena)}
 ${select('frase','Começa nesta frase',(current.frases_midias?.[cue.cena]||[]).map((s,j)=>[j,(j+1)+' · '+s]),cue.frase)}
 ${select('ajuste','Enquadramento',[['herdar','Usar enquadramento geral'],['inteira','Imagem inteira · fundo suave'],['preencher','Recortar para preencher'],['esticar','Redimensionar para a tela']],cue.ajuste||'herdar')}
 ${select('posicao_recorte','Posição do recorte',[['herdar','Usar posição geral'],['centro','Centro'],['esquerda','Esquerda'],['direita','Direita'],['superior','Parte de cima'],['inferior','Parte de baixo']],cue.posicao_recorte||'herdar')}
 </div><div class="config-fields reels-clip-controls"><label>Início no clipe · segundos<input data-cue-key="entrada_s" type="number" min="0" step="0.05" value="${Number(cue.entrada_s)||0}"></label><label>Fim no clipe · segundos<input data-cue-key="saida_s" type="number" min="0.05" step="0.05" placeholder="Até o final" value="${cue.saida_s??''}"></label>
 ${select('fim','Se o clipe acabar antes da fala',[['repetir','Repetir o trecho'],['segurar','Segurar o último quadro']],cue.fim||'repetir')}
 ${select('reiniciar','Posição de reprodução',[['false','Continuar de onde este clipe parou'],['true','Reiniciar no início do corte']],String(cue.reiniciar===true))}</div>
 ${select('transicao','Entrada desta mídia',[['herdar','Usar transição da troca de mídia'],['nenhuma','Corte direto'],['dissolver','Dissolver'],['escurecer','Pelo preto'],['clarear','Pelo branco'],['deslizar_esquerda','Deslizar'],['zoom','Aproximar'],['revelar','Revelar']],cue.transicao||'herdar')}
 <button type="button" class="secondary" data-cue-remove>Remover trecho</button></fieldset>`).join('')||'<p class="small">Sem trechos manuais: as mídias marcadas passam na ordem da biblioteca.</p>';
 pool.querySelectorAll('[data-media-cue]').forEach(el=>{
  const field=k=>el.querySelector('[data-cue-key="'+k+'"]');
  const videoControls=()=>{el.querySelector('.reels-clip-controls').hidden=!(current.videos||[]).includes(field('arquivo').value)};
  field('arquivo').onchange=videoControls;videoControls();
  field('cena').onchange=()=>{field('frase').innerHTML=opt((current.frases_midias?.[Number(field('cena').value)]||[]).map((s,j)=>[j,(j+1)+' · '+s]),0)};
  el.querySelector('[data-cue-remove]').onclick=()=>{const cues=readReelsCues(prefix);cues.splice([...pool.querySelectorAll('[data-media-cue]')].indexOf(el),1);paintReelsCues(prefix,cues)};
 });
}
function bindReelsMedia(prefix){
 window.bindYouTubeClips?.(prefix);
 const framing=()=>paintReelsFraming(prefix);
 $(prefix+'-enquadramento_reels')?.addEventListener('change',framing);
 $(prefix+'-posicao_recorte_reels')?.addEventListener('change',framing);
 $(prefix+'-framing-media')?.addEventListener('change',framing);framing();
 if(prefix!=='edit')return;
 const add=$(prefix+'-media-add'),input=$(prefix+'-media-files');
 if(add)add.onclick=()=>input.click();
 if(input)input.onchange=()=>action(async()=>{
  const pid=current.id,files=[...input.files];if(!files.length)return;
  const note=$(prefix+'-media-status');add.disabled=true;note.textContent='Importando mídias e preparando miniaturas…';
  try{
   const data=new FormData();files.forEach(f=>data.append('files',f));const result=await api('/api/projects/'+pid+'/reels/media',{method:'POST',body:data});
   if(current?.id!==pid)return;
   Object.assign(current,result);
   if(result.adicionadas.some(n=>(result.videos||[]).includes(n))&&$(prefix+'-modo_shorts').value==='fotos'){
    $(prefix+'-modo_shorts').value='clipes';$(prefix+'-modo_shorts').dispatchEvent(new Event('change',{bubbles:true}));
   }
   paintShortPhotos(prefix);paintReelsCues(prefix);
   await save();await refresh();note.textContent='Mídias adicionadas. Escolha a ordem ou posicione os trechos no roteiro.';
  }catch(e){note.textContent=e.message;throw e}finally{add.disabled=false;input.value=''}
 });
 const cueAdd=$(prefix+'-cue-add');if(cueAdd)cueAdd.onclick=()=>action(async()=>{
  const names=mediaNames(prefix);if(!names.length)throw Error('Adicione uma foto ou clipe primeiro.');
  if(!current.cenas.length)throw Error('Gere o roteiro antes de posicionar mídias.');
  const cues=readReelsCues(prefix),last=cues.at(-1),scene=last?.cena||0;
  cues.push({arquivo:names[cues.length%names.length],cena:scene,frase:last?Math.min(last.frase+1,(current.frases_midias?.[scene]?.length||1)-1):0});paintReelsCues(prefix,cues);
 });
 paintReelsCues(prefix);
}

function paintReelsFraming(prefix){
 const mode=$(prefix+'-enquadramento_reels')?.value||'inteira',position=$(prefix+'-posicao_recorte_reels');
 if(position)position.closest('label').hidden=mode!=='preencher';
 const select=$(prefix+'-framing-media'),preview=$(prefix+'-framing-preview');if(!select||!preview||!current)return;
 const names=mediaNames(prefix),before=select.value;
 select.innerHTML=opt(names.map(n=>[n,mediaLabel(n)]),before||names[0]);
 const name=select.value;preview.hidden=!name;if(!name)return;
 const poster=current.videos_meta?.[name]?.miniatura;
 const url='/api/projects/'+encodeURIComponent(current.id)+(poster?'/media/'+encodeURIComponent(poster):'/images/'+encodeURIComponent(name));
 preview.dataset.fit=mode;
 const foreground=preview.querySelector('.reels-fit-foreground');foreground.src=url;
 foreground.style.objectPosition={esquerda:'0% 50%',direita:'100% 50%',superior:'50% 0%',inferior:'50% 100%'}[position?.value]||'50% 50%';
 preview.querySelector('.reels-fit-background').src=url;
}
