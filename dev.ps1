#Requires -Version 5.1
<#
.SYNOPSIS
    OmniTube dev launcher - starts backend + frontend in separate windows.

.DESCRIPTION
    Opens two PowerShell windows: one for the FastAPI backend (port 8000)
    and one for the SvelteKit frontend (port 5173).
    Each window handles its own venv / npm install automatically.

.EXAMPLE
    .\dev.ps1
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "      OmniTube Dev Launcher          " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# -- Backend -----------------------------------------------------------------
Write-Host "Starting backend window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\backend\start.ps1" -WindowStyle Normal

# Brief pause so backend can bind port 8000 before frontend starts
Start-Sleep -Seconds 3

# -- Frontend ----------------------------------------------------------------
Write-Host "Starting frontend window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\frontend\start.ps1" -WindowStyle Normal

Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  API docs: http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Both servers are running in separate windows." -ForegroundColor DarkGray
Write-Host "Close those windows (or press Ctrl+C in each) to stop them." -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press any key to close this launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
