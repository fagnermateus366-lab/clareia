# Músicas e clipes do YouTube no Clareia

Disponível na versão de desenvolvimento. As bibliotecas são compartilhadas entre os projetos deste computador.

## Pesquisar, ouvir e salvar músicas

1. Em **Música de fundo**, abra **Explorar músicas e importar**.
2. Escolha **Buscar no YouTube Music** e digite o nome da música, do artista ou de uma trilha.
3. Confira artista, álbum e duração. **Ouvir** abre a reprodução no player do YouTube; se a faixa já estiver salva, pode ser ouvida a partir do computador.
4. Opcionalmente, preencha os créditos ou a autorização que você possui. Clique em **Baixar para a biblioteca** e acompanhe a importação. Há uma opção de cancelar.
5. Quando terminar, clique em **Usar esta música**. Ela também aparecerá na categoria **YouTube · minhas músicas** nos próximos projetos, tanto em vídeo comum quanto em Reels.

A busca usa o filtro de músicas do YouTube Music. Filmes, vídeos comuns, podcasts e playlists não entram nos resultados desta busca. O nome pode ter versões diferentes: use o artista e a prévia para escolher. Até 30 minutos e 120 MB por faixa. A música salva usa os controles existentes de volume e redução durante a fala.

## Pesquisar e salvar clipes sem o áudio original

1. Escolha **Reels / Shorts → Conteúdo na tela → Fotos e clipes com narração**.
2. Abra **Buscar e baixar clipes do YouTube**. Pesquise pelo nome ou cole o link de um vídeo ou Shorts.
3. Confira o canal e a duração com **Prévia com áudio** ou **Prévia sem áudio**. A reprodução com áudio usa o original no YouTube; a escolha de baixar sem áudio é separada. Escolha a qualidade máxima de **720p** ou **1080p**; a resolução real depende do arquivo disponível na origem.
4. Clique em **Baixar sem áudio**. O arquivo salvo contém apenas o vídeo. Mesmo depois de salvar, **Original com áudio** continua disponível na biblioteca. **Arquivo sem áudio** reproduz a cópia local.
5. Clique em **Usar este clipe**. Na criação, ele fica selecionado para entrar no novo projeto; na revisão, entra nas mídias do projeto atual. Você também pode escolher um clipe já salvo na biblioteca.
6. No roteiro, use **Escolher onde cada mídia aparece** para definir a cena e a frase de entrada. Os controles de início/fim, repetição, último quadro e transições continuam disponíveis.

Os clipes aceitam até 30 minutos e 200 MB. Não são importadas playlists ou transmissões ao vivo. Fotos e clipes locais podem ser combinados. O vídeo usa a voz selecionada no Clareia e a música de fundo escolhida por você. Para usar uma música própria, a opção **Importar minha música** continua disponível. A narração de texto pronto ou a sua voz clonada usam os controles existentes; o áudio original do clipe não participa da mixagem.

As cópias adicionadas aos projetos usam a mesma estrutura das mídias locais. A biblioteca global permite reutilizá-las em novos projetos.

## Continuidade e enquadramento no Reels

**Continuar os clipes entre as cenas** vem marcado. Com um único vídeo, a próxima cena continua na posição em que ele parou. Com uma lista só de vídeos, cada um toca até o fim antes de passar ao seguinte; a lista repete somente depois do último. A duração real da narração determina o avanço. A troca de cena, por si só, não reinicia nem congela o mesmo clipe.

Com trechos manuais ou fotos intercaladas, a posição de cada clipe é guardada. **Reiniciar no início do corte** permite começar de novo em um trecho específico. Desmarcar a continuidade geral recupera o comportamento de reiniciar por cena.

Em **Enquadramento das fotos e clipes**, escolha:

- **Imagem inteira · fundo suave**: comportamento anterior, conservando a mídia toda.
- **Recortar para preencher**: preenche o celular sem deformar, cortando as bordas. Escolha manter o centro, um dos lados, a parte de cima ou de baixo.
- **Redimensionar para a tela**: ocupa a tela toda alterando as proporções.

Em **Ver enquadramento antes de renderizar**, escolha uma mídia para conferir a composição geral. Os trechos manuais também têm enquadramento e posição próprios; **Usar enquadramento geral** acompanha a configuração do projeto. Os arquivos originais são preservados.

## Disponibilidade e direitos de uso

Pesquisar ou conseguir baixar um arquivo não determina sua licença de reutilização. Verifique a permissão do titular para incluir músicas e imagens em um vídeo. Informar créditos não substitui uma licença quando ela for necessária. O Clareia preserva a origem das mídias e os créditos informados, sem classificar automaticamente um resultado como livre de direitos.

É uma integração comunitária. A busca, as prévias online e os downloads dependem da internet e da disponibilidade do YouTube, que pode mudar. As prévias usam o player do YouTube e oferecem um link para abrir a fonte quando a incorporação não estiver disponível. As faixas e os clipes salvos ficam locais. Conteúdos privados, exclusivos de assinatura ou protegidos não são liberados por esta integração. Ela não lê cookies de navegador nem usa as credenciais dos seus canais conectados para publicação.

## Estrutura e dependências

O estudo do MetroList confirmou a separação entre busca filtrada, reprodução e armazenamento local. O Clareia usa uma implementação própria em Python, com **ytmusicapi** para buscar músicas, **yt-dlp** para obter mídia pública e o **FFmpeg** já existente para converter áudio e retirar o áudio dos clipes. Nenhum serviço do MetroList Android é necessário para executar o Clareia.

As versões estão em `requirements.txt`. Downloads precisam de **Node.js 22+** ou **Deno 2.3+**; o computador de desenvolvimento já tinha Node.js 24. As importações têm progresso, cancelamento, limites de tamanho/duração e tempo máximo. Arquivos temporários são separados da biblioteca definitiva.

Referências do estudo:

- [MetroList: busca por tipo e reprodução](https://github.com/MetrolistGroup/Metrolist/blob/main/innertube/src/main/kotlin/com/metrolist/innertube/YouTube.kt).
- [MetroList: armazenamento e downloads](https://github.com/MetrolistGroup/Metrolist/blob/main/app/src/main/kotlin/com/metrolist/music/playback/DownloadUtil.kt).
- [Filtro de pesquisa do ytmusicapi](https://ytmusicapi.readthedocs.io/en/stable/reference/search.html).
- [yt-dlp e seus componentes de execução](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

As demonstrações usam a composição **Carefree**, de Kevin MacLeod, com créditos CC BY 4.0, e trechos de **Big Buck Bunny**, da Blender Foundation, usados para conferir a remoção de áudio. [Licença e atribuição do projeto Big Buck Bunny](https://peach.blender.org/about/): © 2008 Blender Foundation / www.bigbuckbunny.org. Nenhuma demonstração é publicada automaticamente.
