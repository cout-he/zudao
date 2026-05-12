param(
    [string]$PythonExe = "python",
    [string]$VenvName = ".venv_ga",
    [switch]$NoSystemSitePackages
)

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$venvPath = Join-Path $root $VenvName
$venvPython = Join-Path $venvPath "Scripts\\python.exe"
$venvSitePackages = Join-Path $venvPath "Lib\\site-packages"
$activatePs1 = Join-Path $venvPath "Scripts\\activate.ps1"
$activateBat = Join-Path $venvPath "Scripts\\activate.bat"
$requirements = Join-Path $root "requirements.txt"
$basePrefix = (& $PythonExe -c "import sys; print(sys.prefix)").Trim()
$baseSitePackages = (& $PythonExe -c "import site; print([p for p in site.getsitepackages() if p.endswith('site-packages')][0])").Trim()

Write-Host "Project root: $root"
Write-Host "Target venv: $venvPath"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    $venvArgs = @("-m", "venv", $VenvName)
    if (-not $NoSystemSitePackages) {
        $venvArgs += "--system-site-packages"
    }
    & $PythonExe @venvArgs
}
else {
    Write-Host "Virtual environment already exists. Skip creating."
}

if (-not (Test-Path $venvSitePackages)) {
    New-Item -ItemType Directory -Force -Path $venvSitePackages | Out-Null
}

$baseSitePth = Join-Path $venvSitePackages "anaconda_base_site.pth"
$dllPth = Join-Path $venvSitePackages "anaconda_dlls.pth"
Set-Content -Path $baseSitePth -Value $baseSitePackages -Encoding ASCII
Set-Content -Path $dllPth -Value @(
    "import os"
    "os.add_dll_directory(r'$basePrefix')"
    "os.add_dll_directory(r'$basePrefix\\Library\\bin')"
) -Encoding ASCII

Set-Content -Path $activatePs1 -Value @'
$venvRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot "python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Error "python.exe was not found under $PSScriptRoot"
    return
}

$env:VIRTUAL_ENV = $venvRoot

$pathParts = @(
    $PSScriptRoot
    $env:PATH -split ';'
) | Select-Object -Unique
$env:PATH = ($pathParts -join ';')

Write-Host "Activated local environment: $venvRoot"
Write-Host "Python: $venvPython"
'@ -Encoding ASCII

Set-Content -Path $activateBat -Value @'
@echo off
set "VIRTUAL_ENV=%~dp0.."
set "PATH=%~dp0;%PATH%"
echo Activated local environment: %VIRTUAL_ENV%
echo Python: %~dp0python.exe
'@ -Encoding ASCII

Write-Host "Linked base packages from: $baseSitePackages"

$pipCheck = & $venvPython -m pip --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Installing or validating dependencies..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r $requirements
}
else {
    Write-Host "pip is not available inside the venv. Reusing Anaconda site-packages instead."
}

Write-Host ""
Write-Host "Local environment is ready."
Write-Host "Run with:"
Write-Host "1. Double-click: run_client_workflow.bat"
Write-Host "2. PowerShell: .\\run_client_workflow.ps1"
Write-Host "3. Directly: $venvPython run_client_workflow.py"
