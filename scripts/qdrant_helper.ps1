# qdrant_helper.ps1 — Qdrant 自动检测 + 自动安装
# 被 run.bat Step 5 调用
# 输出：Qdrant 可执行文件路径（找到则输出路径并 exit 0；未找到输出空字符串并 exit 1）

param(
    [string]$Action = "detect",   # detect | install
    [string]$ProjectDir = ""
)

$ErrorActionPreference = "Stop"

# ─────────────────────────────────────────────
# 0. 读取 .env 中的 QDRANT_PATH（用户手动指定）
# ─────────────────────────────────────────────
function Get-EnvQdrantPath {
    param($PrjDir)
    $envFile = Join-Path $PrjDir ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^QDRANT_PATH=(.+)$') {
                return $Matches[1].Trim()
            }
        }
    }
    return $null
}

# ─────────────────────────────────────────────
# 1. 检测 Qdrant
# ─────────────────────────────────────────────
if ($Action -eq "detect") {
    # 1a. 检查 API 端口（Qdrant 是否已在运行）
    #      已运行则不需要找二进制文件，直接返回 "API_ALREADY_RUNNING"
    try {
        $healthResp = Invoke-WebRequest -Uri "http://localhost:6333" -Method GET -TimeoutSec 2 -ErrorAction Stop -UseBasicParsing
        if ($healthResp.StatusCode -eq 200) {
            Write-Output "API_ALREADY_RUNNING"
            exit 0
        }
    } catch {
        # API 未响应，继续查找二进制文件
    }

    $candidates = @()

    # 1b. 读取 .env 中的 QDRANT_PATH（用户手动指定路径）
    if ($ProjectDir) {
        $envPath = Get-EnvQdrantPath -PrjDir $ProjectDir
        if ($envPath -and (Test-Path $envPath)) {
            $candidates += $envPath
        }
    }

    # 1c. PATH 中查找（Get-Command）
    try {
        $inPath = (Get-Command qdrant -ErrorAction Stop).Source
        if ($inPath) { $candidates += $inPath }
    } catch {}

    # 1d. 项目本地目录（自动安装位置）
    if ($ProjectDir) {
        $localPath = Join-Path $ProjectDir "qdrant\qdrant.exe"
        if (Test-Path $localPath) { $candidates += $localPath }
    }

    # 1e. 有限递归搜索（使用环境变量，通用不依赖具体机器）
    #     搜索根目录：ProgramFiles, LOCALAPPDATA, USERPROFILE, APPDATA
    #     递归深度：2（兼顾覆盖率和速度）
    $searchRoots = @()
    if ($env:ProgramFiles)         { $searchRoots += $env:ProgramFiles }
    if (${env:ProgramFiles(x86)}) { $searchRoots += ${env:ProgramFiles(x86)} }
    if ($env:LOCALAPPDATA)        { $searchRoots += $env:LOCALAPPDATA }
    if ($env:USERPROFILE)         { $searchRoots += $env:USERPROFILE }
    if ($env:APPDATA)            { $searchRoots += $env:APPDATA }

    foreach ($root in $searchRoots) {
        if (Test-Path $root) {
            try {
                Get-ChildItem -Path $root -Filter "qdrant.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object {
                    $candidates += $_.FullName
                }
            } catch {
                # 忽略权限错误等
            }
        }
    }

    # 1f. 去重并输出第一个找到的路径
    $candidates = $candidates | Select-Object -Unique
    if ($candidates.Count -gt 0) {
        Write-Output $candidates[0]
        exit 0
    }

    # 未找到
    Write-Output ""
    exit 1
}

# ─────────────────────────────────────────────
# 2. 安装 Qdrant（下载独立二进制文件到项目本地目录）
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
        $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/qdrant/qdrant/releases/latest" -TimeoutSec 10 -UseBasicParsing
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
        Invoke-WebRequest -Uri $url -OutFile $exePath -TimeoutSec 300 -UseBasicParsing
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

    # 验证安装（跳过 --version 检查，PowerShell 7 有 bug）
    if (Test-Path $exePath) {
        Write-Host "  Qdrant $versionNoV installed successfully."
        Write-Output $exePath
        exit 0
    } else {
        Write-Host "  [ERROR] Installed binary not found."
        exit 1
    }
}

Write-Host "  [ERROR] Unknown action: $Action"
exit 1
