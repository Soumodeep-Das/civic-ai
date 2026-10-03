param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,
    [string]$RestoreName = ("civicai_restore_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
)

$ErrorActionPreference = "Stop"
if ($RestoreName -notmatch '^civicai_restore_[A-Za-z0-9_]+$') {
    throw "RestoreName must begin with civicai_restore_ and contain only letters, digits and underscores."
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentFile = Join-Path $projectRoot ".env.production"
$resolvedBackup = (Resolve-Path -LiteralPath $BackupDirectory).Path
$databaseArchive = Join-Path $resolvedBackup "database.dump"
$evidenceArchive = Join-Path $resolvedBackup "evidence.tar.gz"
if (-not (Test-Path -LiteralPath $environmentFile -PathType Leaf)) { throw "Missing .env.production." }
if (-not (Test-Path -LiteralPath $databaseArchive -PathType Leaf)) { throw "Missing database.dump." }
if (-not (Test-Path -LiteralPath $evidenceArchive -PathType Leaf)) { throw "Missing evidence.tar.gz." }
$passwordLine = Get-Content -LiteralPath $environmentFile | Where-Object { $_ -match '^POSTGRES_PASSWORD=' } | Select-Object -First 1
if (-not $passwordLine) { throw "POSTGRES_PASSWORD is missing from .env.production." }
$postgresPassword = $passwordLine.Substring("POSTGRES_PASSWORD=".Length)
if (-not $postgresPassword) { throw "POSTGRES_PASSWORD is empty." }

$mediaVolume = "civicai_${RestoreName}_evidence"
Push-Location $projectRoot
try {
    $compose = @("compose", "--env-file", ".env.production", "-f", "compose.production.yml")
    & docker @compose exec -T db createdb --username civicai --template template0 $RestoreName
    if ($LASTEXITCODE -ne 0) { throw "Could not create disposable restore database $RestoreName." }
    & docker @compose cp $databaseArchive "db:/tmp/$RestoreName.dump"
    if ($LASTEXITCODE -ne 0) { throw "Could not copy the backup archive into the database container." }
    & docker @compose exec -T db pg_restore --username civicai --dbname $RestoreName --exit-on-error "/tmp/$RestoreName.dump"
    if ($LASTEXITCODE -ne 0) { throw "Database restore failed. The production database was not targeted." }

    & docker volume create $mediaVolume | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not create disposable evidence volume." }
    $backupMount = ($resolvedBackup -replace "\\", "/")
    & docker run --rm --mount "type=volume,src=$mediaVolume,dst=/restore-media" --mount "type=bind,src=$backupMount,dst=/backup,readonly" alpine:3.23 tar -C /restore-media -xzf /backup/evidence.tar.gz
    if ($LASTEXITCODE -ne 0) { throw "Evidence restore failed." }

    & docker @compose run --rm --no-deps -e APP_ENV=test -e "DATABASE_URL=postgresql+psycopg://civicai:${postgresPassword}@db:5432/$RestoreName" -e UPLOAD_DIR=/restore-media -v "${mediaVolume}:/restore-media:ro" backend python -m civicai.media_audit
    if ($LASTEXITCODE -ne 0) { throw "Restored database/evidence consistency audit failed." }
    Write-Output "Restore verified in disposable database '$RestoreName' and volume '$mediaVolume'."
    Write-Output "Inspect them if needed, then follow docs/BACKUP_RESTORE.md to remove only these disposable targets."
}
finally {
    Pop-Location
}
