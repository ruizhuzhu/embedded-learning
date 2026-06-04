# Embedded C/C++ Daily Question Generator - Windows Task Scheduler Setup
# Run this script as Administrator to create a daily scheduled task at 7:00 AM
#
# Usage: powershell -ExecutionPolicy Bypass -File schedule_windows.ps1

$ErrorActionPreference = "Stop"

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Find Python
$PythonPath = $null
try {
    $PythonPath = (Get-Command python -ErrorAction Stop).Source
} catch {
    try {
        $PythonPath = (Get-Command python3 -ErrorAction Stop).Source
    } catch {
        Write-Host "[ERROR] Python not found! Please install Python 3.x and add to PATH." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Python: $PythonPath" -ForegroundColor Green
Write-Host "Script: $ScriptDir" -ForegroundColor Green

# Task name
$TaskName = "EmbeddedDailyQuiz"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action: run generate.py
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "generate.py" `
    -WorkingDirectory $ScriptDir

# Trigger: daily at 7:00 AM
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "07:00AM"

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Run as current user
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Daily embedded C/C++ practice question generator" `
    -Force

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  [OK] Task '$TaskName' created!" -ForegroundColor Green
Write-Host "  Daily at 7:00 AM -> $ScriptDir\output\" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - Open taskschd.msc to view/modify the task"
Write-Host "  - Test now: python generate.py"
Write-Host "  - Remove task: Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
