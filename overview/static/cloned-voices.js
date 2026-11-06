(() => {
  const dialog = $('voices-dialog');
  let catalog = {motores: [], vozes: []}, recording = null, stream = null;
  let recordedBlob = null, referenceURL = null, recordTimer = null;
  let previewJob = null, previewTimer = null, previewVoice = null;
  let deletingVoice = null;
  const status = message => $('voice-status').textContent = message;
  const nameOf = engine => catalog.motores.find(m => m.id === engine)?.nome || engine;

  function voiceTuning(p) {
    const select = (key, label, choices, value) => `<label>${label}<select id="saved-${p.id}-${key}">${choices.map(([v,n])=>`<option value="${v}" ${String(value)===String(v)?'selected':''}>${n}</option>`).join('')}</select></label>`;
    return `<details class="voice-tuning"><summary>Expressão e fidelidade da voz</summary>
      ${select('interpretation','Interpretação da narração',[['natural','Natural · fala contínua'],['original','Leitura original por trechos']],p.interpretacao??'natural')}
      ${select('expression','Expressividade',[[.3,'Mais contida'],[.5,'Natural'],[.7,'Mais expressiva']],p.expressividade??.5)}
      ${select('fidelity','Direcionamento do modelo',[[0,'Original · recomendado'],[.3,'Leve'],[.5,'Moderado'],[.7,'Alto']],p.fidelidade??0)}
      ${select('variation','Variação da fala',[[.55,'Mais estável'],[.65,'Mais controlada'],[.8,'Original · recomendado']],p.variacao??.8)}
      <button type="button" class="secondary" data-voice-settings-save="${p.id}">Salvar ajustes</button>
      <p class="small">A fala recebe pensamentos completos. As legendas e imagens são sincronizadas depois, sem reiniciar a voz a cada troca. Seu modelo, gravação e ajustes de fidelidade são preservados. Salve os ajustes e gere uma nova prévia.</p></details>`;
  }

  async function updateCatalog() {
    catalog = await api('/api/cloned-voices');
    const previous = $('voice-engine').value;
    $('voice-engine').innerHTML = catalog.motores.map(m => `<option value="${esc(m.id)}" ${m.instalado?'':'disabled'}>${esc(m.nome)}${m.instalado?'':' · instalação pendente'}</option>`).join('');
    if (catalog.motores.some(m => m.id === previous && m.instalado)) $('voice-engine').value = previous;
    else $('voice-engine').value = catalog.motores.find(m => m.instalado)?.id || '';
    engineChanged();
    $('voice-save').disabled = !catalog.motores.some(m => m.instalado);
    $('voice-profiles').innerHTML = catalog.vozes.length ? catalog.vozes.map(p => `<article class="voice-saved"><strong>${esc(p.nome)}</strong><small>${esc(nameOf(p.motor))} · amostra de ${Math.round(p.duracao)}s</small>${p.preparo?`<p class="small">Referência da clonagem: gravação original, sem trocar o trecho da sua voz.</p>${(p.preparo.avisos||[]).map(note=>`<p class="small voice-quality-note">${esc(note)}</p>`).join('')}`:''}${p.preparo_erro?`<p class="small voice-quality-note">Grave uma nova amostra: ${esc(p.preparo_erro)}</p>`:''}<audio controls preload="none" src="/api/cloned-voices/${p.id}/reference" aria-label="Gravação de referência de ${esc(p.nome)}"></audio>${voiceTuning(p)}<div class="toolbar"><button type="button" class="secondary" data-voice-preview="${p.id}">▷ Gerar prévia</button><button type="button" class="secondary" data-voice-clear-preview="${p.id}" aria-label="Apagar prévia de ${esc(p.nome)}" title="Apaga apenas a prévia e seu cache; mantém a voz salva">Apagar prévia</button><button type="button" class="primary" data-voice-use="${p.id}">Usar na narração</button><button type="button" class="secondary voice-delete" data-voice-delete="${p.id}" aria-expanded="false" aria-controls="voice-delete-${p.id}">Apagar voz</button></div><div class="voice-delete-confirm" id="voice-delete-${p.id}" hidden><p>Apagar <strong>${esc(p.nome)}</strong>? A gravação e as prévias desta voz serão removidas. Os vídeos prontos continuam salvos. Projetos, favoritos e agendamentos que usam esta voz precisarão de outra voz para gerar novamente.</p><div class="toolbar"><button type="button" class="secondary voice-delete" data-voice-confirm-delete="${p.id}">Confirmar exclusão</button><button type="button" class="secondary" data-voice-cancel-delete="${p.id}">Cancelar</button></div></div></article>`).join('') : '<p class="voices-empty small">Suas vozes aparecerão aqui depois de salvar uma amostra.</p>';
    dialog.querySelectorAll('[data-voice-preview]').forEach(button => button.onclick = () => action(() => preview(button.dataset.voicePreview)));
    dialog.querySelectorAll('[data-voice-clear-preview]').forEach(button => button.onclick = () => action(() => removePreview(button.dataset.voiceClearPreview)));
    dialog.querySelectorAll('[data-voice-use]').forEach(button => button.onclick = () => action(() => useVoice(button.dataset.voiceUse)));
    dialog.querySelectorAll('[data-voice-settings-save]').forEach(button => button.onclick = () => action(async () => {
      if(previewJob||deletingVoice)throw Error('Aguarde a operação atual antes de ajustar a voz.');
      const voice=button.dataset.voiceSettingsSave;
      deletingVoice=voice;previewButtons(true);
      try {
        await api(`/api/cloned-voices/${voice}/settings`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({expressividade:Number($(`saved-${voice}-expression`).value),fidelidade:Number($(`saved-${voice}-fidelity`).value),variacao:Number($(`saved-${voice}-variation`).value),interpretacao:$(`saved-${voice}-interpretation`).value})});
        await updateCatalog();status('Ajustes salvos. Gere uma nova prévia para comparar o resultado.');
      } finally {deletingVoice=null;previewButtons(!!previewJob)}
    }));
    dialog.querySelectorAll('[data-voice-delete]').forEach(button => button.onclick = () => {
      if (previewJob || deletingVoice) { status('Aguarde a operação atual antes de apagar uma voz.'); return; }
      const voice = button.dataset.voiceDelete;
      dialog.querySelectorAll('.voice-delete-confirm').forEach(panel => panel.hidden = panel.id !== 'voice-delete-' + voice);
      dialog.querySelectorAll('[data-voice-delete]').forEach(item => item.setAttribute('aria-expanded', String(item === button)));
      $('voice-delete-' + voice).querySelector('[data-voice-confirm-delete]').focus();
    });
    dialog.querySelectorAll('[data-voice-cancel-delete]').forEach(button => button.onclick = () => {
      $('voice-delete-' + button.dataset.voiceCancelDelete).hidden = true;
      const trigger = dialog.querySelector(`[data-voice-delete="${button.dataset.voiceCancelDelete}"]`);
      trigger.setAttribute('aria-expanded', 'false'); trigger.focus();
    });
    dialog.querySelectorAll('[data-voice-confirm-delete]').forEach(button => button.onclick = () => action(() => removeVoice(button.dataset.voiceConfirmDelete)));
    previewButtons(!!previewJob || !!deletingVoice);
    await refreshVoiceOptions();
  }

  async function refreshVoiceOptions() {
    if (!studioCatalog) return;
    const options = await api('/api/options');
    studioCatalog.vozes = options.vozes;
    const delivery=$('voice-preview-delivery'),previousDelivery=delivery.value;
    delivery.innerHTML=options.locucoes.map(d=>`<option value="${esc(d.id)}">${esc(d.nome)}</option>`).join('');
    delivery.value=previousDelivery;
    for (const select of document.querySelectorAll('select[id$="-voz"],select[id$="-voz_secundaria"],#animation-voice')) {
      const previous = select.value;
      select.innerHTML = studioCatalog.vozes.map(v => `<option value="${esc(v.id)}" ${v.instalada?'':'disabled'}>${esc(v.nome+' · '+v.motor)}</option>`).join('');
      if (studioCatalog.vozes.some(v => v.id === previous)) select.value = previous;
      else if (previous.startsWith('clone_')) {
        const missing = new Option('Voz apagada · escolha outra voz', previous, true, true);
        missing.disabled = true; select.add(missing); select.dispatchEvent(new Event('change', {bubbles:true}));
      }
    }
  }

  function engineChanged() {
    $('voice-transcript').required = false;
    $('voice-transcript-note').textContent = 'O Chatterbox usa sua gravação. Estas anotações são opcionais e não alteram a clonagem.';
    $('voice-expression-field').hidden = false;
  }

  function showReference(blob) {
    if (referenceURL) URL.revokeObjectURL(referenceURL);
    referenceURL = URL.createObjectURL(blob);
    $('voice-reference-audio').src = referenceURL;
    $('voice-reference-audio').hidden = false;
  }

  function stopRecording() {
    clearTimeout(recordTimer);
    if (recording && recording.state !== 'inactive') recording.stop();
    stream?.getTracks().forEach(track => track.stop());
    stream = null;
    $('voice-record').textContent = '● Gravar amostra';
    $('voice-record').classList.remove('voices-recording');
  }

  async function record() {
    if (recording?.state === 'recording') { stopRecording(); return; }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw Error('Este navegador não oferece gravação. Use Enviar amostra de áudio.');
    stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true}});
    try {
      const chunks = [];
      const started = Date.now();
      recording = new MediaRecorder(stream);
      recording.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
      recording.onstop = () => {
        const type = recording.mimeType || 'audio/webm';
        recordedBlob = new Blob(chunks, {type});
        $('voice-file').value = '';
        showReference(recordedBlob);
        status(Date.now()-started < 5000 ? 'A gravação ficou curta. Grave pelo menos 5 segundos.' : 'Gravação pronta. Confira o áudio e salve sua voz.');
      };
      recording.start();
      $('voice-record').textContent = '■ Parar gravação';
      $('voice-record').classList.add('voices-recording');
      status('Gravando… Fale naturalmente por 10 a 20 segundos, sem música ou outras vozes.');
      recordTimer = setTimeout(stopRecording, 59000);
    } catch (error) { stopRecording(); throw error; }
  }

  async function save(event) {
    event.preventDefault();
    const blob = recordedBlob || $('voice-file').files[0];
    if (recording?.state === 'recording') throw Error('Pare a gravação antes de salvar.');
    if (!blob) throw Error('Grave ou escolha uma amostra de áudio.');
    const data = new FormData();
    data.append('nome', $('voice-name').value);
    data.append('motor', $('voice-engine').value);
    data.append('transcricao', $('voice-transcript').value);
    data.append('expressividade', $('voice-expression').value);
    data.append('fidelidade', $('voice-fidelity').value);
    data.append('variacao', $('voice-variation').value);
    data.append('interpretacao', $('voice-interpretation').value);
    data.append('audio', blob, 'amostra.audio');
    $('voice-save').disabled = true;
    status('Preparando e salvando a amostra no computador…');
    try {
      await api('/api/cloned-voices', {method: 'POST', body: data});
      await updateCatalog();
      status('Voz salva. Use Gerar prévia para comparar o resultado antes da narração.');
    } finally { $('voice-save').disabled = !catalog.motores.some(m => m.instalado); }
  }

  function previewButtons(disabled) { dialog.querySelectorAll('[data-voice-preview],[data-voice-clear-preview],[data-voice-delete],[data-voice-confirm-delete],[data-voice-cancel-delete],[data-voice-settings-save],.voice-tuning select').forEach(button => button.disabled = disabled); }
  function clearPreviewPlayer() {
    const player = $('voice-preview-audio');
    player.pause(); player.removeAttribute('src'); player.load(); player.hidden = true;
    $('voice-preview-status').textContent = '';
    previewVoice = null;
  }
  async function removePreview(voice) {
    if (previewJob || deletingVoice) throw Error('Aguarde a operação atual antes de apagar a prévia.');
    deletingVoice = voice; previewButtons(true);
    const name = catalog.vozes.find(p => p.id === voice)?.nome || 'Voz';
    status(`Apagando a prévia de “${name}”…`);
    try {
      if (previewVoice === voice) clearPreviewPlayer();
      await api(`/api/cloned-voices/${voice}/previews`, {method:'DELETE'});
      status(`Prévia de “${name}” apagada. Altere e salve os ajustes, depois clique em Gerar prévia. Sua voz continua salva.`);
      toast('Prévia apagada. Você já pode gerar outra.');
    } finally { deletingVoice = null; previewButtons(!!previewJob); }
  }
  async function removeVoice(voice) {
    if (previewJob || deletingVoice) throw Error('Aguarde a operação atual antes de apagar uma voz.');
    deletingVoice = voice;
    previewButtons(true);
    const name = catalog.vozes.find(p => p.id === voice)?.nome || 'Voz';
    status('Apagando a voz salva…');
    try {
      dialog.querySelectorAll('.voice-saved audio').forEach(player => { player.pause(); player.removeAttribute('src'); player.load(); });
      clearPreviewPlayer();
      await api(`/api/cloned-voices/${voice}`, {method:'DELETE'});
      await updateCatalog();
      status(`“${name}” foi apagada. Se ela estava selecionada em um projeto, escolha outra voz antes de gerar novamente.`);
      toast('Voz apagada.');
      $('voice-name').focus();
    } catch (error) {
      await updateCatalog(); status(error.message); throw error;
    } finally { deletingVoice = null; previewButtons(!!previewJob); }
  }
  async function preview(voice) {
    if (previewJob || deletingVoice) throw Error('Aguarde a operação atual antes de gerar uma prévia.');
    previewJob = 'iniciando';
    previewButtons(true);
    try {
      const response = await api(`/api/cloned-voices/${voice}/preview`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({texto: $('voice-preview-text').value,estilo_locucao:$('voice-preview-delivery').value,como_narracao:true})});
      clearPreviewPlayer();
      previewVoice = voice;
      previewJob = response.id;
      $('voice-preview-status').textContent = 'Carregando o modelo e gerando a prévia. Na primeira vez pode demorar alguns minutos.';
      pollPreview();
    } catch (error) { previewJob = null; previewButtons(false); throw error; }
  }
  async function pollPreview() {
    if (!previewJob) return;
    try {
      const result = await api(`/api/cloned-voices/previews/${previewJob}`);
      $('voice-preview-status').textContent = result.mensagem;
      if (result.status === 'concluido') {
        $('voice-preview-audio').src = result.url;
        $('voice-preview-audio').hidden = false;
      }
      if (['erro','concluido'].includes(result.status)) { previewJob = null; previewButtons(false); return; }
      previewTimer = setTimeout(pollPreview, 2000);
    } catch (error) {
      $('voice-preview-status').textContent = error.message;
      previewJob = null; previewButtons(false);
    }
  }

  async function useVoice(voice) {
    if (current && (current.processando || ['fila','agendado','roteirizando','renderizando','preparando_publicacao','enviando_youtube'].includes(current.status?.status))) throw Error('Aguarde ou abra a edição do agendamento antes de mudar a voz.');
    const prefix = current ? 'edit' : 'create';
    if ($(prefix+'-gemini_projeto_completo')?.checked) throw Error('Desmarque o modo de projeto completo Gemini nas opções avançadas para usar uma voz local.');
    if (prefix === 'create' && $('use-favorite').checked) {
      $('voice-status').textContent = 'Para este vídeo usar sua voz salva, desmarque Usar configuração favorita ou escolha um favorito com essa voz.';
      return;
    }
    $(prefix+'-voz').value = voice;
    $(prefix+'-voz').dispatchEvent(new Event('change', {bubbles:true}));
    dialog.close();
    toast(current ? 'Voz selecionada. Salve a revisão para aplicar ao projeto.' : 'Sua voz foi selecionada para a narração do novo vídeo.');
  }

  $('voices-open').onclick = () => action(async () => { dialog.showModal(); await updateCatalog(); });
  $('voices-close').onclick = () => dialog.close();
  dialog.addEventListener('close', stopRecording);
  $('voice-engine').onchange = engineChanged;
  $('voice-record').onclick = () => action(record);
  $('voice-file').onchange = () => { recordedBlob = null; if ($('voice-file').files[0]) showReference($('voice-file').files[0]); };
  $('voice-form').onsubmit = event => { event.preventDefault(); action(() => save(event)); };
})();
