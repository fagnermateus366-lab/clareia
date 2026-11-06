// Existing channel playlists, shared by scheduling and manual uploads.
window.PlaylistPicker=class {
 constructor(prefix,onChange,onReconnect){
  this.prefix=prefix;this.onChange=onChange;this.onReconnect=onReconnect;
  this.channel='';this.selected=new Set();this.items=[];this.loading=false;this.canEdit=false;this.error='';this.disabled=false;this.revision=0;
  $(prefix+'-playlists').innerHTML=`<details class="playlist-picker"><summary><strong>Escolher playlists <span class="optional">opcional</span></strong><small id="${prefix}-playlist-summary">Sem playlist</small></summary><div class="playlist-picker-body"><div class="playlist-picker-toolbar"><button type="button" class="secondary" id="${prefix}-playlist-refresh">↻ Atualizar playlists</button><button type="button" class="secondary" id="${prefix}-playlist-clear" hidden>Limpar seleção</button></div><p class="small" id="${prefix}-playlist-status" role="status"></p><button type="button" class="secondary" id="${prefix}-playlist-reconnect" hidden>Reconectar canal com Google</button><div class="playlist-picker-list" id="${prefix}-playlist-items" role="group" aria-label="Playlists do canal"></div></div></details>`;
  $(prefix+'-playlist-refresh').onclick=()=>this.load(this.channel,[...this.selected]);
  $(prefix+'-playlist-clear').onclick=()=>{this.selected.clear();this.paint()};
  $(prefix+'-playlist-reconnect').onclick=()=>action(()=>this.onReconnect(this.channel));
  this.paint(false);
 }
 values(){return [...this.selected]}
 valid(){return !this.loading&&(!this.selected.size||(!this.error&&this.canEdit&&this.values().every(id=>this.items.some(p=>p.id===id))))}
 setDisabled(value){if(this.disabled===value)return;this.disabled=value;this.paint(false)}
 async load(channel,selected=[]){
  const revision=++this.revision;
  this.channel=channel;this.selected=new Set(selected);this.items=[];this.error='';this.canEdit=false;this.loading=!!channel;this.paint();
  if(!channel)return;
  try{
   const data=await api('/api/youtube/channels/'+encodeURIComponent(channel)+'/playlists');
   if(revision!==this.revision)return;
   this.items=data.itens;this.canEdit=data.pode_editar;
  }catch(e){if(revision!==this.revision)return;this.error=e.message}
  finally{if(revision===this.revision){this.loading=false;this.paint()}}
 }
 summary(){
  $(this.prefix+'-playlist-summary').textContent=this.selected.size?this.selected.size+' '+(this.selected.size===1?'selecionada':'selecionadas'):'Sem playlist';
  $(this.prefix+'-playlist-clear').hidden=!this.selected.size;
 }
 paint(notify=true){
  const p=this.prefix,missing=this.values().filter(id=>!this.items.some(item=>item.id===id));
  this.summary();
  $(p+'-playlist-refresh').disabled=this.loading||!this.channel||this.disabled;
  $(p+'-playlist-clear').disabled=this.disabled;
  $(p+'-playlist-reconnect').hidden=!this.channel||this.loading||!!this.error||this.canEdit||this.disabled;
  $(p+'-playlist-status').textContent=!this.channel?'Selecione um canal conectado para ver suas playlists.':this.loading?'Buscando playlists do canal…':this.error||(missing.length?'Uma playlist selecionada está indisponível. Atualize a lista ou desmarque a seleção.':!this.canEdit?'Reconecte o canal com Google para autorizar a inclusão de vídeos nas playlists.':!this.items.length?'Este canal ainda não tem playlists.':'Marque uma ou mais playlists. O vídeo será incluído após o envio.');
  const rows=[...this.items,...missing.map(id=>({id,titulo:'Playlist indisponível · '+id,missing:true}))];
  $(p+'-playlist-items').innerHTML=rows.map(item=>`<label class="playlist-picker-row"><input type="checkbox" value="${esc(item.id)}" ${this.selected.has(item.id)?'checked':''} ${this.disabled||this.loading||(!this.canEdit&&!item.missing)?'disabled':''}><span><strong>${esc(item.titulo)}</strong>${item.missing?'':`<small>${esc(({public:'Pública',private:'Privada',unlisted:'Não listada'})[item.privacidade]||'Playlist')} · ${Number(item.videos)||0} vídeos</small>`}</span></label>`).join('');
  $(p+'-playlist-items').querySelectorAll('input').forEach(input=>input.onchange=()=>{
   if(input.checked)this.selected.add(input.value);else this.selected.delete(input.value);
   this.summary();this.onChange();
  });
  if(notify)this.onChange();
 }
};
