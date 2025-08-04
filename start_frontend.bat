@echo off
echo Starting P2P BitTorrent Web Frontend...
echo.

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo Starting development server...
echo Frontend will be available at: http://localhost:3000
echo.

npm run dev
