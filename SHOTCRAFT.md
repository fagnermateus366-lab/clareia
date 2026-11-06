# Biblioteca manual · ShotCraft

A opção **Animação → Novos modelos · ShotCraft** acrescenta um motor Remotion
separado. Os estilos anteriores continuam disponíveis no motor original.

## Escolher e aplicar

**Explorar 36 movimentos** abre a biblioteca com busca, seis categorias,
descrição, uso sugerido, fonte e prévia animada. **Usar no projeto** define o
padrão. Cada cena tem **Escolher na biblioteca → Usar nesta cena**; salve a
revisão para aplicar. É possível manter um mesmo movimento no vídeo inteiro
ou escolher outros manualmente. Não há mistura obrigatória de estilos.

O catálogo inclui dez modelos de composição: tipografia de estúdio, estúdio
2,5D, mural editorial, canvas luminoso, cartões e carrosséis, vidro e luz,
mesa digital, diagramas, impacto e retrô. Veja todos os movimentos e usos em
[CATALOGO_ANIMACOES.md](CATALOGO_ANIMACOES.md).

O seletor **Modelo de animação** filtra os movimentos. **Todos os modelos**
exibe o catálogo completo. Acabamento e cores são independentes do modelo;
a intensidade controla a energia do movimento. Configurações antigas com
`auto` continuam legíveis e usam um padrão estável do modelo, sem autorizar
a IA a trocar de estilo.

Cada demonstração da galeria é silenciosa, não chama IA nem síntese de voz e
usa o mesmo componente da exportação. A primeira preparação pode levar mais
tempo; a prévia pronta fica em cache. **Ver animações → Testar com esta voz**
permite conferir a narração real. **Ver conteúdo das animações** mostra o
conteúdo organizado por frase no movimento escolhido. Planos antigos não
são apresentados como atuais após uma alteração no roteiro ou nas opções.

Funciona em vídeo comum e Reels / Shorts com **Animações adaptadas**. No
celular, as proporções se reorganizam e aproveitam a tela quando as legendas
grandes estão desligadas.
Reels com fotos e clipes continuam usando seu motor de sequência.

## Figuras por assunto

O novo acervo tem **302 ilustrações vetoriais em 16 assuntos**, incluindo
tecnologia, religiões, história, terror, ciência, corpo, natureza e cotidiano.
Abra **Conhecer 302 figuras**. Nas cenas, **Escolher figuras** permite fixar
até quatro itens; vazio mantém a escolha por contexto. O acervo é separado
do Vox. Veja [FIGURAS_SHOTCRAFT.md](FIGURAS_SHOTCRAFT.md).

Nas configurações do vídeo, **Seleção das figuras** oferece duas opções:

- **Flexível por tema · continuar o vídeo** (padrão): procura primeiro a figura específica; quando não existe, usa uma ilustração mais ampla da frase ou do tema da cena. A falta de correspondência exata não interrompe o fluxo nem deixa cartões vazios. Nos modelos 3D, só usa objetos que têm malhas disponíveis.
- **Rigoroso por trecho · revisar quando faltar**: exige uma figura ou metáfora sustentada por cada trecho. Quando falta, interrompe a geração e destaca a cena para revisão.

A escolha é salva no projeto e nas configurações favoritas, incluindo a retomada e os agendamentos. Projetos antigos sem esse campo usam o modo flexível. Figuras manuais válidas têm prioridade. Ambos os modos preservam a narração e os rótulos aprovados; os nomes das figuras de apoio não viram texto do roteiro. Os créditos usados acompanham o MP4 em `creditos-shotcraft.md`.

Grades com uma linha incompleta centralizam os elementos dessa linha.
Com três cartões no Reels, os dois primeiros ficam em cima e o terceiro
fica no centro da linha de baixo.

## Orientação para as IAs

A IA organiza títulos, rótulos, foco e relações dentro da receita escolhida
pelo usuário. A escolha da cena prevalece sobre a do projeto. O servidor
impõe essa escolha mesmo que a resposta do modelo sugira outra receita.

O escritor recebe instruções de intenção visual, sem rubricas na fala. Após
a aprovação, a organização visual usa a mesma IA do roteiro ou a IA específica
selecionada: Ollama, Gemini, OpenRouter ou GroqCloud. Cada chamada organiza
até quatro frases e recebe apenas o guia da receita selecionada, poupando
tokens. A resposta segue um esquema fechado. Código, HTML e programas
fornecidos pela IA nunca são executados.

Comparações exigem dois lados narrados; redes e diagramas só desenham
conexões sustentadas pela fala. O padrão visual é preservado mesmo quando
não há relação para conectar. As interfaces sem captura fornecida aparecem
como maquetes ilustrativas. O painel de código exibe texto aprovado e não
inventa programas, estatísticas ou resultados de ferramentas.

A narração aprovada não é reescrita nem esticada para caber num efeito. O tempo
vem do áudio. Os dados usados ficam em `export/storyboard.json` e o plano fica
em cache. As fotos escolhidas são usadas pelos modelos que têm área de
imagem. Sem foto, os modelos ilustrados usam figuras selecionadas pelo contexto. Não
são filmagens realistas geradas por difusão.

## Desempenho e instalação

O Remotion e seu navegador de renderização estão isolados em
`overview/shotcraft_renderer/`. Uma página renderiza por vez. A animação
silenciosa fica em cache, e o pipeline existente acrescenta voz, legendas,
música e transições. O decodificador mantém um quadro por vez. Pausar
interrompe apenas os processos dessa renderização e preserva a narração.

A primeira renderização dos modelos novos pode consumir mais tempo e
memória que os estilos antigos. Não se promete desempenho igual. Cache,
resolução, duração, imagens e efeitos influenciam o custo. O marcador de
cache registra tempo e soma de RSS dos processos, uma estimativa que pode
contar memória compartilhada mais de uma vez.

O motor está instalado nesta máquina de desenvolvimento. Para preparar
outra instalação, use `instalar-shotcraft.bat` com Node.js disponível e depois
`atualizar-estudio.bat`. Os estilos anteriores não dependem de Remotion.

Origem: https://github.com/Vincentwei1021/video-shotcraft, revisão fixa
`43bd349a136651865ecfa6ea1cf012f6e957d304`, copyright 2026 Wei Yihao, Apache-2.0.
Receitas, componentes selecionados, licença e hashes estão em
`third_party/video-shotcraft/`. O Remotion tem sua própria licença:
https://www.remotion.dev/license

## Prévia imediata e legendas

A galeria tem 576 exemplos prontos (36 movimentos × quatro paletas × dois formatos × dois acabamentos).
Ao selecionar outro movimento, o exemplo aparece na lateral imediatamente. A
demonstração animada carrega no mesmo espaço; se o estúdio estiver ocupado, a
imagem de composição permanece disponível.

Em **Exibição das legendas**, desligue **Mostrar legendas grandes e palavras em
destaque** para ampliar a animação no Reels. A legenda pequena do rodapé tem
controle independente, fundo escuro, transparente, claro ou personalizado e cor
das letras. Para não mostrar nenhuma, desligue as grandes e escolha **Não mostrar**
no rodapé. Os arquivos SRT continuam disponíveis. Por padrão, Reels com animações deixam as legendas grandes desligadas e a
legenda discreta do rodapé ligada. Fotos e clipes mantêm legendas grandes.
Uma escolha explícita salva pelo usuário tem prioridade.

## Vidro avançado e cartões em sequência

**Acabamento visual → Vidro avançado** acrescenta superfícies de 44% a 72% de
opacidade, desfoque real de fundo, bordas com luz em gradiente, sombras e reflexos
sutis nas figuras. A atmosfera usa luzes difusas em movimento, calculadas por
quadro; desligar a animação congela também a luz. **Original** mantém o acabamento
específico do modelo. A paleta e o movimento continuam sendo escolhas separadas.
Isso se aplica apenas aos novos modelos ShotCraft; os motores anteriores não mudam.

**Janelas em cascata** mantém as mensagens anteriores atrás da mensagem atual.
A sequência acompanha as frases dentro da cena, reúne até quatro cartões e
inicia uma nova pilha no quinto. Um corte para outro movimento encerra a pilha.
A galeria demonstra o mesmo comportamento usado na exportação.
