"""Curated visual meanings, not one generic icon per subject area.

Each composition has a communicative purpose and a closed set of local assets.
Metaphors are illustrations of the script, never new historical/scientific facts.
"""

# id | title | meaning / narrative cues | local subjects | visual grammar
COMPOSITIONS={
'religiao':'''pastor_rebanho|Cuidado do pastor|bom pastor;pastor e rebanho;guiar o rebanho;ovelha perdida;pastorear|pessoa,ovelha|shelter
semente_fe|Semente e fé|grão de mostarda;semente da fé;fé que cresce;semear esperança|planta,sol|growth
caminho_estreito|O caminho estreito|porta estreita;caminho estreito;escolha espiritual;seguir o caminho|porta,pegadas|journey
tempestade_fe|Firmeza na tempestade|tempestade e fé;barco na tempestade;fé na adversidade;acalmar a tempestade|barco,onda_mar,raio|shelter
acolher_retorno|O reencontro e o acolhimento|filho pródigo;acolher o retorno;reconciliação espiritual;voltar para casa|pessoa,familia,casa|bridge
compaixao_proximo|Cuidar do próximo|bom samaritano;amar o próximo;compaixão;ajudar o próximo|pessoas,curativo,coracao_afeto|care
libertacao_espiritual|Libertação interior|libertação espiritual;romper correntes;livrar da culpa;liberdade espiritual|corrente,pomba|release
luz_orientacao|A luz que orienta|luz do mundo;lâmpada para os pés;orientação espiritual;sair das trevas|vela,pegadas|journey''',
'historia':'''rotas_comerciais|Rotas e trocas|rotas comerciais;rota da seda;trocas entre civilizações;comércio antigo|mapa,camelo,moeda|journey
camadas_historia|Vestígios de outras épocas|arqueologia;vestígios históricos;camadas do passado;escavação|anfora,piramide,pergaminho|layers
poder_imperio|Poder e expansão|expansão de impérios;poder imperial;centralização monárquica;império|coroa,arquitetura_classica,mapa|converge
mudanca_industrial|A transformação industrial|revolução industrial;industrialização;da oficina à fábrica;trabalho industrial|ferramentas,fabrica,relogio|sequence
travessias_migracao|Travessias e migração|migração histórica;travessia do oceano;grandes navegações;êxodo|maleta,navio_vela,mapa|journey
documento_direitos|Leis e conquistas|constituição;declaração de direitos;conquista de direitos;documento fundador|pergaminho,lapis,balanca|focus
ruinas_memoria|Ruínas e memória coletiva|ruínas;memória coletiva;patrimônio histórico;preservar o passado|arquitetura_classica,relogio_areia,planta|layers
vontade_popular|Voz coletiva e transformação|revolução política;mobilização popular;participação cidadã;luta por direitos|pessoas,megafone,urna|converge''',
'ciencia':'''hipotese_teste|Da hipótese ao teste|testar uma hipótese;método científico;experimento controlado;hipótese|pergunta,tubo_ensaio,regua|sequence
escala_observacao|Mudança de escala|escala microscópica;do pequeno ao grande;escalas da natureza;observar detalhes|microscopio,atomo,planeta|layers
forcas_equilibrio|Forças em equilíbrio|equilíbrio de forças;ação e reação;forças opostas;balanço de forças|ima,balanca|balance
conexao_genetica|A informação da vida|herança genética;informação genética;expressão dos genes;transmissão genética|dna,planta,pessoas|bridge
busca_evidencia|Evidência e incerteza|evidência científica;avaliar evidências;incerteza científica;prova experimental|tubo_ensaio,regua,pergunta|focus
limites_modelo|O modelo e a realidade|limites de um modelo;modelo científico;representação da realidade;modelo e realidade|atomo,moldura,planeta|split
descoberta_coletiva|Construção coletiva do saber|ciência colaborativa;revisão por pares;descoberta coletiva;conhecimento compartilhado|pessoas,microscopio,aperto_maos|converge
observacao_cosmos|Observar além do alcance|observação astronômica;explorar o cosmos;investigação espacial;observar o universo|telescopio,estrela,galaxia|journey''',
'tecnologia':'''dados_circulacao|Dados em circulação|pacote de dados;tráfego de dados;comunicação digital;dados em rede|computador,rede_digital,servidor|bridge
memoria_processamento|Memória e processamento|memória ram;processamento de dados;cpu e memória;acesso à memória|chip,memoria_ram,computador|sequence
protecao_digital|Proteção da informação|segurança digital;proteção de dados;privacidade digital;criptografia|servidor,cadeado,escudo|shelter
humano_ia|Humano e inteligência artificial|humano e ia;colaboração com ia;inteligência artificial;automação inteligente|pessoa,robo,chip|bridge
acesso_conhecimento|Conexão e acesso|inclusão digital;acesso à internet;barreira digital;conectar pessoas|pessoas,rede_digital,celular|bridge
fragilidade_sistema|Quando um sistema falha|falha de sistema;vulnerabilidade;risco cibernético;dependência tecnológica|servidor,raio,escudo|tension
energia_dispositivo|Energia que sustenta o digital|consumo de energia;eficiência energética digital;bateria e desempenho;economia de bateria|bateria,chip,tomada|balance
sinal_distancia|Sinais que vencem distâncias|sinal de satélite;telecomunicações;transmissão sem fio;comunicação à distância|antena,satelite,planeta|bridge''',
'psicologia':'''memoria_reconstrucao|Memória em reconstrução|memória reconstrutiva;lembrança incompleta;reconstruir lembranças;memória seletiva|cerebro,quebra_cabeca,relogio|layers
atencao_seletiva|O foco e o que fica de fora|atenção seletiva;foco da atenção;cegueira atencional;seleção de estímulos|olho,alvo,moldura|focus
emocao_razao|Emoção e razão|emoção e razão;conflito emocional;decisão emocional;sentir e pensar|cerebro,coracao_afeto,balanca|balance
ansiedade_antecipacao|O peso do futuro|ansiedade;antecipação;preocupação com o futuro;medo do amanhã|cerebro,relogio,nuvem|tension
identidade_reflexo|Quem se vê no espelho|identidade pessoal;autoimagem;autoconhecimento;como me vejo|pessoa,espelho|split
habito_repeticao|O caminho de um hábito|formação de hábitos;comportamento repetitivo;rotina automática;hábito|pegadas,cerebro,relogio|cycle
vies_percepcao|Percepção e seus filtros|viés cognitivo;viés de sobrevivência;percepção distorcida;filtro mental|olho,moldura,cerebro|split
trauma_cuidado|Cuidado e recuperação|trauma emocional;cuidado psicológico;recuperação emocional;ferida emocional|coracao_afeto,curativo,planta|care''',
'filosofia':'''escolha_caminhos|A encruzilhada da escolha|livre arbítrio;escolha moral;encruzilhada;decidir o caminho|pessoa,pegadas,compasso|choice
conhecimento_duvida|Dúvida que abre caminhos|dúvida filosófica;questionar certezas;limites do conhecimento;dúvida metódica|pergunta,porta,olho|journey
tempo_finitude|Tempo e finitude|finitude;impermanência;tempo da vida;consciência da morte|relogio_areia,rosa_murcha,planta|sequence
justica_equidade|O peso da justiça|justiça e equidade;dilema ético;responsabilidade moral;ética|balanca,pessoas,coracao_afeto|balance
realidade_aparencia|O que parece e o que é|aparência e realidade;ilusão e realidade;mito da caverna;sombras da caverna|olho,moldura,vela|split
sentido_existencia|A procura de sentido|sentido da vida;propósito existencial;existência;busca de significado|pessoa,compasso,estrela|journey
liberdade_limites|Liberdade e seus limites|liberdade e responsabilidade;limites da liberdade;libertação;autonomia|corrente,porta,pomba|release
equilibrio_estoico|Firmeza diante do mundo|estoicismo;controle do que depende de nós;serenidade;aceitar o incontrolável|ancora,onda_mar,pessoa|shelter''',
'corpo':'''circulacao_vida|O movimento da circulação|circulação sanguínea;oxigenação;fluxo sanguíneo;transporte de oxigênio|coracao,pulmoes,agua|cycle
sono_restauracao|Descanso e recuperação|sono reparador;recuperação durante o sono;descansar a mente;higiene do sono|cama,lua,cerebro|care
alimentacao_energia|Do alimento à energia|alimentação equilibrada;energia do corpo;nutrição;metabolismo|maca,agua,raio|sequence
corpo_movimento|O corpo em movimento|atividade física;movimento corporal;condicionamento físico;exercício|osso,coracao,bicicleta|bridge
defesa_organismo|As defesas do organismo|sistema imunológico;defesa do organismo;imunidade;proteção imunológica|escudo,placa_petri,seringa|shelter
sentidos_mundo|As portas dos sentidos|percepção sensorial;sentidos humanos;informação sensorial;estímulos sensoriais|olho,ouvido,mao|converge
saude_prevencao|Cuidar antes de adoecer|prevenção em saúde;exames preventivos;cuidado com a saúde;prevenir doenças|estetoscopio,escudo,coracao|care
reabilitacao_progresso|Recuperação passo a passo|reabilitação;recuperação física;fisioterapia;retomar movimentos|curativo,pegadas,escada|growth''',
'terror':'''presenca_invisivel|A presença que não se vê|presença invisível;algo atrás da porta;ameaça desconhecida;presença oculta|porta,olho,fantasma|tension
sombra_incerteza|O que a sombra esconde|medo do desconhecido;sombras ameaçadoras;incerteza e medo;escuridão|lanterna,porta,lua|focus
tempo_ameaca|O tempo que se esgota|contagem regressiva;ameaça iminente;tempo se esgotando;suspense|relogio_areia,porta,cranio|tension
vestigio_abandono|Vestígios de abandono|casa abandonada;lugar esquecido;abandono;ruína assustadora|casa,teia,vela|layers
limiar_misterio|O limiar do mistério|atravessar o desconhecido;limiar;porta proibida;segredo oculto|porta,chave,lanterna|journey
fragilidade_vida|A fragilidade da vida|mortalidade;vida e morte;fragilidade da vida;lembrança da morte|rosa_murcha,cranio,vela|sequence
isolamento_noite|Sozinho na noite|isolamento;solidão noturna;desamparo;sozinho no escuro|pessoa,lua,arvore|tension
enigma_sinais|Ler os sinais do enigma|enigma;mistério a resolver;pistas ocultas;decifrar sinais|chave,pegadas,pergaminho|converge''',
'natureza':'''ciclo_agua|A viagem da água|ciclo da água;evaporação e chuva;água na natureza;circulação da água|agua,nuvem,chuva|cycle
equilibrio_ecossistema|Uma rede de vida|equilíbrio ecológico;ecossistema;interdependência;cadeia alimentar|arvore,abelha,flor|bridge
renovacao_natureza|A renovação da vida|renovação natural;ciclo das estações;renascer na natureza;crescimento|folha,planta,arvore|sequence
raizes_permanencia|Raízes e permanência|raízes;pertencimento à terra;força das raízes;vínculo com a natureza|tronco,planta,arvore|layers
impacto_ambiental|O impacto das escolhas|impacto ambiental;poluição industrial;pressão sobre a natureza;degradação ambiental|fabrica,planeta,folha|tension
agua_escassa|O valor de uma gota|escassez de água;seca;preservar água;recursos hídricos|agua,cacto,sol|balance
metamorfose_vida|Mudança que transforma|metamorfose;transformação natural;mudança de fase;transformação da vida|planta,borboleta,flor|sequence
protecao_biodiversidade|Proteger a diversidade|biodiversidade;preservação ambiental;conservar espécies;proteção da natureza|escudo,arvore,borboleta|shelter''',
'espaco':'''escala_universo|Nosso lugar no universo|escala do universo;imensidão do cosmos;lugar da terra;pequenez humana|pessoa,planeta,galaxia|layers
viagem_espacial|A travessia espacial|exploração espacial;viagem espacial;missão espacial;chegar à lua|foguete,planeta,lua|journey
ciclos_celestes|Ritmos do céu|ciclos celestes;dia e noite;movimento dos astros;ciclo lunar|sol,planeta,lua|cycle
luz_distancia|A luz e a distância|luz das estrelas;distância cósmica;olhar o passado;anos luz|estrela,telescopio,relogio|bridge
forcas_planetarias|Equilíbrio no espaço|gravidade;órbita;atração gravitacional;equilíbrio orbital|planeta,lua,ima|cycle
atmosfera_protecao|O abrigo da atmosfera|atmosfera;proteção do planeta;camada protetora;vida na terra|planeta,nuvem,escudo|shelter
clima_extremos|Entre extremos|eventos extremos;mudanças climáticas;instabilidade climática;crise climática|planeta,raio,tornado|tension
buscar_horizontes|Além do horizonte|novos horizontes;fronteira espacial;ir além do conhecido;descobrir o cosmos|telescopio,foguete,estrela|journey''',
'sociedade':'''cooperacao_trabalho|Construir em conjunto|trabalho em equipe;cooperação;esforço coletivo;colaboração|pessoas,ferramentas,aperto_maos|converge
peso_desigualdade|O peso da desigualdade|desigualdade social;diferença de oportunidades;injustiça social;concentração de riqueza|balanca,dinheiro,pessoas|balance
voz_participacao|Voz e participação|participação social;democracia;direito à voz;decisão coletiva|pessoas,urna,megafone|converge
confianca_instituicoes|O pacto de confiança|confiança nas instituições;pacto social;responsabilidade pública;instituições|arquitetura_classica,aperto_maos,escudo|bridge
trabalho_tempo|Trabalho e tempo de vida|equilíbrio entre vida e trabalho;sobrecarga de trabalho;tempo de trabalho;exaustão profissional|maleta,relogio,coracao_afeto|balance
acesso_oportunidade|A porta das oportunidades|oportunidade;mobilidade social;acesso à educação;abrir oportunidades|porta,escada,formatura|journey
economia_escolhas|Escolhas e recursos|uso de recursos;escolhas financeiras;consumo consciente;planejamento financeiro|moeda,balanca,alvo|choice
comunidade_abrigo|Uma comunidade que acolhe|comunidade;apoio comunitário;solidariedade;pertencimento social|casa,familia,coracao_afeto|shelter''',
'cotidiano':'''cidade_movimento|Os caminhos da cidade|mobilidade urbana;vida na cidade;deslocamento diário;transporte urbano|onibus,bicicleta,carro|bridge
casa_seguranca|O lugar de acolhimento|segurança do lar;sentir se em casa;acolhimento no lar;abrigo|casa,chave,coracao_afeto|shelter
rotina_pausa|Uma pausa na rotina|pausa na rotina;momento de descanso;diminuir o ritmo;respirar na rotina|cafe,relogio,cadeira|care
planejar_jornada|Preparar a jornada|planejar uma viagem;preparar o caminho;planejamento diário;organização pessoal|mapa,compasso,maleta|journey
alimentacao_compartilhar|A mesa e o encontro|partilhar alimento;refeição em família;mesa compartilhada;hospitalidade|pao,queijo,pessoas|converge
escolha_cotidiana|Pequenas escolhas|escolhas diárias;decisões do cotidiano;pequenas decisões;rotas alternativas|pessoa,semaforo,bicicleta|choice
tempo_presente|Estar no presente|viver o presente;atenção plena;apreciar o agora;momento presente|relogio,flor,pessoa|focus
cuidar_espaco|Cuidar do próprio espaço|organizar a casa;cuidar do espaço;ambiente acolhedor;harmonia no lar|casa,planta,vela|care''',
'cultura':'''ideia_criacao|Da ideia à criação|processo criativo;criar uma obra;expressar uma ideia;criação artística|lampada,lapis,paleta|sequence
narrativa_sentido|Como uma história ganha sentido|construção narrativa;contar histórias;estrutura narrativa;significado da história|pessoa,claquete,pegadas|journey
arte_olhar|Outras formas de enxergar|olhar artístico;arte e percepção;interpretar uma obra;ver de outra forma|olho,paleta,moldura|split
conhecimento_portas|Aprender abre caminhos|aprendizagem;educação transforma;aprender algo novo;abrir a mente|escola,porta,planta|growth
musica_emocao|O som e o sentimento|emoção na música;música e memória;expressão musical;poder da música|violao,coracao_afeto,cerebro|bridge
palavra_transformacao|A palavra que transforma|força da palavra;comunicar uma ideia;palavra e ação;escrita criativa|lapis,megafone,planta|sequence
memoria_cultural|O que uma cultura preserva|memória cultural;tradição;identidade cultural;herança cultural|mascaras,pergaminho,pessoas|layers
informacao_criterio|Separar informação e ruído|pensamento crítico;verificar informação;desinformação;análise crítica|jornal,moldura,balanca|split''',
'conceitos':'''clareza_visual|O significado em foco|imagem clara;clareza visual;uma imagem para cada assunto;explicação clara|moldura,olho,alvo|focus
ligar_ideias|Conectar as peças|conectar ideias;integrar conhecimento;ligar os pontos;compreensão|quebra_cabeca,cerebro,ponte|bridge
foco_prioridades|O que merece atenção|prioridade;focar no essencial;concentrar esforços;foco|alvo,olho,relogio|focus
pequenos_passos|A força dos pequenos passos|pequenos passos;progresso gradual;um passo de cada vez;constância|pegadas,escada,planta|growth
equilibrio_escolhas|Encontrar equilíbrio|equilíbrio de escolhas;ponderar alternativas;avaliar opções;equilibrar|balanca,compasso,pessoa|balance
abrir_possibilidades|Uma possibilidade se abre|nova possibilidade;abrir possibilidades;descobrir alternativas;novo caminho|porta,estrela,planta|release
objetivo_horizonte|O objetivo no horizonte|perseguir um objetivo;visão de futuro;meta de vida;rumo ao objetivo|compasso,alvo,montanha|journey
coragem_agir|O instante de agir|coragem para agir;tomar iniciativa;sair da inércia;agir apesar do medo|pessoa,porta,raio|release''',
'relacoes':'''ponte_dialogo|A ponte do diálogo|diálogo;escuta mútua;conversar para compreender;entendimento entre pessoas|pessoas,ouvido,ponte|bridge
confianca_vinculo|O vínculo da confiança|confiança entre pessoas;vínculo afetivo;confiar no outro;construir confiança|aperto_maos,corrente,coracao_afeto|bridge
reparar_ruptura|Reparar um vínculo|reparar uma relação;reconciliação;perdão;restaurar confiança|coracao_afeto,curativo,aperto_maos|care
empatia_perspectiva|Ver pela perspectiva do outro|empatia;perspectiva do outro;compreender sentimentos;se colocar no lugar|pessoas,olho,coracao_afeto|split
limites_saudaveis|Proteger sem se fechar|limites saudáveis;autoproteção;respeito aos limites;preservar o espaço|pessoa,escudo,porta|shelter
solidao_conexao|Da solidão à conexão|superar a solidão;criar laços;conexão humana;reencontro|pessoa,ponte,pessoas|journey
cuidado_reciproco|O cuidado que circula|cuidado recíproco;apoio mútuo;relação de cuidado;reciprocidade|pessoas,coracao_afeto,planta|cycle
despedida_memoria|O que permanece após a despedida|despedida;luto afetivo;saudade;memória de quem partiu|pessoa,rosa_murcha,relogio_areia|layers''',
'desafios':'''recomeco_caminho|Um caminho para recomeçar|recomeço;começar de novo;retomar a vida;novo começo|pegadas,planta,sol|journey
resiliencia_tempestade|Permanecer de pé|resiliência;resistir à adversidade;força na dificuldade;enfrentar a tempestade|arvore,raio,ancora|shelter
medo_coragem|A travessia do medo|superar o medo;coragem;enfrentar o desconhecido;agir com medo|pessoa,ponte,lanterna|journey
queda_aprendizado|Aprender com a queda|aprender com o erro;fracasso e aprendizado;superação do fracasso;erro como aprendizado|escada,curativo,planta|sequence
paciencia_crescimento|O tempo do crescimento|paciência;amadurecimento;respeitar o tempo;esperar o momento|relogio_areia,planta,arvore|growth
persistencia_subida|Continuar a subida|persistência;perseverança;não desistir;esforço continuado|pegadas,montanha,alvo|journey
esperanca_horizonte|Um horizonte possível|esperança;acreditar no futuro;enxergar uma saída;amanhecer|sol,porta,planta|release
autocuidado_limites|A força de respeitar limites|autocuidado;respeitar os próprios limites;descansar sem culpa;recuperar energia|escudo,coracao_afeto,cama|care''',
}

def compositions():
    rows=[]
    for group,lines in COMPOSITIONS.items():
        for line in lines.splitlines():
            key,name,terms,subjects,grammar=line.split('|')
            rows.append({'id':key,'nome':name,'termos':terms.split(';'),'sujeitos':subjects.split(','),
                'gramatica':grammar,'grupo':group,'codigo':'composite','arquivo':key+'.svg',
                'sentido':terms.split(';')[0],'previa':'/api/shotcraft/figures/'+key+'/preview'})
    return rows
