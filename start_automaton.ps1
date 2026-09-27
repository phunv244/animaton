# Conway Automaton Startup Script with Local Antigravity Engine + Web Dashboard
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "    Conway Automaton + Local Antigravity Engine   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Set environment variables for Windows compatibility & Local Antigravity Bridge
$env:HOME = $env:USERPROFILE
$env:CONWAY_API_KEY = "local-antigravity"
$env:OPENAI_API_BASE = "http://127.0.0.1:8888"
$env:OPENAI_BASE_URL = "http://127.0.0.1:8888/v1"
$env:OPENAI_API_KEY = "sk-antigravity"

# Load Tavily Search API key
$configPath = "$env:USERPROFILE\.automaton\automaton.json"
if (Test-Path $configPath) {
    $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
    if ($cfg.tavilyApiKey) {
        $env:TAVILY_API_KEY = $cfg.tavilyApiKey
    }
}
if (-not $env:TAVILY_API_KEY) {
    $env:TAVILY_API_KEY = "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"
}

# 1. Start Antigravity Bridge on port 8888 if not already running
$bridgeRunning = Test-NetConnection -ComputerName 127.0.0.1 -Port 8888 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $bridgeRunning) {
    Write-Host "[1/3] Khoi dong Antigravity Bridge (Port 8888)..." -ForegroundColor Yellow
    $bridgeJob = Start-Process python -ArgumentList "antigravity_bridge.py" -WorkingDirectory $PSScriptRoot -PassThru -NoNewWindow
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/3] Antigravity Bridge da hoat dong tren port 8888." -ForegroundColor Green
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
