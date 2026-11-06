# Gemini: roteiro ou todas as etapas de IA

Em **Roteiro, modelos de IA e opções avançadas**, escolha **Gemini · sua chave**, atualize o catálogo e escolha um modelo de texto.

- Caixa **Usar Gemini em todas as etapas de IA · sem Ollama** desmarcada: mantém o funcionamento anterior, com Gemini no roteiro e modelos locais nas demais etapas.
- Caixa marcada: estudo das fontes, OCR de imagens, checagens, roteiro, planejamento das animações e narração usam Gemini. Não carrega nem consulta Ollama, Kokoro, Piper ou OCR local. Se a API falhar, não troca silenciosamente para modelos locais.

A escolha é salva por projeto. Na opção marcada, escolha também o modelo de voz, a voz principal e, se necessário, a segunda voz. **Conferir modelos de voz** consulta o catálogo da chave; **Ouvir voz Gemini** gera uma amostra pela API. Há 30 vozes e cinco modelos TTS previstos, sujeitos à disponibilidade da conta. Modelos de texto e de voz têm limites separados.

Textos e imagens necessários ao processamento são enviados ao Google. Há consumo de cota e possíveis cobranças de texto/voz. Leitura dos arquivos, desenho das animações, transições, mixagem e montagem do MP4 continuam no computador. Isso reduz a necessidade de modelos locais de IA, mas não é renderização remota do vídeo. A biblioteca de figuras, os movimentos, o controle de música e as pausas de narração nas transições continuam disponíveis.

## Notebook sem Ollama

Use `instalar-api.bat` para instalar dependências sem baixar modelos Ollama, Kokoro, Piper ou OCR. Use `iniciar-api.bat` para abrir. O computador ainda precisa de Python e FFmpeg com libass, disco e capacidade de codificar vídeo. Uma instalação limpa em outro Windows não foi executada nesta validação.

Cadastre a chave no estúdio desse computador. Chaves salvas usam a proteção DPAPI do usuário Windows; copiar o arquivo cifrado de outra máquina não transfere o acesso. A chave não é salva no projeto nem no navegador. Não é necessário desproteger uma chave já funcional nesta instalação.

## Modelos e mensagens de limite

**Testar resposta do modelo · chamada curta à API** envia apenas um pedido mínimo de JSON, sem o conteúdo do projeto. O teste usa a chave cadastrada, pode consumir uma pequena quantidade da cota e não é executado enquanto há uma tarefa ativa no estúdio.

O catálogo informa que um modelo existe, mas não garante que uma chamada de geração será atendida. O estúdio diferencia:

- **RPM/TPM:** requisições ou tokens por minuto. Consumo total baixo pode coincidir com um pico momentâneo.
- **RPD/TPD:** limite diário do modelo/projeto.
- **Cota zero informada pelo Google:** ausência de cota liberada para esse modelo/nível; não prova consumo de 100% da cota total.
- **HTTP 429 sem detalhes:** limite não especificado; o estúdio não inventa a causa.
- **HTTP 500/502/503/504:** indisponibilidade ou sobrecarga, separada de cota.
- **Tempo de resposta excedido:** falha de resposta, separada de cota.
- **Limite de saída:** a resposta foi interrompida por tamanho, separado da cota da conta.

Tentativas transitórias respeitam o atraso informado pelo provedor, com até três chamadas. Uma espera superior a um minuto é apresentada para retomada manual. Cota diária ou zero não dispara tentativas repetidas. As chamadas ao mesmo modelo têm espaçamento; um limite RPM explícito aumenta esse intervalo. Nenhum modelo é trocado automaticamente. O app não consegue consultar a porcentagem total usada apenas pela chave: confira os [limites do projeto no AI Studio](https://aistudio.google.com/rate-limit?timeRange=last-28-days).

## Validação desta entrega

Com a chave existente, sem alterá-la ou exibi-la: catálogo de texto e cinco modelos de voz consultados; Gemini 3.1 Flash Lite respondeu HTTP 200 a um pedido mínimo; Gemini 3.8 Flash não respondeu dentro dos 35 segundos do teste curto. Também foi observado HTTP 503 em uma tentativa desse modelo e, depois, três respostas estruturadas válidas nos registros de uso do projeto ativo. Portanto houve disponibilidade intermitente. Esses resultados não demonstram cota total esgotada e não garantem disponibilidade futura de todos os modelos.

O fluxo importar imagem → OCR → estudo → roteiro → storyboard → narração → MP4 foi exercitado com respostas HTTP simuladas, bloqueando qualquer inferência local e usando FFmpeg real. Não foi feita uma geração completa real de voz Gemini. Os testes também cobrem escolha opcional, isolamento entre projetos, cache, vozes alternadas, música, pausas, limites e proteção de mensagens. Veja `output/gemini-full-validation/VERIFICACAO.md`.

Referências oficiais: [limites](https://ai.google.dev/gemini-api/docs/rate-limits), [erros](https://ai.google.dev/gemini-api/docs/troubleshooting), [voz](https://ai.google.dev/gemini-api/docs/speech-generation), [Interactions](https://ai.google.dev/gemini-api/docs/interactions-overview).
