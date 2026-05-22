@echo off
echo ==========================================
echo       Starting WRC League Manager
echo ==========================================
cd /d "%~dp0"

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR!] Python was not found on your system.
    echo Please install Python from python.org and make sure to check the box
    echo "Add Python to PATH" at the bottom of the installer window!
    pause
    exit
)

:: 2. Setup environment (if missing)
if not exist "venv\Scripts\activate.bat" (
    echo [1/3] First time setup: Creating virtual environment...
    python -m venv venv
    
    echo [2/3] Installing required packages (this will take a minute)...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo Installation complete!
) else (
    echo [1/2] Virtual environment found. Activating...
    call venv\Scripts\activate.bat
)

:: 3. Run Application
echo [Final Step] Starting the server! Your browser will open shortly...
echo ======================================================================
echo   [!] DO NOT CLOSE THIS BLACK WINDOW WHILE USING THE APP!
echo   [!] Closing this window will shut down the server.
echo ======================================================================
start http://127.0.0.1:8000

uvicorn main:app --host 127.0.0.1 --port 8000

echo.
echo [!] The server has been closed or an error occurred.
pause