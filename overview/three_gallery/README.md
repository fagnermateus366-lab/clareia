# Biblioteca 3D do Clareia

48 modelos WebGL reais: 36 alternativas dos movimentos existentes e 12 experiências volumétricas. O catálogo completo do estúdio tem 84 movimentos, preservando os 36 anteriores. A galeria está em `http://127.0.0.1:7860/3d/` e também abre pelo botão **Galeria 3D interativa** das configurações de animação.

Cada alternativa tem seu componente em `../shotcraft_renderer/src/components/3d-library/variants/`. Os componentes usam malhas, espessura geométrica e materiais PBR. As figuras dos cartões são 20 objetos procedurais próprios, definidos em `Subjects.tsx`; não são SVGs colocados em planos. Computador, castelo e cérebro seguem as referências fornecidas como ilustrações estilizadas.

## Integração em Next.js existente

1. Copie `../shotcraft_renderer/src/components/3d-library/` para `components/3d-library/` do seu projeto. Cada modelo pode ser importado isoladamente; `SceneContent.tsx` compõe o ambiente e o catálogo.
2. Copie `components/Gallery.tsx` e ajuste os imports `@three-library/` para o caminho da pasta copiada. Copie os estilos de `app/globals.css` ou adapte-os ao seu Tailwind. O arquivo importa Tailwind 4.
3. Copie `public/models/` e `public/fonts/` para seu `public/`. Preserve `ASSETS.md` e a licença `NotoSans-OFL.txt`.
4. Instale versões compatíveis com React 19: `three@0.186.1`, `@react-three/fiber@9.8.2`, `@react-three/drei@10.7.9`, `@types/three@0.186.0`. A galeria usa React/React DOM 19.3.1, Next 16.4.2, TypeScript 7 e Tailwind 4.3.3. O renderer de vídeo usa Remotion 4.0.538 e `@remotion/three` da mesma versão.
5. Abra a galeria por um componente cliente com `dynamic(() => import('./Gallery'), {ssr:false})`, como em `app/page.tsx`. Use `modelUrl:'/models/clareia-robot.glb'` e `fontUrl:'/fonts/noto_sans_pt.typeface.json'` nos valores iniciais de `defaultSettings` se o projeto não usar `/3d` como base path.

Este projeto independente tem `output:'export'` e `basePath:'/3d'` para ser servido pelo FastAPI existente. Não copie essas opções sobre a configuração de um projeto Next que já tenha outras rotas. Em uma integração normal, ajuste apenas os imports e URLs de assets. Não são necessários HDRIs externos: `Environment` usa Lightformers locais.

## Interação

- Arraste para orbitar; use a roda para aproximar. Os limites preservam a leitura das faces dos cartões.
- Ajuste velocidade, luz, cor, ambiente, qualidade e malha. Em **Movimento das formas 3D**, escolha original, composição parada, giro suave, aproximação, flutuação ou apresentação combinada. Giros limitados mantêm as faces dos textos visíveis; a aproximação respeita as margens da câmera. A pausa congela o movimento. O movimento fica salvo no projeto ou na cena, junto com o modelo.
- Clique nos objetos para selecionar. A dispersão tem pontos instanciados, barras volumétricas e tooltip com coordenadas. Pode receber até 200 pontos em JSON com `x`, `y`, `z` e `label` opcional; a amostra é explicitamente ilustrativa.
- O viewer GLB inclui esqueleto e clips Idle/Walk. GLBs próprios podem ser inspecionados localmente (até 30 MB); esse upload de inspeção não é aplicado aos vídeos.
- A escolha do modelo na galeria envia somente dados ao estúdio da mesma origem. Salve a revisão para persistir a escolha. Os rótulos demonstrativos da galeria não substituem o roteiro.
- O acervo dos cartões 3D mostra somente objetos que têm malhas implementadas. **Seleção das figuras → Flexível por tema** é o padrão: quando falta o objeto exato, escolhe um objeto 3D mais amplo do assunto e continua. **Rigoroso por trecho** exige revisão da cena quando não encontra correspondência. Nenhum modo substitui os objetos 3D por figuras planas ou cartões vazios.

## Renderização e estabilidade

O vídeo usa os mesmos componentes em `ThreeCanvas`. O tempo vem do quadro de Remotion; fontes e GLB são incorporados ao manifesto como data URIs locais. A captura aguarda geometria e fontes. A narração, as legendas e a exportação de áudio continuam no pipeline existente.

A câmera enquadra as dimensões reais da composição; o piso fica abaixo do menor limite dos objetos, incluindo margem para a entrada. Os layouts independentes mantêm espaçamento. A pilha em cascata mantém até quatro cartões, com sobreposição deliberada. Textos usam fonte Noto com acentos portugueses, geometria extrudada e ajuste medido à face; chamadas dos anéis ficam fora da silhueta.

As duas pirâmides constroem uma camada por frase, mantendo as anteriores: base, meio, topo. A quarta frase inicia outra base com um novo rótulo. Cada ciclo tem três níveis, mesmo quando a última sequência termina com apenas uma ou duas frases. O enquadramento e o piso permanecem estáveis durante a construção. A galeria demonstra esse ciclo; o vídeo usa os tempos reais da narração.

O monitor mostra FPS e desenhos por quadro medidos no dispositivo. Qualidade econômica reduz sombras, resolução da superfície fluida, partículas e DPR. Instancing é usado nas teclas e nos pontos; geometrias próprias são liberadas ao desmontar. 60 FPS é uma meta, dependente da GPU, da resolução e do modelo selecionado.

## Verificação

`python -m tools.verify_three_render` captura os 48 modelos pelo renderer de produção e rejeita viewports vazios. Acrescente `--vertical` para Reels. A verificação usa uma pasta própria em `output/` e respeita o bloqueio do processamento do usuário.

`python -m pytest tests/test_three_library.py` verifica o acervo 3D, fontes, GLB, limites dos controles, fidelidade das citações, divisão de tempo, continuidade do vidro e separação entre cartões. O build Next verifica todos os componentes TypeScript.

`python -m tools.verify_context_choreography` renderiza a sequência 1→2→3→1 das duas pirâmides nos dois formatos, compara os seis movimentos e codifica um MP4 com seleção temática. Não altera os projetos e só inicia com o processamento livre.
