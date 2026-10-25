Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    # Invoke the Windows command shim; npm.ps1 is incompatible with strict mode
    # in some Node.js/PowerShell versions ($MyInvocation.Statement is absent).
    foreach ($tool in @("git", "uv", "node", "npm.cmd")) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "Install $tool using docs/08-windows-setup.md, then open a new PowerShell terminal."
        }
    }
    & "$PSScriptRoot/Set-GitIdentity.ps1"
    uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw "Python installation failed" }
    uv sync --project backend --frozen
    if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed" }
    if (-not (Test-Path .env)) {
        uv run --project backend python scripts/configure_local.py
        if ($LASTEXITCODE -ne 0) { throw "Local configuration failed" }
    } else { Write-Host "Existing .env preserved." }
    Push-Location frontend
    try {
        npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed" }
    } finally { Pop-Location }
    Write-Host "Dependencies prepared. Follow the native PostgreSQL step in docs/08-windows-setup.md."
} finally { Pop-Location }
