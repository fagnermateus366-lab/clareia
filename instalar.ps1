param([switch]$SomenteApi, [switch]$Completo, [switch]$SemModelos, [switch]$SemWinGet)

$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'tools\instalacao-windows.ps1')
Refresh-ClareiaPath

$requirements = if ($SomenteApi) { 'requirements-api.txt' } else { 'requirements-lock.txt' }
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$uv = Get-ClareiaUv $PSScriptRoot
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    & $uv venv --python 3.12 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar Python 3.12.' }
}
& $uv pip install --python $python -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias Python.' }

if ($Completo) {
    if (-not (Find-ClareiaExecutable 'ffmpeg.exe') -or -not (Find-ClareiaExecutable 'ffprobe.exe')) {
        Install-ClareiaPackage 'Gyan.FFmpeg'
    }
    foreach ($exe in @('ffmpeg.exe', 'ffprobe.exe')) {
        if (-not (Find-ClareiaExecutable $exe)) { throw "$exe nao encontrado. Abra outro PowerShell e repita o comando." }
    }
}

if (-not $SomenteApi -and -not $SemModelos -and -not (Find-ClareiaExecutable 'ollama.exe')) {
    if ($Completo) { Install-ClareiaPackage 'Ollama.Ollama' }
    if (-not (Find-ClareiaExecutable 'ollama.exe')) {
        throw 'Ollama nao encontrado. Instale-o em https://ollama.com/download/windows e repita o comando.'
    }
}

if ($Completo) {
    $node = Find-ClareiaExecutable 'node.exe'
    $major = 0
    if ($node) {
        $nodeVersion = & $node --version
        if ($LASTEXITCODE -eq 0 -and $nodeVersion -match '^v([0-9]+)\.') { $major = [int]$Matches[1] }
    }
    if ($major -lt 22 -or (-not (Find-ClareiaExecutable 'npm.cmd') -and -not (Find-ClareiaExecutable 'pnpm.cmd'))) {
        Install-ClareiaPackage 'OpenJS.NodeJS.LTS'
    }
    & (Join-Path $PSScriptRoot 'tools\instalar_shotcraft.ps1') -ComGaleria
}

$bootstrapOptions = @()
if ($SomenteApi) { $bootstrapOptions += '--api-only' }
if ($SemModelos) { $bootstrapOptions += '--check-only' }
& $python (Join-Path $PSScriptRoot 'tools\bootstrap.py') @bootstrapOptions
if ($LASTEXITCODE -ne 0) { throw 'A instalacao nao concluiu. Veja o erro acima e repita o comando.' }
