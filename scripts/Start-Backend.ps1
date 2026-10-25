Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location (Join-Path (Split-Path $PSScriptRoot -Parent) "backend")
try {
    uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
    if ($LASTEXITCODE -ne 0) { throw "Backend exited with an error" }
} finally { Pop-Location }
