"""Public diagnostics extracted from API status/typed details, never raw bodies."""
import math
import re


class ProviderError(ValueError):
    def __init__(self,message,diagnostic):
        super().__init__(message)
        self.diagnostic=diagnostic


def seconds(value):
    try:
        n=float(str(value).removesuffix('s'))
        return n if math.isfinite(n) and 0<=n<=86400 else None
    except (TypeError,ValueError):return None


def diagnose(response,provider,model=''):
    code=response.status_code
    try:data=response.json()
    except (ValueError,TypeError):data={}
    error=data.get('error',{}) if isinstance(data,dict) else {}
    if not isinstance(error,dict):error={}
    details=error.get('details',[])
    if not isinstance(details,list):details=[]
    retry=seconds(response.headers.get('retry-after'))
    limits=[]
    for d in details:
        if not isinstance(d,dict):continue
        if d.get('@type','').endswith('RetryInfo'):
            delay=seconds(d.get('retryDelay'))
            if delay is not None:retry=delay
        violations=d.get('violations',[])
        if not isinstance(violations,list):continue
        for v in violations:
            if not isinstance(v,dict):continue
            label=(str(v.get('quotaMetric',''))+' '+str(v.get('quotaId',''))).lower()
            per_day=bool(re.search(r'per.?day|daily|dia',label))
            per_minute=bool(re.search(r'per.?minute|minute|rpm|tpm',label))
            token='token' in label
            kind=('TPD' if token else 'RPD') if per_day else ('TPM' if token else 'RPM') if per_minute else 'outro'
            try:
                value=float(v.get('quotaValue'))
                if not math.isfinite(value) or not 0<=value<=1e15:value=None
            except (TypeError,ValueError):value=None
            limits.append({'tipo':kind,'valor':value})
    raw_message=error.get('message','')
    raw_message=raw_message[:6000] if isinstance(raw_message,str) else ''
    # Some Google QuotaFailure payloads omit quotaValue and state it only here.
    explicit_zero=bool(re.search(r'\blimit:\s*0(?:\.0+)?(?=\s|,|$)',raw_message,re.I))
    if retry is None:
        matched=re.search(r'\bretry in\s+(\d+(?:\.\d+)?)s',raw_message,re.I)
        if matched:retry=seconds(matched.group(1))
    if provider=='groq' and code==429:
        # Documented headers: requests are per day; tokens are per minute.
        for suffix,kind in (('requests','RPD'),('tokens','TPM')):
            if response.headers.get('x-ratelimit-remaining-'+suffix)=='0':
                value=seconds(response.headers.get('x-ratelimit-limit-'+suffix))
                limits.append({'tipo':kind,'valor':value})
    zero=any(l['valor']==0 for l in limits) or (explicit_zero and provider=='gemini')
    daily=any(l['tipo'] in ('RPD','TPD') for l in limits)
    minute=any(l['tipo'] in ('RPM','TPM') for l in limits)
    name={'gemini':'Gemini','openrouter':'OpenRouter','groq':'GroqCloud'}.get(provider,provider)+(f' · {model}' if model else '')
    if code==429:
        if zero and provider=='gemini':
            kind='sem_cota_modelo';message=f'{name}: o Google informou cota zero para este modelo no projeto da chave. Isso indica ausência de cota liberada nesse nível, não que você consumiu 100% da sua cota total. Confira o acesso e os limites do modelo no AI Studio.'
        elif zero:
            kind='sem_cota_modelo';message=f'{name}: o provedor não liberou cota para este modelo. Confira o plano e os limites no painel do provedor.'
        elif daily:
            kind='limite_diario';message=f'{name}: a API informou um limite diário deste modelo/projeto (RPD ou TPD). O consumo total de outros modelos pode continuar baixo. Confira o limite diário no painel do provedor.'
        elif minute:
            kind='limite_minuto';message=f'{name}: a API informou limite por minuto (RPM ou TPM). Isso não significa que sua cota total acabou.'
        else:
            kind='limite_nao_especificado';message=f'Cota ou limite temporário da API ({name}, HTTP 429). O provedor não especificou qual limite foi atingido; não é possível concluir que sua cota total acabou.'
        known=[f"{l['tipo']}={l['valor']:g}" for l in limits if l['tipo']!='outro' and l['valor'] is not None]
        if known:message+=' Limite informado pela API: '+', '.join(known)+'.'
        if retry and not daily and not zero:message+=f' Aguarde cerca de {math.ceil(retry)} segundos antes de retomar.'
    elif code in (500,502,503,504):
        kind='indisponivel';message=f'{name}: serviço temporariamente indisponível ou sobrecarregado (HTTP {code}). Esse erro não indica cota esgotada. Aguarde e tente novamente.'
    else:
        kind={400:'formato',401:'chave',402:'saldo',403:'acesso',404:'modelo'}.get(code,'http')
        message={400:'Modelo ou formato não aceito pela API.',401:'Chave de API inválida.',402:'A API recusou por saldo ou limite da conta.',403:'Chave sem acesso ao modelo ou serviço.',404:'Modelo indisponível. Atualize o catálogo e escolha outro.'}.get(code,f'API indisponível (HTTP {code}).')
    return {'provedor':provider,'modelo':model,'http':code,'tipo':kind,'espera_s':retry,'limites':limits,'mensagem':message,
            'repetir':code in (429,500,502,503,504) and not zero and not daily}
