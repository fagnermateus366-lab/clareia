const projectColorStyles=['ilustracoes','recortes','tipografia','infografico'];
function usesProjectBackground(prefix,style){return projectColorStyles.includes(style)&&!(document.querySelector(`input[name="${prefix}-tipo_video"]:checked`)?.value==='shorts'&&['fotos','clipes'].includes($(prefix+'-modo_shorts').value))}
function videoPaletteOptions(value,inherit=false){
 return opt([...(inherit?[['herdar','Usar a cor do projeto']]:[]),...(studioCatalog.paletas_video||[{id:'oceano',nome:'Oceano · verde'},{id:'papel',nome:'Papel · claro'},{id:'noturno',nome:'Noturno · violeta'}]).map(p=>[p.id,p.nome])],value);
}
function videoBackgroundImages(value=''){
 return opt([['','Escolha uma imagem adicionada ao projeto'],...(current?.imagens||[]).map((name,i)=>[name,'Imagem '+(i+1)+' · '+(current.imagens_meta?.[name]?.nome_original||name)])],value);
}
function videoBackgroundSample(){return '<div class="video-background-sample"><div></div><span>Prévia do fundo<br><b>Uma ideia com clareza.</b></span></div>'}
function paintVideoBackgroundSample(box,palette,image,strength){
 const sample=box.querySelector('.video-background-sample');if(!sample)return;
 const p=studioCatalog.paletas_video.find(p=>p.id===palette)||studioCatalog.paletas_video[0];
 sample.style.background=p.fundo;sample.style.color=p.texto;
 const photo=sample.querySelector('div');photo.style.backgroundImage=image?'url("/api/projects/'+current.id+'/images/'+encodeURIComponent(image)+'")':'none';photo.style.opacity=strength;
}
function videoBackgroundFields(prefix,s){
 if(!studioCatalog.paletas_video)return '';
 const sample=videoBackgroundSample();
 if(prefix==='create')return '<div id="create-backgrounds" class="video-background-controls">'+sample+'<p class="small">Depois de criar o projeto, você poderá escolher também uma imagem de fundo e variar o fundo por cena.</p></div>';
 return `<fieldset id="${prefix}-backgrounds" class="video-background-controls"><legend>Fundo do vídeo</legend><div class="config-fields"><label>Tipo de fundo<select id="${prefix}-tipo_fundo">${opt([['cor','Cor do projeto'],['imagem','Imagem de fundo']],s.imagem_fundo?'imagem':'cor')}</select></label><label data-background-image-wrap>Imagem de fundo<select id="${prefix}-imagem_fundo" data-background-image>${videoBackgroundImages(s.imagem_fundo||'')}</select></label><label data-background-strength>Visibilidade da imagem <output>${Math.round((s.intensidade_fundo??.28)*100)}%</output><input type="range" id="${prefix}-intensidade_fundo" min="5" max="40" step="1" value="${Math.round((s.intensidade_fundo??.28)*100)}"></label></div>${sample}<p class="small" data-background-note></p><button type="button" class="secondary" data-background-upload>＋ Adicionar imagem de fundo</button></fieldset>`;
}
function videoBackgroundConfig(prefix){
 if(prefix!=='edit'||!$(prefix+'-backgrounds'))return {};
 const type=$(prefix+'-tipo_fundo').value,image=$(prefix+'-imagem_fundo').value;
 if(type==='imagem'&&!image)throw Error('Escolha uma imagem para o fundo do projeto.');
 return {imagem_fundo:type==='imagem'?image:null,intensidade_fundo:Number($(prefix+'-intensidade_fundo').value)/100};
}
function bindVideoBackgrounds(prefix){
 const root=$(prefix+'-backgrounds');if(!root)return;
 const update=()=>{
  const compatible=usesProjectBackground(prefix,$(prefix+'-animacao').value),type=$(prefix+'-tipo_fundo')?.value||'cor';
  root.querySelectorAll('[data-background-image-wrap],[data-background-strength]').forEach(el=>el.hidden=type!=='imagem');
  root.querySelectorAll('input,select,button').forEach(el=>el.disabled=!compatible);
  root.querySelector('[data-background-strength] output')?.replaceChildren(Math.round(Number($(prefix+'-intensidade_fundo')?.value||28))+'%');
  const note=root.querySelector('[data-background-note]');if(note)note.textContent=compatible?'A imagem fica discreta atrás da animação. Cada cena pode herdar este fundo ou escolher outro.':'Este modelo tem fundo próprio. Esta escolha ficará guardada para modelos que usam as cores do projeto.';
  paintVideoBackgroundSample(root,$(prefix+'-estilo').value,compatible&&type==='imagem'?$(prefix+'-imagem_fundo').value:null,Number($(prefix+'-intensidade_fundo')?.value||28)/100);
  if(prefix==='edit')document.querySelectorAll('[data-scene]').forEach(el=>updateSceneBackground(el));
 };
 root.addEventListener('input',update);root.addEventListener('change',update);
 $(prefix+'-estilo').addEventListener('change',update);$(prefix+'-animacao').addEventListener('change',update);
 $(prefix+'-modo_shorts').addEventListener('change',update);document.querySelectorAll(`input[name="${prefix}-tipo_video"]`).forEach(el=>el.addEventListener('change',update));
 root.querySelector('[data-background-upload]')?.addEventListener('click',()=>$('review-images-add').click());update();
}
function addSceneBackground(el,s){
 if(!studioCatalog.paletas_video)return;
 el.dataset.backgroundProject=current.id;
 const box=document.createElement('details');box.className='scene-background-controls';
 box.innerHTML='<summary>Cor ou imagem de fundo desta cena</summary><div class="config-fields"><label>Fundo desta cena<select data-key="fundo_cena">'+opt([['herdar','Usar o fundo do projeto'],['cor','Escolher uma cor'],['imagem','Escolher uma imagem']],s.fundo_cena||'herdar')+'</select></label><label data-scene-background-color>Cor desta cena<select data-key="estilo_cena">'+videoPaletteOptions(s.estilo_cena||'herdar',true)+'</select></label><label data-scene-background-image>Imagem de fundo da cena<select data-key="imagem_fundo" data-background-image>'+videoBackgroundImages(s.imagem_fundo||'')+'</select></label><label data-scene-background-image>Visibilidade da imagem <output></output><input type="range" data-key="intensidade_fundo" min="5" max="40" step="1" value="'+Math.round((s.intensidade_fundo??current.config.intensidade_fundo??.28)*100)+'"></label></div>'+videoBackgroundSample()+'<p class="small" data-background-note></p><button type="button" class="secondary" data-background-upload>＋ Adicionar imagem ao projeto</button>';
 el.querySelector('.scene-body>div:last-child').append(box);
 box.querySelector('[data-background-upload]').onclick=()=>$('review-images-add').click();
 box.addEventListener('input',()=>updateSceneBackground(el));box.addEventListener('change',()=>updateSceneBackground(el));
 el.querySelector('[data-key="animacao"]').addEventListener('change',()=>updateSceneBackground(el));
 box.open=(s.fundo_cena||'herdar')!=='herdar';updateSceneBackground(el);
}
function updateSceneBackground(el){
 if(el.dataset.backgroundProject!==current?.id)return;
 const box=el.querySelector('.scene-background-controls');if(!box)return;
 let style=el.querySelector('[data-key="animacao"]').value;if(style==='herdar')style=$('edit-animacao').value;
 const compatible=usesProjectBackground('edit',style),mode=box.querySelector('[data-key="fundo_cena"]').value;
 const color=box.querySelector('[data-key="estilo_cena"]').value;
 box.querySelector('[data-scene-background-color]').hidden=mode==='herdar';
 box.querySelectorAll('[data-scene-background-image]').forEach(e=>e.hidden=mode!=='imagem');
 box.querySelectorAll('input,select,button').forEach(e=>e.disabled=!compatible);
 box.querySelector('output').textContent=box.querySelector('[data-key="intensidade_fundo"]').value+'%';
 box.querySelector('[data-background-note]').textContent=compatible?'Este fundo não altera a imagem de referência nem a ordem das imagens da cena.':'Este modelo mantém seu fundo próprio. As opções acima ficam guardadas.';
 const photo=mode==='herdar'?($('edit-tipo_fundo').value==='imagem'?$('edit-imagem_fundo').value:null):mode==='imagem'?box.querySelector('[data-key="imagem_fundo"]').value:null;
 const strength=mode==='herdar'?Number($('edit-intensidade_fundo').value)/100:Number(box.querySelector('[data-key="intensidade_fundo"]').value)/100;
 paintVideoBackgroundSample(box,mode==='herdar'||color==='herdar'?$('edit-estilo').value:color,compatible?photo:null,strength);
}
function readSceneBackground(el,s){
 const box=el.querySelector('.scene-background-controls');
 if(!box)return;
 s.fundo_cena=box.querySelector('[data-key="fundo_cena"]').value;s.estilo_cena=box.querySelector('[data-key="estilo_cena"]').value;
 s.imagem_fundo=box.querySelector('[data-key="imagem_fundo"]').value||null;
 s.intensidade_fundo=s.fundo_cena==='imagem'?Number(box.querySelector('[data-key="intensidade_fundo"]').value)/100:null;
 if(s.fundo_cena==='imagem'&&!s.imagem_fundo)throw Error('Escolha a imagem de fundo da cena.');
}
function refreshVideoBackgroundImages(){
 document.querySelectorAll('[data-background-image]').forEach(select=>{const value=select.value;select.innerHTML=videoBackgroundImages(value)});
 $('edit-tipo_fundo')?.dispatchEvent(new Event('change',{bubbles:true}));
}
