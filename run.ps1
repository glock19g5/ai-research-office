$ErrorActionPreference = "Stop"

function Get-PythonCommand {
    $bundledPython = "C:\Users\HP ZBook 14 G8\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundledPython) {
        return $bundledPython
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return "py"
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return "python"
        }
    }

    return $null
}

$python = Get-PythonCommand

if (-not $python) {
    Write-Host "ไม่พบ Python ในเครื่องนี้" -ForegroundColor Red
    Write-Host "ให้ติดตั้ง Python จาก https://www.python.org/downloads/windows/"
    Write-Host "ตอนติดตั้งให้ติ๊ก Add python.exe to PATH แล้วเปิด PowerShell ใหม่"
    exit 1
}

if (-not $env:GEMINI_API_KEY) {
    $env:GEMINI_API_KEY = Read-Host "วาง GEMINI_API_KEY ของคุณ แล้วกด Enter"
}

& $python -m streamlit run app.py
