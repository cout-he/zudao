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
$entryScript = Join-Path $root "run_client_workflow.py"

New-Item -ItemType Directory -Force -Path (Join-Path $root "outputs") | Out-Null

Write-Host "============================================================"
Write-Host "Running client workflow..."
Write-Host "Input  : please select an Excel workbook in the popup window"
Write-Host "Output : outputs\client_runs"
Write-Host "Log    : $logFile"
Write-Host "============================================================"
Write-Host ""

& $pythonExe $entryScript *>&1 | Tee-Object -FilePath $logFile

Write-Host ""
Write-Host "Workflow completed successfully."
Write-Host "Please check outputs\client_runs for the result workbook, drawings and reports."
Write-Host "Log file:"
Write-Host "  $logFile"
