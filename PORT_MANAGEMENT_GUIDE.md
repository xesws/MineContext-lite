# 🔌 端口管理完全指南

解决端口冲突问题的完整解决方案

---

## 📋 问题说明

当你运行 MineContext-v2 时，默认使用 **8000 端口**，可能与其他服务冲突：
- 其他开发服务器（Django, Flask, etc.）
- 数据库管理工具
- 其他正在运行的应用

---

## 🎯 解决方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **方案1: 自动端口检测** | 零配置、自动避免冲突 | 每次端口可能不同 | 临时使用、快速测试 |
| **方案2: 配置文件** | 固定端口、可预测 | 需要手动检查冲突 | 个人开发环境 |
| **方案3: Docker 容器** | 完全隔离、易于管理 | 需要安装 Docker | 生产环境、长期运行 |

---

## 🚀 方案1: 自动端口检测（推荐用于开发）

### 使用新的自动端口检测脚本

```bash
# 自动检测并使用可用端口（从 8000 开始）
python run_auto_port.py

# 尝试使用 8080，如果被占用则自动找下一个
python run_auto_port.py -p 8080

# 从 9000 开始搜索可用端口
python run_auto_port.py --start-port 9000

# 强制使用指定端口，不自动检测（如果被占用则失败）
python run_auto_port.py -p 8080 --no-auto
```

### 示例输出

```
⚠️  Port 8000 is occupied
✅ Found available port: 8002
============================================================
🚀 MineContext-v2 Server (Auto Port Detection)
============================================================
Server:       http://127.0.0.1:8002
API Docs:     http://127.0.0.1:8002/docs
TodoList:     http://127.0.0.1:8002/todolist/frontend/my-todos.html
Health Check: http://127.0.0.1:8002/health
============================================================

💡 Tip: Save this port to your config to use it next time!
   Edit config.yaml and set: server.port = 8002
```

---

## ⚙️ 方案2: 配置文件自定义端口

### 方法 2.1: 修改配置文件

编辑 `config.yaml`:

```yaml
server:
  host: 127.0.0.1
  port: 8888  # 改成你想要的端口
  debug: false
```

然后正常启动：
```bash
python run.py
```

### 方法 2.2: 使用环境变量

创建或编辑 `.env` 文件：

```bash
# .env
SERVER_PORT=8888
SERVER_HOST=127.0.0.1
```

### 方法 2.3: 命令行参数

```bash
# 使用 8888 端口
python run.py -p 8888

# 使用 9000 端口并监听所有网络接口
python run.py -p 9000 -H 0.0.0.0
```

### 如何选择合适的端口？

常见的替代端口：
- **8080**: 最常见的备用端口
- **8888**: Jupyter Notebook 也常用，但很流行
- **9000-9999**: 通常较少冲突
- **3000**: 如果不用 React/Node.js 开发

**检查端口是否被占用**:
```bash
# macOS/Linux
lsof -i :8000

# 或者
netstat -an | grep 8000
```

---

## 🐳 方案3: Docker 容器化（推荐用于生产/长期运行）

### 为什么选择 Docker？

✅ **优势**:
1. **完全隔离**: 容器内的端口不会直接占用宿主机端口
2. **端口映射灵活**: 可以随时改变映射关系
3. **环境一致**: 开发、测试、生产环境完全一致
4. **易于管理**: 一条命令启动/停止
5. **资源隔离**: 不影响宿主机其他服务
6. **持久化运行**: 可以设置自动重启

### 3.1 使用 Docker Compose（最简单）

#### 步骤 1: 安装 Docker

如果还没安装：
```bash
# macOS
brew install --cask docker

# 或者从官网下载: https://www.docker.com/products/docker-desktop
```

#### 步骤 2: 修改端口映射

编辑 `docker-compose.yml`，修改端口映射：

```yaml
services:
  minecontext:
    ports:
      - "8888:8000"  # 宿主机 8888 -> 容器 8000
      # 左边改成任意你想要的端口
```

#### 步骤 3: 启动服务

```bash
# 构建并启动（首次运行）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

#### 步骤 4: 访问服务

```
http://localhost:8888  # 使用你设置的端口
```

### 3.2 端口冲突处理

如果宿主机 8888 也被占用，只需要改配置：

```yaml
ports:
  - "9527:8000"  # 随便改成其他端口
```

然后重启：
```bash
docker-compose down
docker-compose up -d
```

### 3.3 运行多个实例

如果需要同时运行多个实例（例如生产和开发环境）：

```bash
# 启动生产环境（端口 8000）
docker-compose up -d minecontext

# 启动开发环境（端口 8001）
docker-compose --profile dev up -d minecontext-dev
```

访问：
- 生产环境: http://localhost:8000
- 开发环境: http://localhost:8001

### 3.4 设置自动启动

```yaml
services:
  minecontext:
    restart: unless-stopped  # 已经配置好了
```

这样系统重启后，Docker 会自动启动容器。

### 3.5 数据持久化

数据会自动保存到宿主机：
```
./data/          -> 数据库文件
./screenshots/   -> 截图文件
```

即使删除容器，数据也不会丢失。

---

## 📊 各方案对比示例

### 场景 1: 临时测试（使用几个小时）

**推荐**: 方案1 - 自动端口检测

```bash
python run_auto_port.py
```

- ✅ 无需配置
- ✅ 自动避免冲突
- ✅ 快速启动

---

### 场景 2: 个人开发环境（每天使用）

**推荐**: 方案2 - 固定端口配置

修改 `config.yaml`:
```yaml
server:
  port: 8888
```

- ✅ 端口固定，易于记忆
- ✅ 可以添加到书签
- ✅ 无需 Docker

---

### 场景 3: 长期运行（7x24小时）

**推荐**: 方案3 - Docker 容器

```bash
docker-compose up -d
```

- ✅ 自动重启
- ✅ 资源隔离
- ✅ 易于管理
- ✅ 端口映射灵活

---

## 🔍 端口冲突诊断

### 检查端口占用

```bash
# 查看 8000 端口被哪个进程占用
lsof -i :8000

# 输出示例：
# COMMAND   PID  USER   FD   TYPE DEVICE
# python3.9 1234 user   3u   IPv4 ...
```

### 释放被占用的端口

```bash
# 找到进程 PID 后，终止进程
kill 1234

# 或者强制终止
kill -9 1234
```

### 查找可用端口范围

```bash
# 列出所有监听端口
netstat -an | grep LISTEN

# 或者使用 Python 脚本
python -c "
import socket
for port in range(8000, 8100):
    try:
        s = socket.socket()
        s.bind(('127.0.0.1', port))
        s.close()
        print(f'Port {port} is available')
        break
    except:
        pass
"
```

---

## 💡 最佳实践建议

### 开发阶段
1. 使用 **自动端口检测脚本** (`run_auto_port.py`)
2. 端口范围: 8000-8999 或 9000-9999
3. 记录常用端口避免忘记

### 生产部署
1. 使用 **Docker Compose**
2. 映射到标准端口（80/443 使用反向代理）
3. 启用健康检查和自动重启
4. 定期备份数据目录

### 团队协作
1. 在 `README.md` 中记录默认端口
2. 使用 `.env.example` 提供配置模板
3. 建议使用 Docker 统一环境

---

## 🚨 常见问题

### Q1: Docker 容器端口映射后仍然冲突？

**A**: 检查是否是宿主机端口冲突，而不是容器内部：

```bash
# 错误示例
ports:
  - "8000:8000"  # 宿主机 8000 被占用

# 正确做法
ports:
  - "8888:8000"  # 改变宿主机端口
```

### Q2: 如何在 Docker 中使用不同端口？

**A**: 只需修改容器的环境变量：

```yaml
environment:
  - SERVER_PORT=9000  # 容器内部端口
ports:
  - "8888:9000"  # 映射关系也要改
```

### Q3: 自动端口检测每次都不一样怎么办？

**A**: 找到可用端口后，将其写入配置文件：

```bash
# 第一次运行，发现使用了 8002
python run_auto_port.py

# 然后固定下来
echo "server:" > config.yaml
echo "  port: 8002" >> config.yaml

# 以后直接用
python run.py
```

---

## 📚 推荐方案总结

### 你的情况（长期运行）

根据你的需求：**服务会运行很久，长期占用端口**

🏆 **最佳方案: Docker Compose**

```bash
# 1. 修改 docker-compose.yml 端口映射
vi docker-compose.yml
# 改成: - "9527:8000"

# 2. 启动服务
docker-compose up -d

# 3. 以后管理
docker-compose logs -f      # 查看日志
docker-compose restart      # 重启
docker-compose down         # 停止
```

**优势**:
- ✅ 完全避免端口冲突（容器隔离）
- ✅ 系统重启自动启动
- ✅ 随时更改端口映射无需改代码
- ✅ 数据持久化安全
- ✅ 资源使用可控

---

## 🎓 快速上手命令

```bash
# 开发/测试（临时使用）
python run_auto_port.py

# 个人使用（固定端口）
python run.py -p 8888

# 生产/长期运行（推荐）
docker-compose up -d
```

---

需要帮助? 查看日志:
```bash
# 直接运行
检查终端输出

# Docker
docker-compose logs -f
```
