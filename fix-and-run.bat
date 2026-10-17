@echo off
REM ================================================================
REM  SPECTRA-UPI — Fix AppLocker + Rebuild venv + Start both servers
REM  Run this as Administrator for best results.
REM  It will try C:\Program Files\Python314 first (AppLocker-safe),
REM  then fall back to your existing Python if that path works.
REM ================================================================

echo ============================================================
echo  SPECTRA-UPI Setup + Launch
echo ============================================================

set PROJ=C:\Users\Girish\OneDrive\Desktop\SPECTRA-UPI
set BACKEND=%PROJ%\backend
set FRONTEND=%PROJ%\frontend

REM --- Detect Python ---
set PY=
if exist "C:\Program Files\Python314\python.exe" (
    set PY=C:\Program Files\Python314\python.exe
    echo [OK] Found Python in Program Files - AppLocker-safe path
) else if exist "C:\Program Files\Python313\python.exe" (
    set PY=C:\Program Files\Python313\python.exe
    echo [OK] Found Python313 in Program Files
) else if exist "C:\Program Files\Python312\python.exe" (
    set PY=C:\Program Files\Python312\python.exe
    echo [OK] Found Python312 in Program Files
) else (
    echo [WARN] No Python found in C:\Program Files\
    echo        Trying AppData Python (may hit AppLocker)...
    set PY=C:\Users\Girish\AppData\Local\Programs\Python\Python314\python.exe
)

echo [INFO] Using Python: %PY%
echo.

REM --- Rebuild venv ---
echo [1/4] Rebuilding venv in backend...
if exist "%BACKEND%\venv" (
    rmdir /s /q "%BACKEND%\venv"
    echo       Old venv removed.
)
"%PY%" -m venv "%BACKEND%\venv"
if errorlevel 1 (
    echo [ERROR] venv creation failed. Make sure Python is installed.
    pause
    exit /b 1
)
echo       venv created.

REM --- Install requirements ---
echo [2/4] Installing dependencies (this takes 2-3 minutes)...
"%BACKEND%\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%BACKEND%\venv\Scripts\pip.exe" install -r "%BACKEND%\requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed. Check requirements.txt.
    pause
    exit /b 1
)
echo       All packages installed.

REM --- Test imports ---
echo [3/4] Testing backend imports...
"%BACKEND%\venv\Scripts\python.exe" -c "import sklearn, xgboost, fastapi, sqlalchemy; print('[OK] All imports successful')"
if errorlevel 1 (
    echo [ERROR] Import test failed - AppLocker may still be blocking.
    echo         Solution: Reinstall Python to C:\Program Files\Python314
    echo         from python.org with 'Customize installation' and set path there.
    pause
    exit /b 1
)

REM --- Start backend in new window ---
echo [4/4] Starting servers...
start "SPECTRA-UPI Backend" cmd /k "cd /d %BACKEND% && venv\Scripts\activate.bat && echo Starting FastAPI... && uvicorn api.main:app --reload --port 8000"

REM --- Wait for backend to come up ---
timeout /t 4 /nobreak >nul

REM --- Start frontend in new window ---
start "SPECTRA-UPI Frontend" cmd /k "cd /d %FRONTEND% && echo Starting React dev server... && npm run dev"

echo.
echo ============================================================
echo  Both servers starting in separate windows.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ============================================================
echo.
echo  Opening frontend in browser in 8 seconds...
timeout /t 8 /nobreak >nul
start http://localhost:5173

pause
