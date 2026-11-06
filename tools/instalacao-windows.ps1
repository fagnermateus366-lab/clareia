function Refresh-ClareiaPath {
    $registered = @(
        [Environment]::GetEnvironmentVariable('Path', 'Machine')
        [Environment]::GetEnvironmentVariable('Path', 'User')
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links')
        (Join-Path $env:LOCALAPPDATA 'Programs\Ollama')
    )
    $env:Path = [Environment]::ExpandEnvironmentVariables(($registered -join ';')) + ';' + $env:Path
}

function Find-ClareiaExecutable([string]$Name) {
    $local = Join-Path $PSScriptRoot $Name
    if (Test-Path -LiteralPath $local -PathType Leaf) { return $local }
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { return $command.Source }
    return $null
}

function Install-ClareiaPackage([string]$Id) {
    if ($SemWinGet) { throw "Pre-requisito indisponivel: $Id. Instale-o antes de usar -SemWinGet." }
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Para instalar $Id, instale/atualize o Instalador de Aplicativos (App Installer) pela Microsoft Store e execute o comando novamente."
    }
    Write-Host "Preparando $Id ..."
    & $winget.Source install --id $Id --exact --source winget --no-upgrade
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar $Id (codigo $LASTEXITCODE). Confira a mensagem do WinGet e execute novamente."
    }
    Refresh-ClareiaPath
}

function Get-ClareiaUv([string]$Root) {
    $command = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $folder = Join-Path $Root 'tools\uv'
    $exe = Join-Path $folder 'uv.exe'
    if (Test-Path -LiteralPath $exe -PathType Leaf) { return $exe }
    $archive = Join-Path $Root 'tools\uv.zip'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile $archive
    Expand-Archive -LiteralPath $archive -DestinationPath $folder -Force
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw 'O executavel uv.exe nao foi encontrado no pacote oficial.'
    }
    Remove-Item -LiteralPath $archive
    return $exe
}
