# Backup script for the project folder
# Creates a zip on Desktop\project_backups excluding venv, node_modules, .git, large binaries, etc.

# 1) Determine project path (the directory where this script lives)
$projectPath = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent

# 2) Backup root on Desktop
$backupRoot = Join-Path $env:USERPROFILE "Desktop\project_backups"
if (-not (Test-Path -Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
}

# 3) Project name and timestamped zip filename
$projectName = Split-Path -Path $projectPath -Leaf
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipName = "${projectName}_${timestamp}.zip"
$zipPath = Join-Path $backupRoot $zipName

# 4) Exclusions (folder/file names, case-insensitive)
$excludes = @('.venv','venv','env','__pycache__','.mypy_cache','.pytest_cache','node_modules','.git','.idea','.vscode')

Write-Host "Creating backup for project: $projectName"
Write-Host "Project path: $projectPath"
Write-Host "Backup destination: $zipPath"

# Helper: decide whether to include item based on path segments and extension
function Should-IncludeItem($fullPath, $rootPath, $excludes) {
    # Skip if path is null or empty
    if ([string]::IsNullOrEmpty($fullPath)) { return $false }

    # Normalize separators
    $rel = $fullPath.Substring($rootPath.Length).TrimStart('\','/')
    if ($rel -eq '') { return $true } # root itself

    # Split into segments and check exclusions (case-insensitive)
    $segments = $rel -split '[\\/]'
    foreach ($seg in $segments) {
        foreach ($ex in $excludes) {
            if ($seg -ieq $ex) { return $false }
        }
    }

    # Skip executables
    try {
        $ext = [IO.Path]::GetExtension($fullPath)
        if ($ext -and $ext -ieq '.exe') { return $false }
    } catch { }

    return $true
}

# 4a) Collect items to include (files and directories)
$items = Get-ChildItem -Path $projectPath -Force -Recurse -ErrorAction SilentlyContinue
$pathsToInclude = New-Object System.Collections.Generic.List[string]

# Include the top-level project folder contents (but apply exclusions)
foreach ($it in $items) {
    $full = $it.FullName
    if (Should-IncludeItem $full $projectPath $excludes) {
        # Add both files and directories; Compress-Archive accepts both
        $pathsToInclude.Add($full) | Out-Null
    }
}

# Also include top-level files that Get-ChildItem may have returned earlier; ensure unique
$pathsToInclude = $pathsToInclude | Select-Object -Unique

if ($pathsToInclude.Count -eq 0) {
    Write-Host "No items to include in archive. Aborting." -ForegroundColor Yellow
    exit 1
}

# 4b) Create the zip (without modifying source files)
# Compress-Archive can accept multiple -LiteralPath entries as an array
Try {
    Compress-Archive -LiteralPath $pathsToInclude -DestinationPath $zipPath -CompressionLevel Optimal -Force
} Catch {
    Write-Host "Compress-Archive failed: $_" -ForegroundColor Red
    exit 1
}

# 5) Do not delete or change files — script only reads files

# 6) Print success and path
Write-Host "Backup created successfully:" -ForegroundColor Green
Write-Host $zipPath -ForegroundColor Cyan

exit 0
