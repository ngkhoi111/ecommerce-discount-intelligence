$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    throw 'Run scripts/setup.ps1 first.'
}
& ./.venv/Scripts/python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Boundary or evaluation tests failed.' }
& ./.venv/Scripts/python.exe scripts/run_pipeline.py --stage all
if ($LASTEXITCODE -ne 0) { throw 'Pipeline failed; see output above.' }
Write-Host 'Complete. Open reports/dashboard.html in your browser.'
