@echo off
title SPECTRA-UPI Dev Servers

echo.
echo  ========================================
echo    SPECTRA-UPI - Starting Dev Servers
echo  ========================================
echo.

:: Start Backend
echo  [1/2] Starting FastAPI backend on port 8000...
start "SPECTRA-UPI Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && uvicorn api.main:app --reload --port 8000"

:: Wait a moment for backend to init
timeout /t 3 /nobreak > nul

:: Start Frontend
echo  [2/2] Starting React frontend on port 5173...
start "SPECTRA-UPI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo  Both servers starting...
echo.
echo  Backend API:  http://localhost:8000
echo  API Docs:     http://localhost:8000/docs
echo  Frontend App: http://localhost:5173
echo.
echo  Close this window at any time.
echo  To stop servers: close their terminal windows.
echo.
pause
