@echo off
echo Starting P2P BitTorrent Desktop Client...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r desktop_client\requirements.txt >nul 2>&1

REM Start the desktop client
echo Starting desktop client...
python desktop_client\main.py

pause
