@echo off
echo ======================================================
echo   VIBETRAVEL: One-Click AI Brain Generator (Isolated)
echo ======================================================

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Python is not installed. 
    echo Please install Python from https://www.python.org/downloads/
    echo (Make sure to check "Add Python to PATH" during installation)
    pause
    exit /b
)

:: 2. Create the isolate "bubble" folder (venv)
if not exist venv (
    echo [*] Creating isolated environment (this won't touch your system files)...
    python -m venv venv
)

:: 3. Install packages into the bubble
echo [*] Entering the bubble and installing AI libraries...
call venv\Scripts\activate
pip install -r requirements.txt

:: 4. Run the script
echo [*] Starting the generator!
python generate_embeddings.py

echo.
echo ======================================================
echo   SUCCESS! "destination_embeddings.json" is ready.
echo   You can now delete this whole folder if you want.
echo ======================================================
pause
