# Artes de História ilustrada

Criadas nesta conversa com a ferramenta integrada `image_gen` (habilidade imagegen), sem CLI ou chave de API. São ilustrações originais para o aplicativo; não reutilizam fotogramas ou personagens do vídeo de referência. A geração das artes ocorreu durante o desenvolvimento; a animação e a voz continuam locais na execução do aplicativo.

## Arquivos do projeto

- `rostos.png`: atlas de cinco identidades e três expressões.
- `{pessoa,idoso,mulher,menina,lobo}-{serena,reflexiva,surpresa}.png`: quinze recortes com transparência, usados pelo renderizador.
- `corpos.png`: cinco personagens completos com roupas e anatomia detalhadas.
- `corpo-{pessoa,idoso,mulher,menina,lobo}.png`: personagens normalizados para articulação.
- `rua.png`: cenário pintado de bairro residencial.
- `estudio.png`: cenário pintado de biblioteca/estudo.

Os recortes preservam a transparência original. Componentes conectados separam as figuras do atlas, inclusive onde o retângulo de uma orelha invade a faixa de outro personagem; não são cortados simplesmente por uma grade fixa. As expressões de cada identidade compartilham escala e apoio inferior. O renderizador move membros por articulações e usa as expressões e a aproximação de câmera nos limites da fala. São recortes articulados, não vídeo livre por IA ou captura de movimento.

## Especificações dos prompts utilizados

### 1. Atlas de rostos

Use case: illustration-story. Production asset for a 2D narrated animation app: a clean expression sprite atlas, genuinely transparent background, no text or grid lines. Three columns and five rows of floating head-and-short-neck cutouts. Detailed, beautiful hand-painted 2D animation, adult editorial storybook look, organic fine brown ink contours, subtle cel shading, warm natural skin, clear expressive almond eyes with irises and highlights, natural nose, lips, cheek planes, individually drawn layered hair strands. Semi realistic human anatomy rather than round emoji heads or simple geometric cartoons. Same identity and exact hairstyle across each row. Columns: gently attentive neutral; thoughtful reflective with slightly furrowed asymmetric brows and contemplative gaze; mild natural surprise with lifted brows and softly parted lips. Rows: Brazilian adult man with dark wavy hair and gray temples; elderly man with swept back gray hair and fine wrinkles; Brazilian woman with dark wavy hair; auburn-haired teenage girl in a red hood; dignified gray storybook wolf. Consistent scale and head positioning. No shoulders, body, text, logos, watermark or painted checkerboard.

### 2. Rua

Use case: illustration-story. Wide empty 2D background for educational narrated animation. A beautifully hand-painted residential street in a quiet Brazilian small town, viewed across the sidewalk at eye level, wide 16:9. Cream plaster houses with terracotta tiled roofs, wooden garden fences, lush layered trees, front porch, flowerpots and a street receding gently at one side. Entire lower 35 percent: broad unobstructed sidewalk for animated characters. Refined semi realistic 2D story animation, elegant organic ink contours, nuanced cel-painted shadows, textured plaster, individual leaf clusters, believable perspective, warm afternoon daylight, muted sage, ochre, cream and brown. No people, animals, foreground vehicles, text, signs, logos or watermark.

### 3. Estudo/biblioteca

Use case: illustration-story. Richly hand-painted 2D animation background, wide 16:9. Empty warm home study/library, elegant organic ink contours and nuanced cel-painted shading. Wooden bookshelves with individual books, a sunlit window and linen curtains, small plant and modest desk to one side, textured plaster and warm wood. Central and lower 40 percent: clear floor stage for separate characters. Eye-level perspective, warm cream, sage, chestnut and terracotta, layered depth and believable materials. No flat geometric placeholder look, people, animals, lettering, logos or watermark.

### 4. Personagens completos

Use case: illustration-story. Production sprite sheet: five separate full-body original 2D characters on a truly transparent background, five equal columns in a single row, no overlap. Refined semi realistic hand-painted story animation, softly inked natural contours, rich cel painting, realistic cloth folds, woven shirts, seams, buttons, pockets, dimensional leather shoes and hands with individual fingers. Front-facing relaxed A-pose, arms slightly away from the torso, straight forearms, fingers down, transparent gaps between arms and body, legs apart and full shoes visible. Consistent anatomy and landmarks for animation. Columns: Brazilian adult man in sage button shirt and dark trousers; elderly man with swept back silver hair, cream plaid shirt, brown vest, ochre trousers and worn leather shoes; Brazilian woman with wavy hair, teal blouse and dark trousers; auburn-haired red-hooded girl with cream blouse, red skirt and boots; upright gray wolf with layered fur and olive traveler vest. No props, floor shadows, text, labels, borders, logos or watermark.

## Originais gerados

Arquivos originais de geração:

- Rostos: `exec-710b5633-c52a-48d6-a92d-f8d54031a48c.png`
- Rua: `exec-aa1ae4b6-71d7-4dc6-9076-ad05b40826e9.png`
- Estudo: `exec-5de344d7-920b-47a1-bcc4-98275c1e276f.png`
- Corpos: `exec-19e17a59-e831-42c2-990e-f439009840f9.png`
