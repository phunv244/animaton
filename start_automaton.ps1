# Conway Automaton Startup Script with Local Antigravity Engine + Web Dashboard
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "    Conway Automaton + Local Antigravity Engine   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$env:HOME = $env:USERPROFILE

# Load .env (see .env.example). Empty values are skipped.
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Thieu file .env. Copy .env.example thanh .env roi dien key." -ForegroundColor Red
    exit 1
}
Get-Content $envFile | Where-Object { $_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$' } | ForEach-Object {
    Set-Item "env:$($Matches[1])" $Matches[2]
}
$bridgePort = if ($env:BRIDGE_PORT) { [int]$env:BRIDGE_PORT } else { 8888 }

# 1. Start Antigravity Bridge if not already running
$bridgeRunning = Test-NetConnection -ComputerName 127.0.0.1 -Port $bridgePort -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $bridgeRunning) {
    Write-Host "[1/3] Khoi dong Antigravity Bridge (Port $bridgePort)..." -ForegroundColor Yellow
    $bridgeJob = Start-Process python -ArgumentList "antigravity_bridge.py" -WorkingDirectory $PSScriptRoot -PassThru -NoNewWindow
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/3] Antigravity Bridge da hoat dong tren port $bridgePort." -ForegroundColor Green
}

# 2. Start Web Dashboard on port 5050 if not already running
$dashRunning = Test-NetConnection -ComputerName 127.0.0.1 -Port 5050 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $dashRunning) {
    Write-Host "[2/3] Khoi dong Giao dien Web Dashboard (Port 5050)..." -ForegroundColor Yellow
    $dashJob = Start-Process python -ArgumentList "dashboard.py" -WorkingDirectory $PSScriptRoot -PassThru -NoNewWindow
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5050"
} else {
    Write-Host "[2/3] Giao dien Web Dashboard dang mo tren http://localhost:5050" -ForegroundColor Green
}

Write-Host "[3/3] Khoi dong Automaton Runtime..." -ForegroundColor Yellow
Write-Host "Agent se su dung truc tiep Gemini/Claude cua Antigravity tren may local!" -ForegroundColor Green
Write-Host "Xem giao dien truc quan tai: http://localhost:5050`n" -ForegroundColor Cyan

try {
    node dist/index.js --run
} finally {
    if ($bridgeJob -and -not $bridgeJob.HasExited) {
        Write-Host "Dung Antigravity Bridge..." -ForegroundColor Yellow
        Stop-Process -Id $bridgeJob.Id -Force -ErrorAction SilentlyContinue
    }
    if ($dashJob -and -not $dashJob.HasExited) {
        Write-Host "Dung Web Dashboard..." -ForegroundColor Yellow
        Stop-Process -Id $dashJob.Id -Force -ErrorAction SilentlyContinue
    }
}
