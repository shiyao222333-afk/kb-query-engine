@echo off
REM ============================================
REM WorkBuddy 知识库检索服务
REM 架构: Qdrant(向量库) + Ollama(嵌入) + kb_query.py(检索) + WorkBuddy(理解+生成)
REM ============================================

echo ============================================
echo   知识库检索服务启动中...
echo ============================================

REM --- 1. 启动 Qdrant 独立服务器 ---
echo [1/2] 启动 Qdrant 向量数据库...
tasklist /FI "IMAGENAME eq qdrant.exe" 2>NUL | find /I "qdrant.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    start "Qdrant" /MIN D:\qdrant\qdrant.exe --config-path D:/qdrant/config/config.yaml
    echo   Qdrant 已启动 (端口 6333)
    timeout /t 3 /nobreak >nul
) else (
    echo   Qdrant 已在运行
)

REM --- 2. 确认 Ollama 运行 ---
echo [2/2] 确认 Ollama 嵌入服务...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo   [!] Ollama 未运行，请手动启动 Ollama
) else (
    echo   Ollama 已在运行 (端口 11434)
)

echo.
echo ============================================
echo   服务已就绪!
echo   Qdrant:  http://localhost:6333
echo   Ollama:  http://localhost:11434
echo.
echo   使用 kb_query.py 进行检索:
echo     python kb_query.py "你的问题"
echo     python kb_query.py --ingest 文档路径
echo ============================================
pause
