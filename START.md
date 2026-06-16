# 🚀 启动 Athanor

快速启动 Web UI 界面。（v0.4.1 NiceGUI SPA）

## 📋 前置要求

1. **Python 3.13+** 已安装
2. **Qdrant** 向量数据库已安装并运行（端口 6333）
3. **Ollama** 嵌入服务已安装并运行（端口 11434）

## 🪟 Windows 用户

### 方法一：一键启动（推荐）

```bash
.\run.bat
```

脚本会自动：
1. 检查并杀死旧进程
2. 清理 Python 缓存
3. 启动 NiceGUI SPA

### 方法二：手动启动

```bash
python run.py
```

## 🍎 macOS / 🐧 Linux 用户

```bash
python run.py
```

## 🌐 访问地址

启动成功后，访问：
- **本地地址**: http://localhost:8080
- **网络地址**: http://你的IP地址:8080

## ⚠️ 常见问题

### 1. 端口 8080 被占用

**Windows**:
```bash
netstat -ano | find ":8080"
taskkill /PID <进程ID> /F
```

**macOS/Linux**:
```bash
lsof -i :8080
kill -9 <进程ID>
```

### 2. 浏览器没有自动打开

手动打开浏览器，访问 http://localhost:8080

### 3. 提示"Qdrant 未找到"

请参考 [README.md](README.md) 中的"快速开始"部分，安装并启动 Qdrant。

### 4. 依赖安装失败

```bash
pip install nicegui requests qdrant-client -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 🆘 需要帮助？

- 检查 [README.md](README.md)
- 在 GitHub 提交 Issue

---

**祝使用愉快！** 🎉
