param(
    [string]$OutputRoot = "backups"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentFile = Join-Path $projectRoot ".env.production"
if (-not (Test-Path -LiteralPath $environmentFile -PathType Leaf)) {
    throw "Missing .env.production. Backup refused because the target stack is not explicit."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$resolvedRoot = if ([IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot } else { Join-Path $projectRoot $OutputRoot }
$backupDirectory = Join-Path $resolvedRoot $timestamp
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null

Push-Location $projectRoot
try {
    $compose = @("compose", "--env-file", ".env.production", "-f", "compose.production.yml")
    & docker @compose exec -T db pg_dump --username civicai --dbname civicai --format=custom --file=/tmp/civicai.dump
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }
    & docker @compose cp db:/tmp/civicai.dump (Join-Path $backupDirectory "database.dump")
    if ($LASTEXITCODE -ne 0) { throw "Could not copy the database archive from the database container." }
    & docker @compose exec -T db rm -f /tmp/civicai.dump
    if ($LASTEXITCODE -ne 0) { throw "Could not remove the temporary database archive." }

    $backupMount = ($backupDirectory -replace "\\", "/")
    & docker run --rm --mount "type=volume,src=civicai_evidence_data,dst=/evidence,readonly" --mount "type=bind,src=$backupMount,dst=/backup" alpine:3.23 tar -C /evidence -czf /backup/evidence.tar.gz .
    if ($LASTEXITCODE -ne 0) { throw "Evidence backup failed." }

    $manifest = Get-ChildItem -LiteralPath $backupDirectory -File | Sort-Object Name | ForEach-Object {
        $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
        "{0}  {1}" -f $hash.Hash.ToLowerInvariant(), $_.Name
    }
    Set-Content -LiteralPath (Join-Path $backupDirectory "SHA256SUMS.txt") -Value $manifest -Encoding utf8
    Write-Output "Backup completed: $backupDirectory"
}
finally {
    Pop-Location
}
