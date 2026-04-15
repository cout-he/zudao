@echo off
set ROOT=%~dp0
if not exist "%ROOT%.venv_ga\Scripts\python.exe" (
    echo Local virtual environment .venv_ga was not found.
    echo Run setup_local_env.ps1 first.
    exit /b 1
)

"%ROOT%.venv_ga\Scripts\python.exe" "%ROOT%scripts\main_ga.py"
