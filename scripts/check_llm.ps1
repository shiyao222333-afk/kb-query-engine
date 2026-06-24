# check_llm.ps1 — LLM API 可用性检查
# 用法: powershell -NoProfile -File check_llm.ps1 -ProjectDir "D:\citrinitas"
param(
    [string]$ProjectDir = ""
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$envFile = Join-Path $ProjectDir ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "  [!] .env not found. LLM API key not configured."
    Write-Host "  AI classification will not work."
    exit 0
}

$key = ""
$url = ""
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^KB_LLM_API_KEY=(.+)$') { $key = $Matches[1] }
    elseif ($_ -match '^KB_LLM_BASE_URL=(.+)$') { $url = $Matches[1] }
}

if (-not $key) {
    Write-Host "  [!] LLM API key not set"
    exit 0
}

Write-Host "  LLM API key configured"

if (-not $url) {
    Write-Host "  [!] KB_LLM_BASE_URL not set, skipping API check"
    exit 0
}

try {
    $testUrl = $url.TrimEnd('/') + '/v1/models'
    $null = Invoke-WebRequest -Uri $testUrl -Method GET `
        -Headers @{Authorization = "Bearer $key" } `
        -TimeoutSec 5 -ErrorAction Stop -UseBasicParsing
    Write-Host "  LLM API reachable"
} catch {
    Write-Host ("  [!] LLM API unreachable: " + $_.Exception.Message)
}
