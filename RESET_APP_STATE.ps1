# RESET_APP_STATE.ps1 — Horus Full Reset (PowerShell version)
# Run with: powershell -ExecutionPolicy Bypass -File RESET_APP_STATE.ps1

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_ROOT

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "               HORUS FULL RESET (START FRESH)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will permanently delete:" -ForegroundColor Yellow
Write-Host "  - SQLite database files (horus.db, -wal, -shm)"
Write-Host "  - Runtime result artifacts (reports, signal archive, journal)"
Write-Host "  - Runtime logs"
Write-Host "  - Local market data lake files under data\ (history/intraday/ticks/cache/wfa)"
Write-Host ""
Write-Host "It does NOT delete your source code." -ForegroundColor Green
Write-Host ""
$confirm = Read-Host "Type RESET to continue"
if ($confirm -ne "RESET") {
    Write-Host ""
    Write-Host "Reset cancelled." -ForegroundColor Yellow
    exit 1
}

# ── Helper Functions ─────────────────────────────────────────────────────────

function Remove-FileIfExists($path) {
    if (Test-Path $path) {
        Remove-Item -Force $path -ErrorAction SilentlyContinue
        if (Test-Path $path) {
            Write-Host "[WARN] Could not delete $path (may be in use)." -ForegroundColor Yellow
        } else {
            Write-Host "[OK] Deleted $path"
        }
    } else {
        Write-Host "[SKIP] $path not found."
    }
}

function New-JsonFile($path, $content) {
    $content | Out-File -Encoding utf8 -FilePath $path -Force
    if (Test-Path $path) {
        Write-Host "[OK] Created $path"
    } else {
        Write-Host "[WARN] Failed to create $path" -ForegroundColor Yellow
    }
}

function New-EmptyFile($path) {
    "" | Out-File -Encoding utf8 -FilePath $path -Force
    Write-Host "[OK] Created $path"
}

function Stop-HorusExe {
    $procs = Get-Process -Name "HorusAnalytics" -ErrorAction SilentlyContinue
    foreach ($proc in $procs) {
        Write-Host "[INFO] Stopping HorusAnalytics.exe (PID $($proc.Id))..."
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

function Get-PortPid($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) { return $conn.OwningProcess }
    # Fallback via netstat
    $lines = netstat -ano 2>$null | Select-String ":$port\s.*LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.Line -split '\s+' | Where-Object { $_ -ne "" })
        if ($parts.Count -ge 5) { return $parts[-1] }
    }
    return $null
}

function Assert-PortFree($port, $label) {
    $foundPid = Get-PortPid $port
    if ($foundPid) {
        Write-Host "[WARN] $label appears to be running on port $port (PID $foundPid)." -ForegroundColor Yellow
        Write-Host "       Close Horus API/UI windows, then run reset again." -ForegroundColor Yellow
        return $false
    }
    return $true
}

# ── Preflight ────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Preflight: validating no running Horus services..."
Stop-HorusExe

if (-not (Assert-PortFree 8200 "API backend")) {
    Write-Host ""
    Write-Host "Reset aborted." -ForegroundColor Red
    exit 1
}
if (-not (Assert-PortFree 3000 "Frontend UI")) {
    Write-Host ""
    Write-Host "Reset aborted." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] No active Horus services detected." -ForegroundColor Green

# ── Step 1: Database files ────────────────────────────────────────────────────

Write-Host ""
Write-Host "[1/7] Removing database files..."
Remove-FileIfExists "horus.db"
Remove-FileIfExists "horus.db-wal"
Remove-FileIfExists "horus.db-shm"

# ── Step 2: Runtime artifacts ─────────────────────────────────────────────────

Write-Host ""
Write-Host "[2/7] Removing runtime result artifacts..."
Remove-FileIfExists "signal_archive.json"
Remove-FileIfExists "journal.json"
Remove-FileIfExists "genesis.lock"

if (Test-Path "reports") {
    Get-ChildItem "reports\*.md" -ErrorAction SilentlyContinue | Remove-Item -Force
    if (Test-Path "reports\tabs") {
        Get-ChildItem "reports\tabs\*.md" -ErrorAction SilentlyContinue | Remove-Item -Force
    }
    Write-Host "[OK] Cleared report markdown files."
} else {
    Write-Host "[SKIP] reports folder not found."
}

# ── Step 3: Runtime logs ──────────────────────────────────────────────────────

Write-Host ""
Write-Host "[3/7] Removing runtime logs..."
Remove-FileIfExists "api_errors.log"
Remove-FileIfExists "autotrader.log"
Remove-FileIfExists "scanner.log"

# _internal/logs/horus.log is the live log in the PyInstaller bundle
if (Test-Path "_internal\logs\horus.log") {
    Clear-Content "_internal\logs\horus.log" -ErrorAction SilentlyContinue
    Write-Host "[OK] Cleared _internal\logs\horus.log (bundled application log)"
}
Get-ChildItem "_internal\logs" -Filter "horus.log.*" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
}

# logs/horus.log is the live log when running from source
if (Test-Path "logs\horus.log") {
    Clear-Content "logs\horus.log" -ErrorAction SilentlyContinue
    Write-Host "[OK] Cleared logs\horus.log (source application log)"
}
Get-ChildItem "logs" -Filter "horus.log.*" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
}

# ── Step 4: Data lake ─────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[4/7] Removing market data lake files..."
$lakeRoot = "data"
if (-not (Test-Path $lakeRoot)) { New-Item -ItemType Directory $lakeRoot | Out-Null }

Get-ChildItem $lakeRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $_.FullName) {
        Write-Host "[WARN] Could not remove folder $($_.FullName)" -ForegroundColor Yellow
    }
}
Get-ChildItem $lakeRoot -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
}
Write-Host "[OK] Cleared data lake files under $lakeRoot"

# Recreate layout
$dirs = @("data","data\cache","data\wfa","data\EGX","data\EGX\history","data\EGX\ticks","data\EGX\dlq","data\EGX\dlq\history","data\EGX\dlq\intraday")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory $d | Out-Null }
}
New-JsonFile "data\pipeline_worker_state.json" "{}"
New-JsonFile "data\cache\analytics_cache.json" "{}"
New-JsonFile "data\wfa\trade_gate.json" "{}"
Write-Host "[OK] Recreated data lake directory layout."

# ── Step 4.5: Settings ────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[4.5/7] Removing persisted runtime settings..."
Remove-FileIfExists "settings.json"

# ── Step 5: Re-initialize DB ─────────────────────────────────────────────────

Write-Host ""
Write-Host "[5/7] Re-initializing fresh database schema..."

# Look for Python: check both current project root and (if in dist) the actual source root
$sourceRoot = if ($PROJECT_ROOT -match "dist\\HorusApp$") { Split-Path -Parent (Split-Path -Parent $PROJECT_ROOT) } else { $PROJECT_ROOT }
$pyCandidates = @(
    (Join-Path $sourceRoot ".venv313\Scripts\python.exe"),
    (Join-Path $sourceRoot ".venv\Scripts\python.exe"),
    (Join-Path $PROJECT_ROOT ".venv313\Scripts\python.exe"),
    (Join-Path $PROJECT_ROOT ".venv\Scripts\python.exe")
)
$pyExe = $pyCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($pyExe) {
    $env:PYTHONPATH = $sourceRoot
    $initCmd = "import sys; sys.path.insert(0,r'$pwd'); import database; database.initialize_db(); print('Initialized database successfully')"
    $null = & $pyExe -c $initCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] DB init via source venv returned non-zero - exe will self-initialize on first launch." -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Schema initialized."
    }
} else {
    Write-Host "[INFO] No source venv found - skipping pre-init. HorusAnalytics.exe will initialize horus.db on first launch." -ForegroundColor Yellow
}

# ── Step 6: Baseline files ────────────────────────────────────────────────────

Write-Host ""
Write-Host "[6/7] Creating fresh runtime baseline files..."
New-JsonFile "signal_archive.json" "[]"
New-JsonFile "journal.json" "[]"
if (-not (Test-Path "reports")) { New-Item -ItemType Directory "reports" | Out-Null }
if (-not (Test-Path "reports\tabs")) { New-Item -ItemType Directory "reports\tabs" | Out-Null }
New-EmptyFile "api_errors.log"
New-EmptyFile "autotrader.log"
New-EmptyFile "scanner.log"
Write-Host "[INFO] genesis.lock intentionally left absent (fresh-first-run state)."

# ── Step 7: Launch ────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[7/7] Launching app in clean mode..."
if (-not $pyExe) { $pyExe = "python" }
$env:PYTHONPATH = $PROJECT_ROOT
$env:SESSION_MODE = "LIVE"
$env:SKIP_STARTUP_SYNC = "true"
$env:FORCE_BOOTSTRAP_SYNC = "0"
$env:HORUS_DISABLE_STARTUP_THREAD = "1"

if (Test-Path "HorusAnalytics.exe") {
    Write-Host "[START] Packaged app executable: HorusAnalytics.exe"
    Start-Process "HorusAnalytics.exe"
} else {
    Write-Host "[START] Backend API (clean mode): http://127.0.0.1:8200"
    Start-Process "cmd" -ArgumentList "/k `"cd /d `"$PROJECT_ROOT`" && `"$pyExe`" -m uvicorn api:app --port 8200`""

    if (Test-Path "frontend\package.json") {
        Write-Host "[START] Frontend UI: http://localhost:3000"
        Start-Process "cmd" -ArgumentList "/k `"cd /d `"${PROJECT_ROOT}frontend`" && npm run dev`""
    } else {
        Write-Host "[WARN] frontend\package.json not found. Frontend was not started." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Reset complete. Clean runtime started." -ForegroundColor Green
Write-Host "- Backend:  http://127.0.0.1:8200/docs"
Write-Host "- Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Notes:"
Write-Host "- Startup sync is disabled to preserve a truly fresh empty state."
Write-Host "- Startup background thread is disabled for this clean run."
Write-Host "- Enable sync manually when you want to repopulate market/signal data."
Write-Host "============================================================" -ForegroundColor Cyan
