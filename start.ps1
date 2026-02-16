$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $root ".runlogs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Step {
    param([string]$Message)
    Write-Host "[stock-ai] $Message"
}

function Test-PortListening {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return $null -ne $conn
    }
    catch {
        return $false
    }
}

function Start-Detached {
    param(
        [string]$Name,
        [string]$WorkingDir,
        [string]$Command,
        [string]$LogFile
    )

    $cmdLine = "cd /d `"$WorkingDir`" && $Command >> `"$LogFile`" 2>&1"
    $proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmdLine -WindowStyle Minimized -PassThru
    Write-Step "$Name started (PID: $($proc.Id))"
}

function Start-ComposeDeps {
    param([string]$RepoRoot)

    $services = "postgres redis influxdb"
    Push-Location $RepoRoot
    try {
        Write-Step "Starting docker dependencies: $services"
        & docker compose up -d postgres redis influxdb | Out-Host
        if ($LASTEXITCODE -eq 0) { return }
    }
    catch {}
    finally {
        Pop-Location
    }

    Push-Location $RepoRoot
    try {
        & docker-compose up -d postgres redis influxdb | Out-Host
        if ($LASTEXITCODE -eq 0) { return }
        throw "docker compose command failed"
    }
    finally {
        Pop-Location
    }
}

Write-Step "Workspace: $root"

try {
    Start-ComposeDeps -RepoRoot $root
}
catch {
    Write-Warning "Docker dependencies not started automatically. Ensure Docker Desktop is running, then retry."
}

$backendPort = 8001
$frontendPort = 3000

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backendLog = Join-Path $logDir "backend-$stamp.log"
$frontendLog = Join-Path $logDir "frontend-$stamp.log"

if (Test-PortListening -Port $backendPort) {
    Write-Step "Backend already listening on port $backendPort, skip startup."
}
else {
    $backendDir = Join-Path $root "backend"
    Start-Detached `
        -Name "Backend (FastAPI)" `
        -WorkingDir $backendDir `
        -Command "python -m uvicorn main:app --host 0.0.0.0 --port 8001" `
        -LogFile $backendLog
}

if (Test-PortListening -Port $frontendPort) {
    Write-Step "Frontend already listening on port $frontendPort, skip startup."
}
else {
    $frontendDir = Join-Path $root "frontend"
    Start-Detached `
        -Name "Frontend (Vite)" `
        -WorkingDir $frontendDir `
        -Command "npm run dev -- --host 0.0.0.0 --port 3000" `
        -LogFile $frontendLog
}

Write-Host ""
Write-Host "Done."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8001"
Write-Host "Backend log:  $backendLog"
Write-Host "Frontend log: $frontendLog"

Start-Sleep -Seconds 3
if (Test-PortListening -Port $backendPort) {
    Write-Step "Backend port $backendPort is listening."
}
else {
    Write-Warning "Backend port $backendPort is not listening yet. Check: $backendLog"
}

if (Test-PortListening -Port $frontendPort) {
    Write-Step "Frontend port $frontendPort is listening."
}
else {
    Write-Warning "Frontend port $frontendPort is not listening yet. Check: $frontendLog"
}
