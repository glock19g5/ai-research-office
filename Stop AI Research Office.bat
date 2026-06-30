@echo off
echo Stopping AI Research Office on port 8501...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$connections = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue; if (-not $connections) { Write-Host 'No running server found on port 8501.'; exit 0 }; $connections | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped process ' + $_) }"
pause
