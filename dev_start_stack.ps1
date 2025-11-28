# dev_start_stack.ps1
# Starts backend (uvicorn) and frontend (npm run dev) in separate processes.
# Usage: pwsh -File .\dev_start_stack.ps1

# 1) Determine project path (directory where this script lives) and cd there
$projectPath = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $projectPath

# 2) Try to activate the virtualenv if it exists
$venvPath = Join-Path $projectPath ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Found virtualenv at: $($venvPath)" -ForegroundColor Green
    try {
        & $venvPath
        Write-Host "Virtual environment activated." -ForegroundColor Green
    } catch {
        Write-Host "Failed to activate virtual environment: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "No .venv folder found at project root. Skipping venv activation." -ForegroundColor Yellow
}

# 3) Start the backend in a separate process (runs API on port 8000)
# This will start: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
$backendCmd = 'python'
$backendArgs = '-m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'
Write-Host "Starting backend: $backendCmd $backendArgs" -ForegroundColor Cyan
try {
    Start-Process -FilePath $backendCmd -ArgumentList $backendArgs -WorkingDirectory $projectPath
    Write-Host "Backend started (expected at http://localhost:8000)." -ForegroundColor Green
} catch {
    Write-Host "Failed to start backend process: $_" -ForegroundColor Red
}

# 4) Discover frontend folder (look for package.json in common candidate folders or scan subfolders)
$candidates = @('admin-frontend','frontend','admin','dashboard')
$frontendPath = $null
foreach ($c in $candidates) {
    $p = Join-Path $projectPath $c
    if (Test-Path (Join-Path $p 'package.json')) {
        $frontendPath = $p
        break
    }
}

if (-not $frontendPath) {
    # fallback: scan immediate subdirectories for package.json
    $dirs = Get-ChildItem -Path $projectPath -Directory -Force -ErrorAction SilentlyContinue
    foreach ($d in $dirs) {
        if (Test-Path (Join-Path $d.FullName 'package.json')) {
            $frontendPath = $d.FullName
            break
        }
    }
}

if (-not $frontendPath) {
    Write-Host "Could not locate a frontend folder with package.json. Please run npm manually in your frontend folder." -ForegroundColor Yellow
    Write-Host "Searched candidates: $($candidates -join ', ')" -ForegroundColor Yellow
    # Print brief summary and exit (backend may still be running)
    Write-Host "Summary of started services:" -ForegroundColor Cyan
    Write-Host "- Backend: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 (started or attempted)" -ForegroundColor Cyan
    exit 0
}

# 4b) Change to frontend folder
Set-Location $frontendPath
Write-Host "Frontend folder detected: $frontendPath" -ForegroundColor Green

# 5) Start frontend dev server in separate process
# Using npm run dev from the frontend folder
$npmCmd = 'npm'
$npmArgs = 'run dev'
Write-Host "Starting frontend: $npmCmd $npmArgs (from $frontendPath)" -ForegroundColor Cyan
try {
    Start-Process -FilePath $npmCmd -ArgumentList $npmArgs -WorkingDirectory $frontendPath
    Write-Host "Frontend started (typical URL: http://localhost:5173). Check terminal output for exact URL." -ForegroundColor Green
} catch {
    Write-Host "Failed to start frontend process with 'npm'. Ensure Node.js and npm are installed and on PATH." -ForegroundColor Red
}

# 6) Comments (this script does not modify project files; it only starts processes)
# - venv activation is attempted in the current session
# - backend and frontend are started in separate processes

# 7) Print summary of commands and expected URLs
Write-Host "\nSummary:" -ForegroundColor Magenta
Write-Host "- Backend command: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Magenta
Write-Host "  Expected URL: http://localhost:8000" -ForegroundColor Magenta
Write-Host "- Frontend command: npm run dev (started in $frontendPath)" -ForegroundColor Magenta
Write-Host "  Typical Vite URL: http://localhost:5173 (check frontend terminal output)" -ForegroundColor Magenta

# Return to project root
Set-Location $projectPath

Write-Host "Dev stack startup script finished (processes started where possible)." -ForegroundColor Green

exit 0
