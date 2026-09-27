# Mo nhanh giao dien Web Dashboard cua Conway Automaton
$dashRunning = Test-NetConnection -ComputerName 127.0.0.1 -Port 5050 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $dashRunning) {
    Write-Host "Khoi dong Web Dashboard tren port 5050..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "dashboard.py" -NoNewWindow
    Start-Sleep -Seconds 2
}
Start-Process "http://localhost:5050"
Write-Host "Da mo giao dien tai: http://localhost:5050" -ForegroundColor Green
