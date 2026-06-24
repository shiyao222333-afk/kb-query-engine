# qdrant_helper.ps1 — Qdrant 自动检测 + 自动安装
# 被 run.bat Step 5 调用
# 输出：QDRANT_PATH 环境变量

param(
    [string]$Action = "detect",   # detect | install
    [string]$ProjectDir = ""
)

$ErrorActionPreference = "Stop"

# ─────────────────────────────────────────────
# 1. 检测 Qdrant
# ─────────────────────────────────────────────
if ($Action -eq "detect") {
    $candidates = @()

    # 1a. PATH 中查找
    try {
        $inPath = (Get-Command qdrant -ErrorAction Stop).Source
        if ($inPath) { $candidates += $inPath }
    } catch {}

    # 1b. 项目本地目录
    $localPath = Join-Path $ProjectDir "qdrant\qdrant.exe"
    if (Test-Path $localPath) { $candidates += $localPath }

    # 1c. 常见安装路径
    $commonPaths = @(
        "D:\qdrant\qdrant.exe",
        "C:\Program Files\qdrant\qdrant.exe",
        "C:\qdrant\qdrant.exe",
        "$env:LOCALAPPDATA\qdrant\qdrant.exe",
        "$env:APPDATA\qdrant\qdrant.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) { $candidates += $p }
    }

    # 1d. 输出第一个找到的路径
    if ($candidates.Count -gt 0) {
        # 验证文件确实可运行（--version 测试，路径含空格时用引号包裹）
        $test = & "$($candidates[0])" --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Output $candidates[0]
            exit 0
        }
    }

    # 未找到
    Write-Output ""
    exit 1
}

# ─────────────────────────────────────────────
# 2. 安装 Qdrant（下载独立二进制文件）
# ─────────────────────────────────────────────
if ($Action -eq "install") {
    $installDir = Join-Path $ProjectDir "qdrant"
    $exePath    = Join-Path $installDir "qdrant.exe"
    $cfgDir     = Join-Path $installDir "config"
    $cfgPath    = Join-Path $cfgDir "config.yaml"

    # 创建目录
    if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
    if (-not (Test-Path $cfgDir))     { New-Item -ItemType Directory -Path $cfgDir -Force | Out-Null }

    # 获取最新版本号
    Write-Host "  Fetching latest Qdrant version..."
    try {
        $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/qdrant/qdrant/releases/latest" -TimeoutSec 10
        $version = $releaseInfo.tag_name
    } catch {
        $version = "v1.13.4"   # 兜底版本
        Write-Host "  [!] GitHub API unreachable, using fallback version $version"
    }
    $versionNoV = $version -replace "^v", ""
    Write-Host "  Version: $versionNoV"

    # 下载 URL
    $arch = "x86_64-pc-windows-msvc"
    $url  = "https://github.com/qdrant/qdrant/releases/download/$version/qdrant-$arch.exe"
    Write-Host "  Downloading: $url"

    # 下载（显示进度）
    $progressPref = $ProgressPreference
    $ProgressPreference = "Continue"
    try {
        Invoke-WebRequest -Uri $url -OutFile $exePath -TimeoutSec 300
    } catch {
        # 备用：用 curl.exe
        Write-Host "  [!] Invoke-WebRequest failed, trying curl..."
        curl.exe -L -o $exePath $url
    }
    $ProgressPreference = $progressPref

    if (-not (Test-Path $exePath)) {
        Write-Host "  [ERROR] Download failed. Please install Qdrant manually."
        Write-Host "  Visit: https://github.com/qdrant/qdrant/releases"
        exit 1
    }
    Write-Host "  Downloaded to: $exePath"

    # 生成默认配置文件
    $defaultConfig = @"
# Qdrant 默认配置（由 run.bat 自动生成）
storage:
  storage_path: "$($installDir.Replace('\', '\\'))\\storage"
  on_disk_payload: true
  wal:
    wal_capacity_mb: 32
    max_segment_size_kb: 200

service:
  http_port: 6333
  grpc_port: 6334
  enable_cors: true
  host: 127.0.0.1

log_level: INFO
"@
    Set-Content -Path $cfgPath -Value $defaultConfig -Encoding UTF8
    Write-Host "  Config written to: $cfgPath"

    # 验证安装
    $test = & $exePath --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Qdrant $versionNoV installed successfully."
        Write-Output $exePath
        exit 0
    } else {
        Write-Host "  [ERROR] Installed binary failed version check."
        exit 1
    }
}

Write-Host "  [ERROR] Unknown action: $Action"
exit 1
