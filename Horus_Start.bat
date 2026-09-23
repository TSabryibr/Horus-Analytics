@echo off
:: Quote the title to handle the pipe character correctly
TITLE "THE INFINITY SCEPTER | HORUS ANALYTICS v1.0"
COLOR 0D

:: Get the directory of the batch file and ensure we are in it
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: Check for Python in venv with valid dependencies, otherwise fallback to system python
set "PY_CMD=python"
if exist ".venv313\Scripts\python.exe" (
    .venv313\Scripts\python.exe -c "import duckdb, fastapi" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=.venv313\Scripts\python.exe"
    )
) else if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import duckdb, fastapi" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=.venv\Scripts\python.exe"
    )
)


:MENU
cls
echo ======================================================================
echo       THE INFINITY SCEPTER ^| HORUS ANALYTICS v1.0 ^| ASGARDIAN EDITION
echo ======================================================================
echo   "I drink from the well of Mimir, and I drink from the fire of Muspelheim."
echo ======================================================================
echo.
echo   [1] AWAKEN THE GOD MODE (Launch Chitauri Scepter CLI)
echo   [2] ENGAGE THE FULL STACK (API Backend + Next.js Frontend)
echo   [3] BRIDGE THE WORLDS (Sync MetaStock to Parquet Lake)
echo   [4] HEIMDALL'S SIGHT (Portfolio Guardian Diagnostics)
echo   [5] SOUND THE GJALLARHORN (Live Sentinel Monitor)
echo   [6] RUN THE LEGACY SYNC (Direct CSV/Intraday Ingest)
echo   [7] ACTIVATE THE TEMPORAL ENGINE (Adaptive Sync Worker)
echo.
echo   [Q] Exit
echo.
echo ======================================================================
echo Current Path: %CD%
echo.

set /p choice="Command > "

if "%choice%"=="1" goto GODMODE
if "%choice%"=="2" goto FULLSTACK
if "%choice%"=="3" goto MARKETSYNC
if "%choice%"=="4" goto GUARDIAN
if "%choice%"=="5" goto GJALLARHORN
if "%choice%"=="6" goto DATASYNC
if "%choice%"=="7" goto SYNCWORKER
if /i "%choice%"=="Q" exit
goto MENU

:GODMODE
echo.
echo 🔮 Invoking the Master Command Module...
set "PYTHONPATH=%PROJECT_ROOT%"
"%PY_CMD%" ChitauriScepter.py
if errorlevel 1 (
    echo.
    echo ❌ Error: Failed to launch ChitauriScepter.py
    pause
)
goto MENU

:FULLSTACK
echo.
echo 🔱 Engaging the Infinity Web Stack...
call :SESSION_PROMPT
if "%SESS_CHOICE%"=="Q" goto MENU

echo [1/2] Starting Backend API (Port 8000)...
set "PYTHONPATH=%PROJECT_ROOT%"
set "SESSION_MODE=%SESSION_MODE%"
start "Horus API" cmd /c ""%PY_CMD%" -m uvicorn api:app --port 8000"
timeout /t 3 >nul

echo [2/2] Starting Frontend Interface (Port 3100)...
if exist "frontend" (
    cd frontend
    start "Horus UI" cmd /c "npm run dev -- --hostname 127.0.0.1 --port 3100"
    cd ..
) else (
    echo ❌ Error: /frontend directory not found.
    pause
)
echo.
echo System deployment initiated.
echo - Dashboard: http://127.0.0.1:3100
echo - API Docs:  http://127.0.0.1:8000/docs
pause
goto MENU

:MARKETSYNC
echo.
echo 🔄 Crossing the Bifröst (Syncing MetaStock to Parquet)...
set "PYTHONPATH=%PROJECT_ROOT%"
"%PY_CMD%" MarketSync.py
if errorlevel 1 (
    echo.
    echo ❌ Error: MarketSync failed.
    pause
) else (
    echo.
    echo ✅ Sync Complete.
    pause
)
goto MENU

:GUARDIAN
echo.
echo 🛡️  Activating the Portfolio Guardian...
set "PYTHONPATH=%PROJECT_ROOT%"
"%PY_CMD%" PortfolioGuardian.py
echo.
pause
goto MENU

:GJALLARHORN
echo.
echo 📯 Sounding the Gjallarhorn (Live Monitoring)...
set "PYTHONPATH=%PROJECT_ROOT%"
"%PY_CMD%" Gjallarhorn.py
echo.
pause
goto MENU

:DATASYNC
echo.
echo 🔄 Synchronizing the Legacy Data Engine...
set "PYTHONPATH=%PROJECT_ROOT%"
"%PY_CMD%" -c "from data_engine.sync import sync_all; sync_all()"
if errorlevel 1 (
    echo.
    echo ❌ Error: Sync failed.
    pause
) else (
    echo.
    echo ✅ Legacy Sync Complete.
    pause
)
goto MENU

:SYNCWORKER
echo.
echo ⏳ Activating the Temporal Engine (Adaptive Sync Worker)...
call :SESSION_PROMPT
if "%SESS_CHOICE%"=="Q" goto MENU

set "PYTHONPATH=%PROJECT_ROOT%"
set "SESSION_MODE=%SESSION_MODE%"
start "Horus Sync Worker" cmd /c ""%PY_CMD%" -m data_engine.pipeline_worker"
echo.
echo ✅ Dedicated Sync Worker initiated in background.
pause
goto MENU

:SESSION_PROMPT
echo.
echo   [1] Live Market Session (Continuous Sync)
echo   [2] Analysis Session    (One-time Sync at startup)
echo.
set /p sess_choice="Select Session Mode [1] > "
if "%sess_choice%"=="" set "sess_choice=1"
if "%sess_choice%"=="1" (
    set "SESSION_MODE=LIVE"
    echo 🟢 Mode: LIVE MARKET
) else if "%sess_choice%"=="2" (
    set "SESSION_MODE=ANALYSIS"
    echo 🔵 Mode: ANALYSIS
) else (
    set "SESS_CHOICE=Q"
)
exit /b
