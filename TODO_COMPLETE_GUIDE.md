# MineContext-v2 TODO功能完整指南

**完成日期**: 2025-10-18
**功能状态**: ✅ 100% 完成

---

## 🎉 功能概览

成功实现了完整的TODO管理系统，包括：
- ✅ 手动创建TODO（带标题、截止日期、优先级、备注）
- ✅ AI自动提取TODO
- ✅ 完整的CRUD操作
- ✅ 专用的TODO管理页面
- ✅ Dashboard TODO小部件
- ✅ 即将到期提醒
- ✅ 快速添加功能

---

## 📱 使用方式

### 1. TODO管理页面

**访问**: http://127.0.0.1:8000/todos.html

**功能**:
- 📊 统计卡片（待办/已完成/即将到期）
- 🔍 多维度过滤（状态/优先级/来源）
- ➕ 创建/编辑表单
- 📋 TODO列表展示
- ✅ 完成/重新打开
- 🗑️ 删除功能

**操作步骤**:
1. 填写右侧表单（标题可选，内容必填）
2. 选择优先级（低/中/高）
3. 设置截止日期（可选）
4. 添加备注（可选）
5. 点击"创建TODO"

### 2. Dashboard小部件

**访问**: http://127.0.0.1:8000/dashboard.html

**功能**:
- 📊 3个统计指标（Pending / Due Soon / Completed）
- 📝 显示前5个即将到期的TODO
- ⚡ 快速添加TODO（底部输入框）
- ✓ 一键完成TODO
- 🔴 24小时内到期的TODO高亮显示（红色背景）
- 🔗 "View All →" 链接到完整TODO页面

**快速添加**:
- 在底部输入框输入TODO内容
- 点击"Add"按钮
- 自动创建为中等优先级TODO

---

## 🎨 界面特性

### TODO卡片设计

**颜色编码**:
- 🔴 高优先级: 红色标签
- 🟡 中优先级: 黄色标签
- 🟢 低优先级: 绿色标签

**来源图标**:
- ✏️ 手动创建
- 🤖 AI提取

**状态显示**:
- ⚠️ 已逾期（红色高亮）
- 📅 正常到期
- ✅ 已完成（半透明+删除线）

**时间显示**:
- "今天"、"明天" - 相对时间
- "X天后"、"X小时后" - 具体倒计时
- 逾期时显示"(overdue)"

### Dashboard小部件特性

**紧急提醒**:
- 24小时内到期: 红色边框+红色背景
- 正常到期: 灰色边框+白色背景

**统计指标**:
- Pending: 黄色背景
- Due Soon: 红色背景（3天内）
- Completed: 绿色背景

---

## 🔌 API接口

### 基础操作

```bash
# 创建TODO
curl -X POST "http://127.0.0.1:8000/api/todos" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成项目文档",
    "todo_text": "整理并完善项目技术文档",
    "priority": "high",
    "due_date": "2025-10-20T18:00:00",
    "notes": "包括架构图和API文档"
  }'

# 获取所有待办事项
curl "http://127.0.0.1:8000/api/todos?status=pending"

# 获取3天内到期的TODO
curl "http://127.0.0.1:8000/api/todos/upcoming/deadline?days=3"

# 完成TODO
curl -X POST "http://127.0.0.1:8000/api/todos/1/complete"

# 更新TODO
curl -X PATCH "http://127.0.0.1:8000/api/todos/1" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "medium",
    "due_date": "2025-10-21T12:00:00"
  }'

# 删除TODO
curl -X DELETE "http://127.0.0.1:8000/api/todos/1"
```

### 高级过滤

```bash
# 获取高优先级待办事项
curl "http://127.0.0.1:8000/api/todos?status=pending&priority=high"

# 获取手动创建的TODO
curl "http://127.0.0.1:8000/api/todos?status=pending&created_by=manual"

# 获取AI提取的TODO
curl "http://127.0.0.1:8000/api/todos?status=pending&created_by=ai_extracted"

# 获取已完成的TODO
curl "http://127.0.0.1:8000/api/todos?status=completed&limit=50"
```

---

## 📊 数据库结构

### extracted_todos 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| screenshot_id | INTEGER | 关联截图（可选） |
| todo_text | TEXT | TODO内容（必填） |
| priority | TEXT | 优先级（low/medium/high） |
| status | TEXT | 状态（pending/completed） |
| extracted_at | DATETIME | 创建时间 |
| completed_at | DATETIME | 完成时间 |
| **due_date** | DATETIME | ⭐ 截止日期 |
| **created_by** | TEXT | ⭐ 创建方式（manual/ai_extracted） |
| **title** | TEXT | ⭐ TODO标题 |
| **notes** | TEXT | ⭐ 备注信息 |

**注**: ⭐ 标记的为新增字段

---

## 🎯 使用场景

### 场景1: 日常任务管理

```
1. 打开 http://127.0.0.1:8000/todos.html
2. 创建今日待办事项
   - 标题: "完成周报"
   - 内容: "总结本周工作内容"
   - 优先级: 高
   - 截止: 今天18:00
3. 查看Dashboard小部件跟踪进度
4. 完成后点击 ✓ 标记完成
```

### 场景2: 项目截止日期管理

```
1. 创建项目相关TODO
   - 标题: "项目演示准备"
   - 内容: "准备PPT和demo环境"
   - 优先级: 高
   - 截止: 2025-10-20 14:00
   - 备注: "需要包含新功能展示"
2. Dashboard会自动显示在"Due Soon"
3. 临近截止时间时高亮提醒
```

### 场景3: AI辅助+手动管理

```
1. AI从截图中自动提取TODO
   - 识别代码注释中的TODO
   - 识别文档中的任务列表
   - 识别聊天记录中的待办事项

2. 手动补充截止日期
   - 在TODO管理页面编辑AI提取的TODO
   - 添加截止日期和优先级

3. 统一跟踪和管理
   - 所有TODO在一个页面
   - 过滤器区分来源
```

### 场景4: 快速记录想法

```
1. 在Dashboard底部快速输入框
2. 输入: "研究新的UI框架"
3. 点击"Add"
4. 自动创建为中等优先级TODO
5. 后续在TODO页面补充详情
```

---

## 🚀 技术实现

### 前端技术栈

- **HTML5** + **Tailwind CSS** - 响应式UI
- **原生JavaScript** - 无框架依赖
- **Fetch API** - RESTful通信
- **Chart.js** - Dashboard图表（已有）

### 后端技术栈

- **FastAPI** - RESTful API框架
- **SQLite** - 数据持久化
- **Pydantic** - 数据验证

### 代码统计

**新增代码**:
- `backend/api/todos_routes.py` - 378行
- `frontend/todos.html` - 236行
- `frontend/js/todos.js` - 450行
- Dashboard小部件 - ~200行

**修改代码**:
- `backend/database.py` - +150行
- `frontend/js/dashboard.js` - +190行
- `backend/main.py` - +2行
- `frontend/dashboard.html` - +55行
- `frontend/reports.html` - +3行

**总计**: 约1400行新代码 + 200行修改

---

## 📝 文件清单

### 新增文件
```
backend/api/todos_routes.py      # TODO API路由
frontend/todos.html              # TODO管理页面
frontend/js/todos.js             # TODO JavaScript逻辑
TODO_FEATURE_SUMMARY.md          # 功能总结文档
TODO_COMPLETE_GUIDE.md           # 本文档
```

### 修改文件
```
backend/database.py              # 数据库扩展
backend/main.py                  # 集成TODO路由
frontend/dashboard.html          # 添加TODO小部件
frontend/js/dashboard.js         # TODO小部件逻辑
frontend/reports.html            # 添加导航链接
```

---

## ✨ 功能亮点

### 1. 智能时间处理
- 相对时间显示（"今天"、"明天"、"X天后"）
- 逾期自动检测和高亮
- 24小时内紧急提醒

### 2. 灵活的优先级管理
- 三级优先级（高/中/低）
- 颜色编码可视化
- 自动排序（优先级+截止日期）

### 3. 双源统一管理
- AI自动提取 + 手动创建
- 来源图标区分
- 统一界面管理

### 4. Dashboard集成
- 快速查看即将到期
- 一键完成功能
- 快速添加入口

### 5. 完整的CRUD
- 创建、读取、更新、删除
- 批量操作支持
- 状态管理（完成/重新打开）

---

## 🎓 最佳实践

### 1. 优先级设置建议

**高优先级**:
- 当天必须完成
- 紧急重要任务
- 阻塞其他工作的任务

**中优先级**:
- 本周内完成
- 重要但不紧急
- 日常工作任务

**低优先级**:
- 可延后的任务
- 学习和改进类任务
- 锦上添花的功能

### 2. 截止日期设置

- 具体任务设置具体时间（如 14:00）
- 日常任务设置当天EOD（如 18:00）
- 项目里程碑设置整点（如 12:00）

### 3. 标题vs内容

**标题**: 简短概括（3-8个字）
- 例如: "完成周报"、"修复登录bug"

**内容**: 详细描述（具体执行步骤）
- 例如: "总结本周开发工作，包括新功能、bug修复和性能优化"

### 4. 备注使用

- 相关链接（Jira、文档URL）
- 依赖信息（等待某人回复）
- 注意事项（需要测试环境）

---

## 🔧 故障排除

### 问题1: TODO不显示

**可能原因**:
- 过滤器设置错误
- 服务器未运行
- API调用失败

**解决方法**:
1. 检查过滤器设置（状态/优先级/来源）
2. 确认服务器运行: http://127.0.0.1:8000/health
3. 查看浏览器控制台错误信息
4. 刷新页面重新加载

### 问题2: 快速添加不工作

**可能原因**:
- 输入框为空
- JavaScript未加载
- API端点不可用

**解决方法**:
1. 确保输入了TODO内容
2. 刷新页面
3. 检查控制台错误
4. 测试API: `curl http://127.0.0.1:8000/api/todos`

### 问题3: 时间显示不正确

**可能原因**:
- 时区问题
- 日期格式错误

**解决方法**:
- 使用ISO 8601格式: `YYYY-MM-DDTHH:MM:SS`
- 浏览器会自动转换为本地时区显示

---

## 📈 未来增强建议

### Phase 6.1 - 高级功能
- [ ] TODO分类/标签系统
- [ ] 重复任务（每日/每周）
- [ ] 子任务支持
- [ ] 批量操作（批量完成/删除）

### Phase 6.2 - 提醒系统
- [ ] 邮件提醒（到期前24小时）
- [ ] 桌面通知
- [ ] 浏览器通知

### Phase 6.3 - 导出与集成
- [ ] 导出为Markdown
- [ ] 导出为CSV/Excel
- [ ] 同步到Notion
- [ ] 同步到Obsidian

### Phase 6.4 - 协作功能
- [ ] 分享TODO链接
- [ ] 多人协作
- [ ] 评论功能
- [ ] 历史记录

---

## 🎯 使用技巧

### 技巧1: 每日回顾
```
1. 早上打开Dashboard
2. 查看"Due Soon"统计
3. 规划今日优先级
4. 使用快速添加记录新任务
```

### 技巧2: 每周规划
```
1. 周一创建本周TODO
2. 设置合理的截止日期
3. 按优先级分配
4. 每日检查和调整
```

### 技巧3: 紧急任务处理
```
1. 高优先级 + 今天截止
2. Dashboard会高亮显示
3. 置顶处理
4. 完成后立即标记
```

### 技巧4: AI辅助工作流
```
1. 正常工作（AI自动捕获TODO）
2. 定期查看AI提取的TODO
3. 补充截止日期和优先级
4. 合并相似任务
```

---

## 📞 支持与反馈

**API文档**: http://127.0.0.1:8000/docs
**系统健康**: http://127.0.0.1:8000/health
**TODO管理**: http://127.0.0.1:8000/todos.html
**Dashboard**: http://127.0.0.1:8000/dashboard.html

---

## ✅ 功能检查清单

- [x] 手动创建TODO
- [x] 设置截止日期
- [x] 设置优先级（高/中/低）
- [x] 添加标题和备注
- [x] 编辑TODO
- [x] 删除TODO
- [x] 标记完成
- [x] 重新打开已完成
- [x] 多维度过滤
- [x] 即将到期提醒
- [x] Dashboard小部件
- [x] 快速添加功能
- [x] AI提取集成
- [x] 双源统一管理
- [x] RESTful API

---

**版本**: v1.0
**状态**: ✅ 生产就绪
**最后更新**: 2025-10-18

🎉 **TODO管理系统已全部实现，可以开始使用！**
