# test_detect.ps1 - 测试 Qdrant 检测
# 手动运行：在 PowerShell 里执行 .\test_detect.ps1

$scriptPath = "D:\citrinitas\scripts\qdrant_helper.ps1"
$projectDir = "D:\citrinitas"

Write-Host "=== 测试 Get-EnvQdrantPath 函数 ==="
& $scriptPath -Action detect -ProjectDir $projectDir

# 读取结果文件
$tmpFile = Join-Path $env:TEMP "qdrant_detect_result.txt"
if (Test-Path $tmpFile) {
    $result = Get-Content $tmpFile -Raw
    Write-Host "检测结果: [$result]"
    if ($result -and $result -ne "") {
        Write-Host "✅ 成功检测到 Qdrant: $result"
    } else {
        Write-Host "❌ 未检测到 Qdrant"
    }
} else {
    Write-Host "❌ 结果文件未生成"
}
