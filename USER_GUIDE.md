# MineContext-v2 使用指南

**AI驱动的智能截图管理与分析系统**

---

## 📖 项目简介

MineContext-v2 是一个轻量级、本地优先的上下文感知AI应用程序，能够自动捕获屏幕截图、使用AI进行智能分析，并提供工作分析、报告生成和语义搜索等功能。

**核心特性：**
- 🎯 自动截图捕获与智能去重
- 🤖 多AI提供商支持（OpenAI、Anthropic、OpenRouter）
- 📊 工作分析与生产力报告
- 🔍 语义搜索与上下文检索
- 📈 可视化仪表盘与图表
- 💾 本地存储，保护隐私

---

## 🚀 快速开始

### 系统要求

- Python 3.9 或更高版本
- pip 包管理器
- macOS、Linux 或 Windows

### 安装步骤

1. **克隆或进入项目目录**
   ```bash
   cd tasker_dev
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量（可选，启用AI功能）**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，添加API密钥
   ```

5. **启动服务器**
   ```bash
   python run.py
   ```

### 访问应用

服务器启动后，访问以下地址：

- **主界面（Gallery）**: http://127.0.0.1:8000/
- **分析仪表盘**: http://127.0.0.1:8000/dashboard.html
- **报告页面**: http://127.0.0.1:8000/reports.html
- **API文档**: http://127.0.0.1:8000/docs

---

## 🎨 界面功能详解

### 1. Gallery（画廊页面）

**访问地址**: http://127.0.0.1:8000/

**主要功能：**
- **截图控制**
  - `Start Capture` - 开始自动截图（默认间隔5秒）
  - `Stop Capture` - 停止自动截图
  - `Capture Now` - 立即手动截图
  - `Analyze Batch (AI)` - 批量AI分析未处理的截图
  - `Generate Embeddings` - 生成向量嵌入以支持语义搜索

- **截图展示**
  - 网格布局显示所有截图
  - 每张截图显示：缩略图、AI生成的标签、时间戳、描述
  - 点击截图查看详情

- **语义搜索**
  - 勾选 `🔍 Semantic Search` 启用AI语义搜索
  - 输入查询内容，例如："Python代码编辑"、"浏览器查看文档"
  - 基于内容相似度返回结果

- **统计信息**
  - Screenshots: 截图总数
  - Embeddings: 已生成向量嵌入的截图数量
  - Status: 捕获状态（Capturing/Stopped）

### 2. Dashboard（仪表盘）

**访问地址**: http://127.0.0.1:8000/dashboard.html

**主要功能：**
- **统计卡片**
  - Total Screenshots - 截图总数
  - Work Sessions - 工作会话数量
  - Productivity Score - 生产力评分（0-100）
  - App Switches - 应用切换次数

- **可视化图表**（使用Chart.js）
  - **Activity Breakdown** - 活动类型分布（饼图）
  - **Activity by Hour** - 每小时活动分布（柱状图）
  - **Top Applications** - 最常使用的应用（柱状图）
  - **Productivity Trend** - 7天生产力趋势（折线图）

- **工作会话表**
  - 显示所有工作会话的开始时间、持续时间、截图数量和主要活动

- **时间段选择器**
  - Today - 今天
  - Yesterday - 昨天
  - This Week - 本周（默认）
  - Custom Range - 自定义日期范围

### 3. Reports（报告页面）

**访问地址**: http://127.0.0.1:8000/reports.html

**主要功能：**
- **报告生成**
  - 选择报告类型：Daily Report（每日报告）或 Weekly Report（周报告）
  - 选择日期
  - 点击 `Generate Report` 生成Markdown格式的报告

- **报告内容**（Markdown渲染）
  - 活动概览和统计数据
  - 应用使用情况
  - 生产力分析
  - 可操作的洞察建议

- **历史报告**
  - 查看最近生成的报告列表
  - 点击历史报告快速加载

- **下载功能**
  - 点击 `Download Report` 下载Markdown文件

---

## 🔧 配置说明

### AI功能配置

编辑 `config/config.yaml`:

```yaml
ai:
  enabled: true                    # 启用AI功能
  provider: openrouter             # 选择: openai, anthropic, openrouter
  model: anthropic/claude-3.5-sonnet
  auto_analyze: false              # 是否自动分析新截图
  analyze_on_demand: true          # 是否支持按需分析

embeddings:
  enabled: true                    # 启用向量嵌入
  model: all-MiniLM-L6-v2         # 嵌入模型
  auto_generate: true              # 分析后自动生成嵌入
  batch_size: 32

vector_db:
  enabled: true                    # 启用向量数据库
  path: ./data/chroma_db
  collection_name: screenshot_contexts
  similarity_threshold: 0.3
  max_results: 10
```

在 `.env` 文件中设置API密钥：

```bash
# OpenRouter (推荐，支持多种模型)
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# 或使用 OpenAI
OPENAI_API_KEY=sk-xxxxx

# 或使用 Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 截图捕获配置

```yaml
capture:
  interval_seconds: 5              # 截图间隔（秒）
  auto_start: false                # 是否自动开始捕获
  screenshot_dir: ./screenshots    # 截图保存目录
  max_screenshots: 10000           # 最大截图数量
  deduplicate: true                # 启用去重
  hash_threshold: 5                # 图像相似度阈值
```

---

## 📊 使用场景示例

### 场景1：日常工作追踪

1. **启动捕获**: 打开 Gallery 页面，点击 `Start Capture`
2. **正常工作**: 系统每5秒自动截图并去重
3. **查看分析**: 访问 Dashboard 查看今日工作统计
4. **生成报告**: 在 Reports 页面生成每日工作报告

### 场景2：项目回顾

1. **语义搜索**: 在 Gallery 页面使用语义搜索
   - 输入 "FastAPI 路由开发"
   - 查找所有相关编码截图
2. **时间筛选**: 在 Dashboard 选择特定日期范围
3. **导出报告**: 生成周报告并下载

### 场景3：生产力分析

1. **查看仪表盘**: 打开 Dashboard
2. **分析趋势**: 查看7天生产力趋势图
3. **识别模式**: 查看 Activity by Hour 找出高效时段
4. **应用分析**: 查看 Top Applications 了解时间分配

---

## 🛠️ API使用

### 主要端点

**截图管理**
- `GET /api/screenshots` - 获取截图列表
- `GET /api/screenshots/{id}` - 获取单个截图详情
- `PATCH /api/screenshots/{id}` - 更新截图元数据
- `DELETE /api/screenshots/{id}` - 删除截图

**捕获控制**
- `POST /api/capture/start` - 开始捕获
- `POST /api/capture/stop` - 停止捕获
- `GET /api/capture/status` - 获取捕获状态
- `POST /api/capture/now` - 立即截图

**AI分析**
- `POST /api/screenshots/{id}/analyze` - 分析单个截图
- `POST /api/screenshots/analyze-batch` - 批量分析

**语义搜索**
- `POST /api/search/semantic` - 语义搜索
- `GET /api/screenshots/{id}/similar` - 查找相似截图

**分析报告**
- `GET /api/analytics/daily` - 每日分析
- `GET /api/analytics/weekly` - 每周分析
- `POST /api/reports/daily` - 生成每日报告
- `POST /api/reports/weekly` - 生成周报告

**完整API文档**: http://127.0.0.1:8000/docs

---

## 📁 项目结构

```
tasker_dev/
├── backend/
│   ├── main.py                 # FastAPI应用入口
│   ├── capture.py              # 截图捕获服务
│   ├── database.py             # 数据库操作
│   ├── models.py               # 数据模型
│   ├── config.py               # 配置管理
│   ├── vector_store.py         # 向量数据库
│   ├── api/
│   │   ├── routes.py           # 主要API路由
│   │   ├── analytics_routes.py # 分析API
│   │   └── reports_routes.py   # 报告API
│   ├── services/               # 业务服务
│   │   ├── activity_analyzer.py      # 活动分析
│   │   ├── report_generator.py       # 报告生成
│   │   ├── pattern_recognition.py    # 模式识别
│   │   ├── todo_extractor.py         # TODO提取
│   │   ├── context_qa.py             # 问答系统
│   │   └── notification_engine.py    # 通知引擎
│   └── utils/
│       ├── image_utils.py      # 图像处理
│       ├── ai_utils.py         # AI工具
│       └── embedding_utils.py  # 嵌入生成
├── frontend/
│   ├── index.html              # Gallery页面
│   ├── dashboard.html          # 仪表盘页面
│   ├── reports.html            # 报告页面
│   ├── js/
│   │   ├── app.js              # Gallery逻辑
│   │   ├── dashboard.js        # 仪表盘逻辑
│   │   └── reports.js          # 报告逻辑
│   └── styles.css              # 自定义样式
├── config/
│   └── config.yaml             # 应用配置
├── data/
│   ├── minecontext.db          # SQLite数据库
│   └── chroma_db/              # 向量数据库
├── screenshots/                # 截图存储目录
├── requirements.txt            # Python依赖
├── .env.example               # 环境变量模板
└── run.py                     # 启动脚本
```

---

## 🧪 测试结果

### Playwright自动化测试（2025-10-17）

**测试覆盖：**
- ✅ Dashboard页面 - 所有4个图表正常渲染
- ✅ Reports页面 - UI功能正常，API验证通过
- ✅ Gallery页面 - 截图展示和元数据显示正常
- ✅ 页面导航 - 所有链接工作正常
- ✅ 控制台错误 - 无JavaScript错误

**已修复的Bug：**
1. **数据库迁移顺序问题** (`backend/database.py`)
   - 问题：索引创建在列添加之前
   - 影响：服务器无法启动
   - 状态：已修复 ✅

2. **HTTP方法不匹配** (`frontend/js/reports.js`)
   - 问题：前端使用GET，后端期望POST
   - 影响：报告生成功能不可用
   - 状态：已修复 ✅

**详细测试报告**: `PLAYWRIGHT_TEST_SUMMARY.md`

---

## 🎯 功能完成度

### Phase 5A: 活动分析与报告 ✅ 完成

**后端服务：**
- ✅ ActivityAnalyzer - 时间范围活动统计
- ✅ ReportGenerator - 每日/周报告生成
- ✅ 工作会话检测
- ✅ 生产力评分算法

**数据库扩展：**
- ✅ 4个新表（work_sessions, activity_summaries, generated_reports, extracted_todos）
- ✅ 新字段（session_id, productivity_score, duration_seconds, app_category）

**API端点：**
- ✅ 15+ 新端点用于分析和报告

**前端界面：**
- ✅ Dashboard页面（4个图表）
- ✅ Reports页面（报告生成和查看）

### Phase 5B: 语义搜索与向量存储 ✅ 完成

**向量数据库：**
- ✅ ChromaDB集成
- ✅ 自动嵌入生成管道
- ✅ 语义相似度搜索

**嵌入服务：**
- ✅ Sentence-Transformers集成
- ✅ 批量嵌入生成
- ✅ 相似度计算

### Phase 5C: 智能特性 ✅ 完成

**高级功能：**
- ✅ 模式识别（工作节奏、高峰时段）
- ✅ TODO提取（AI驱动）
- ✅ 上下文问答（RAG系统）
- ✅ 智能通知引擎

---

## 💡 最佳实践

### 1. AI使用建议

- **API密钥选择**: 推荐使用 OpenRouter，支持多种模型且性价比高
- **模型选择**:
  - 性能优先: `anthropic/claude-3.5-sonnet`
  - 成本优先: `openai/gpt-4o-mini`
- **批量分析**: 对于大量截图，使用 `Analyze Batch` 而非逐个分析
- **嵌入生成**: 分析后自动生成嵌入以支持语义搜索

### 2. 性能优化

- **截图间隔**: 根据工作性质调整（编码可用10-15秒，快速切换用5秒）
- **去重阈值**: 默认5，数值越小越严格
- **定期清理**: 定期删除不需要的旧截图
- **数据库维护**: 大量数据时考虑定期VACUUM优化

### 3. 隐私保护

- **本地存储**: 所有数据默认本地存储
- **API密钥安全**: 使用 `.env` 文件，不要提交到版本控制
- **选择性分析**: 手动选择需要AI分析的截图
- **敏感内容**: 可以暂停捕获或删除特定截图

---

## 🔍 故障排除

### 服务器启动失败

**问题**: `sqlite3.OperationalError: no such column`
**解决**: 删除 `data/minecontext.db`，让系统重新创建数据库

### 端口冲突

**问题**: `Address already in use`
**解决**:
```bash
# 查找占用8000端口的进程
lsof -i :8000
# 终止进程
kill <PID>
```

### AI分析不工作

**问题**: API调用失败
**检查**:
1. `.env` 文件中API密钥是否正确
2. `config.yaml` 中 `ai.enabled` 是否为 `true`
3. 网络连接是否正常
4. API配额是否充足

### 语义搜索无结果

**问题**: 搜索返回空结果
**解决**:
1. 确认截图已生成嵌入（Embeddings: X/Y）
2. 点击 `Generate Embeddings` 生成缺失的嵌入
3. 检查 `data/chroma_db/` 目录是否存在

---

## 🚀 未来增强（可选）

### 潜在功能

1. **桌面应用**
   - Electron封装
   - 系统托盘集成
   - 全局快捷键

2. **高级分析**
   - 项目时间跟踪
   - 客户/项目计费
   - 团队协作洞察

3. **多源上下文**
   - 浏览器扩展
   - 邮件集成
   - 日历同步

4. **导出与集成**
   - Notion导出
   - Obsidian同步
   - Slack机器人

---

## 📄 相关文档

- **完整实现总结**: `IMPLEMENTATION_SUMMARY.md`
- **测试报告**: `PLAYWRIGHT_TEST_SUMMARY.md`
- **功能差距分析**: `GAP_ANALYSIS.md`
- **实现计划**: `plan.md`

---

## 🙏 致谢

本项目受 [MineContext](https://github.com/volcengine/MineContext) by Volcengine 启发，实现了其核心功能的轻量级版本。

---

## 📞 支持

遇到问题或有建议？

- 查看文档：`/docs` 目录
- API文档：http://127.0.0.1:8000/docs
- 查看日志：控制台输出

---

**版本**: v2.0 (Phase 5 Complete)
**最后更新**: 2025-10-17
**状态**: ✅ 生产就绪
