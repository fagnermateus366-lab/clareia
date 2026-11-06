// Browse the local cutouts and insert explicit, editable visual terms in a scene.
(() => {
 let figures=[],target=null;
 const categories={archive:'Arquivo e história',science:'Ciência e conceitos',health:'Saúde',nature:'Natureza e energia',technology:'Tecnologia',society:'Sociedade e educação',economy:'Economia e trabalho',daily:'Cotidiano e cultura'};
 const norm=value=>String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 document.addEventListener('DOMContentLoaded',()=>{
  const dialog=document.createElement('dialog');dialog.id='collage-library';dialog.setAttribute('aria-labelledby','collage-library-title');
  dialog.innerHTML=`<div class="dialog-head"><h2 id="collage-library-title">96 figuras · acervo Vox</h2><button type="button" class="secondary" data-close-library aria-label="Fechar biblioteca">×</button></div><p class="small">Recortes ilustrativos. A escolha automática acompanha cada trecho da fala. Use suas próprias imagens ou a busca opcional para assuntos fora do acervo.</p><div class="config-fields"><label>Buscar figura<input id="collage-search" type="search" placeholder="Microscópio, avião, escola…"></label><label>Área<select id="collage-category"><option value="">Todas as áreas</option>${Object.entries(categories).map(([k,n])=>`<option value="${k}">${n}</option>`).join('')}</select></label></div><p id="collage-count" class="small" role="status"></p><div id="collage-grid"></div>`;
  document.body.append(dialog);
  const paint=()=>{
   const query=norm($('collage-search').value),category=$('collage-category').value;
   const visible=figures.filter(r=>(!category||r.category===category)&&norm([r.name,...r.tags].join(' ')).includes(query));
   $('collage-count').textContent=visible.length+(visible.length===1?' figura encontrada':' figuras encontradas')+(target?' · clique para acrescentar à cena':'');
   $('collage-grid').innerHTML=visible.map(r=>`<${target?'button type="button"':'article'} class="collage-figure" ${target?'data-use-figure="'+esc(r.id)+'"':''}><img loading="lazy" src="/api/collage/figures/${encodeURIComponent(r.id)}" alt="${esc(r.name)}"><b>${esc(r.name)}</b><small>${esc(categories[r.category])}</small><small>${esc(r.movimento?.nome||'Balanço de adesivo')}</small></${target?'button':'article'}>`).join('');
  };
  $('collage-search').oninput=paint;$('collage-category').onchange=paint;
  dialog.querySelector('[data-close-library]').onclick=()=>dialog.close();
  window.openCollageLibrary=(scene=null)=>action(async()=>{
   target=scene?.querySelector('[data-key="figuras_colagem"]')||null;
   if(!figures.length)figures=await api('/api/collage/figures');
   $('collage-search').value='';$('collage-category').value='';paint();dialog.showModal();$('collage-search').focus();
  });
  document.addEventListener('click',event=>{
   const open=event.target.closest('[data-collage-library]');
   if(open)window.openCollageLibrary(open.closest('[data-scene]'));
   const pick=event.target.closest('[data-use-figure]');
   if(pick&&target?.isConnected){const r=figures.find(r=>r.id===pick.dataset.useFigure);const terms=target.value.trim();const next=(terms?terms+'; ':'')+r.tags[0];if(next.length>1000){toast('O campo de figuras desta cena está cheio.',true);return}target.value=next;target.dispatchEvent(new Event('input',{bubbles:true}));toast(r.name+' acrescentado às figuras da cena. Salve para aplicar.');}
  });
 });
})();
