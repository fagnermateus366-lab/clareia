"""Editorial tones and modest delivery presets, independent of speaker identity."""
from typing import Literal

ScriptTone = Literal['didático','jornalístico','conversa','motivacional','motivacional_intenso',
    'motivacional_suave','motivacional_acolhedor','motivacional_epico','motivacional_determinado','motivacional_reflexivo']

MOTIVATIONAL_STYLES = {
    'motivacional': {
        'nome':'Motivacional · presença e confiança','velocidade':1.02,'pausa':.17,'pitch':1.,'limite_pausa':.32,
        'escrita':'Reconheça a dificuldade, mostre uma possibilidade concreta e incentive um primeiro passo com empatia e confiança.',
        'interpretacao':'presente, acolhedora e confiante, com ênfase natural nas ações e incentivo a passos possíveis',
        'descricao':'Incentivo equilibrado e firme. Um ponto de partida para mensagens de superação.'},
    'motivacional_intenso': {
        'nome':'Motivacional · intenso e marcante','velocidade':1.06,'pausa':.14,'pitch':1.,'limite_pausa':.27,
        'escrita':'Crie energia crescente, contrastes concretos e verbos de ação. Conecte períodos curtos e médios, terminando com uma decisão prática. Firmeza sem agressividade ou humilhação.',
        'interpretacao':'intensa, enérgica e marcante, com impulso e ênfase nos verbos de ação, sem gritar',
        'descricao':'Mais energia e ritmo direto, para mensagens de virada e superação. Sem gritos ou palavras esticadas.'},
    'motivacional_suave': {
        'nome':'Motivacional · suave e sereno','velocidade':.99,'pausa':.18,'pitch':1.,'limite_pausa':.34,
        'escrita':'Incentive sem pressionar. Use imagens cotidianas e uma progressão tranquila até um passo acessível. Prefira frases conectadas e claras; suavidade não significa arrastar a fala.',
        'interpretacao':'suave, serena e próxima, com leveza e fluidez, sem voz sonolenta',
        'descricao':'Incentivo tranquilo e fluido, adequado a recomeços. Mantém o ritmo próximo do natural.'},
    'motivacional_acolhedor': {
        'nome':'Motivacional · acolhedor e humano','velocidade':1.,'pausa':.18,'pitch':1.,'limite_pausa':.34,
        'escrita':'Valide a dificuldade sem assumir sentimentos do público. Fale como numa conversa de apoio, reconheça limites e convide a uma ação possível sem julgar ou infantilizar.',
        'interpretacao':'acolhedora, humana e empática, como uma conversa próxima e respeitosa',
        'descricao':'Conversa de apoio, com presença e empatia. Combine com uma voz de que você goste.'},
    'motivacional_epico': {
        'nome':'Motivacional · épico e inspirador','velocidade':1.03,'pausa':.19,'pitch':1.,'limite_pausa':.34,
        'escrita':'Construa um arco crescente de dificuldade, escolha e conquista possível. Use uma metáfora concreta e um fechamento memorável que retome a abertura. Evite grandiloquência, clichês e promessas de vitória garantida.',
        'interpretacao':'inspiradora, ampla e crescente, com um fechamento marcante e firme, sem teatralidade excessiva',
        'descricao':'Progressão de conquista e fechamento marcante. A interpretação expressiva depende do motor da voz.'},
    'motivacional_determinado': {
        'nome':'Motivacional · foco e determinação','velocidade':1.04,'pausa':.15,'pitch':1.,'limite_pausa':.29,
        'escrita':'Organize a mensagem em decisão, atitude concreta e continuidade. Use linguagem objetiva, verbos específicos e um compromisso pequeno que a pessoa possa cumprir hoje. Disciplina sem culpa ou pressão abusiva.',
        'interpretacao':'determinada, objetiva e segura, com dicção firme e ritmo contínuo',
        'descricao':'Cadência firme e objetiva para foco, constância e disciplina, sem pausas longas.'},
    'motivacional_reflexivo': {
        'nome':'Motivacional · reflexivo e profundo','velocidade':.98,'pausa':.20,'pitch':1.,'limite_pausa':.36,
        'escrita':'Parta de uma observação cotidiana ou pergunta breve. Desenvolva seu significado com um exemplo concreto e termine com uma escolha possível. Profundidade com linguagem simples e continuidade, sem fragmentar frases para criar silêncio.',
        'interpretacao':'reflexiva, sincera e contemplativa, com intenção e continuidade, sem lentidão artificial',
        'descricao':'Espaço para refletir com continuidade. Evita transformar reflexão em fala excessivamente lenta.'},
}

TONES = [
    {'id':'didático','nome':'Didático','grupo':'Explicação'},
    {'id':'jornalístico','nome':'Jornalístico','grupo':'Explicação'},
    {'id':'conversa','nome':'Conversa','grupo':'Explicação'},
] + [{'id':key,'nome':style['nome'],'grupo':'Motivacional','descricao':style['escrita']}
     for key,style in MOTIVATIONAL_STYLES.items()]

# These are transparent combinations of existing speakers and delivery modes,
# not extra models or copies of real narrators' voices.
VOICE_PRESETS = [
    {'id':'antonio_intenso','nome':'Antonio · intenso e marcante','voz':'ms_antonio','tom':'motivacional_intenso'},
    {'id':'francisca_acolhedora','nome':'Francisca · acolhedora e humana','voz':'ms_francisca','tom':'motivacional_acolhedor'},
    {'id':'thalita_suave','nome':'Thalita · suave e serena','voz':'ms_thalita','tom':'motivacional_suave'},
    {'id':'santa_reflexivo','nome':'Santa · reflexivo e profundo','voz':'pm_santa','tom':'motivacional_reflexivo'},
    {'id':'alex_determinado','nome':'Alex · foco e determinação','voz':'pm_alex','tom':'motivacional_determinado'},
    {'id':'cadu_epico','nome':'Cadu · épico e inspirador','voz':'piper_cadu','tom':'motivacional_epico'},
    {'id':'brian_epico','nome':'Brian · épico e inspirador · multilíngue','voz':'ms_brian','tom':'motivacional_epico'},
    {'id':'andrew_intenso','nome':'Andrew · intenso e marcante · multilíngue','voz':'ms_andrew','tom':'motivacional_intenso'},
    {'id':'emma_acolhedora','nome':'Emma · acolhedora e humana · multilíngue','voz':'ms_emma','tom':'motivacional_acolhedor'},
]


def tone_guide(settings):
    style=MOTIVATIONAL_STYLES.get(settings.tom)
    if not style:return ''
    return ('\nTOM DO ROTEIRO: '+style['nome']+'. '+style['escrita']+
        ' Preserve a estrutura escolhida, os fatos e a intenção do autor. Use português brasileiro falado. '
        'Não escreva rubricas, SSML, instruções de atuação ou efeitos sonoros no texto narrado.\n')
