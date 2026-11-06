param(
    [ValidatePattern('^v[0-9]+\.[0-9]+\.[0-9]+$')]
    [string]$Versao = 'v0.1.0',
    [string]$Destino = (Join-Path $env:LOCALAPPDATA 'Clareia-GitHub'),
    [switch]$SomenteApi
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'Use o PowerShell de 64 bits em um Windows x64.'
}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$repository = 'fagnermateus366-lab/clareia'
$target = [IO.Path]::GetFullPath($Destino)
$parent = Split-Path -Parent $target
$marker = Join-Path $target '.clareia-github.json'
$mode = if ($SomenteApi) { 'api' } else { 'local' }

if (Test-Path -LiteralPath $target) {
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        throw "O destino ja existe e nao foi preparado por este instalador: $target. Escolha outra pasta com -Destino."
    }
    $record = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($record.repository -ne $repository -or $record.version -ne $Versao -or $record.mode -ne $mode) {
        throw 'A pasta pertence a outra versao ou modo. Escolha outra pasta com -Destino.'
    }
} else {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $stage = Join-Path (Resolve-Path -LiteralPath $parent).ProviderPath ('.clareia-download-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    try {
        $archive = Join-Path $stage 'clareia.zip'
        Write-Host "Baixando Clareia $Versao ..."
        Invoke-WebRequest -UseBasicParsing -Uri "https://codeload.github.com/$repository/zip/refs/tags/$Versao" -OutFile $archive
        $extract = Join-Path $stage 'source'
        Expand-Archive -LiteralPath $archive -DestinationPath $extract
        $roots = @(Get-ChildItem -LiteralPath $extract -Directory)
        if ($roots.Count -ne 1 -or -not (Test-Path -LiteralPath (Join-Path $roots[0].FullName 'instalar.ps1') -PathType Leaf)) {
            throw 'O pacote nao possui a estrutura esperada do Clareia.'
        }
        @{ repository = $repository; version = $Versao; mode = $mode } | ConvertTo-Json |
            Set-Content -LiteralPath (Join-Path $roots[0].FullName '.clareia-github.json') -Encoding UTF8
        if (Test-Path -LiteralPath $target) { throw 'O destino foi ocupado durante o download.' }
        Move-Item -LiteralPath $roots[0].FullName -Destination $target
    } finally {
        $resolved = (Resolve-Path -LiteralPath $stage).ProviderPath
        if ($resolved -eq $stage -and (Split-Path -Leaf $resolved) -match '^\.clareia-download-[a-f0-9]{32}$' -and
            -not ((Get-Item -LiteralPath $resolved -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
}

Push-Location -LiteralPath $target
try {
    & (Join-Path $target 'instalar.ps1') -Completo -SomenteApi:$SomenteApi
} finally { Pop-Location }
$launcher = if ($SomenteApi) { 'iniciar-api.bat' } else { 'iniciar.bat' }
Write-Host ''
Write-Host "Clareia $Versao instalado em: $target"
Write-Host "Para abrir: & '$target\$launcher'"
