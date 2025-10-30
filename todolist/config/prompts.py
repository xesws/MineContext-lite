"""AI prompt templates for TodoList module."""

PROGRESS_ANALYSIS_PROMPT = """你是一个任务进度分析专家。用户有一个待办事项，请根据他的活动记录分析进度。

**用户的TODO：**
标题：{todo_title}
描述：{todo_description}

**活动时间轴：**
{activities_timeline}

**请以JSON格式返回分析结果：**
{{
  "completed_aspects": [
    "具体已完成的内容1（要详细具体）",
    "具体已完成的内容2"
  ],
  "remaining_aspects": [
    "仍需完成的内容1（要明确具体）",
    "仍需完成的内容2"
  ],
  "completion_percentage": 65,
  "summary": "一句话总结当前进度（30字以内）",
  "next_steps": [
    "建议的下一步行动1（要可操作）",
    "建议的下一步行动2"
  ]
}}

**分析要求：**
1. 基于实际活动证据，不要臆测
2. 区分"已完成"和"待完成"要具体明确
3. completion_percentage 要合理（基于活动内容和TODO目标）
4. next_steps 要可操作、有指导性
5. 如果TODO描述模糊，根据活动内容推断用户意图
6. 只返回JSON，不要有其他文字

**示例场景：**
TODO: 学习机器学习中的随机森林
活动：
1. [2025-10-25 14:30] 阅读决策树原理文档（30分钟）
   内容：机器学习实战 - 决策树章节
2. [2025-10-26 10:15] 观看随机森林教学视频（45分钟）
   内容：Random Forest Tutorial on YouTube
3. [2025-10-27 15:00] 编写Python代码实现（60分钟）
   内容：在VS Code中实现随机森林分类器

分析：
{{
  "completed_aspects": ["理解了决策树的基本原理", "学习了随机森林的集成学习思想", "完成了基础代码实现"],
  "remaining_aspects": ["特征重要性分析", "超参数调优", "实际数据集应用"],
  "completion_percentage": 60,
  "summary": "已掌握随机森林基础理论和代码实现",
  "next_steps": ["学习特征重要性分析方法", "在实际数据集上应用随机森林"]
}}
"""

ACTIVITY_TYPE_CLASSIFICATION_PROMPT = """根据截屏描述，判断活动类型：

截屏内容：{screenshot_description}

请从以下类型中选择一个：
- reading: 阅读文档、书籍、文章
- coding: 编写代码、调试程序
- video: 观看视频教程、讲座
- browsing: 网页浏览、搜索
- communication: 邮件、聊天、会议
- design: 设计、画图、建模
- general: 其他

只返回类型名称，例如：coding
"""

SEMANTIC_MATCH_PROMPT = """判断以下截屏活动是否与TODO相关：

TODO描述：{todo_description}
截屏内容：{screenshot_description}

请以JSON格式返回：
{{
  "is_related": true/false,
  "confidence": 0-100,
  "reason": "一句话说明理由"
}}

只返回JSON，不要有其他文字。

示例：
{{
  "is_related": true,
  "confidence": 85,
  "reason": "用户正在阅读随机森林的算法原理文档，与TODO高度相关"
}}
"""

TASK_DECOMPOSITION_PROMPT = """请将以下任务拆解为 3-7 个具体、可执行的子任务：

任务标题: {title}
任务描述: {description}
预估时间: {estimated_hours} 小时

要求：
1. 子任务应该具体、可衡量、可完成
2. 子任务应该有逻辑顺序
3. 为每个子任务估算所需时间
4. 标注优先级 (high/medium/low)
5. 如果总时间已指定，子任务时间应大致符合总时间
6. 子任务应该是主任务的组成部分，不是独立任务

返回 JSON 格式:
[
  {{
    "title": "子任务标题（简洁、面向行动）",
    "description": "需要做什么的简要说明",
    "estimated_hours": 2.0,
    "priority": "high"
  }},
  ...
]

返回 3-7 个子任务的 JSON 数组。
"""

SUBTASK_DISCOVERY_PROMPT = """分析用户的工作活动，判断是否在完成 TODO 的具体子任务。

TODO 信息:
- 标题: {todo_title}
- 描述: {todo_description}

最近活动:
{activities_timeline}

要求：
1. 如果发现用户在完成具体的子任务，提取出来
2. 子任务应该是 TODO 的一部分，不是新的独立任务
3. 子任务标题应该简洁明确
4. 每个子任务都应该有信心分数（0-1）

返回 JSON 格式:
[
  {{
    "title": "子任务标题",
    "description": "从活动中推断的描述",
    "confidence": 0.85
  }},
  ...
]

如果没有检测到明确的子任务，返回空数组 []。
"""

COMPLETION_DETECTION_PROMPT = """分析 TODO 的完成情况。

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
  "reason": "简要说明理由"
}}

只返回JSON，不要有其他文字。
"""
