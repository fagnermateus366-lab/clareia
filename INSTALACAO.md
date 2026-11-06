# Instalação do Clareia no Windows

## 1. Escolha o modo

- **Local:** instala o Ollama, Qwen3 14B, Kokoro, Piper e o reconhecimento de fala.
  Depois do primeiro download, os componentes locais de IA funcionam sem conta.
- **API:** instala a interface e os motores de vídeo sem baixar os modelos
  locais de IA. Para o fluxo completo sem Ollama, é necessária uma chave
  Gemini própria e internet. A chave é cadastrada no Clareia após abrir.
  Cotas e cobranças dependem do provedor e da conta.

Os dois modos preparam Python, FFmpeg/FFprobe, Node.js, ShotCraft e a galeria
3D. O instalador baixa dependências das fontes de distribuição. A instalação
AMD particular de clonagem de voz e amostras de pessoas não fazem parte desta
versão pública.

## 2. Instale por comando

Use Windows 10/11 x64 atualizado com o
[Instalador de Aplicativos](https://learn.microsoft.com/windows/package-manager/winget/)
e conexão à internet. Deixe espaço livre para as dependências e para seus
vídeos; no modo local, reserve **cerca de 20 GB ou mais** como ponto de partida.
O Qwen3 14B requer um PC com memória suficiente; a versão atual não foi
validada em notebooks de 4 GB.

Abra o **PowerShell de 64 bits**. Para instalar no modo local:

```powershell
$instalador = Join-Path $env:TEMP 'clareia-instalar-v0.1.1.ps1'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/fagnermateus366-lab/clareia/v0.1.1/instalar-github.ps1' -OutFile $instalador -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $instalador
```

Para instalar no **modo API**:

```powershell
$instalador = Join-Path $env:TEMP 'clareia-instalar-v0.1.1.ps1'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/fagnermateus366-lab/clareia/v0.1.1/instalar-github.ps1' -OutFile $instalador -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $instalador -SomenteApi -Destino "$env:LOCALAPPDATA\Clareia-API"
```

Você também pode baixar e ler o [script da versão](https://github.com/fagnermateus366-lab/clareia/blob/v0.1.1/instalar-github.ps1) antes de executá-lo.
O WinGet pode pedir confirmação para instalar dependências. A execução do
script não altera a política permanente do Windows.

## 3. Abra e produza o primeiro vídeo

Modo local:

```powershell
& "$env:LOCALAPPDATA\Clareia-GitHub\iniciar.bat"
```

Modo API:

```powershell
& "$env:LOCALAPPDATA\Clareia-API\iniciar-api.bat"
```

1. Acesse [127.0.0.1:7860](http://127.0.0.1:7860/) e mantenha o terminal aberto.
2. No modo API, em **Configurações → Chaves de API**, cadastre a chave Gemini.
   Selecione Gemini e marque **Usar Gemini em todas as etapas de IA · sem Ollama**.
3. Importe uma fonte curta ou cole um texto e gere o roteiro.
4. Revise o roteiro, escolha voz e animação, salve e execute o vídeo.
5. Baixe o MP4 e as legendas. A galeria fica em **Galeria 3D interativa**.

## Repetir a instalação, atualizar e resolver problemas

- Se um download falhar, repita o mesmo comando. A mesma versão na mesma pasta
  reaproveita as dependências disponíveis e preserva projetos e configurações.
- Se a pasta de destino já existir e não tiver sido preparada pelo instalador,
  informe outra com `-Destino`. Para outra versão, use o comando da nova
  versão em uma pasta separada. Mantenha a pasta antiga até concluir o backup.
- Se o WinGet não estiver disponível, instale o **Instalador de Aplicativos** pela
  Microsoft Store ou instale os pré-requisitos pelos sites oficiais e repita.
- Se a instalação falhar em Python ou Node, copie a mensagem do terminal ao
  abrir um relato no GitHub. Não inclua chaves, projetos nem amostras de voz.
- Se o navegador isolado falhar ao iniciar o WebGL durante uma exportação 3D,
  o ShotCraft tenta novamente com o Chrome completo, sem abrir uma janela.
  Se ele não estiver instalado, a primeira tentativa alternativa baixa o
  Chrome for Testing. A galeria interativa usa o suporte WebGL do seu navegador.

Para quem já baixou o ZIP do GitHub, extraia e execute na pasta extraída:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\instalar.ps1 -Completo
```

Veja também [ShotCraft](SHOTCRAFT.md), [Gemini](GEMINI.md) e as
[licenças dos componentes](THIRD_PARTY.md).
