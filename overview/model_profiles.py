"""Portuguese model cards; purpose suggestions are editorial guidance, not benchmarks."""
import re
LOCAL_MODELS={
    'qwen2.5:1.5b':('Qwen 2.5 1.5B','Escrita e revisão · 1.5B local',
        'Opção leve para testar rascunhos e roteiros curtos. Revise os fatos e a fidelidade às fontes.'),
    'qwen2.5:3b':('Qwen 2.5 3B','Escrita e revisão · 3B local',
        'Alternativa de 3B para testar planejamento e escrita. Requer mais memória que a versão de 1.5B; revise o resultado.'),
    'qwen3:14b':('Qwen 3 14B','Texto local, sem chave de API',
        'Planeja, escreve e revisa o roteiro nesta máquina. É o modelo local padrão do Clareia.'),
    'qwen3.5:9b':('Qwen 3.5 9B','Organização de ideias e texto · 9B local',
        'Alternativa local de 9B para estudo, planejamento, escrita e revisão. Neste fluxo, o modelo recebe os trechos textuais de estudo.'),
    'gemma4:12b':('Gemma 4 12B','Compreensão e produção de texto · 12B local',
        'Alternativa local de 12B para estudar as fontes, planejar e escrever o roteiro. Neste fluxo, o modelo recebe os trechos textuais de estudo.'),
}


def describe(provider, model):
    item=dict(model)
    name=item['id'].lower()
    metadata=item.get('descricao_catalogo','').lower()
    headline=metadata.split('. ')[0][:500]
    if provider=='local':
        specialty='Texto local, sem chave de API'
        use='Planeja, escreve e revisa o roteiro nesta máquina. Útil para trabalhar sem enviar as fontes a um serviço externo.'
        source=''
        if name in LOCAL_MODELS:
            item['nome'],specialty,use=LOCAL_MODELS[name]
            source='https://ollama.com/library/'+name
    elif provider=='gemini':
        source='https://ai.google.dev/gemini-api/docs/models'
        if 'argon' in name:
            specialty='Raciocínio e contextos extensos'
            use='Opção para materiais extensos e relações difíceis: organizar o conteúdo, conferir coerência e desenvolver explicações em várias etapas.'
        elif 'flash-lite' in name:
            specialty='Respostas rápidas e eficiência de custo'
            use='Útil para resumos, primeiros rascunhos e aulas de assunto direto. Revise com atenção os conceitos mais difíceis.'
        elif 'pro' in name:
            specialty='Raciocínio avançado'
            use='Opção para temas complexos e revisão detalhada. Os limites variam por modelo e projeto; confira o teste de resposta e o painel do AI Studio.'
        elif 'flash' in name:
            specialty='Tarefas gerais e explicações em várias etapas'
            use='Útil para criar e revisar roteiros e explicações gerais. Disponibilidade e limites variam por modelo e projeto; o catálogo não garante acesso à geração.'
        else:
            specialty='Compreensão e produção de texto'
            use='Pode escrever e revisar explicações. Confira a descrição do catálogo e avalie um roteiro antes de usar em um projeto maior.'
    elif provider=='groq':
        source='https://console.groq.com/docs/models'
        specialty='Raciocínio e produção de texto na nuvem'
        use='Organiza explicações, escreve e revisa o roteiro ou prepara uma fonte de estudo. Avalie a fidelidade aos fatos e às fontes antes de publicar.'
    else:
        source='https://openrouter.ai/models/'+item['id']
        if name=='openrouter/free':
            specialty='Escolha automática entre modelos gratuitos'
            use='O OpenRouter escolhe um modelo gratuito disponível. A identidade do modelo e o resultado podem variar entre as chamadas.'
        elif any(term in name for term in ('coder','-code','laguna')) or re.search(r'\b(?:coding|code)[ -](?:agent|model|generation)\b',headline):
            specialty='Programação e código'
            use='Mais adequado para aulas de programação, algoritmos e exemplos de código. Para outros assuntos, prefira um modelo de texto geral.'
        elif any(term in name+' '+headline for term in ('reasoning','raciocínio','mathematical')):
            specialty='Raciocínio e resolução de problemas'
            use='Opção para construir explicações com etapas, resolver exemplos e revisar a lógica da aula. Confira a fidelidade às fontes.'
        elif 'image' in item.get('modalidades_entrada',[]):
            specialty='Texto e compreensão multimodal'
            use='Entende texto e também pode aceitar imagens na API. Neste aplicativo, a escrita do roteiro recebe somente os trechos textuais de estudo.'
        else:
            specialty='Compreensão e produção de texto'
            use='Útil para rascunhos, explicações e sínteses. Faça uma amostra para avaliar clareza, português e qualidade dos exemplos.'
    item.update(especialidade=specialty,uso_no_roteiro=use,fonte_descricao=source,
        observacao=('Sugestão de uso, não uma nota de qualidade. Gratuidade e cotas dependem da sua conta no Gemini.'
                    if provider=='gemini' else 'Disponível no plano Free da Groq, sujeito a cotas. Use chave de uma organização Free; em organização paga, o mesmo modelo pode gerar cobrança. O catálogo não informa o plano da chave.'
                    if provider=='groq' else 'Sugestão de uso, não uma nota de qualidade. Modelos gratuitos têm cotas e disponibilidade variável.'
                    if provider=='openrouter' else 'O processamento do roteiro permanece local.'))
    return item
