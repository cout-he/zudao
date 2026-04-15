$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$venvPython = Join-Path $root ".venv_ga\\Scripts\\python.exe"
$mainScript = Join-Path $root "scripts\\main_ga.py"

if (-not (Test-Path $venvPython)) {
    Write-Host "Local virtual environment .venv_ga was not found."
    Write-Host "Run this first: .\\setup_local_env.ps1"
    exit 1
}

& $venvPython $mainScript
