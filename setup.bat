@echo off
echo ============================================================
echo   KINETIK // Automated Setup & Environment Launcher
echo ============================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.12+.
    pause
    exit /b 1
)

REM Create virtual environment if it does not exist
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment in .venv...
    python -m venv .venv
)

echo [INFO] Installing / Updating dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [INFO] Running environment test verification...
pytest tests/ -q

echo.
echo ============================================================
echo   Setup Complete! Launching KINETIK...
echo ============================================================
python main.py
