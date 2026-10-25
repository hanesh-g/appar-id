Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location (Join-Path (Split-Path $PSScriptRoot -Parent) "frontend")
try {
    # Avoid npm.ps1 inheriting strict mode from this helper.
    npm.cmd run dev
    if ($LASTEXITCODE -ne 0) { throw "Frontend exited with an error" }
} finally { Pop-Location }
