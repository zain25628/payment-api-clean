# run_tests.ps1
# Helper script to activate .venv and run pytest, returning pytest's exit code.

$projectPath = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $projectPath

if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment '.venv' not found in project root: $projectPath" -ForegroundColor Red
    Write-Host "Please create or point to your virtual environment before running tests." -ForegroundColor Red
    exit 1
}

Write-Host "Activating virtual environment '.venv'..." -ForegroundColor Yellow
try {
    & ".\.venv\Scripts\Activate.ps1"
} catch {
    Write-Host "Failed to activate virtual environment (.venv). Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Running pytest -q..." -ForegroundColor Cyan
python -m pytest -q
$exit = $LASTEXITCODE

if ($exit -eq 0) {
    Write-Host "All tests passed ✅" -ForegroundColor Green
} else {
    Write-Host "Some tests failed ❌ - check output above." -ForegroundColor Red
}

exit $exit
