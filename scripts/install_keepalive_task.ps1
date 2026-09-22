# install_keepalive_task.ps1
# Registers a Windows Scheduled Task to run horus_keepalive.ps1 daily at 10:00 AM (Sun-Thu).
#
# Task operations:
#   Install:   powershell.exe -ExecutionPolicy Bypass -File .\scripts\install_keepalive_task.ps1
#   Inspect:   Get-ScheduledTask -TaskName "HorusAnalyticsKeepAlive" | Get-ScheduledTaskInfo
#   Uninstall: Unregister-ScheduledTask -TaskName "HorusAnalyticsKeepAlive" -Confirm:$false

$OutputEncoding = [System.Text.Encoding]::UTF8

$TaskName = "HorusAnalyticsKeepAlive"
$ScriptPath = Join-Path $PSScriptRoot "horus_keepalive.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

# EGX Trading Days: Sunday, Monday, Tuesday, Wednesday, Thursday
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday, Monday, Tuesday, Wednesday, Thursday -At 10:00AM

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Keeps system awake during Horus Analytics market session (10:00 to 15:30 EEST). Application market/holiday guards remain authoritative." -Force

Write-Host "✅ Scheduled Task '$TaskName' successfully registered to run daily at 10:00 AM (Sun-Thu)."
Write-Host "   Script: $ScriptPath"
Write-Host "   To inspect: Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
Write-Host "   To uninstall: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
