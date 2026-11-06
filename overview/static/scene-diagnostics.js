// Locate art failures without rebuilding scene inputs or discarding unsaved edits.
(() => {
 function jump(index){
  const scene=document.querySelector(`[data-scene="${index}"]`);if(!scene)return;
  scene.scrollIntoView({behavior:'smooth',block:'start'});
  scene.querySelector('[data-key="titulo"]')?.focus({preventScroll:true});
 }
 function paint(p){
  const notes=p.erros_cenas||[],busy=['fila','renderizando','roteirizando'].includes(p.status?.status);
  let summary=$('scene-error-summary');
  if(!summary){summary=document.createElement('div');summary.id='scene-error-summary';summary.setAttribute('aria-label','Cenas que precisam de revisão');$('status-text').closest('.status-panel').append(summary)}
  const key=JSON.stringify(notes);
  if(summary.dataset.notes!==key||summary.dataset.project!==p.id){
   summary.replaceChildren();summary.dataset.notes=key;summary.dataset.project=p.id;
   for(const note of notes){
    const button=document.createElement('button');button.type='button';button.className='secondary';
    button.textContent=`Ir para a cena ${note.cena} · ${note.titulo}`;button.onclick=()=>jump(note.indice);summary.append(button);
   }
  }
  summary.hidden=!notes.length;
  for(const scene of document.querySelectorAll('[data-scene]')){
   const index=Number(scene.dataset.scene),note=notes.find(n=>n.indice===index);
   scene.classList.toggle('scene-art-error',!!note);
   let notice=scene.querySelector('.scene-art-notice');
   if(!note){notice?.remove();continue}
   const identity=JSON.stringify(note);
   if(!notice||notice.dataset.note!==identity){
    notice?.remove();notice=document.createElement('section');notice.className='scene-art-notice';notice.dataset.note=identity;
    notice.setAttribute('aria-label',`Revisão de arte da cena ${note.cena}`);
    const title=document.createElement('strong');title.textContent=`Cena ${note.cena} · Revisar direção de arte`;notice.append(title);
    const intro=document.createElement('p');intro.textContent='Não foi encontrada uma figura ou metáfora adequada para os elementos abaixo.';notice.append(intro);
    if(note.detalhes?.length){
     const list=document.createElement('ul');
     for(const detail of note.detalhes){
      const item=document.createElement('li'),label=document.createElement('b');
      label.textContent=`Trecho ${detail.frase+1} · ${detail.elementos.join(', ')}`;item.append(label);
      const quote=document.createElement('p');quote.textContent=detail.texto;item.append(quote);list.append(item);
     }
     notice.append(list);
    }else{const text=document.createElement('p');text.textContent=note.mensagem;notice.append(text)}
    const help=document.createElement('p');help.textContent='Escolha figuras para esta cena ou revise a intenção visual. Depois, gere a prévia para conferir.';notice.append(help);
    const button=document.createElement('button');button.type='button';button.className='secondary';button.dataset.reviewArt='';button.textContent='Escolher figuras desta cena';
    button.onclick=()=>scene.querySelector('[data-scene-figures]')?.click();notice.append(button);
    scene.querySelector('.scene-head').insertAdjacentElement('afterend',notice);
   }
   notice.querySelector('button').disabled=busy;
  }
 }
 function start(){
  const previousPaint=paintScenes,previousStatus=status;
  paintScenes=()=>{previousPaint();if(current)paint(current)};
  status=p=>{const busy=previousStatus(p);if(current?.id===p.id)current.erros_cenas=p.erros_cenas||[];paint(p);return busy};
  if(current)paint(current);
 }
 if(window.studioReady)start();else window.addEventListener('studio-ready',start,{once:true});
})();
