# Clareia

Estúdio local de vídeos explicativos. Transforme documentos e texto em um
roteiro editável, narração em português e vídeo com legendas. O Clareia exporta
MP4 e SRT, com vídeo comum e Reels. O catálogo inclui ShotCraft, 3D e colagem
documental.

## Instalar no Windows

Abra o **PowerShell** de 64 bits e cole o comando abaixo. Ele baixa o instalador
da versão indicada, prepara as dependências e mostra como abrir o Clareia.

```powershell
$instalador = Join-Path $env:TEMP 'clareia-instalar-v0.1.0.ps1'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/fagnermateus366-lab/clareia/v0.1.0/instalar-github.ps1' -OutFile $instalador -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $instalador
```

O modo local inclui um download de aproximadamente **9,3 GB só para o modelo de
texto**, além das vozes e dependências. Use Windows 10/11 x64 com internet e
[WinGet](https://learn.microsoft.com/windows/package-manager/winget/). Consulte
o [guia passo a passo](INSTALACAO.md) para saber como abrir, repetir a instalação
ou escolher o modo com API, que dispensa os modelos locais.

O código do Clareia tem licença [MIT](LICENSE). Modelos, mídias e dependências
têm [licenças próprias](THIRD_PARTY.md).
