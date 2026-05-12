@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE="

if exist "%ROOT%.venv_ga\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT%.venv_ga\Scripts\python.exe"
) else if exist "%ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
)

if "%PYTHON_EXE%"=="" (
    echo Local Python environment was not found.
    echo Expected one of:
    echo   %ROOT%.venv_ga\Scripts\python.exe
    echo   %ROOT%.venv\Scripts\python.exe
    echo.
    echo Please run setup_local_env.ps1 first.
    pause
    exit /b 1
)

if not exist "%ROOT%outputs" (
    mkdir "%ROOT%outputs"
)

echo ============================================================
echo Running client workflow...
echo Input  : please select an Excel workbook in the popup window
echo Output : outputs\client_runs
echo Log    : saved inside the current run folder
echo ============================================================
echo.

"%PYTHON_EXE%" "%ROOT%run_client_workflow.py"

if errorlevel 1 (
    echo Workflow failed. Please check the latest folder under outputs\client_runs.
    pause
    exit /b 1
)

echo Workflow completed successfully.
echo Please check outputs\client_runs for the result workbook, drawings and reports.
echo.
pause
