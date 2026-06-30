@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $shortcutPath=Join-Path $desktop 'AI Research Office.lnk'; $shell=New-Object -ComObject WScript.Shell; $shortcut=$shell.CreateShortcut($shortcutPath); $shortcut.TargetPath=(Join-Path (Get-Location) 'Open AI Research Office.vbs'); $shortcut.WorkingDirectory=(Get-Location).Path; $shortcut.IconLocation='%SystemRoot%\System32\SHELL32.dll,13'; $shortcut.Save(); Write-Host ('Created shortcut: ' + $shortcutPath)"
pause
