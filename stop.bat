@echo off
REM 停止知识库检索服务

echo 正在停止服务...

REM 停止 PrivateGPT (查找占用8080端口的进程)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080.*LISTENING" 2^>NUL') do (
    taskkill /F /PID %%a >NUL 2>&1
    echo   PrivateGPT 已停止
)

REM 停止 Qdrant
taskkill /F /IM qdrant.exe >NUL 2>&1
echo   Qdrant 已停止

echo 完成。
pause
