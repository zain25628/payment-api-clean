# Usage: .\dev_frontend.ps1
# Starts the admin frontend dev server from the project root.

$projectPath = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $projectPath

$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    Write-Host "The 'npm' command was not found. Please install Node.js (which includes npm) and ensure it is on your PATH, then re-open PowerShell/VS Code." -ForegroundColor Red
    exit 1
}

$frontendPath = Join-Path $projectPath "admin-frontend"

if (-not (Test-Path $frontendPath)) {
    Write-Host "Admin frontend folder not found: $frontendPath" -ForegroundColor Red
    exit 1
}

Set-Location $frontendPath

$nodeModules = Join-Path $frontendPath "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    try {
        & $npmCmd.Name install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "npm install failed with exit code $LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    } catch {
        Write-Host "Failed to run 'npm install'. Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Starting admin frontend: npm run dev" -ForegroundColor Cyan
& $npmCmd.Name run dev

# Note: This script intentionally runs `npm run dev` in the foreground so logs appear in this terminal.
