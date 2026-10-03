$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    docker compose --env-file .env.production -f compose.production.yml down
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose shutdown failed." }
    Write-Output "CivicAI services stopped. Persistent database, evidence and certificate volumes were retained."
}
finally { Pop-Location }
