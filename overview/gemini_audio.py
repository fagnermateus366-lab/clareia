"""Google TTS with explicit model selection, phrase cache and no local-voice fallback."""
import base64
import binascii
import io
import json
import os
import time

import numpy as np
import soundfile as sf

from .core import binary,digest,run

TTS_MODELS=['gemini-3.8-flash-lite-tts','gemini-3.8-flash-tts','gemini-3.1-flash-tts-preview',
            'gemini-2.5-flash-preview-tts','gemini-2.5-pro-preview-tts']
VOICES=['Kore','Puck','Charon','Zephyr','Fenrir','Leda','Orus','Aoede','Callirrhoe','Autonoe',
        'Enceladus','Iapetus','Umbriel','Algieba','Despina','Erinome','Algenib','Rasalgethi',
        'Laomedeia','Achernar','Alnilam','Schedar','Gacrux','Pulcherrima','Achird','Zubenelgenubi',
        'Vindemiatrix','Sadachbia','Sadaltager','Sulafat']
VERSION='gemini-tts-v1'


def identity(settings,secondary=False):
    return [VERSION,settings.gemini_modelo_voz,settings.gemini_voz_secundaria if secondary else settings.gemini_voz,
            settings.velocidade,settings.estilo_locucao]


def available_models():
    from .providers import get_key,request
    result=[];token=None
    while True:
        data=request('GET','https://generativelanguage.googleapis.com/v1beta/models',headers={'x-goog-api-key':get_key('gemini')},
                     params={'pageSize':1000,**({'pageToken':token} if token else {})})
        result.extend({'id':m['name'].removeprefix('models/'),'nome':m.get('displayName',m['name'])} for m in data.get('models',[])
                      if m['name'].removeprefix('models/') in TTS_MODELS)
        token=data.get('nextPageToken')
        if not token:break
    return sorted(result,key=lambda r:TTS_MODELS.index(r['id']))


def audio_part(data,modern):
    if modern:
        parts=[p for s in data.get('steps',[]) if s.get('type')=='model_output' for p in s.get('content',[]) if p.get('type')=='audio']
        if not parts and isinstance(data.get('output_audio'),dict):parts=[data['output_audio']]
        return [(p.get('data',''),p.get('mime_type','audio/l16')) for p in parts]
    return [(p['inlineData'].get('data',''),p['inlineData'].get('mimeType','audio/L16;rate=24000'))
            for c in data.get('candidates',[])[:1] for p in c.get('content',{}).get('parts',[]) if 'inlineData' in p]


def synthesize(text,settings,cache,glossary=None,secondary=False):
    from .providers import get_key,request
    from .speech import normalize,SR
    from .voices import DELIVERIES
    model=settings.gemini_modelo_voz
    voice=settings.gemini_voz_secundaria if secondary else settings.gemini_voz
    if model not in TTS_MODELS or voice not in VOICES:raise ValueError('Escolha um modelo e uma voz Gemini válidos.')
    spoken=normalize(text,glossary)
    key=digest(*identity(settings,secondary),spoken)
    wav=cache/(key+'.wav')
    if wav.is_file():return wav,spoken
    headers={'x-goog-api-key':get_key('gemini')}
    style={'natural':'natural, clara e acolhedora','documental':'documental, firme e pausada',
           'reflexiva':'calma e contemplativa','envolvente':'envolvente e expressiva',
           'suspense':'de suspense, com tensão contida e firmeza, mantendo ritmo natural sem alongar palavras',
           'terror':'sombria e séria, como uma história de terror, sem gritos, sussurros inaudíveis ou lentidão artificial',
           'motivacional':'motivacional, acolhedora e confiante, com intenção e ênfase natural, sem gritar, alongar palavras ou recitar de forma teatral',
           'misterio':'investigativa e curiosa, com ênfase discreta nas pistas e ritmo natural'}
    from .narration_styles import MOTIVATIONAL_STYLES
    style.update({key:profile['interpretacao']+', sem alongar palavras, silêncios artificiais ou gritos'
                  for key,profile in MOTIVATIONAL_STYLES.items()})
    style=style[settings.estilo_locucao]
    direction='Português do Brasil, sotaque brasileiro. Narração educativa '+style+'. Sem música ou efeitos sonoros.'
    modern=model.startswith('gemini-3.8-')
    if modern:
        data=request('POST','https://generativelanguage.googleapis.com/v1beta/interactions',headers=headers,json={
            'model':model,'store':False,'input':[{'type':'user_input','content':[{'type':'text','text':spoken,
            'annotations':[{'type':'speech_metadata','style':direction}]}]}],
            'response_format':{'type':'audio','mime_type':'audio/l16','sample_rate':SR},
            'generation_config':{'speech_config':[{'voice':voice}]}})
    else:
        data=request('POST',f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',headers=headers,json={
            'contents':[{'role':'user','parts':[{'text':direction+' Leia somente o texto a seguir:\n'+spoken}]}],
            'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'prebuiltVoiceConfig':{'voiceName':voice}}}}})
    pieces=[]
    try:
        for encoded,mime in audio_part(data,modern):
            if not mime.lower().startswith(('audio/l16','audio/pcm','audio/wav','audio/x-wav')):raise ValueError()
            if len(encoded)>32_000_000:raise ValueError()
            raw=base64.b64decode(encoded,validate=True)
            if raw.startswith(b'RIFF'):
                samples,rate=sf.read(io.BytesIO(raw),dtype='float32',always_2d=True)
                if rate!=SR or samples.shape[1]!=1:raise ValueError()
                samples=samples[:,0]
            else:
                if len(raw)%2 or not raw:raise ValueError()
                samples=np.frombuffer(raw,dtype='<i2').astype('float32')/32768
            pieces.append(samples)
        audio=np.concatenate(pieces) if pieces else np.array([],dtype='float32')
        if not SR*.08<=len(audio)<=SR*180 or not np.isfinite(audio).all() or float(np.max(np.abs(audio)))<.001:raise ValueError()
    except (ValueError,TypeError,binascii.Error,RuntimeError):
        raise ValueError('O Gemini não devolveu áudio válido. Confira o modelo de voz e a cota da API; não será usada uma voz local automaticamente.') from None
    cache.mkdir(parents=True,exist_ok=True)
    temp=wav.with_suffix('.partial.wav')
    try:
        sf.write(temp,audio,SR,subtype='PCM_16')
        pace=settings.velocidade*DELIVERIES[settings.estilo_locucao]['velocidade']
        if abs(pace-1)>1e-6:
            paced=wav.with_suffix('.paced.wav')
            try:
                run([binary('ffmpeg'),'-y','-v','error','-i',temp,'-af',f'atempo={pace:.6f}',paced])
                os.replace(paced,temp)
            finally:paced.unlink(missing_ok=True)
        os.replace(temp,wav)
    finally:temp.unlink(missing_ok=True)
    with open(cache/'gemini-tts-metrics.jsonl','a',encoding='utf-8') as log:
        log.write(json.dumps({'modelo':model,'voz':voice,'instante':time.time(),'uso':data.get('usage',data.get('usageMetadata',{}))})+'\n')
    return wav,spoken
