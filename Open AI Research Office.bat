@echo off
cd /d "%~dp0"
start "AI Research Office Server" "%~dp0launch_server.bat"
timeout /t 3 /nobreak >nul
start "" "http://localhost:8501"
