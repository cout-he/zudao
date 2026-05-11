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

set "LOG_FILE=%ROOT%outputs\run_client_workflow.log"

if not exist "%ROOT%outputs" (
    mkdir "%ROOT%outputs"
)

echo ============================================================
echo Running actual production workflow...
echo Input  : default workbook under the data folder
echo Output : default workbook under the outputs folder
echo Log    : %LOG_FILE%
echo ============================================================
echo.

"%PYTHON_EXE%" "%ROOT%scripts\main_actual_production.py" ^
  --decoder-mode auto ^
  --panel-widths 1000,1240,1250,1500 > "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo Workflow failed. Please check:
    echo   %LOG_FILE%
    pause
    exit /b 1
)

echo Workflow completed successfully.
echo Result workbook and artifact paths were written by the program.
echo Please check the outputs folder.
echo Log file:
echo   %LOG_FILE%
echo.
pause
