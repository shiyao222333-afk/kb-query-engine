"""
Citrinitas 一键启动器（仅开发用）
⚠️ 生产环境请使用 run.bat（自动管理 Qdrant 启停 + Ollama 健康检查 + 模型预热）
用法: python run.py
功能:
  1. 自动杀掉占用 8080 端口的旧 Python 进程
  2. 启动 NiceGUI Web 服务
  3. 浏览器关闭 → 进程自动退出（约 10 秒后）
"""

import subprocess
import sys
import time
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(SCRIPT_DIR, "main.py")
PYTHON = sys.executable or "python"
PORT = 8080


def kill_existing():
    """杀掉占用目标端口的旧进程。"""
    print(f"[run.py] 检查端口 {PORT}...")
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                f"$pids = (netstat -ano | Select-String ':{PORT}' "
                "| Select-String 'LISTENING' "
                "| ForEach-Object { ($_ -split '\\\\s+')[-1] } "
                "| Sort-Object -Unique); "
                "foreach ($p in $pids) { "
                "  try { $proc = Get-Process -Id $p -ErrorAction Stop; "
                "    if ($proc.ProcessName -like '*python*') { "
                "      Stop-Process -Id $p -Force; "
                "      Write-Output \"Killed PID:$p\" "
                "    } "
                "  } catch {} "
                "}",
            ],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                print(f"[run.py] {line.strip()}")
        time.sleep(1.5)
        print(f"[run.py] 端口清理完成")
    except Exception as e:
        print(f"[run.py] 端口清理失败: {e}")


def clear_cache():
    """清除 __pycache__。"""
    for root, dirs, _files in os.walk(SCRIPT_DIR):
        if "__pycache__" in dirs:
            path = os.path.join(root, "__pycache__")
            shutil.rmtree(path, ignore_errors=True)
            dirs.remove("__pycache__")


if __name__ == "__main__":
    print("=" * 50)
    print("  Citrinitas · 熔知")
    print("  NiceGUI v3.13.0")
    print("=" * 50)

    # 1. 清理
    kill_existing()
    clear_cache()

    # 2. 确保依赖
    print(f"[run.py] 启动中...")
    print(f"[run.py] 打开浏览器访问: http://127.0.0.1:{PORT}")
    print(f"[run.py] 关闭浏览器后，进程将自动退出")
    print("=" * 50)

    # 3. 启动
    os.chdir(SCRIPT_DIR)
    subprocess.run([PYTHON, MAIN_PY])
