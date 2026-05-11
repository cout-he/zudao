$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$venvGaPython = Join-Path $root ".venv_ga\Scripts\python.exe"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (Test-Path $venvGaPython) {
    $pythonExe = $venvGaPython
}
elseif (Test-Path $venvPython) {
    $pythonExe = $venvPython
}
else {
    Write-Host "Local Python environment was not found."
    Write-Host "Expected one of:"
    Write-Host "  $venvGaPython"
    Write-Host "  $venvPython"
    Write-Host ""
    Write-Host "Please run setup_local_env.ps1 first."
    exit 1
}

$logFile = Join-Path $root "outputs\run_client_workflow.log"
$mainScript = Join-Path $root "scripts\main_actual_production.py"

New-Item -ItemType Directory -Force -Path (Join-Path $root "outputs") | Out-Null

Write-Host "============================================================"
Write-Host "Running actual production workflow..."
Write-Host "Input  : default workbook under the data folder"
Write-Host "Output : default workbook under the outputs folder"
Write-Host "Log    : $logFile"
Write-Host "============================================================"
Write-Host ""

& $pythonExe $mainScript `
    --decoder-mode auto `
    --panel-widths 1000,1240,1250,1500 *>&1 | Tee-Object -FilePath $logFile

Write-Host ""
Write-Host "Workflow completed successfully."
Write-Host "Result workbook and artifact paths were written by the program."
Write-Host "Please check the outputs folder."
Write-Host "Log file:"
Write-Host "  $logFile"
