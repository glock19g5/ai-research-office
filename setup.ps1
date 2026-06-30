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

Write-Host "ใช้ Python command: $python" -ForegroundColor Green
Write-Host "กำลังอัปเกรด pip..." -ForegroundColor Cyan
& $python -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw "ensurepip failed" }
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }

Write-Host "กำลังติดตั้ง dependencies จาก requirements.txt..." -ForegroundColor Cyan
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "dependency install failed" }

Write-Host "ติดตั้งเสร็จแล้วครับ ต่อไปให้รัน .\run.ps1" -ForegroundColor Green
