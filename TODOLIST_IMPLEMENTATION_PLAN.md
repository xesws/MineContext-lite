# 🤖 智能 TODO 自动更新系统 - 实现计划

## 📋 项目概述

实现一个**智能 TODO 自动更新系统**，让 AI 根据截图分析自动更新 TODO 的状态、进度和子任务。

### 核心理念
- **智能分析**：AI 分析截图活动，识别 TODO 完成情况
- **自动更新**：基于子任务数量自动计算进度（如 3/5 = 60%）
- **混合模式**：简单更新自动执行，重要操作需用户确认
- **任务拆解**：AI 智能拆解大任务为具体子任务

### 用户交互模式（根据你的选择）
- ✅ **更新方式**：混合模式（自动 + 确认）
- ✅ **触发时机**：手动触发（点击按钮）
- ✅ **任务拆解**：创建时和分析时都支持
- ✅ **进度计算**：基于子任务完成数量

---

## 🏗️ 系统架构

### 新增文件结构

```
todolist/backend/services/
├── todo_updater.py           # 新增：智能 TODO 更新引擎
└── task_decomposer.py        # 新增：任务拆解服务

todolist/config/
└── prompts.py                # 扩展：添加拆解任务和更新建议提示词

todolist/backend/api/
└── routes.py                 # 扩展：添加新 API 端点

todolist/frontend/
├── my-todos.html             # 扩展：智能分析按钮、建议确认对话框
└── js/
    ├── todo-api.js           # 扩展：新 API 方法
    ├── todo-manager.js       # 扩展：智能分析功能
    └── todo-components.js    # 扩展：建议列表组件、进度增强
```

---

## 📦 Phase 1: 后端核心服务

### 1.1 创建 `todolist/backend/services/todo_updater.py`

**智能 TODO 更新引擎**

```python
class TodoAutoUpdater:
    """智能 TODO 自动更新服务"""

    def __init__(self, db_connection):
        self.conn = db_connection
        self.activity_matcher = ActivityMatcher(db_connection)
        self.progress_analyzer = ProgressAnalyzer(db_connection)

    async def analyze_and_generate_suggestions(self, todo_id: int) -> Dict:
        """
        分析 TODO 并生成更新建议

        Returns:
            {
                'auto_suggestions': [  # 自动执行的建议
                    {
                        'type': 'update_progress',
                        'data': {'percentage': 60},
                        'reason': '3/5 个子任务已完成'
                    }
                ],
                'confirm_suggestions': [  # 需要确认的建议
                    {
                        'type': 'mark_complete',
                        'confidence': 0.95,
                        'reason': '所有子任务已完成'
                    },
                    {
                        'type': 'create_subtask',
                        'data': {
                            'title': '实现登录功能',
                            'description': '...'
                        },
                        'confidence': 0.85,
                        'reason': '检测到相关开发活动'
                    }
                ]
            }
        """

    async def apply_suggestions(self, todo_id: int, approved_suggestions: List[Dict]):
        """应用用户确认的建议"""

    def calculate_progress_from_subtasks(self, todo_id: int) -> int:
        """
        基于子任务数量计算进度

        Returns:
            进度百分比 (0-100)
        """
```

**核心逻辑**：

1. **进度计算**：
   ```python
   subtasks = get_subtasks(todo_id)
   if not subtasks:
       return current_progress

   total = len(subtasks)
   completed = len([t for t in subtasks if t.status == 'completed'])
   return int(completed / total * 100)
   ```

2. **完成检测**：
   ```python
   # 条件1: 所有子任务完成
   if subtasks and all(t.status == 'completed' for t in subtasks):
       return True, 1.0, "所有子任务已完成"

   # 条件2: AI 分析认为已完成
   ai_result = await self.progress_analyzer.analyze_completion(todo_id)
   if ai_result.confidence > 0.9:
       return True, ai_result.confidence, ai_result.reason
   ```

3. **子任务发现**：
   ```python
   # AI 分析最近活动，发现新子任务
   activities = self.activity_matcher.get_recent_activities(todo_id)
   prompt = f"""
   TODO: {todo.title}
   描述: {todo.description}
   最近活动: {format_activities(activities)}

   分析用户是否在完成这个 TODO 的具体子任务。
   如果是，提取子任务的标题和描述。
   返回 JSON 格式: [{{"title": "...", "description": "..."}}]
   """
   suggested_subtasks = await call_ai_structured(prompt)
   ```

### 1.2 创建 `todolist/backend/services/task_decomposer.py`

**任务拆解服务**

```python
class TaskDecomposer:
    """AI 任务拆解服务"""

    async def decompose_task(
        self,
        title: str,
        description: str,
        estimated_hours: Optional[float] = None
    ) -> List[Dict]:
        """
        AI 拆解任务为子任务列表

        Returns:
            [
                {
                    'title': '设计数据库表结构',
                    'description': '...',
                    'estimated_hours': 2.0,
                    'priority': 'high'
                },
                ...
            ]
        """
        prompt = f"""
        请将以下任务拆解为 3-7 个具体、可执行的子任务：

        任务标题: {title}
        任务描述: {description}
        预估时间: {estimated_hours or '未指定'} 小时

        要求：
        1. 子任务应该具体、可衡量、可完成
        2. 子任务应该有逻辑顺序
        3. 为每个子任务估算所需时间
        4. 标注优先级 (high/medium/low)

        返回 JSON 格式的子任务列表。
        """

        subtasks = await call_ai_structured(prompt)
        return subtasks
```

### 1.3 扩展 `todolist/backend/api/routes.py`

**新增 API 端点**：

```python
@router.post("/todos/{todo_id}/smart-analyze")
async def smart_analyze_todo(todo_id: int):
    """
    智能分析 TODO 并生成更新建议

    Returns:
        {
            'auto_applied': [...],      # 已自动应用的更新
            'suggestions': [...],       # 需要用户确认的建议
            'current_progress': 60,     # 当前进度
            'analyzed_at': '...'
        }
    """
    updater = TodoAutoUpdater(get_connection())

    # 生成建议
    result = await updater.analyze_and_generate_suggestions(todo_id)

    # 自动应用简单更新
    for suggestion in result['auto_suggestions']:
        await updater.apply_suggestions(todo_id, [suggestion])

    return {
        'auto_applied': result['auto_suggestions'],
        'suggestions': result['confirm_suggestions'],
        'current_progress': result['progress'],
        'analyzed_at': datetime.now().isoformat()
    }


@router.post("/todos/{todo_id}/apply-suggestions")
async def apply_todo_suggestions(
    todo_id: int,
    suggestions: List[Dict]  # 用户选中的建议
):
    """应用用户确认的建议"""
    updater = TodoAutoUpdater(get_connection())
    await updater.apply_suggestions(todo_id, suggestions)

    # 返回更新后的 TODO
    return await get_todo(todo_id)


@router.post("/todos/{todo_id}/decompose")
async def decompose_todo(todo_id: int):
    """AI 拆解任务（用于已创建的 TODO）"""
    todo = get_todo(todo_id)
    decomposer = TaskDecomposer()

    subtasks = await decomposer.decompose_task(
        title=todo['title'],
        description=todo['description'],
        estimated_hours=todo['estimated_hours']
    )

    return {'suggested_subtasks': subtasks}


@router.post("/todos/preview-decompose")
async def preview_decompose(data: Dict):
    """预览任务拆解（用于创建时）"""
    decomposer = TaskDecomposer()

    subtasks = await decomposer.decompose_task(
        title=data['title'],
        description=data.get('description'),
        estimated_hours=data.get('estimated_hours')
    )

    return {'suggested_subtasks': subtasks}
```

### 1.4 扩展 `todolist/config/prompts.py`

**新增提示词**：

```python
TASK_DECOMPOSITION_PROMPT = """
请将以下任务拆解为 3-7 个具体、可执行的子任务：

任务标题: {title}
任务描述: {description}
预估时间: {estimated_hours} 小时

要求：
1. 子任务应该具体、可衡量、可完成
2. 子任务应该有逻辑顺序
3. 为每个子任务估算所需时间
4. 标注优先级 (high/medium/low)

返回 JSON 格式:
[
  {{
    "title": "子任务标题",
    "description": "详细描述",
    "estimated_hours": 2.0,
    "priority": "high"
  }},
  ...
]
"""

SUBTASK_DISCOVERY_PROMPT = """
分析用户的工作活动，判断是否在完成 TODO 的具体子任务。

TODO 信息:
- 标题: {todo_title}
- 描述: {todo_description}

最近活动:
{activities_timeline}

要求：
1. 如果发现用户在完成具体的子任务，提取出来
2. 子任务应该是 TODO 的一部分，不是新的独立任务
3. 子任务标题应该简洁明确

返回 JSON 格式:
[
  {{
    "title": "子任务标题",
    "description": "从活动中推断的描述",
    "confidence": 0.85
  }},
  ...
]
"""

COMPLETION_DETECTION_PROMPT = """
分析 TODO 的完成情况。

TODO 信息:
- 标题: {todo_title}
- 描述: {todo_description}
- 子任务: {subtasks_summary}

最近活动:
{activities_timeline}

判断这个 TODO 是否应该标记为已完成。

返回 JSON 格式:
{{
  "should_complete": true/false,
  "confidence": 0.95,
  "reason": "所有子任务已完成，且最近无相关活动"
}}
"""
```

---

## 📦 Phase 2: 前端交互界面

### 2.1 扩展 `todolist/frontend/my-todos.html`

**新增 UI 元素**：

```html
<!-- 在 TODO 详情页顶部添加智能分析按钮 -->
<div class="flex justify-between items-center mb-6">
    <h2 id="detail-title" class="text-2xl font-bold"></h2>
    <div class="flex space-x-2">
        <button id="smart-analyze-btn" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            🤖 智能分析
        </button>
        <button id="edit-todo-btn" class="px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded">
            ✏️ Edit
        </button>
        <button id="delete-todo-btn" class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded">
            🗑️ Delete
        </button>
    </div>
</div>

<!-- 增强进度显示 - 添加子任务计数 -->
<div class="mb-6">
    <div class="flex justify-between items-center mb-2">
        <h3 class="text-sm font-semibold text-gray-700">Progress</h3>
        <div class="text-sm">
            <span id="detail-progress-percent" class="font-medium text-blue-600">0%</span>
            <span id="detail-subtasks-count" class="ml-2 text-gray-500">(0/0 subtasks)</span>
        </div>
    </div>
    <div class="progress-bar">
        <div id="detail-progress-fill" class="progress-fill" style="width: 0%"></div>
    </div>
    <p id="last-analyzed" class="text-xs text-gray-400 mt-1"></p>
</div>

<!-- 建议确认对话框 -->
<div id="suggestions-modal" class="modal">
    <div class="bg-white rounded-lg shadow-xl p-6 max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">🤖 AI 分析结果</h2>
            <button id="close-suggestions-modal" class="text-gray-500 hover:text-gray-700 text-2xl">×</button>
        </div>

        <!-- 自动更新通知 -->
        <div id="auto-updates-section" class="mb-6 hidden">
            <h3 class="text-sm font-semibold text-green-700 mb-2">✅ 已自动更新</h3>
            <div id="auto-updates-list" class="space-y-2"></div>
        </div>

        <!-- 建议列表 -->
        <div id="suggestions-section" class="mb-6">
            <h3 class="text-sm font-semibold text-gray-700 mb-2">💡 建议（请勾选要应用的）</h3>
            <div id="suggestions-list" class="space-y-3">
                <!-- 动态生成建议项 -->
            </div>
        </div>

        <div class="flex justify-end space-x-3">
            <button id="cancel-suggestions-btn" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                取消
            </button>
            <button id="apply-suggestions-btn" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                应用选中建议
            </button>
        </div>
    </div>
</div>

<!-- 在创建 TODO 表单中添加 AI 拆解按钮 -->
<div id="todo-modal" class="modal">
    <div class="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4">
        <h2 id="modal-title" class="text-xl font-bold mb-4">Create New TODO</h2>
        <form id="todo-form">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                    <input type="text" id="todo-title" required class="w-full px-3 py-2 border rounded-lg">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea id="todo-description" rows="4" class="w-full px-3 py-2 border rounded-lg"></textarea>
                </div>

                <!-- AI 拆解按钮 -->
                <div class="flex justify-end">
                    <button type="button" id="ai-decompose-btn" class="px-3 py-1 text-sm bg-purple-50 text-purple-700 rounded hover:bg-purple-100">
                        🧩 AI 智能拆解
                    </button>
                </div>

                <!-- 预览拆解结果 -->
                <div id="decompose-preview" class="hidden">
                    <label class="block text-sm font-medium text-gray-700 mb-2">建议的子任务</label>
                    <div id="subtasks-preview-list" class="space-y-2 max-h-60 overflow-y-auto">
                        <!-- 动态生成子任务预览 -->
                    </div>
                </div>

                <!-- 其他字段 -->
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                        <select id="todo-priority" class="w-full px-3 py-2 border rounded-lg">
                            <option value="low">Low</option>
                            <option value="medium" selected>Medium</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Estimated Hours</label>
                        <input type="number" id="todo-estimated-hours" min="0" step="0.5" class="w-full px-3 py-2 border rounded-lg">
                    </div>
                </div>
            </div>

            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" id="cancel-modal-btn" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                    Cancel
                </button>
                <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Save
                </button>
            </div>
        </form>
    </div>
</div>
```

### 2.2 扩展 `todolist/frontend/js/todo-api.js`

**新增 API 方法**：

```javascript
const TodoAPI = {
    // ... 现有方法 ...

    /**
     * 智能分析 TODO
     */
    async smartAnalyze(todoId) {
        return await this.request(`/todos/${todoId}/smart-analyze`, {
            method: 'POST'
        });
    },

    /**
     * 应用建议
     */
    async applySuggestions(todoId, suggestions) {
        return await this.request(`/todos/${todoId}/apply-suggestions`, {
            method: 'POST',
            body: JSON.stringify(suggestions)
        });
    },

    /**
     * AI 拆解任务（已创建的 TODO）
     */
    async decomposeTodo(todoId) {
        return await this.request(`/todos/${todoId}/decompose`, {
            method: 'POST'
        });
    },

    /**
     * 预览任务拆解（创建时）
     */
    async previewDecompose(title, description, estimatedHours) {
        return await this.request('/todos/preview-decompose', {
            method: 'POST',
            body: JSON.stringify({
                title: title,
                description: description,
                estimated_hours: estimatedHours
            })
        });
    }
};
```

### 2.3 扩展 `todolist/frontend/js/todo-manager.js`

**新增功能**：

```javascript
const TodoManager = {
    // ... 现有代码 ...

    state: {
        todos: [],
        selectedTodoId: null,
        filter: 'all',
        editingTodoId: null,
        pendingSuggestions: [],      // 新增
        decomposedSubtasks: []        // 新增
    },

    setupEventListeners() {
        // ... 现有监听器 ...

        // 智能分析按钮
        document.getElementById('smart-analyze-btn').addEventListener('click', async () => {
            if (this.state.selectedTodoId) {
                await this.smartAnalyze(this.state.selectedTodoId);
            }
        });

        // AI 拆解按钮（创建表单内）
        document.getElementById('ai-decompose-btn').addEventListener('click', async () => {
            await this.previewDecompose();
        });

        // 应用建议
        document.getElementById('apply-suggestions-btn').addEventListener('click', async () => {
            await this.applySuggestions();
        });

        // 关闭建议对话框
        document.getElementById('close-suggestions-modal').addEventListener('click', () => {
            document.getElementById('suggestions-modal').classList.remove('active');
        });

        document.getElementById('cancel-suggestions-btn').addEventListener('click', () => {
            document.getElementById('suggestions-modal').classList.remove('active');
        });
    },

    /**
     * 智能分析 TODO
     */
    async smartAnalyze(todoId) {
        try {
            TodoComponents.showToast('正在分析...', 'info');

            const result = await TodoAPI.smartAnalyze(todoId);

            // 保存建议到状态
            this.state.pendingSuggestions = result.suggestions || [];

            // 显示建议对话框
            this.showSuggestionsModal(result);

            // 刷新 TODO 详情（显示自动更新）
            await this.loadTodoDetails(todoId);

        } catch (error) {
            console.error('Smart analyze error:', error);
            TodoComponents.showToast('分析失败: ' + error.message, 'error');
        }
    },

    /**
     * 显示建议对话框
     */
    showSuggestionsModal(result) {
        const modal = document.getElementById('suggestions-modal');

        // 显示自动更新
        if (result.auto_applied && result.auto_applied.length > 0) {
            const autoSection = document.getElementById('auto-updates-section');
            const autoList = document.getElementById('auto-updates-list');

            autoList.innerHTML = result.auto_applied.map(update => `
                <div class="p-2 bg-green-50 rounded text-sm text-gray-700">
                    ✓ ${update.reason}
                </div>
            `).join('');

            autoSection.classList.remove('hidden');
        }

        // 显示建议列表
        const suggestionsList = document.getElementById('suggestions-list');

        if (result.suggestions && result.suggestions.length > 0) {
            suggestionsList.innerHTML = result.suggestions.map((suggestion, index) => `
                <div class="suggestion-item p-3 border rounded hover:bg-gray-50">
                    <label class="flex items-start cursor-pointer">
                        <input type="checkbox" checked class="mt-1 mr-3" data-index="${index}">
                        <div class="flex-1">
                            <div class="font-medium text-gray-900">
                                ${this.getSuggestionIcon(suggestion.type)} ${this.getSuggestionTitle(suggestion)}
                            </div>
                            <div class="text-sm text-gray-600 mt-1">${suggestion.reason}</div>
                            <div class="text-xs text-gray-400 mt-1">
                                置信度: ${(suggestion.confidence * 100).toFixed(0)}%
                            </div>
                        </div>
                    </label>
                </div>
            `).join('');
        } else {
            suggestionsList.innerHTML = '<div class="text-center text-gray-500 py-4">暂无建议</div>';
        }

        modal.classList.add('active');
    },

    /**
     * 获取建议图标
     */
    getSuggestionIcon(type) {
        const icons = {
            'mark_complete': '✅',
            'create_subtask': '➕',
            'update_status': '🔄',
            'update_progress': '📊'
        };
        return icons[type] || '💡';
    },

    /**
     * 获取建议标题
     */
    getSuggestionTitle(suggestion) {
        switch (suggestion.type) {
            case 'mark_complete':
                return '标记为已完成';
            case 'create_subtask':
                return `创建子任务: ${suggestion.data.title}`;
            case 'update_status':
                return `更新状态为: ${suggestion.data.status}`;
            case 'update_progress':
                return `更新进度为: ${suggestion.data.percentage}%`;
            default:
                return '应用建议';
        }
    },

    /**
     * 应用选中的建议
     */
    async applySuggestions() {
        try {
            // 获取选中的建议
            const checkboxes = document.querySelectorAll('#suggestions-list input[type="checkbox"]:checked');
            const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
            const selectedSuggestions = selectedIndices.map(i => this.state.pendingSuggestions[i]);

            if (selectedSuggestions.length === 0) {
                TodoComponents.showToast('请至少选择一个建议', 'error');
                return;
            }

            TodoComponents.showToast('正在应用建议...', 'info');

            // 调用 API
            await TodoAPI.applySuggestions(this.state.selectedTodoId, selectedSuggestions);

            // 关闭对话框
            document.getElementById('suggestions-modal').classList.remove('active');

            // 刷新 TODO
            await this.loadTodos();
            await this.loadTodoDetails(this.state.selectedTodoId);

            TodoComponents.showToast('建议已应用', 'success');

        } catch (error) {
            console.error('Apply suggestions error:', error);
            TodoComponents.showToast('应用失败: ' + error.message, 'error');
        }
    },

    /**
     * 预览任务拆解
     */
    async previewDecompose() {
        try {
            const title = document.getElementById('todo-title').value.trim();
            const description = document.getElementById('todo-description').value.trim();
            const estimatedHours = parseFloat(document.getElementById('todo-estimated-hours').value) || null;

            if (!title) {
                TodoComponents.showToast('请先输入任务标题', 'error');
                return;
            }

            TodoComponents.showToast('正在 AI 拆解任务...', 'info');

            const result = await TodoAPI.previewDecompose(title, description, estimatedHours);

            // 保存拆解结果
            this.state.decomposedSubtasks = result.suggested_subtasks || [];

            // 显示预览
            this.showDecomposePreview(result.suggested_subtasks);

            TodoComponents.showToast('拆解完成', 'success');

        } catch (error) {
            console.error('Decompose error:', error);
            TodoComponents.showToast('拆解失败: ' + error.message, 'error');
        }
    },

    /**
     * 显示拆解预览
     */
    showDecomposePreview(subtasks) {
        const preview = document.getElementById('decompose-preview');
        const list = document.getElementById('subtasks-preview-list');

        if (subtasks && subtasks.length > 0) {
            list.innerHTML = subtasks.map((subtask, index) => `
                <div class="p-3 border rounded bg-purple-50">
                    <div class="flex items-start">
                        <input type="checkbox" checked class="mt-1 mr-2" data-subtask-index="${index}">
                        <div class="flex-1">
                            <div class="font-medium text-sm">${this.escapeHtml(subtask.title)}</div>
                            ${subtask.description ? `<div class="text-xs text-gray-600 mt-1">${this.escapeHtml(subtask.description)}</div>` : ''}
                            <div class="text-xs text-gray-500 mt-1">
                                ${subtask.estimated_hours ? `预估: ${subtask.estimated_hours}h` : ''}
                                ${subtask.priority ? `优先级: ${subtask.priority}` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

            preview.classList.remove('hidden');
        }
    },

    /**
     * 保存 TODO（扩展：处理拆解的子任务）
     */
    async saveTodo() {
        try {
            const formData = {
                title: document.getElementById('todo-title').value.trim(),
                description: document.getElementById('todo-description').value.trim(),
                priority: document.getElementById('todo-priority').value,
                estimated_hours: parseFloat(document.getElementById('todo-estimated-hours').value) || null,
                tags: document.getElementById('todo-tags').value.trim()
            };

            if (!formData.title) {
                TodoComponents.showToast('Title is required', 'error');
                return;
            }

            // 创建主 TODO
            const result = await TodoAPI.createTodo(formData);
            const todoId = result.id;

            // 如果有拆解的子任务，创建它们
            if (this.state.decomposedSubtasks.length > 0) {
                const selectedCheckboxes = document.querySelectorAll('#subtasks-preview-list input[type="checkbox"]:checked');
                const selectedIndices = Array.from(selectedCheckboxes).map(cb => parseInt(cb.dataset.subtaskIndex));

                for (const index of selectedIndices) {
                    const subtask = this.state.decomposedSubtasks[index];
                    await TodoAPI.createTodo({
                        title: subtask.title,
                        description: subtask.description,
                        parent_id: todoId,
                        priority: subtask.priority || 'medium',
                        estimated_hours: subtask.estimated_hours || null
                    });
                }

                TodoComponents.showToast(`TODO 和 ${selectedIndices.length} 个子任务已创建`, 'success');
            } else {
                TodoComponents.showToast('TODO created successfully', 'success');
            }

            // 清空状态
            this.state.decomposedSubtasks = [];

            this.hideModal();
            await this.loadTodos();
            this.state.selectedTodoId = todoId;
            await this.loadTodoDetails(todoId);

        } catch (error) {
            console.error('Error saving TODO:', error);
            TodoComponents.showToast('Failed to save TODO', 'error');
        }
    },

    /**
     * 加载 TODO 详情（扩展：显示子任务计数）
     */
    async loadTodoDetails(todoId) {
        try {
            document.getElementById('empty-state').classList.add('hidden');
            document.getElementById('details-content').classList.remove('hidden');

            const todo = await TodoAPI.getTodo(todoId);

            // 更新基本信息
            document.getElementById('detail-title').textContent = todo.title;
            document.getElementById('detail-status').outerHTML = TodoComponents.getStatusBadge(todo.status);
            document.getElementById('detail-priority').innerHTML = TodoComponents.getPriorityDisplay(todo.priority);
            document.getElementById('detail-time').textContent = TodoComponents.formatTime(todo.total_time_spent);
            document.getElementById('detail-description').textContent = todo.description || 'No description';

            // 更新进度（含子任务计数）
            const progress = todo.completion_percentage || 0;
            document.getElementById('detail-progress-percent').textContent = `${progress}%`;
            document.getElementById('detail-progress-fill').style.width = `${progress}%`;

            // 显示子任务计数
            if (todo.children && todo.children.length > 0) {
                const completed = todo.children.filter(c => c.status === 'completed').length;
                const total = todo.children.length;
                document.getElementById('detail-subtasks-count').textContent = `(${completed}/${total} subtasks)`;
            } else {
                document.getElementById('detail-subtasks-count').textContent = '';
            }

            // 显示最后分析时间
            if (todo.latest_progress && todo.latest_progress.analyzed_at) {
                const analyzedTime = TodoComponents.formatDate(todo.latest_progress.analyzed_at);
                document.getElementById('last-analyzed').textContent = `上次分析: ${analyzedTime}`;
            } else {
                document.getElementById('last-analyzed').textContent = '';
            }

            // 其余代码保持不变...
            // （渲染 progress analysis, activities 等）

        } catch (error) {
            console.error('Error loading TODO details:', error);
            TodoComponents.showToast('Failed to load TODO details', 'error');
        }
    }
};
```

### 2.4 扩展 `todolist/frontend/js/todo-components.js`

**新增渲染函数**：

```javascript
const TodoComponents = {
    // ... 现有方法 ...

    /**
     * 渲染建议项
     */
    renderSuggestionItem(suggestion, index) {
        const icon = this.getSuggestionIcon(suggestion.type);
        const title = this.getSuggestionTitle(suggestion);

        return `
            <div class="suggestion-item p-3 border rounded hover:bg-gray-50">
                <label class="flex items-start cursor-pointer">
                    <input type="checkbox" checked class="mt-1 mr-3" data-index="${index}">
                    <div class="flex-1">
                        <div class="font-medium text-gray-900">
                            ${icon} ${title}
                        </div>
                        <div class="text-sm text-gray-600 mt-1">${this.escapeHtml(suggestion.reason)}</div>
                        <div class="text-xs text-gray-400 mt-1">
                            置信度: ${(suggestion.confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                </label>
            </div>
        `;
    },

    getSuggestionIcon(type) {
        const icons = {
            'mark_complete': '✅',
            'create_subtask': '➕',
            'update_status': '🔄',
            'update_progress': '📊'
        };
        return icons[type] || '💡';
    },

    getSuggestionTitle(suggestion) {
        switch (suggestion.type) {
            case 'mark_complete':
                return '标记为已完成';
            case 'create_subtask':
                return `创建子任务: ${suggestion.data.title}`;
            case 'update_status':
                return `更新状态为: ${suggestion.data.status}`;
            case 'update_progress':
                return `更新进度为: ${suggestion.data.percentage}%`;
            default:
                return '应用建议';
        }
    }
};
```

---

## 📦 Phase 3: 智能算法实现

### 3.1 实现 `TodoAutoUpdater` 核心逻辑

**详细实现见 Phase 1.1**

关键算法：
1. 进度计算：`completed_subtasks / total_subtasks * 100`
2. 完成检测：所有子任务完成 + AI 确认
3. 子任务发现：AI 分析活动内容

### 3.2 实现 `TaskDecomposer` 核心逻辑

**详细实现见 Phase 1.2**

### 3.3 集成现有 `ActivityMatcher` 和 `ProgressAnalyzer`

确保：
- ActivityMatcher 正确匹配截图到 TODO
- ProgressAnalyzer 提供活动时间线数据

---

## 🎯 实施优先级

### P0 - 核心功能（第一批实现）
- [x] 基于子任务数量计算进度
- [x] 智能分析按钮
- [x] 建议生成（mark_complete, update_progress）
- [x] 建议应用

### P1 - 增强功能（第二批实现）
- [ ] AI 任务拆解（创建时预览）
- [ ] 子任务自动发现（分析时建议）
- [ ] 建议确认界面（带勾选框）

### P2 - 体验优化（第三批实现）
- [ ] 置信度显示
- [ ] 分析历史记录
- [ ] 批量操作支持

---

## 🔄 工作流程

```
用户创建 TODO
    ↓
[可选] 点击"AI 拆解" → 预览子任务 → 确认创建
    ↓
系统捕获截图
    ↓
ActivityMatcher 自动匹配到 TODO
    ↓
用户点击"智能分析"按钮
    ↓
TodoAutoUpdater 分析
    ├─ 计算子任务进度 → 自动更新
    ├─ 检测完成情况 → 生成建议
    └─ 发现新子任务 → 生成建议
    ↓
展示建议对话框
    ├─ 自动更新：已应用（显示通知）
    └─ 需确认：用户勾选建议
    ↓
用户点击"应用选中建议"
    ↓
系统应用更新 → 刷新 TODO 显示
```

---

## ✅ 预期成果

### 功能成果
- ✅ TODO 自动更新进度百分比（基于子任务）
- ✅ 智能建议标记完成（混合模式：需确认）
- ✅ AI 拆解大任务为子任务（创建时 + 分析时）
- ✅ 进度条显示子任务计数（3/5 completed）
- ✅ 手动触发智能分析（点击按钮）
- ✅ 建议系统（自动执行 + 用户确认）

### 用户体验
- 📊 直观的进度显示（百分比 + 子任务计数）
- 🤖 AI 智能辅助（拆解、分析、建议）
- 🎯 混合模式（平衡自动化和控制权）
- ⚡ 手动触发（不消耗过多 API 额度）

---

## 🚀 开始实施

按照以下顺序实施：
1. **Phase 1.1-1.3**：后端核心服务和 API
2. **Phase 2.1-2.3**：前端界面和交互
3. **测试和优化**：完整工作流测试
4. **Phase 3**：算法调优和增强

预计实施时间：
- P0 核心功能：2-3 小时
- P1 增强功能：1-2 小时
- P2 体验优化：1 小时

总计：4-6 小时完成完整功能。
