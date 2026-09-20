$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$logDirectory = Join-Path $projectRoot "logs"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

function Test-Endpoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri
    )

    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Wait-ForEndpoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Uri
    )

    for ($attempt = 1; $attempt -le 40; $attempt++) {
        if (Test-Endpoint -Uri $Uri) {
            return
        }

        Start-Sleep -Milliseconds 250
    }

    throw "$Name did not become available at $Uri. Check the latest files in $logDirectory."
}

$backendHealthUrl = "http://127.0.0.1:8000/health"
$frontendUrl = "http://127.0.0.1:5173/"
$proxyUrl = "http://127.0.0.1:5173/api/v1/complaints"

if (Test-Endpoint -Uri $backendHealthUrl) {
    Write-Output "Backend is already running."
}
else {
    $pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw "Python environment not found at $pythonPath. Complete the README setup first."
    }

    Start-Process `
        -FilePath $pythonPath `
        -ArgumentList @("-m", "uvicorn", "civicai.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDirectory "backend-$runId.out.log") `
        -RedirectStandardError (Join-Path $logDirectory "backend-$runId.err.log") | Out-Null

    Wait-ForEndpoint -Name "Backend" -Uri $backendHealthUrl
    Write-Output "Backend started."
}

if (Test-Endpoint -Uri $frontendUrl) {
    Write-Output "Frontend is already running."
}
else {
    $nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($null -eq $nodeCommand) {
        throw "node.exe was not found. Install Node.js 22.12 or newer, then follow the README setup."
    }

    $vitePath = Join-Path $projectRoot "frontend\node_modules\vite\bin\vite.js"
    if (-not (Test-Path -LiteralPath $vitePath -PathType Leaf)) {
        throw "Frontend dependencies are missing. Run npm install inside the frontend directory first."
    }

    Start-Process `
        -FilePath $nodeCommand.Source `
        -ArgumentList @($vitePath, "--host", "127.0.0.1", "--port", "5173", "--strictPort") `
        -WorkingDirectory (Join-Path $projectRoot "frontend") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDirectory "frontend-$runId.out.log") `
        -RedirectStandardError (Join-Path $logDirectory "frontend-$runId.err.log") | Out-Null

    Wait-ForEndpoint -Name "Frontend" -Uri $frontendUrl
    Write-Output "Frontend started."
}

$proxyResponse = Invoke-WebRequest -Uri $proxyUrl -UseBasicParsing -TimeoutSec 5
$proxyContentType = [string]$proxyResponse.Headers["Content-Type"]

if ($proxyResponse.StatusCode -ne 200 -or -not $proxyContentType.StartsWith("application/json")) {
    throw "The frontend is reachable, but its API proxy is not healthy. Check the latest files in $logDirectory."
}

Write-Output "CivicAI is ready: $frontendUrl"
Write-Output "API health: $backendHealthUrl"
Write-Output "API proxy verified: $proxyUrl"
