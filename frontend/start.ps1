#Requires -Version 5.1
<#
.SYNOPSIS
    Start the OmniTube SvelteKit frontend dev server.

.DESCRIPTION
    - Runs npm install if node_modules is missing or package.json is newer
    - Runs svelte-kit sync to regenerate type declarations if needed
    - Starts the Vite dev server on port 5173

.EXAMPLE
    .\start.ps1
    .\start.ps1 -Port 5174
#>
param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $ScriptDir

# -- Check for Node.js --------------------------------------------------------
try {
    $nodeVer = node --version 2>&1
    Write-Host "Node.js: $nodeVer" -ForegroundColor DarkGray
} catch {
    Write-Error "Node.js not found. Install it from https://nodejs.org"
    exit 1
}

# -- Install node_modules if missing or stale ---------------------------------
$NodeModules = Join-Path $ScriptDir "node_modules"
$PackageJson = Join-Path $ScriptDir "package.json"
$PackageLock = Join-Path $ScriptDir "package-lock.json"
$Stamp       = Join-Path $NodeModules ".install_stamp"

$needsInstall = $true
if (Test-Path $NodeModules) {
    if (Test-Path $Stamp) {
        $stampTime = (Get-Item $Stamp).LastWriteTime

        # Compare stamp against package.json and package-lock.json
        $pkgNewer = (Test-Path $PackageJson) -and ((Get-Item $PackageJson).LastWriteTime -gt $stampTime)
        $lockNewer = (Test-Path $PackageLock) -and ((Get-Item $PackageLock).LastWriteTime -gt $stampTime)

        if (-not $pkgNewer -and -not $lockNewer) {
            $needsInstall = $false
        }
    }
}

if ($needsInstall) {
    Write-Host "Running npm install..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install failed."
        exit 1
    }
    New-Item -ItemType File -Path $Stamp -Force | Out-Null
    Write-Host "Packages installed." -ForegroundColor Green
} else {
    Write-Host "node_modules up-to-date." -ForegroundColor DarkGray
}

# -- Run svelte-kit sync if .svelte-kit is missing ----------------------------
$SvelteKit = Join-Path $ScriptDir ".svelte-kit"
if (-not (Test-Path $SvelteKit)) {
    Write-Host "Running svelte-kit sync..." -ForegroundColor Cyan
    npx svelte-kit sync
    if ($LASTEXITCODE -ne 0) {
        Write-Error "svelte-kit sync failed."
        exit 1
    }
}

# -- Start Vite dev server ----------------------------------------------------
Write-Host ""
Write-Host "Starting OmniTube frontend..." -ForegroundColor Cyan
Write-Host "  URL: http://localhost:$Port" -ForegroundColor Green
Write-Host "  Backend must be running on port 8000." -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

$env:PORT = $Port
npm run dev -- --port $Port
