$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
$previousHash = $env:CIVICAI_DEMO_MODEL_SHA256
try {
    $siteLine = Get-Content -LiteralPath ".env.production" | Where-Object { $_ -match '^CIVICAI_SITE_ADDRESS=' } | Select-Object -Last 1
    if (($siteLine -replace '^CIVICAI_SITE_ADDRESS=', '').Trim() -ne 'localhost') { throw 'This demo script is restricted to CIVICAI_SITE_ADDRESS=localhost.' }
    $modelPath = Join-Path $projectRoot "research/results/exploratory-ai-labels-v1/experimental-model.joblib"
    if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf)) { throw 'Trusted local experiment model is missing.' }
    $indexPath = Join-Path $projectRoot "research/results/exploratory-ai-labels-v1/artifacts.json"
    $index = Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
    $hash = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $index.'experimental-model.joblib') { throw 'Model differs from experiment artifact index.' }
    & docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is unavailable.' }
    & (Join-Path $PSScriptRoot 'backup-production.ps1')
    $env:CIVICAI_DEMO_MODEL_SHA256 = $hash
    $compose = @('compose', '--env-file', '.env.production', '-f', 'compose.production.yml', '-f', 'compose.demo.yml', '-f', 'compose.production.mailpit.yml')
    & docker @compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Compose validation failed.' }
    & docker @compose up -d --build --wait
    if ($LASTEXITCODE -ne 0) { throw 'Demo startup failed. Inspect Docker logs; do not remove database volumes.' }
    & docker @compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=5).status)"
    if ($LASTEXITCODE -ne 0) { throw 'Backend readiness check failed.' }
    Write-Output 'Local experimental demo ready at https://localhost/municipal. Sign in and open a complaint.'
    Write-Output 'Local demo mail inbox: http://127.0.0.1:8025 (messages are captured locally, not delivered externally).'
} finally {
    $env:CIVICAI_DEMO_MODEL_SHA256 = $previousHash
    Pop-Location
}
