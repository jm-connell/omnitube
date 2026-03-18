#Requires -Version 5.1
<#
.SYNOPSIS
    Start the OmniTube FastAPI backend dev server.

.DESCRIPTION
    - Finds or creates a Python virtual environment
    - Installs requirements if needed
    - Starts uvicorn with --reload on port 8000

.EXAMPLE
    .\start.ps1
    .\start.ps1 -Port 8001
#>
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $ScriptDir

# -- Find virtual environment -------------------------------------------------
# Prefer backend/venv, fall back to root .venv
$VenvCandidates = @(
    (Join-Path $ScriptDir "venv"),
    (Join-Path (Split-Path -Parent $ScriptDir) ".venv")
)

$VenvDir = $null
foreach ($candidate in $VenvCandidates) {
    if (Test-Path (Join-Path $candidate "Scripts\uvicorn.exe")) {
        $VenvDir = $candidate
        break
    }
}

# -- Create venv if none found ------------------------------------------------
if (-not $VenvDir) {
    Write-Host "No virtual environment found. Creating one..." -ForegroundColor Yellow

    # Find Python via Windows Launcher (py) or fallback
    $PyExe = $null
    foreach ($candidate in @("py", "python3", "python")) {
        try {
            $ver = & $candidate --version 2>&1
            if ($ver -match "Python 3") {
                $PyExe = $candidate
                break
            }
        } catch {}
    }

    if (-not $PyExe) {
        Write-Error "Python 3 not found. Install Python from python.org or the Microsoft Store."
        exit 1
    }

    $NewVenv = Join-Path $ScriptDir "venv"
    Write-Host "Creating venv at $NewVenv using $PyExe..." -ForegroundColor Cyan
    & $PyExe -m venv $NewVenv
    $VenvDir = $NewVenv
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe    = Join-Path $VenvDir "Scripts\pip.exe"
$UvicornExe = Join-Path $VenvDir "Scripts\uvicorn.exe"

Write-Host "Using venv: $VenvDir" -ForegroundColor DarkGray

# -- Install / sync requirements ----------------------------------------------
$ReqFile = Join-Path $ScriptDir "requirements.txt"
$Stamp   = Join-Path $VenvDir ".installed_stamp"

$needsInstall = $true
if (Test-Path $Stamp) {
    $stampTime = (Get-Item $Stamp).LastWriteTime
    $reqTime   = (Get-Item $ReqFile).LastWriteTime
    if ($stampTime -gt $reqTime) {
        $needsInstall = $false
    }
}

if ($needsInstall) {
    Write-Host "Installing/updating requirements..." -ForegroundColor Cyan
    & $PipExe install -r $ReqFile --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pip install failed."
        exit 1
    }
    New-Item -ItemType File -Path $Stamp -Force | Out-Null
    Write-Host "Requirements installed." -ForegroundColor Green
} else {
    Write-Host "Requirements up-to-date." -ForegroundColor DarkGray
}

# -- Ensure data directory exists ----------------------------------------------
$DataDir = Join-Path $ScriptDir "data"
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}

# -- Start uvicorn ------------------------------------------------------------
Write-Host ""
Write-Host "Starting OmniTube backend..." -ForegroundColor Cyan
Write-Host "  URL:  http://localhost:$Port" -ForegroundColor Green
Write-Host "  Docs: http://localhost:$Port/docs" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

& $UvicornExe "app.main:app" --reload --port $Port --host "0.0.0.0"
