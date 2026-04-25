@echo off
:: Strictly ASCII to avoid encoding issues on Chinese Windows
setlocal enabledelayedexpansion

:: Get root directory
set "ROOT_DIR=%~dp0"

echo ------------------------------------------
echo Goddess Photoshoot - Startup Sequence
echo ------------------------------------------

:: 1. Check venv
if not exist "%ROOT_DIR%venv\Scripts\activate.bat" (
    echo [Info] venv not found, creating...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [Error] Failed to create venv.
        pause
        exit /b 1
    )
    echo [Info] Installing dependencies...
    call "%ROOT_DIR%venv\Scripts\activate.bat" && pip install -r "%ROOT_DIR%backend\requirements.txt"
)

:: 2. Start Backend
echo [1/2] Starting Backend...
start "Goddess-Backend" /d "%ROOT_DIR%backend" cmd /c "call ..\venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 3. Start Frontend
echo [2/2] Starting Frontend...
if exist "%ROOT_DIR%frontend\node_modules\" (
    start "Goddess-Frontend" /d "%ROOT_DIR%frontend" cmd /c "npm run dev"
) else (
    echo [Info] node_modules not found, installing...
    start "Goddess-Frontend" /d "%ROOT_DIR%frontend" cmd /c "npm install && npm run dev"
)

echo ------------------------------------------
echo All commands sent! 
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:5173
echo ------------------------------------------
pause
