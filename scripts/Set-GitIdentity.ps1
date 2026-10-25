Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    git config --local user.name "hanesh-g"
    if ($LASTEXITCODE -ne 0) { throw "Could not set author name" }
    git config --local user.email "haneshgourishetti@gmail.com"
    if ($LASTEXITCODE -ne 0) { throw "Could not set author email" }
    git config --local user.useConfigOnly true
    if ($LASTEXITCODE -ne 0) { throw "Could not enforce configured identity" }
    Write-Host "Repository commit identity set to hanesh-g <haneshgourishetti@gmail.com>."
} finally { Pop-Location }
