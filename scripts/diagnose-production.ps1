$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $compose = @("compose", "--env-file", ".env.production", "-f", "compose.production.yml")
    & docker @compose ps
    & docker @compose exec -T backend python -m civicai.media_audit
    & docker @compose exec -T db psql --username civicai --dbname civicai --tuples-only --command "SELECT version_num FROM alembic_version;"
    & docker @compose logs --tail 50 backend proxy db
}
finally {
    Pop-Location
}
