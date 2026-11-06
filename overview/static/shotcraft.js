// Manual recipe IDs select reviewed local components; AI supplies data only.
function shotcraftFigureSelectionFields(prefix,s){
 return `<label>Seleção das figuras<select id="${prefix}-shotcraft_selecao_figuras" aria-describedby="${prefix}-shotcraft-figure-selection-note">${opt([['tematico','Flexível por tema · continuar o vídeo'],['rigoroso','Rigoroso por trecho · revisar quando faltar']],s.shotcraft_selecao_figuras||'tematico')}</select></label><p class="small" id="${prefix}-shotcraft-figure-selection-note"></p>`;
}
function updateShotcraftFigureSelection(prefix){
 const note=$(prefix+'-shotcraft-figure-selection-note');if(!note)return;
 note.textContent=$(prefix+'-shotcraft_selecao_figuras')?.value==='rigoroso'?'Exige uma figura ou metáfora apoiada em cada trecho. Se faltar, interrompe a geração e indica a cena para revisão.':'Busca primeiro a figura específica. Se não encontrar, usa uma ilustração mais ampla do tema para continuar a renderização, sem cartões vazios. Suas escolhas manuais válidas têm prioridade.';
}
function shotcraftFields(prefix,s={}){
 const c=studioCatalog.shotcraft||{},recipes=c.receitas||[];
 return `<fieldset class="shotcraft-settings" id="${prefix}-shotcraft-options" ${s.animacao==='shotcraft'?'':'hidden'}><legend>Biblioteca de animações · ShotCraft</legend><p class="small">${recipes.length} movimentos em ${(c.grupos||[]).length} categorias. Escolha um padrão para o projeto e, se quiser, outro para cada cena. A IA organiza títulos e elementos dentro da sua escolha. As animações anteriores continuam disponíveis.</p><div class="config-fields"><label>Modelo de animação<select id="${prefix}-shotcraft_modelo">${opt((c.modelos||[]).map(x=>[x.id,x.nome]),s.shotcraft_modelo||'auto')}</select></label><label>Paleta de cores<select id="${prefix}-shotcraft_estilo">${opt((c.estilos||[]).map(x=>[x.id,x.nome]),s.shotcraft_estilo||'editorial')}</select></label><label>Acabamento visual<select id="${prefix}-shotcraft_acabamento">${opt((c.acabamentos||[]).map(x=>[x.id,x.nome]),s.shotcraft_acabamento||'vidro_avancado')}</select></label><label>Intensidade dos movimentos<select id="${prefix}-shotcraft_intensidade">${opt((c.intensidades||[]).map(x=>[x.id,x.nome]),s.shotcraft_intensidade||'equilibrada')}</select></label><label>Movimento do projeto<select id="${prefix}-shotcraft_receita">${opt(recipes.map(x=>[x.id,x.nome]),s.shotcraft_receita==='auto'||!s.shotcraft_receita?'titulo_marcado':s.shotcraft_receita)}</select></label></div>${shotcraftFigureSelectionFields(prefix,s)}<label>Orientação visual · opcional<textarea id="${prefix}-shotcraft_orientacao" rows="2" maxlength="600" placeholder="Ex.: rótulos curtos, foco na imagem da cena, destaque para a conclusão.">${esc(s.shotcraft_orientacao||'')}</textarea></label><p class="small">O movimento permanece o escolhido. Conexões e comparações usam apenas relações presentes na fala. Disponível em vídeo comum e Reels com animações; fotos e clipes mantêm sua sequência de mídias.</p><div class="toolbar"><button type="button" class="secondary" data-shotcraft-library="${prefix}">▷ Explorar ${recipes.length} movimentos</button>${prefix==='edit'?'<button type="button" class="secondary" data-shotcraft-plan>Ver conteúdo das animações</button>':''}</div>${threeOptionsField(prefix,s)}${stageAIFields(prefix+'-shotcraft',s.shotcraft_ia,'Usar uma IA específica para organizar o conteúdo visual','Prepara títulos, rótulos e foco dentro do movimento escolhido por você. Mantém a narração aprovada.')}</fieldset>`;
}
function shotcraftConfig(prefix,validate=true){
 return {three_options:readThreeOptions(prefix),shotcraft_selecao_figuras:$(prefix+'-shotcraft_selecao_figuras')?.value||'tematico',shotcraft_acabamento:$(prefix+'-shotcraft_acabamento')?.value||'vidro_avancado',shotcraft_modelo:$(prefix+'-shotcraft_modelo')?.value||'auto',shotcraft_estilo:$(prefix+'-shotcraft_estilo')?.value||'editorial',shotcraft_intensidade:$(prefix+'-shotcraft_intensidade')?.value||'equilibrada',shotcraft_receita:$(prefix+'-shotcraft_receita')?.value||'titulo_marcado',shotcraft_orientacao:$(prefix+'-shotcraft_orientacao')?.value.trim()||'',shotcraft_ia:stageAIRead(prefix+'-shotcraft',validate&&$(prefix+'-animacao')?.value==='shotcraft')};
}
function updateShotcraftRecipes(prefix){
 const model=$(prefix+'-shotcraft_modelo')?.value||'auto',select=$(prefix+'-shotcraft_receita');if(!select)return;
 const before=select.value,recipes=studioCatalog.shotcraft.receitas.filter(r=>model==='auto'||r.modelo===model);
 select.innerHTML=opt(recipes.map(r=>[r.id,r.nome]),recipes.some(r=>r.id===before)?before:recipes[0].id);
}
function updateShotcraft(prefix){
 const active=$(prefix+'-animacao')?.value==='shotcraft',box=$(prefix+'-shotcraft-options');if(box)box.hidden=!active;
 const artButton=box?.querySelector('[data-shotcraft-figures]');if(artButton){const recipe=studioCatalog.shotcraft.receitas.find(r=>r.id===$(prefix+'-shotcraft_receita')?.value);artButton.hidden=!recipe?.figuras;artButton.textContent=recipe?.acervo3d?'▦ Conhecer '+studioCatalog.shotcraft.figuras3d.length+' objetos 3D':'▦ Conhecer '+studioCatalog.shotcraft.figuras.length+' figuras';}
 document.querySelectorAll('[data-scene]').forEach(el=>{const choice=el.querySelector('[data-key="animacao"]')?.value,effective=choice==='herdar'?$('edit-animacao')?.value:choice;
  const control=el.querySelector('[data-shotcraft-scene]');if(control){control.hidden=effective!=='shotcraft';const selected=el.querySelector('[data-key="shotcraft_receita"]').value;const recipe=studioCatalog.shotcraft.receitas.find(r=>r.id===(['herdar','auto'].includes(selected)?$('edit-shotcraft_receita').value:selected));control.querySelector('[data-shotcraft-figure-controls]')?.toggleAttribute('hidden',!recipe?.figuras);}
  el.querySelectorAll('[data-scene-vox]').forEach(control=>control.hidden=effective!=='colagem_documental');
 });
}
function bindShotcraft(prefix){
 $(prefix+'-shotcraft_selecao_figuras')?.addEventListener('change',()=>updateShotcraftFigureSelection(prefix));updateShotcraftFigureSelection(prefix);
 $(prefix+'-shotcraft_receita')?.addEventListener('change',()=>updateShotcraft(prefix));bindThreeLibrary(prefix);bindStageAI(prefix+'-shotcraft');$(prefix+'-shotcraft_modelo')?.addEventListener('change',()=>{updateShotcraftRecipes(prefix);updateShotcraft(prefix)});updateShotcraftRecipes(prefix);
 document.querySelectorAll(`[data-shotcraft-library="${prefix}"]`).forEach(b=>b.onclick=()=>openShotcraftLibrary(prefix));
 const box=$(prefix+'-shotcraft-options');if(box&&!box.querySelector('[data-shotcraft-figures]')){const button=document.createElement('button');button.type='button';button.className='secondary';button.dataset.shotcraftFigures='';button.textContent='▦ Conhecer '+studioCatalog.shotcraft.figuras.length+' figuras';box.querySelector('.toolbar').append(button);button.onclick=()=>openShotcraftFigures(null,prefix)}
 document.querySelectorAll('[data-shotcraft-plan]').forEach(b=>b.onclick=()=>action(showShotcraftPlan));updateShotcraft(prefix);
}
function shotcraftDialog(){
 if($('shotcraft-dialog'))return $('shotcraft-dialog');
 const dialog=document.createElement('dialog');dialog.id='shotcraft-dialog';dialog.setAttribute('aria-labelledby','shotcraft-title');
 dialog.innerHTML='<div class="dialog-head"><h2 id="shotcraft-title">Biblioteca de animações</h2><button type="button" class="secondary" aria-label="Fechar biblioteca de animações">×</button></div><div id="shotcraft-dialog-content"></div>';
 dialog.querySelector('button').onclick=()=>dialog.close();dialog.addEventListener('close',()=>dialog.querySelectorAll('iframe').forEach(frame=>frame.src='about:blank'));document.body.append(dialog);return dialog;
}
function shotcraftPreviewURL(prefix,id,followRecipe=false){
 const c=shotcraftConfig(prefix,false),short=document.querySelector(`input[name="${prefix}-tipo_video"]:checked`)?.value==='shorts';
 let recipe=studioCatalog.shotcraft.receitas.find(r=>r.id===id)||studioCatalog.shotcraft.receitas[0];
 if(!followRecipe&&c.shotcraft_modelo!=='auto'&&recipe.modelo!==c.shotcraft_modelo)recipe=studioCatalog.shotcraft.receitas.find(r=>r.modelo===c.shotcraft_modelo);
 return '/api/shotcraft/recipes/'+encodeURIComponent(recipe.id)+'/preview?'+new URLSearchParams({estilo:c.shotcraft_estilo,acabamento:c.shotcraft_acabamento,intensidade:c.shotcraft_intensidade,vertical:String(short),modelo:recipe.modelo});
}
function openShotcraftLibrary(prefix,sceneElement=null){
 const dialog=shotcraftDialog(),c=studioCatalog.shotcraft;
 let initial=sceneElement?.querySelector('[data-key="shotcraft_receita"]').value||$(prefix+'-shotcraft_receita').value;if(['herdar','auto'].includes(initial))initial=$(prefix+'-shotcraft_receita').value;
 $('shotcraft-title').textContent=`${c.receitas.length} movimentos · escolha manual`;
 $('shotcraft-dialog-content').innerHTML=`<p class="small">${sceneElement?'Aplicar somente à cena selecionada.':'Aplicar como padrão do projeto.'} Cada prévia usa o mesmo motor da exportação, sem IA nem voz. A primeira preparação leva mais tempo; as demonstrações prontas ficam em cache.</p><div class="shotcraft-filters"><label>Categoria<select id="shotcraft-group">${opt([['','Todas as categorias'],...c.grupos.map(g=>[g.id,g.nome])],'')}</select></label><label>Buscar movimento<input id="shotcraft-search" type="search" placeholder="Ex.: vidro, carrossel, monitor…"></label></div><div class="shotcraft-library"><nav aria-label="Escolher movimento"></nav><div class="shotcraft-demo"><p id="shotcraft-demo-status" role="status">Preparando demonstração…</p><img id="shotcraft-demo-poster" alt="Exemplo de composição do movimento escolhido"><img id="shotcraft-demo-image" hidden alt="Demonstração animada do movimento escolhido"><iframe id="shotcraft-demo-3d" title="Exemplo interativo 3D" hidden></iframe><h3 id="shotcraft-demo-title"></h3><p id="shotcraft-demo-description"></p><p class="small" id="shotcraft-demo-use"></p><div class="toolbar"><button type="button" class="primary" id="shotcraft-use">${sceneElement?'Usar nesta cena':'Usar no projeto'}</button><button type="button" class="secondary" id="shotcraft-retry">Recarregar prévia</button><a id="shotcraft-source" target="_blank" rel="noopener noreferrer">Inspiração e receita ↗</a></div></div></div>`;
 let selected=c.receitas.some(r=>r.id===initial)?initial:c.receitas[0].id;
 const show=id=>{
  selected=id;const r=c.receitas.find(r=>r.id===id),img=$('shotcraft-demo-image'),poster=$('shotcraft-demo-poster'),note=$('shotcraft-demo-status');
  dialog.querySelectorAll('[data-shotcraft-recipe]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.shotcraftRecipe===id)));
  $('shotcraft-demo-title').textContent=r.nome;$('shotcraft-demo-description').textContent=r.descricao;
  $('shotcraft-demo-use').textContent='Modelo: '+c.modelos.find(m=>m.id===r.modelo).nome+'. Quando usar: '+r.usar;$('shotcraft-source').href=r.fonte;
  const three=$('shotcraft-demo-3d');three.hidden=!r.modelo3d;if(r.modelo3d){three.src='/3d/?embed=1&model='+encodeURIComponent(r.modelo3d)+'&format='+(document.querySelector(`input[name="${prefix}-tipo_video"]:checked`)?.value||'video')+'&movement='+encodeURIComponent(readThreeOptions(prefix).movement||'padrao');img.hidden=true;poster.hidden=true;note.textContent='Modelo 3D real · arraste para girar';}else{three.src='about:blank';
  note.textContent='Exemplo de composição · preparando a demonstração animada…';img.hidden=true;poster.hidden=false;const previewURL=shotcraftPreviewURL(prefix,id,true);poster.src=previewURL.replace('/preview?','/poster?');
  img.onload=()=>{img.hidden=false;poster.hidden=true;note.textContent='Demonstração animada pronta · sem áudio'};
  img.onerror=()=>{img.hidden=true;poster.hidden=false;note.textContent='Exemplo de composição pronto. A animação será preparada quando o processamento estiver livre; use Recarregar prévia.'};img.src=shotcraftPreviewURL(prefix,id,true);}
  $('shotcraft-use').onclick=()=>{
   if(sceneElement){sceneElement.querySelector('[data-key="animacao"]').value='shotcraft';const field=sceneElement.querySelector('[data-key="shotcraft_receita"]');field.value=id;field.dispatchEvent(new Event('change',{bubbles:true}));updateShotcraft('edit')}
   else{$(prefix+'-animacao').value='shotcraft';$(prefix+'-shotcraft_modelo').value=r.modelo;updateShotcraftRecipes(prefix);$(prefix+'-shotcraft_receita').value=id;$(prefix+'-animacao').dispatchEvent(new Event('change'))}
   dialog.close();toast(sceneElement?'Movimento da cena escolhido. Salve a revisão para aplicar.':'Movimento do projeto escolhido. Gere uma prévia para conferir com sua narração.');
  };
 };
 const list=()=>{
  const group=$('shotcraft-group').value,query=$('shotcraft-search').value.toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const matches=c.receitas.filter(r=>(!group||r.grupo===group)&&(r.nome+' '+r.descricao+' '+r.categoria).toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').includes(query));
  const nav=dialog.querySelector('nav');nav.innerHTML=c.grupos.map(g=>{const rows=matches.filter(r=>r.grupo===g.id);return rows.length?`<h3>${esc(g.nome)}</h3>${rows.map(r=>`<button type="button" class="secondary" data-shotcraft-recipe="${r.id}" aria-pressed="${r.id===selected}"><b>${esc(r.nome)}</b><small>${esc(c.modelos.find(m=>m.id===r.modelo).nome.split(' · ')[0])}</small></button>`).join('')}`:''}).join('')||'<p>Nenhum movimento encontrado.</p>';
  nav.querySelectorAll('[data-shotcraft-recipe]').forEach(b=>b.onclick=()=>show(b.dataset.shotcraftRecipe));
 };
 $('shotcraft-group').onchange=list;$('shotcraft-search').oninput=list;$('shotcraft-retry').onclick=()=>show(selected);list();show(selected);dialog.showModal();
}
async function showShotcraftPlan(){
 if(!current)return;const report=await api('/api/projects/'+current.id+'/shotcraft'),dialog=shotcraftDialog(),c=studioCatalog.shotcraft;
 $('shotcraft-title').textContent='Conteúdo dentro das suas animações';
 $('shotcraft-dialog-content').innerHTML=`<p class="small">${esc(report.aviso)}</p>${report.cenas.map(s=>`<section class="shotcraft-report"><h3>${s.cena} · ${esc(s.titulo)}</h3>${s.pronto?s.momentos.map(b=>`<article><b>Frase ${b.frase+1} · ${esc(c.receitas.find(r=>r.id===b.receita)?.nome||b.receita)}</b><small>${esc(c.modelos.find(m=>m.id===b.linguagem)?.nome||'')}</small><p>${esc(b.titulo)}</p><p class="small">${esc(b.motivo||'Movimento escolhido por você.')}</p></article>`).join(''):'<p>Gere uma prévia desta cena ou renderize para preparar seu conteúdo visual.</p>'}</section>`).join('')||'<p>Escolha Novos modelos · ShotCraft no projeto ou em uma cena.</p>'}`;dialog.showModal();
}
function addShotcraftSceneControl(el,scene){
 const label=document.createElement('div');label.dataset.shotcraftScene='';
 label.innerHTML='<label>Movimento ShotCraft desta cena<select data-key="shotcraft_receita">'+opt([['herdar','Usar o do projeto'],...studioCatalog.shotcraft.receitas.map(r=>[r.id,r.nome])],scene.shotcraft_receita==='auto'?'herdar':scene.shotcraft_receita||'herdar')+'</select></label><button type="button" class="secondary" data-scene-library>▷ Escolher na biblioteca</button><label>Figuras preferidas · opcional<input data-key="shotcraft_figuras" maxlength="600" placeholder="Automáticas conforme a frase" value="'+esc(scene.shotcraft_figuras||'')+'"></label><small>Vazio: a IA escolhe pelo contexto. Escolha até quatro figuras e defina sua distribuição na cena.</small><button type="button" class="secondary" data-scene-figures>▦ Escolher figuras</button>';
 const controls=document.createElement('div');controls.dataset.shotcraftFigureControls='';
 const field=label.querySelector('[data-key="shotcraft_figuras"]').closest('label'),help=label.querySelector('small'),button=label.querySelector('[data-scene-figures]');
 controls.append(field,help,button);help.textContent='Escolha até quatro figuras. Por padrão, elas dividem igualmente o tempo real desta cena.';
 controls.insertAdjacentHTML('beforeend','<label>Distribuição das figuras<select data-key="distribuicao_figuras">'+opt([['tempo_igual','Tempo igual na cena · uma após a outra'],['por_elemento','Por posição nos elementos · simultâneas']],scene.distribuicao_figuras||'tempo_igual')+'</select></label>');label.append(controls);
 label.insertAdjacentHTML('beforeend','<p class="small">A imagem de referência escolhida acima fica em destaque; a animação se organiza ao lado dela no vídeo comum ou abaixo dela no Reels. Sem imagem, o modelo mantém sua composição original.</p>');
 el.querySelector('.scene-body>div:last-child').append(label);label.querySelector('button').onclick=()=>openShotcraftLibrary('edit',el);
 label.querySelector('[data-scene-figures]').onclick=()=>openShotcraftFigures(el);
 addThreeSceneControl(el,scene);
 el.querySelector('[data-key="animacao"]').addEventListener('change',()=>updateShotcraft('edit'));
 el.querySelector('[data-key="shotcraft_receita"]').addEventListener('change',()=>updateShotcraft('edit'));
}

function openShotcraftFigures(sceneElement=null,prefix='edit'){
 const dialog=shotcraftDialog(),field=sceneElement?.querySelector('[data-key="shotcraft_figuras"]');
 let selectedRecipe=sceneElement?.querySelector('[data-key="shotcraft_receita"]').value||$(prefix+'-shotcraft_receita')?.value;
 if(['herdar','auto'].includes(selectedRecipe))selectedRecipe=$(prefix+'-shotcraft_receita')?.value;
 const meshArt=studioCatalog.shotcraft.receitas.find(r=>r.id===selectedRecipe)?.acervo3d;
 const c={...studioCatalog.shotcraft,figuras:studioCatalog.shotcraft.figuras.filter(r=>!meshArt||studioCatalog.shotcraft.figuras3d.includes(r.id))};
 let selected=(field?.value||'').split(';').map(x=>x.trim()).filter(x=>c.figuras.some(r=>r.id===x)).slice(0,4);
 $('shotcraft-title').textContent=c.figuras.length+(meshArt?' objetos · acervo 3D real':' figuras · acervo ShotCraft');
 $('shotcraft-dialog-content').innerHTML=`<p class="small">Ilustrações vetoriais locais, independentes do estilo Vox. A IA escolhe pelo objeto e pela frase, sem trocar seu modelo de animação. ${$(prefix+'-shotcraft_selecao_figuras')?.value==='rigoroso'?'No modo rigoroso, a falta de figura interrompe a geração e indica a cena para revisão.':'No modo flexível, a seleção usa figuras mais amplas do tema quando falta uma correspondência específica e continua a renderização.'} ${field?'Escolha até quatro figuras para fixar nesta cena.':'Para fixar figuras, use Escolher figuras dentro de uma cena.'}</p><div class="shotcraft-filters"><label>Assunto<select id="shotcraft-art-group">${opt([['','Todos os assuntos'],...c.grupos_figuras.map(g=>[g.id,g.nome])],'')}</select></label><label>Buscar figura<input id="shotcraft-art-search" type="search" placeholder="Ex.: memória, igreja, castelo, fantasma…"></label></div><p id="shotcraft-art-selected" class="small" role="status"></p><div class="shotcraft-art-grid"></div><div class="toolbar">${field?'<button type="button" class="primary" id="shotcraft-art-apply">Usar figuras escolhidas</button><button type="button" class="secondary" id="shotcraft-art-auto">Usar seleção por contexto</button>':''}<a href="https://github.com/jdecked/twemoji" target="_blank" rel="noopener noreferrer">Ilustrações Twemoji · CC BY 4.0 ↗</a></div><p class="small">As figuras são ilustrações, não fotografias históricas. Os créditos das figuras utilizadas acompanham o vídeo exportado.</p>`;
 const fold=x=>x.toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 const status=()=>{$('shotcraft-art-selected').textContent=field?(selected.length?'Selecionadas: '+selected.map(id=>c.figuras.find(r=>r.id===id).nome).join(' · '):'Nenhuma figura fixada · seleção pelo contexto'):'Escolha um assunto ou busque pelo nome.'};
 const draw=()=>{const group=$('shotcraft-art-group').value,q=fold($('shotcraft-art-search').value);
  const rows=c.figuras.filter(r=>(!group||r.grupo===group)&&fold(r.nome+' '+r.termos.join(' ')).includes(q));
  dialog.querySelector('.shotcraft-art-grid').innerHTML=rows.map(r=>`<button type="button" class="secondary shotcraft-art" data-figure="${r.id}" aria-pressed="${selected.includes(r.id)}"><img loading="lazy" src="${r.previa}" alt="${esc(r.nome)}"><b>${esc(r.nome)}</b></button>`).join('')||'<p>Nenhuma figura encontrada.</p>';
  dialog.querySelectorAll('[data-figure]').forEach(button=>button.onclick=()=>{if(!field){$('shotcraft-art-selected').textContent=button.querySelector('b').textContent+' · disponível para seleção por contexto';return}const id=button.dataset.figure;if(selected.includes(id))selected=selected.filter(x=>x!==id);else if(selected.length<4)selected.push(id);else{toast('Escolha até quatro figuras. Desmarque uma para trocar.');return}button.setAttribute('aria-pressed',String(selected.includes(id)));status()});status();
 };
 $('shotcraft-art-group').onchange=draw;$('shotcraft-art-search').oninput=draw;
 if(field){$('shotcraft-art-apply').onclick=()=>{field.value=selected.join('; ');dialog.close();toast('Figuras da cena escolhidas. Salve a revisão para aplicar.')};$('shotcraft-art-auto').onclick=()=>{field.value='';dialog.close();toast('A cena usará figuras escolhidas pelo contexto.')}}
 draw();dialog.showModal();
 if(meshArt){dialog.querySelector('#shotcraft-dialog-content>p').textContent='Objetos modelados com geometria tridimensional real. Os ícones abaixo identificam cada objeto; a galeria 3D mostra seu acabamento em volume. Escolha até quatro objetos para esta cena.';dialog.querySelector('a[href*="twemoji"]').hidden=true;dialog.querySelector('#shotcraft-dialog-content>p:last-child').textContent='Modelagem original do Clareia. Os rótulos do vídeo acompanham a narração.';}
}
