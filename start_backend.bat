@echo off
echo Starting P2P BitTorrent Backend Server...
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
pip install -r requirements.txt >nul 2>&1

REM Start the backend server exposed to network
echo Starting backend server on all interfaces...
echo Backend will be available at:
echo   Local:   http://localhost:8000
echo   Network: http://[YOUR-IP]:8000
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
