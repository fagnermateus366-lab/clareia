param([switch]$ComGaleria)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$rendererRoot = Join-Path $projectRoot 'overview\shotcraft_renderer'
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$nodePath = if ($nodeCommand) { $nodeCommand.Source } else { $null }
if (-not $nodePath) {
    $runtimePrefix = & (Join-Path $projectRoot '.venv\Scripts\python.exe') -c 'import sys; print(sys.base_prefix)'
    if ($LASTEXITCODE -ne 0) { throw 'Prepare primeiro o ambiente Python do Clareia.' }
    $candidate = Join-Path (Split-Path $runtimePrefix.Trim() -Parent) 'node\bin\node.exe'
    if (Test-Path -LiteralPath $candidate) { $nodePath = $candidate }
}
if (-not $nodePath) { throw 'Instale o Node.js LTS do site oficial nodejs.org. As animações anteriores continuam disponíveis.' }
$pnpmPath = Join-Path (Split-Path (Split-Path $nodePath -Parent) -Parent) 'node_modules\pnpm\bin\pnpm.cjs'
if ($ComGaleria) {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    $pnpm = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
    function Invoke-ClareiaPnpm {
        if (Test-Path -LiteralPath $pnpmPath) { & $nodePath $pnpmPath @args }
        elseif ($npm) { & $npm.Source exec --yes --package=pnpm@11.25.0 -- pnpm @args }
        elseif ($pnpm) { & $pnpm.Source @args }
        else { throw 'npm nao encontrado. Repare a instalacao oficial do Node.js.' }
        if ($LASTEXITCODE -ne 0) { throw "O pnpm falhou (codigo $LASTEXITCODE)." }
    }
    foreach ($folder in @($rendererRoot, (Join-Path $projectRoot 'overview\three_gallery'))) {
        Push-Location -LiteralPath $folder
        try {
            Invoke-ClareiaPnpm install --frozen-lockfile --ignore-scripts --store-dir (Join-Path $projectRoot '.pnpm-store') --config.manage-package-manager-versions=false
            if ($folder -ne $rendererRoot) {
                $env:NEXT_TELEMETRY_DISABLED = '1'
                Invoke-ClareiaPnpm run build
                if (-not (Test-Path -LiteralPath 'out\index.html')) { throw 'A galeria 3D nao foi gerada.' }
            }
        } finally { Pop-Location }
    }
    Push-Location -LiteralPath $rendererRoot
    try {
        & $nodePath (Join-Path $rendererRoot 'render.mjs') --browser
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o navegador isolado.' }
    } finally { Pop-Location }
    return
}
Push-Location -LiteralPath $rendererRoot
try {
    if (Test-Path -LiteralPath $pnpmPath) {
        & $nodePath $pnpmPath install --frozen-lockfile --ignore-scripts --store-dir (Join-Path $projectRoot 'output\shotcraft-pnpm-store') --config.manage-package-manager-versions=false
    } else {
        $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if (-not $npmCommand) { throw 'npm não encontrado. Repare sua instalação oficial do Node.js.' }
        & $npmCommand.Source install --ignore-scripts --no-audit --no-fund --cache (Join-Path $projectRoot 'output\shotcraft-npm-cache')
    }
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar o motor ShotCraft.' }
    & $nodePath (Join-Path $rendererRoot 'render.mjs') --browser
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar o navegador isolado de renderização.' }
    Write-Host 'ShotCraft preparado. Use atualizar-estudio.bat para carregar as opções.'
} finally { Pop-Location }
