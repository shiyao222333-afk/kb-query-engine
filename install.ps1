<#
.SYNOPSIS
    Citrinitas 一键部署脚本
.DESCRIPTION
    检测环境、创建虚拟环境、安装依赖、初始化目录结构。
    双击或 PowerShell 中运行： .\install.ps1
.NOTES
    需要 Windows PowerShell 5.1+
#>

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Citrinitas · 熔知 一键安装              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════
# 第 1 步：检测 Python
# ═══════════════════════════════════════════
Write-Host "[1/6] 检测 Python 环境..." -ForegroundColor Yellow

$PythonExe = $null
$PythonPaths = @(
    "$ProjectDir\venv\Scripts\python.exe",
    "python3",
    "python"
)

foreach ($path in $PythonPaths) {
    try {
        $ver = & $path --version 2>$null
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            $PythonExe = $path
            Write-Host "  ✓ 找到 $ver ($path)" -ForegroundColor Green
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
                Write-Host "  ✗ Python 版本过低（需要 3.11+），请安装 Python 3.11 或更高版本" -ForegroundColor Red
                exit 1
            }
            break
        }
    } catch {}
}

if (-not $PythonExe) {
    Write-Host "  ✗ 未找到 Python。请安装 Python 3.11+：https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# ═══════════════════════════════════════════
# 第 2 步：创建虚拟环境
# ═══════════════════════════════════════════
Write-Host "[2/6] 创建虚拟环境..." -ForegroundColor Yellow

$VenvDir = "$ProjectDir\venv"
if (Test-Path $VenvDir) {
    Write-Host "  ⚠ 虚拟环境已存在，跳过创建" -ForegroundColor DarkYellow
} else {
    & $PythonExe -m venv $VenvDir
    Write-Host "  ✓ 虚拟环境已创建" -ForegroundColor Green
}

$VenvPython = "$VenvDir\Scripts\python.exe"
$VenvPip = "$VenvDir\Scripts\pip.exe"

# ═══════════════════════════════════════════
# 第 3 步：安装依赖（使用精确锁定版本）
# ═══════════════════════════════════════════
Write-Host "[3/6] 安装 Python 依赖包..." -ForegroundColor Yellow
Write-Host "  这可能需要几分钟，请耐心等待..."

$LockFile = "$ProjectDir\requirements.lock"
if (Test-Path $LockFile) {
    & $VenvPip install -r $LockFile --quiet
    Write-Host "  ✓ 依赖安装完成（从 requirements.lock）" -ForegroundColor Green
} else {
    Write-Host "  ⚠ requirements.lock 不存在，改用 requirements.txt" -ForegroundColor DarkYellow
    & $VenvPip install -r "$ProjectDir\requirements.txt" --quiet
    Write-Host "  ✓ 依赖安装完成（从 requirements.txt）" -ForegroundColor Green
}

# ═══════════════════════════════════════════
# 第 4 步：初始化目录结构
# ═══════════════════════════════════════════
Write-Host "[4/6] 初始化目录结构..." -ForegroundColor Yellow

$Dirs = @(
    "$ProjectDir\local_data",
    "$ProjectDir\local_data\dead_letter",
    "$ProjectDir\snapshots",
    "$ProjectDir\storage",
    "$ProjectDir\storage\ocr_cache",
    "$ProjectDir\data",
    "$ProjectDir\data\watch",
    "$ProjectDir\data\watch_staging",
    "$ProjectDir\data\watch_processed",
    "$ProjectDir\data\watch_dead_letter"
)

foreach ($dir in $Dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "  ✓ 目录结构就绪" -ForegroundColor Green

# ═══════════════════════════════════════════
# 第 5 步：配置文件
# ═══════════════════════════════════════════
Write-Host "[5/6] 配置环境变量..." -ForegroundColor Yellow

$EnvFile = "$ProjectDir\.env"
$EnvExample = "$ProjectDir\.env.example"

if (Test-Path $EnvFile) {
    Write-Host "  ⚠ .env 已存在，跳过复制" -ForegroundColor DarkYellow
    Write-Host "  如需重新生成，请删除 .env 后重试" -ForegroundColor DarkYellow
} elseif (Test-Path $EnvExample) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "  ✓ .env 已从模板创建" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║  ⚠ 请编辑 .env 填入你的 API Key！       ║" -ForegroundColor Magenta
    Write-Host "  ║     notepad .env                         ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
} else {
    Write-Host "  ⚠ .env.example 不存在，跳过" -ForegroundColor DarkYellow
}

# ═══════════════════════════════════════════
# 第 6 步：预热 + 验证
# ═══════════════════════════════════════════
Write-Host "[6/6] 验证安装..." -ForegroundColor Yellow
Write-Host ""

$AllPassed = $true

# 关键模块导入测试（P1-5）
$Modules = @(
    @{Name="nicegui";       Desc="Web 框架"},
    @{Name="qdrant_client"; Desc="向量数据库"},
    @{Name="fastapi";       Desc="API 服务器"},
    @{Name="openai";        Desc="LLM 客户端"},
    @{Name="pypdf";         Desc="PDF 解析"},
    @{Name="docx";          Desc="Word 解析"},
    @{Name="watchdog";      Desc="文件监控"},
    @{Name="jieba";         Desc="中文分词"},
    @{Name="PIL";           Desc="图片处理"},
    @{Name="yaml";          Desc="YAML 配置"},
    @{Name="dotenv";        Desc="环境变量"},
    @{Name="requests";      Desc="HTTP 客户端"}
)

foreach ($mod in $Modules) {
    $result = & $VenvPython -c "import $($mod.Name)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $($mod.Desc) ($($mod.Name))" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($mod.Desc) ($($mod.Name)) — 缺失" -ForegroundColor Red
        $AllPassed = $false
    }
}

# PaddleOCR 预热下载模型（P1-1）
Write-Host ""
Write-Host "  预热 PaddleOCR 模型（首次需下载 ~200MB）..." -ForegroundColor Yellow
$ocrResult = & $VenvPython -c @"
import paddleocr, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
try:
    ocr = paddleocr.PaddleOCR(lang='ch', use_angle_cls=False, show_log=False)
    print('  ✓ PaddleOCR 中文模型就绪')
except Exception as e:
    print(f'  ⚠ PaddleOCR 预热失败: {e}')
    print('  首次摄入图片时会自动下载模型')
"@ 2>&1
if ($ocrResult) { Write-Host $ocrResult }

# ═══════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor $(if ($AllPassed) { "Green" } else { "Yellow" })
Write-Host "║  安装完成！                              ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""

if (-not $AllPassed) {
    Write-Host "⚠ 部分模块未能导入，请检查上方 ✗ 标记的项" -ForegroundColor Yellow
    Write-Host "  可能原因：安装过程中网络问题，重新运行此脚本即可" -ForegroundColor Yellow
}

Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  1. 编辑 .env 文件，填入你的 API Key：  notepad .env"
Write-Host "  2. 双击 run.bat 启动知识引擎"
Write-Host ""

pause
