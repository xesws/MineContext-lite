# 🚀 端口问题快速解决方案

## 3 种方法，选一个就行！

---

## 方法 1️⃣: 自动端口检测 ⭐ 最简单

```bash
python run_auto_port.py
```

✅ 自动找到可用端口，零配置！

---

## 方法 2️⃣: 手动指定端口

```bash
# 使用 8888 端口
python run.py -p 8888

# 或编辑 config.yaml
server:
  port: 8888
```

✅ 端口固定，易记

---

## 方法 3️⃣: Docker 容器 ⭐ 推荐长期运行

```bash
# 1. 改端口（编辑 docker-compose.yml）
ports:
  - "9527:8000"  # 左边改成你想要的

# 2. 启动
docker-compose up -d

# 3. 访问
# http://localhost:9527
```

✅ 完全隔离，自动重启，最稳定！

---

## 🆘 端口被占用？

```bash
# 查看谁在用 8000
lsof -i :8000

# 杀掉进程
kill -9 [PID]
```

---

## 💡 我的推荐

- **临时测试**: 用方法 1
- **日常开发**: 用方法 2
- **长期运行**: 用方法 3 🏆

详细文档: 📖 [PORT_MANAGEMENT_GUIDE.md](./PORT_MANAGEMENT_GUIDE.md)
