# horus_keepalive.ps1
# Prevents Windows system idle sleep during market hours (10:00 to 15:30 EEST).

param (
    [int]$DurationMinutes = 330,
    [string]$TargetEndTime = "15:30",
    [switch]$KeepDisplayAwake,
    [switch]$NotifyTelegram
)

$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class WinAPI {
    [Flags]
    public enum ExecutionState : uint {
        ES_SYSTEM_REQUIRED  = 0x00000001,
        ES_DISPLAY_REQUIRED = 0x00000002,
        ES_CONTINUOUS       = 0x80000000
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern ExecutionState SetThreadExecutionState(ExecutionState esFlags);
}
"@

$ES_SYSTEM_REQUIRED  = [WinAPI+ExecutionState]::ES_SYSTEM_REQUIRED
$ES_DISPLAY_REQUIRED = [WinAPI+ExecutionState]::ES_DISPLAY_REQUIRED
$ES_CONTINUOUS       = [WinAPI+ExecutionState]::ES_CONTINUOUS

# System sleep prevention by default; display sleep prevention is opt-in (-KeepDisplayAwake)
$keepAliveFlags = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED
if ($KeepDisplayAwake) {
    $keepAliveFlags = $keepAliveFlags -bor $ES_DISPLAY_REQUIRED
}

$startTime = Get-Date
$targetParts = $TargetEndTime.Split(":")
$targetHour = [int]$targetParts[0]
$targetMinute = [int]$targetParts[1]
$todayTarget = Get-Date -Hour $targetHour -Minute $targetMinute -Second 0

# If task starts at or after target market close time, exit immediately
if ($startTime -ge $todayTarget) {
    Write-Host "[Horus KeepAlive] Started at $($startTime.ToString('HH:mm')) which is at or past target end time ($TargetEndTime). Exiting."
    exit 0
}

$endTime = $todayTarget

[WinAPI]::SetThreadExecutionState($keepAliveFlags) | Out-Null
Write-Host "[Horus KeepAlive] System sleep prevention ACTIVE starting at $startTime."
Write-Host "[Horus KeepAlive] Target coverage window: 10:00 -> $TargetEndTime."

# Opt-in Telegram notification
if ($NotifyTelegram) {
    try {
        $projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
        $pythonExe = Join-Path $projectRoot ".venv313\Scripts\python.exe"
        if (Test-Path $pythonExe) {
            Set-Location $projectRoot
            & $pythonExe -c "from core import AlertManager; AlertManager.broadcast_alert('⚡ *[HORUS MARKET KEEP-ALIVE]*\nSystem sleep prevention ACTIVE for trading session (10:00 - 15:30 EEST).')" 2>$null
        } else {
            Write-Host "[Horus KeepAlive] Python virtualenv not found at $pythonExe; notification skipped."
        }
    } catch {
        Write-Host "[Horus KeepAlive] Telegram notification skipped: $_"
    }
}

try {
    while ((Get-Date) -lt $endTime) {
        $remaining = New-TimeSpan -Start (Get-Date) -End $endTime
        Write-Host "[Horus KeepAlive] Heartbeat $((Get-Date).ToString('HH:mm:ss')) | Remaining: $($remaining.Hours)h $($remaining.Minutes)m"
        Start-Sleep -Seconds 300
    }
}
finally {
    [WinAPI]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
    Write-Host "[Horus KeepAlive] System sleep prevention RELEASED at $(Get-Date)."
}
