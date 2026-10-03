$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentFile = Join-Path $projectRoot ".env.production"
if (-not (Test-Path -LiteralPath $environmentFile -PathType Leaf)) {
    throw "Create .env.production from .env.production.example and replace every placeholder first."
}
if (Select-String -LiteralPath $environmentFile -Pattern "REPLACE_WITH|example\.org" -Quiet) {
    throw ".env.production still contains placeholder values. Production startup refused."
}

Push-Location $projectRoot
try {
    docker compose --env-file .env.production -f compose.production.yml up --build --detach --wait
    if ($LASTEXITCODE -ne 0) { throw "Production-like stack did not become healthy." }
    docker compose --env-file .env.production -f compose.production.yml ps
    Write-Output "CivicAI production-like services are healthy. Open the CIVICAI_SITE_ADDRESS configured in .env.production."
}
finally { Pop-Location }
