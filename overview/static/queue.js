// Persistent processing queue, in-app notifications and manual YouTube sharing.
(() => {
  let queueData={tarefas:[],historico:[]}, notices={itens:[],nao_lidas:0};
  let channels=[], youtubeProject=null, lastNotice=null, refreshing=false, signature='';
  let oauthConfigured=false,oauthAttempt=null,uploadState={},sending=false;
  let youtubeGeneratedChoice='mesma-ia-do-roteiro',youtubeChoiceDirty=false,copyGenerating=false;
  for(const prefix of ['schedule','youtube'])$(prefix+'-dialog').querySelector('.dialog-head').insertAdjacentHTML('afterend',`<p class="short-publication-note" id="${prefix}-short-note" hidden></p>`);
  function shortNotice(prefix){
    const note=$(prefix+'-short-note');note.hidden=current?.config?.tipo_video!=='shorts';
    note.textContent=current?.status?.aviso_shorts||'Reels / Shorts · vertical 9:16. O YouTube classifica o vídeo como Shorts quando o arquivo tem até 3 minutos. O Clareia verifica o MP4 antes de enviar e preserva a narração completa.';
  }
  const copyLabel='Usar uma IA específica para título e descrição do YouTube';
  $('schedule-brief').closest('label').insertAdjacentHTML('afterend',stageAIFields('schedule-copy',{},copyLabel,'O fluxo agendado preparará os textos com esta IA. O título que você preencher será respeitado.'));
  $('schedule-copy-box').insertAdjacentHTML('beforebegin',stageAIFields('schedule-plan',{},'Usar uma IA específica para planejar o vídeo','Organiza o objetivo, os conceitos, o exemplo e a conclusão antes da escrita do roteiro.'));
  $('youtube-description').closest('label').insertAdjacentHTML('afterend',stageAIFields('youtube-copy',{},copyLabel,'Escolha a IA e clique em Gerar título e descrição para preparar os textos. Você pode editar o resultado antes de enviar.')+'<p class="small stage-ai-result" id="youtube-ai-result" role="status"></p>');
  bindStageAI('schedule-copy',updateScheduleControls);bindStageAI('schedule-plan',updateScheduleControls);
  const youtubeCopyPicker=bindStageAI('youtube-copy',()=>{
    youtubeChoiceDirty=stageAIKey(stageAIRead('youtube-copy',false))!==youtubeGeneratedChoice;
    if(youtubeChoiceDirty)$('youtube-ai-result').textContent='IA alterada. Use Gerar título e descrição para aplicar a escolha antes de enviar.';
    updateUploadControls();
  });
  const labels={fila:'Na fila',agendado:'Agendado',executando:'Processando',concluido:'Vídeo pronto',enviado_youtube:'Enviado ao YouTube',revisao:'Roteiro pronto',pausado:'Pausado',erro:'Erro',pulado:'Pulado',perdido:'Horário perdido',cancelado:'Cancelado'};
  const kinds={render:'Vídeo',render_youtube:'Criar vídeo → descrição → publicar no YouTube',roteiro:'Roteiro',preview:'Prévia',youtube:'Envio ao YouTube'};
  const date=timestamp=>new Date(timestamp*1000).toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'});
  const json=body=>({headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const schedulePlaylists=new PlaylistPicker('schedule',()=>updateScheduleControls(),cid=>connectGoogle(cid));
  const youtubePlaylists=new PlaylistPicker('youtube',()=>updateUploadControls(),cid=>connectGoogle(cid));
  function updateScheduleControls(){
    $('schedule-confirm').disabled=!channels.some(c=>c.conectado&&c.id===$('schedule-channel').value)||!schedulePlaylists.valid()||!stageAIReady('schedule-copy')||(!$('schedule-plan-box').hidden&&!stageAIReady('schedule-plan'));
  }
  async function reloadOpenPlaylists(){
    for(const [prefix,picker] of [['schedule',schedulePlaylists],['youtube',youtubePlaylists]]){
      if($(prefix+'-dialog').open){const cid=$(prefix+'-channel').value;await picker.load(cid,picker.channel===cid?picker.values():[])}
    }
  }

  document.querySelector('.header-actions').insertAdjacentHTML('afterbegin',
    '<button id="queue-open" class="secondary" type="button">☷ Fila <span id="queue-count">0</span></button><button id="notifications-open" class="secondary" type="button" aria-label="Notificações"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg><span id="notification-count" hidden></span></button>');
  $('render').textContent='Executar vídeo';
  $('render').insertAdjacentHTML('afterend','<button id="schedule" class="secondary" type="button" disabled>◷ Agendar vídeo</button><button id="project-cancel-wait" class="secondary" type="button" hidden>Cancelar espera</button>');
  $('exports').querySelector('.downloads').insertAdjacentHTML('beforeend','<button id="youtube-open" class="primary" type="button">Compartilhar no YouTube ↗</button>');
  $('api-settings').insertAdjacentHTML('afterend','<button id="channels-open" class="aside-action" type="button">▶ Canais do YouTube</button>');
  const zone=Intl.DateTimeFormat().resolvedOptions().timeZone;
  document.querySelectorAll('[data-local-zone]').forEach(el=>el.textContent=zone);
  document.querySelectorAll('[data-close-dialog]').forEach(b=>b.onclick=()=>$(b.dataset.closeDialog).close());

  window.updateQueueControls=(p,busy)=>{
    $('schedule').disabled=busy||(!p.cenas.length&&!p.assunto?.assunto&&!p.fontes?.length);
    $('schedule').textContent=p.agendamento_em_edicao?'Salvar e reagendar':'◷ Agendar vídeo';
    $('schedule-draft-note').hidden=!p.agendamento_em_edicao;
    $('pause').disabled=!p.processando;
    const job=queueData.tarefas.find(j=>j.project===p.id&&['fila','agendado'].includes(j.status));
    $('project-cancel-wait').hidden=!job;
    $('project-cancel-wait').dataset.job=job?.id||'';
  };

  function rows(items,history=false){
    if(!items.length)return '<p class="small queue-empty">'+(history?'Ainda não há tarefas finalizadas.':'Nenhum projeto aguardando. Revise um roteiro e escolha Executar vídeo ou Agendar vídeo.')+'</p>';
    let position=0;
    return items.map(j=>{
      if(j.status==='fila')position++;
      return `<article class="queue-row"><div><span class="queue-state state-${esc(j.status)}">${j.atrasado?'Aguardando a vez':esc(labels[j.status]||j.status)}${j.status==='fila'?' · posição '+position:''}</span><button type="button" class="queue-project" data-queue-project="${esc(j.project)}">${esc(j.publication?.titulo||j.title)}</button><small>${esc(kinds[j.kind]||(j.kind.startsWith('scene_preview:')?'Prévia de cena':'Cena'))} · ${j.scheduled?'Agendado: '+date(j.scheduled):'Adicionado: '+date(j.submitted)}</small><p class="small">${esc(j.message)}</p></div>${['fila','agendado'].includes(j.status)?`<button type="button" class="secondary" data-cancel-job="${j.id}">Cancelar</button>`:''}</article>`;
    }).join('');
  }

  function bindRows(container){
    container.querySelectorAll('[data-cancel-job]').forEach(b=>b.onclick=()=>action(()=>cancelJob(b.dataset.cancelJob)));
    container.querySelectorAll('[data-queue-project]').forEach(b=>b.onclick=()=>action(async()=>{
      for(const id of ['queue-dialog','notifications-dialog'])if($(id).open)$(id).close();
      await openProject(b.dataset.queueProject);
    }));
  }

  function paintQueue(){
    $('queue-items').innerHTML=rows(queueData.tarefas);
    $('queue-history').innerHTML=rows(queueData.historico,true);
    bindRows($('queue-dialog'));
  }

  function paintNotifications(){
    $('notification-items').innerHTML=notices.itens.length?notices.itens.map(n=>`<article class="queue-row ${n.seen?'':'notice-unread'}"><div><span class="queue-state state-${esc(n.status)}">${esc(labels[n.status]||n.status)}</span><button type="button" class="queue-project" data-queue-project="${esc(n.project)}">${esc(n.title)}</button><small>${date(n.created)}</small><p>${esc(n.message)}</p></div></article>`).join(''):'<p class="small queue-empty">As conclusões, publicações, pausas e erros aparecerão aqui, mesmo quando você estiver em outro projeto.</p>';
    $('notifications-read').disabled=!notices.nao_lidas;
    bindRows($('notifications-dialog'));
  }

  async function refreshGlobal(){
    if(refreshing)return;
    refreshing=true;
    try{
      [queueData,notices]=await Promise.all([api('/api/queue'),api('/api/notifications')]);
      $('queue-count').textContent=queueData.tarefas.length;
      $('notification-count').hidden=!notices.nao_lidas;
      $('notification-count').textContent=notices.nao_lidas;
      $('notifications-open').setAttribute('aria-label',`Notificações: ${notices.nao_lidas} não lidas`);
      const newest=notices.itens[0]?.id||0;
      if(lastNotice!==null&&newest>lastNotice){
        const n=notices.itens[0];toast(`${n.title}: ${n.message}`,n.status==='erro');
      }
      lastNotice=newest;
      const next=JSON.stringify([queueData,notices]);
      if(next!==signature){
        signature=next;
        if($('queue-dialog').open)paintQueue();
        if($('notifications-dialog').open)paintNotifications();
        await list();
      }else if(queueData.ocupado)await list();
      if(current)window.updateQueueControls(current,['fila','agendado','roteirizando','renderizando','importando','preparando_publicacao','enviando_youtube'].includes(current.status.status));
      if($('youtube-dialog').open&&youtubeProject)await refreshUpload();
    }finally{refreshing=false}
  }

  async function cancelJob(id){
    await api('/api/queue/'+id,{method:'DELETE'});
    await refreshGlobal();
    if(current)await refresh();
    toast('Espera cancelada. O projeto pode ser editado novamente.');
  }
  window.editScheduledProject=async id=>{
    await api('/api/projects/'+id+'/schedule/edit',{method:'POST'});
    await openProject(id);await refreshGlobal();
    $('project-options').open=true;
    toast('Agendamento suspenso para edição. Altere o roteiro/configurações e use Salvar e reagendar para reativar.');
  };
  $('queue-open').onclick=()=>action(async()=>{await refreshGlobal();paintQueue();$('queue-dialog').showModal()});
  $('notifications-open').onclick=()=>action(async()=>{await refreshGlobal();paintNotifications();$('notifications-dialog').showModal()});
  $('notifications-read').onclick=()=>action(async()=>{await api('/api/notifications/read',{method:'POST',...json({ate:notices.itens[0]?.id||0})});await refreshGlobal();paintNotifications()});
  $('project-cancel-wait').onclick=()=>action(()=>cancelJob($('project-cancel-wait').dataset.job));
  function scheduleChoices(selected){
    const available=channels.filter(c=>c.conectado);
    const choice=available.some(c=>c.id===selected)?selected:available.find(c=>c.padrao)?.id||available[0]?.id;
    $('schedule-channel').innerHTML=available.length?available.map(c=>`<option value="${esc(c.id)}" ${choice===c.id?'selected':''}>${esc(c.nome)}${c.padrao?' · padrão':''}</option>`).join(''):'<option value="">Conecte um canal com Google para agendar</option>';
    updateScheduleControls();
  }
  $('schedule').onclick=()=>action(async()=>{
    if(!current)return;
    channels=await api('/api/youtube/channels');
    const previous=current.agendamento||{};scheduleChoices(previous.canal);
    $('schedule-video-title').value=previous.titulo??(current.titulo_manual?current.titulo:'');
    $('schedule-brief').value=previous.orientacao||'';
    $('schedule-plan-box').hidden=!!current.cenas.length||current.config.roteiro_pronto;
    $('schedule-plan-box').querySelector('p').textContent=(current.config.tipo_roteiro==='motivacional'?'Planeja público, identificação, perspectiva, ação e fechamento. ':'Organiza o objetivo, os conceitos, o exemplo e a conclusão antes da escrita do roteiro. ')+'Desmarcado: usa a mesma IA do roteiro.';
    stageAISet('schedule-plan',current.config.planejamento_ia||{});
    stageAISet('schedule-copy',previous.youtube_ia||current.config.youtube_ia||{});
    $('schedule-include-sources').checked=previous.incluir_fontes??false;
    $('schedule-include-credits').checked=previous.incluir_creditos??false;
    $('schedule-privacy').value=previous.privacidade||'public';
    $('schedule-kids').value=String(previous.conteudo_infantil??false);
    const next=new Date(Date.now()+3600000);next.setSeconds(0,0);
    if(previous.horario&&new Date(previous.horario)>new Date())next.setTime(new Date(previous.horario).getTime());
    const local=new Date(next.getTime()-next.getTimezoneOffset()*60000).toISOString().slice(0,16);
    $('schedule-time').value=local;
    const minimum=new Date(Date.now()+60000);
    $('schedule-time').min=new Date(minimum.getTime()-minimum.getTimezoneOffset()*60000).toISOString().slice(0,16);
    $('schedule-project').textContent=current.titulo;
    shortNotice('schedule');
    $('schedule-dialog').showModal();
    await schedulePlaylists.load($('schedule-channel').value,previous.canal===$('schedule-channel').value?previous.playlists||[]:[]);
  });
  $('schedule-channel').onchange=()=>action(()=>schedulePlaylists.load($('schedule-channel').value));
  $('schedule-form').onsubmit=e=>{
    e.preventDefault();action(async()=>{
      const moment=new Date($('schedule-time').value);
      if(!Number.isFinite(moment.getTime())||moment.getTime()<=Date.now())throw Error('Escolha uma data e um horário no futuro.');
      $('schedule-confirm').disabled=true;
      try{
        if(!current.cenas.length)await stageAISet('edit-plan',stageAIRead('schedule-plan'));
        await save();
        await api('/api/projects/'+current.id+'/schedule',{method:'POST',...json({horario:moment.toISOString(),canal:$('schedule-channel').value,
          titulo:$('schedule-video-title').value,orientacao:$('schedule-brief').value,privacidade:$('schedule-privacy').value,conteudo_infantil:$('schedule-kids').value==='true',
          incluir_fontes:$('schedule-include-sources').checked,incluir_creditos:$('schedule-include-credits').checked,gerar_roteiro:!current.cenas.length,playlists:schedulePlaylists.values(),youtube_ia:stageAIRead('schedule-copy')})});
        syncYoutubeAIChoice(current.id,stageAIRead('schedule-copy'));
        $('schedule-dialog').close();await refresh();await refreshGlobal();
        toast('Criação e publicação automática agendadas para '+moment.toLocaleString('pt-BR')+'.');
      }finally{updateScheduleControls()}
    });
  };

  function channelChoices(selected){
    const choice=channels.some(c=>c.id===selected)?selected:channels.find(c=>c.padrao)?.id;
    $('youtube-channel').innerHTML=channels.length?channels.map(c=>`<option value="${esc(c.id)}" ${choice===c.id?'selected':''}>${esc(c.nome)}${c.padrao?' · padrão':''}</option>`).join(''):'<option value="">Cadastre um canal para continuar</option>';
    $('youtube-studio').disabled=!channels.length;
    if($('schedule-dialog').open)scheduleChoices($('schedule-channel').value||selected);
    updateUploadControls();
  }
  async function showChannels(){
    const [items,config]=await Promise.all([api('/api/youtube/channels'),api('/api/youtube/oauth/config')]);
    channels=items;oauthConfigured=config.configurado;
    $('google-connection-status').textContent=oauthConfigured?'Acesso Google configurado. Conecte o canal para autorizar os envios.':'Primeiro, configure o cliente OAuth do Google para ativar o envio direto.';
    $('channel-items').innerHTML=channels.length?channels.map(c=>`<article class="queue-row"><div><strong>${esc(c.nome)}</strong><small>${esc(c.id)}${c.padrao?' · Canal padrão':''}</small><small>${c.conectado?'✓ Conectado para envio direto':'Atalho cadastrado · conexão Google pendente'}</small></div><div class="toolbar"><button class="secondary" type="button" data-connect-channel="${esc(c.id)}">${c.conectado?'Reconectar':'Conectar com Google'}</button>${c.conectado?`<button class="secondary" type="button" data-disconnect-channel="${esc(c.id)}">Desconectar</button>`:''}<button class="secondary" type="button" data-edit-channel="${esc(c.id)}">Editar</button><button class="secondary" type="button" data-remove-channel="${esc(c.id)}">Remover</button></div></article>`).join(''):'<p class="small">Conecte com Google para importar seu canal automaticamente.</p>';
    document.querySelectorAll('[data-connect-channel]').forEach(b=>b.onclick=()=>action(()=>connectGoogle(b.dataset.connectChannel)));
    document.querySelectorAll('[data-disconnect-channel]').forEach(b=>b.onclick=()=>action(async()=>{await api('/api/youtube/channels/'+b.dataset.disconnectChannel+'/connection',{method:'DELETE'});await showChannels()}));
    document.querySelectorAll('[data-edit-channel]').forEach(b=>b.onclick=()=>{
      const c=channels.find(c=>c.id===b.dataset.editChannel);$('channel-name').value=c.nome;$('channel-id').value=c.id;$('channel-default').checked=c.padrao;$('channel-name').focus();
    });
    document.querySelectorAll('[data-remove-channel]').forEach(b=>b.onclick=()=>action(async()=>{
      await api('/api/youtube/channels/'+b.dataset.removeChannel,{method:'DELETE'});await showChannels();
    }));
    channelChoices($('youtube-channel').value);
    await reloadOpenPlaylists();
    if(!$('channels-dialog').open)$('channels-dialog').showModal();
  }
  $('channels-open').onclick=$('youtube-manage-channels').onclick=()=>action(showChannels);
  $('schedule-manage-channels').onclick=()=>action(showChannels);
  $('channel-form').onsubmit=e=>{
    e.preventDefault();action(async()=>{
      await api('/api/youtube/channels',{method:'POST',...json({nome:$('channel-name').value,canal:$('channel-id').value,padrao:$('channel-default').checked})});
      $('channel-form').reset();await showChannels();toast('Canal salvo.');
    });
  };
  async function fillYoutube(data){
    const choice=data.youtube_ia||current?.config?.youtube_ia||{};
    youtubeGeneratedChoice=stageAIKey(choice);youtubeChoiceDirty=false;
    await youtubeCopyPicker.set(choice);
    $('youtube-ai-result').textContent=data.aviso||(data.ia_textos?'Textos gerados com '+providerName(data.ia_textos.provedor)+' · '+data.ia_textos.modelo+'.':'Os textos podem ser editados ou gerados novamente com a IA escolhida.');
    $('youtube-video-title').value=data.titulo;
    $('youtube-description').value=data.descricao;
    $('youtube-stale').hidden=!data.desatualizado;
    $('youtube-include-sources').checked=data.incluir_fontes??false;
    $('youtube-include-credits').checked=data.incluir_creditos??false;
    channelChoices(data.canal);
    const selected=data.playlists??(uploadState.arquivo_atual&&uploadState.channel===$('youtube-channel').value?uploadState.playlists||[]:[]);
    await youtubePlaylists.load($('youtube-channel').value,data.canal&&data.canal!==$('youtube-channel').value?[]:selected);
  }
  async function saveYoutube(){
    const choice=stageAIRead('youtube-copy');
    const data=await api('/api/projects/'+youtubeProject+'/youtube',{method:'PUT',...json({titulo:$('youtube-video-title').value,descricao:$('youtube-description').value,canal:$('youtube-channel').value,playlists:youtubePlaylists.values(),youtube_ia:choice})});
    syncYoutubeAIChoice(youtubeProject,choice);
    $('youtube-stale').hidden=!data.desatualizado;
  }
  $('youtube-open').onclick=()=>action(async()=>{
    youtubeProject=current.id;
    const [data,items,config,state]=await Promise.all([api('/api/projects/'+youtubeProject+'/youtube'),api('/api/youtube/channels'),api('/api/youtube/oauth/config'),api('/api/projects/'+youtubeProject+'/youtube/upload')]);
    channels=items;oauthConfigured=config.configurado;uploadState=state;
    $('youtube-privacy').value=state.arquivo_atual?state.privacy||'public':'public';
    $('youtube-kids').value=state.arquivo_atual&&typeof state.made_for_kids==='boolean'?String(state.made_for_kids):'false';
    $('youtube-download').href='/api/projects/'+youtubeProject+'/download/video.mp4';
    $('youtube-text-download').href='/api/projects/'+youtubeProject+'/download/youtube.txt';
    shortNotice('youtube');
    $('youtube-dialog').showModal();
    await fillYoutube(data);paintUpload();
  });
  for(const [button,input] of [['youtube-copy-title','youtube-video-title'],['youtube-copy-description','youtube-description']]){
    $(button).onclick=()=>action(async()=>{await navigator.clipboard.writeText($(input).value);await saveYoutube();toast(input==='youtube-video-title'?'Título copiado.':'Descrição copiada.')});
  }
  $('youtube-save').onclick=()=>action(async()=>{await saveYoutube();toast('Textos salvos.')});
  $('youtube-regenerate').onclick=()=>action(async()=>{
    copyGenerating=true;updateUploadControls();
    try{
      const data=await api('/api/projects/'+youtubeProject+'/youtube/regenerate',{method:'POST',...json({incluir_fontes:$('youtube-include-sources').checked,incluir_creditos:$('youtube-include-credits').checked,youtube_ia:stageAIRead('youtube-copy')})});
      syncYoutubeAIChoice(youtubeProject,data.youtube_ia);
      await fillYoutube({...data,canal:$('youtube-channel').value,playlists:youtubePlaylists.values()});toast('Título e descrição criados sobre o tema do vídeo.');
    }finally{copyGenerating=false;updateUploadControls()}
  });
  $('youtube-text-download').onclick=e=>{e.preventDefault();action(async()=>{await saveYoutube();window.location.assign($('youtube-text-download').href)})};
  $('youtube-studio').onclick=()=>action(async()=>{
    const channel=channels.find(c=>c.id===$('youtube-channel').value);
    if(!channel)throw Error('Cadastre e selecione um canal primeiro.');
    window.open(channel.studio,'_blank','noopener,noreferrer');
    await saveYoutube();toast('Confira o canal no Studio e selecione o MP4 para enviar.');
  });

  function updateUploadControls(){
    const channel=channels.find(c=>c.id===$('youtube-channel').value);
    const queued=queueData.tarefas.find(j=>j.project===youtubeProject);
    const sameVideo=uploadState.arquivo_atual&&uploadState.video_id&&uploadState.channel===channel?.id;
    const samePlaylists=youtubePlaylists.values().length===(uploadState.playlists||[]).length&&youtubePlaylists.values().every(id=>(uploadState.playlists||[]).includes(id));
    const complete=sameVideo&&samePlaylists&&uploadState.playlists_concluidas!==false;
    const resumable=uploadState.retomavel&&uploadState.arquivo_atual&&uploadState.status!=='expirado';
    const changed=uploadState.retomavel&&(!uploadState.arquivo_atual||uploadState.channel!==channel?.id);
    const frozen=!!queued||resumable||copyGenerating;
    $('youtube-send').disabled=sending||copyGenerating||youtubeChoiceDirty||!stageAIReady('youtube-copy')||!!queued||!!complete||!!changed||!youtubePlaylists.valid();
    $('youtube-send').textContent=complete?'Vídeo já enviado':sameVideo?'Continuar com as playlists':resumable?'Retomar envio ao YouTube':'Enviar vídeo ao YouTube';
    $('youtube-connect').hidden=!!channel?.conectado;
    $('youtube-connect-note').textContent=channel?.conectado?'✓ Canal conectado. O arquivo será enviado diretamente para '+channel.nome+'.':oauthConfigured?'Conecte este canal com Google para autorizar o envio direto.':'Configure o acesso Google uma vez para enviar o vídeo diretamente do projeto.';
    for(const id of ['youtube-channel','youtube-privacy','youtube-kids','youtube-video-title','youtube-description','youtube-regenerate','youtube-include-sources','youtube-include-credits'])$(id).disabled=frozen;
    youtubePlaylists.setDisabled(frozen);
    youtubeCopyPicker.setDisabled(frozen||sending);
    $('youtube-restart').hidden=!(uploadState.status==='expirado'||changed)||!!queued;
    $('youtube-restart').disabled=sending;
    $('youtube-restart').textContent=changed?'Enviar arquivo atual em nova sessão':'Iniciar nova sessão de envio';
    $('youtube-pause-upload').hidden=!(['youtube','render_youtube'].includes(queued?.kind)&&queued.status==='executando');
    $('youtube-cancel-upload').hidden=!(queued?.kind==='youtube'&&queued.status==='fila');
    $('youtube-cancel-upload').dataset.job=queued?.id||'';
  }

  function paintUpload(){
    $('youtube-upload-panel').hidden=!uploadState.status;
    $('youtube-upload-message').textContent=uploadState.message||'';
    $('youtube-upload-progress').value=(uploadState.sent||0)/(uploadState.total||1);
    const privacy={private:'privado',unlisted:'não listado',public:'público'};
    $('youtube-upload-detail').textContent=uploadState.video_id?'Visibilidade informada pelo YouTube: '+(privacy[uploadState.privacy]||uploadState.privacy)+'. Para editar o vídeo enviado, abra-o no Studio.':uploadState.total?formatBytes(uploadState.sent||0)+' de '+formatBytes(uploadState.total)+(uploadState.retomavel?' · A retomada preserva os dados do envio iniciado.':''):'';
    for(const [id,key] of [['youtube-result','url'],['youtube-result-studio','studio']]){
      $(id).hidden=!uploadState[key];if(uploadState[key])$(id).href=uploadState[key];
    }
    updateUploadControls();
  }
  async function refreshUpload(){
    uploadState=await api('/api/projects/'+youtubeProject+'/youtube/upload');paintUpload();
  }
  $('youtube-channel').onchange=()=>action(async()=>{updateUploadControls();await youtubePlaylists.load($('youtube-channel').value)});
  $('google-setup-open').onclick=()=>{$('google-setup-status').textContent=oauthConfigured?'Já existe uma configuração Google salva. Para trocar de projeto OAuth, desconecte os canais antes.':'';$('google-setup-dialog').showModal()};
  $('google-setup-form').onsubmit=e=>{
    e.preventDefault();action(async()=>{
      const file=$('google-client-file').files[0];if(!file||file.size>30000)throw Error('Selecione o JSON do cliente OAuth, com até 30 KB.');
      const config=await api('/api/youtube/oauth/config',{method:'POST',...json({documento:await file.text()})});
      oauthConfigured=config.configurado;$('google-client-file').value='';$('google-setup-dialog').close();
      if($('channels-dialog').open)await showChannels();else updateUploadControls();
      toast('Configuração salva. Agora conecte seu canal com Google.');
    });
  };
  async function connectGoogle(expected=''){
    if(!oauthConfigured){$('google-setup-open').click();return}
    const popup=window.open('about:blank','_blank');
    try{
      const attempt=await api('/api/youtube/oauth/start',{method:'POST',...json({canal:expected})});
      if(!popup)throw Error('Permita abrir a janela do Google no seu navegador e clique em Conectar novamente.');
      popup.opener=null;popup.location.href=attempt.url;oauthAttempt=attempt.id;
      $('google-connection-status').textContent='Autorize o canal na janela do Google. A conexão será reconhecida automaticamente.';
      const poll=async()=>{
        if(oauthAttempt!==attempt.id)return;
        try{
          const state=await api('/api/youtube/oauth/attempts/'+attempt.id);
          if(state.status==='conectado'){
            oauthAttempt=null;
            if($('channels-dialog').open)await showChannels();else channels=await api('/api/youtube/channels');
            channelChoices(state.channel);await reloadOpenPlaylists();toast(state.message);return;
          }
          if(state.status==='erro'){oauthAttempt=null;toast(state.message,true);$('google-connection-status').textContent=state.message;return}
          setTimeout(poll,1500);
        }catch(e){oauthAttempt=null;toast(e.message,true)}
      };
      setTimeout(poll,1000);
    }catch(e){popup?.close();throw e}
  }
  $('google-connect').onclick=()=>action(()=>connectGoogle());
  $('youtube-connect').onclick=()=>action(()=>connectGoogle($('youtube-channel').value));
  async function sendUpload(restart=false){
    const channel=channels.find(c=>c.id===$('youtube-channel').value);
    if(!channel?.conectado){await connectGoogle(channel?.id||'');return}
    if(!$('youtube-kids').value)throw Error('Informe se o vídeo é feito para crianças antes de enviar.');
    sending=true;updateUploadControls();
    try{
      await saveYoutube();
      const response=await api('/api/projects/'+youtubeProject+'/youtube/upload',{method:'POST',...json({canal:channel.id,privacidade:$('youtube-privacy').value,conteudo_infantil:$('youtube-kids').value==='true',nova_sessao:restart,playlists:youtubePlaylists.values()})});
      uploadState=response.envio;paintUpload();await refreshGlobal();
      if(current?.id===youtubeProject)await refresh();
      toast(response.ja_enviado?'Este vídeo já foi enviado. Abra o link do resultado.':'Envio solicitado. Você pode acompanhar aqui ou pelo sino.');
    }finally{sending=false;updateUploadControls()}
  }
  $('youtube-send').onclick=()=>action(()=>sendUpload());
  $('youtube-restart').onclick=()=>action(()=>sendUpload(true));
  $('youtube-pause-upload').onclick=()=>action(async()=>{await api('/api/projects/'+youtubeProject+'/pause',{method:'POST'});toast('Pausa solicitada. Aguarde o trecho em envio terminar.')});
  $('youtube-cancel-upload').onclick=()=>action(async()=>{await cancelJob($('youtube-cancel-upload').dataset.job);await refreshUpload()});
  refreshGlobal().catch(e=>toast('Não foi possível carregar a fila: '+e.message,true));
  setInterval(()=>refreshGlobal().catch(()=>{}),2000);
})();
