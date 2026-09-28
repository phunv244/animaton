# Mo nhanh giao dien Web Dashboard cua Conway Automaton
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$' } | ForEach-Object {
        Set-Item "env:$($Matches[1])" $Matches[2]
    }
}
$dashRunning = Test-NetConnection -ComputerName 127.0.0.1 -Port 5050 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $dashRunning) {
    Write-Host "Khoi dong Web Dashboard tren port 5050..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "dashboard.py" -WorkingDirectory $PSScriptRoot -NoNewWindow
    Start-Sleep -Seconds 2
}
Start-Process "http://localhost:5050"
Write-Host "Da mo giao dien tai: http://localhost:5050" -ForegroundColor Green
