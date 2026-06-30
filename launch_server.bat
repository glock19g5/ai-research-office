@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\HP ZBook 14 G8\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if exist "%PYTHON_EXE%" goto run

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_EXE=py"
  goto run
)

where python >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_EXE=python"
  goto run
)

echo ไม่พบ Python สำหรับรันแอป
echo กรุณาติดตั้ง Python หรือเปิดผ่าน Codex runtime
pause
exit /b 1

:run
"%PYTHON_EXE%" -m streamlit run app.py --server.port 8501 --server.address localhost
