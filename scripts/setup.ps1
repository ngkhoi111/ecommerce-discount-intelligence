$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required. Install Python 3.11 and retry.' }
}
$dependencyFile = 'requirements.txt'
if (Test-Path -LiteralPath 'requirements-lock.txt') { $dependencyFile = 'requirements-lock.txt' }
& ./.venv/Scripts/python.exe -m pip install -r $dependencyFile
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& ./.venv/Scripts/python.exe -m ipykernel install --sys-prefix --name discount-intelligence --display-name 'Discount Intelligence (.venv)'
if ($LASTEXITCODE -ne 0) { throw 'Notebook kernel setup failed.' }
Write-Host 'Python environment ready. Follow the learning steps in the chat.'

