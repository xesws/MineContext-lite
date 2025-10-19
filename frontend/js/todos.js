/**
 * TODO Management JavaScript for MineContext-v2
 */

const API_BASE = window.location.origin + '/api';

let currentEditId = null;
let allTodos = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadTodos();
    loadStats();
});

function setupEventListeners() {
    // Form submission
    document.getElementById('todo-form').addEventListener('submit', handleFormSubmit);

    // Filter changes
    document.getElementById('filter-status').addEventListener('change', loadTodos);
    document.getElementById('filter-priority').addEventListener('change', applyFilters);
    document.getElementById('filter-source').addEventListener('change', applyFilters);

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadTodos();
        loadStats();
    });

    // Cancel edit button
    document.getElementById('cancel-btn').addEventListener('click', cancelEdit);
}

async function loadTodos() {
    try {
        const status = document.getElementById('filter-status').value;

        const response = await fetch(`${API_BASE}/todos?status=${status}&limit=200`);

        if (!response.ok) {
            throw new Error('Failed to load TODOs');
        }

        allTodos = await response.json();
        applyFilters();

    } catch (error) {
        console.error('Error loading TODOs:', error);
        showNotification('加载TODO失败', 'error');
    }
}

function applyFilters() {
    const priority = document.getElementById('filter-priority').value;
    const source = document.getElementById('filter-source').value;

    let filtered = [...allTodos];

    if (priority !== 'all') {
        filtered = filtered.filter(t => t.priority === priority);
    }

    if (source !== 'all') {
        filtered = filtered.filter(t => t.created_by === source);
    }

    displayTodos(filtered);
}

function displayTodos(todos) {
    const container = document.getElementById('todos-list');
    const emptyState = document.getElementById('empty-state');

    if (todos.length === 0) {
        container.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }

    emptyState.classList.add('hidden');

    // Sort by priority (high -> medium -> low) and due date
    todos.sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];

        if (priorityDiff !== 0) return priorityDiff;

        // If same priority, sort by due date
        if (a.due_date && b.due_date) {
            return new Date(a.due_date) - new Date(b.due_date);
        }
        if (a.due_date) return -1;
        if (b.due_date) return 1;

        return 0;
    });

    container.innerHTML = todos.map(todo => createTodoCard(todo)).join('');
}

function createTodoCard(todo) {
    const priorityColors = {
        high: 'bg-red-100 text-red-800 border-red-300',
        medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
        low: 'bg-green-100 text-green-800 border-green-300'
    };

    const priorityLabels = {
        high: '高',
        medium: '中',
        low: '低'
    };

    const sourceIcon = todo.created_by === 'manual' ? '✏️' : '🤖';
    const sourceLabel = todo.created_by === 'manual' ? '手动创建' : 'AI提取';

    const isCompleted = todo.status === 'completed';
    const isOverdue = todo.due_date && new Date(todo.due_date) < new Date() && !isCompleted;
    const isUpcoming = todo.due_date && !isCompleted && !isOverdue;

    const dueDateClass = isOverdue ? 'text-red-600 font-semibold' : isUpcoming ? 'text-orange-600' : 'text-gray-600';

    return `
        <div class="p-4 hover:bg-gray-50 ${isCompleted ? 'opacity-60' : ''}">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center space-x-2 mb-2">
                        ${todo.title ? `<h3 class="font-semibold text-gray-900 ${isCompleted ? 'line-through' : ''}">${escapeHtml(todo.title)}</h3>` : ''}
                        <span class="px-2 py-1 text-xs font-medium rounded ${priorityColors[todo.priority]}">
                            ${priorityLabels[todo.priority]}
                        </span>
                        <span class="text-xs text-gray-500" title="${sourceLabel}">
                            ${sourceIcon}
                        </span>
                        ${isOverdue ? '<span class="text-xs text-red-600 font-semibold">⚠️ 已逾期</span>' : ''}
                    </div>

                    <p class="text-sm text-gray-700 ${isCompleted ? 'line-through' : ''} whitespace-pre-wrap">
                        ${escapeHtml(todo.todo_text)}
                    </p>

                    ${todo.notes ? `<p class="text-sm text-gray-500 mt-1 italic">备注: ${escapeHtml(todo.notes)}</p>` : ''}

                    <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        ${todo.due_date ? `
                            <span class="${dueDateClass}">
                                📅 ${formatDateTime(todo.due_date)}
                            </span>
                        ` : ''}
                        <span>创建于 ${formatDateTime(todo.extracted_at)}</span>
                        ${todo.completed_at ? `<span>完成于 ${formatDateTime(todo.completed_at)}</span>` : ''}
                    </div>
                </div>

                <div class="flex items-center space-x-2 ml-4">
                    ${!isCompleted ? `
                        <button
                            onclick="completeTodo(${todo.id})"
                            class="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                            title="标记为完成"
                        >
                            ✓
                        </button>
                        <button
                            onclick="editTodo(${todo.id})"
                            class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                            title="编辑"
                        >
                            ✏️
                        </button>
                    ` : `
                        <button
                            onclick="reopenTodo(${todo.id})"
                            class="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700"
                            title="重新打开"
                        >
                            ↩️
                        </button>
                    `}
                    <button
                        onclick="deleteTodo(${todo.id})"
                        class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                        title="删除"
                    >
                        🗑️
                    </button>
                </div>
            </div>
        </div>
    `;
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const title = document.getElementById('todo-title').value.trim();
    const todoText = document.getElementById('todo-text').value.trim();
    const priority = document.getElementById('todo-priority').value;
    const dueDate = document.getElementById('todo-due-date').value;
    const notes = document.getElementById('todo-notes').value.trim();

    if (!todoText) {
        showNotification('请输入TODO内容', 'error');
        return;
    }

    const todoData = {
        title: title || null,
        todo_text: todoText,
        priority: priority,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        notes: notes || null
    };

    try {
        if (currentEditId) {
            // Update existing TODO
            const response = await fetch(`${API_BASE}/todos/${currentEditId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(todoData)
            });

            if (!response.ok) {
                throw new Error('Failed to update TODO');
            }

            showNotification('TODO更新成功', 'success');
            cancelEdit();
        } else {
            // Create new TODO
            const response = await fetch(`${API_BASE}/todos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(todoData)
            });

            if (!response.ok) {
                throw new Error('Failed to create TODO');
            }

            showNotification('TODO创建成功', 'success');
            document.getElementById('todo-form').reset();
        }

        loadTodos();
        loadStats();

    } catch (error) {
        console.error('Error saving TODO:', error);
        showNotification('保存TODO失败', 'error');
    }
}

async function completeTodo(id) {
    try {
        const response = await fetch(`${API_BASE}/todos/${id}/complete`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to complete TODO');
        }

        showNotification('TODO已完成', 'success');
        loadTodos();
        loadStats();

    } catch (error) {
        console.error('Error completing TODO:', error);
        showNotification('操作失败', 'error');
    }
}

async function reopenTodo(id) {
    try {
        const response = await fetch(`${API_BASE}/todos/${id}/reopen`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to reopen TODO');
        }

        showNotification('TODO已重新打开', 'success');
        loadTodos();
        loadStats();

    } catch (error) {
        console.error('Error reopening TODO:', error);
        showNotification('操作失败', 'error');
    }
}

async function editTodo(id) {
    try {
        const response = await fetch(`${API_BASE}/todos/${id}`);

        if (!response.ok) {
            throw new Error('Failed to load TODO');
        }

        const todo = await response.json();

        // Populate form
        document.getElementById('todo-title').value = todo.title || '';
        document.getElementById('todo-text').value = todo.todo_text;
        document.getElementById('todo-priority').value = todo.priority;
        document.getElementById('todo-notes').value = todo.notes || '';

        if (todo.due_date) {
            // Convert ISO to datetime-local format
            const date = new Date(todo.due_date);
            const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
            document.getElementById('todo-due-date').value = localDate.toISOString().slice(0, 16);
        } else {
            document.getElementById('todo-due-date').value = '';
        }

        // Update form state
        currentEditId = id;
        document.getElementById('form-title').textContent = '编辑TODO';
        document.getElementById('submit-btn').textContent = '💾 保存修改';
        document.getElementById('cancel-btn').classList.remove('hidden');

        // Scroll to form
        document.getElementById('todo-form').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Error loading TODO:', error);
        showNotification('加载TODO失败', 'error');
    }
}

function cancelEdit() {
    currentEditId = null;
    document.getElementById('todo-form').reset();
    document.getElementById('form-title').textContent = '创建TODO';
    document.getElementById('submit-btn').textContent = '➕ 创建TODO';
    document.getElementById('cancel-btn').classList.add('hidden');
    document.getElementById('edit-todo-id').value = '';
}

async function deleteTodo(id) {
    if (!confirm('确定要删除这个TODO吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/todos/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete TODO');
        }

        showNotification('TODO已删除', 'success');
        loadTodos();
        loadStats();

    } catch (error) {
        console.error('Error deleting TODO:', error);
        showNotification('删除失败', 'error');
    }
}

async function loadStats() {
    try {
        // Load pending and completed counts
        const [pendingRes, completedRes, upcomingRes] = await Promise.all([
            fetch(`${API_BASE}/todos?status=pending&limit=1000`),
            fetch(`${API_BASE}/todos?status=completed&limit=1000`),
            fetch(`${API_BASE}/todos/upcoming/deadline?days=3`)
        ]);

        const pending = await pendingRes.json();
        const completed = await completedRes.json();
        const upcoming = await upcomingRes.json();

        document.getElementById('pending-count').textContent = pending.length;
        document.getElementById('completed-count').textContent = completed.length;
        document.getElementById('upcoming-count').textContent = upcoming.length;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function formatDateTime(isoString) {
    if (!isoString) return '';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = date - now;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    const formatted = date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });

    // Add relative time for due dates
    if (diffDays === 0) {
        return `${formatted} (今天)`;
    } else if (diffDays === 1) {
        return `${formatted} (明天)`;
    } else if (diffDays === -1) {
        return `${formatted} (昨天)`;
    } else if (diffDays > 0 && diffDays <= 7) {
        return `${formatted} (${diffDays}天后)`;
    } else if (diffDays < 0 && diffDays >= -7) {
        return `${formatted} (${Math.abs(diffDays)}天前)`;
    }

    return formatted;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-100 border-green-400 text-green-700',
        error: 'bg-red-100 border-red-400 text-red-700',
        info: 'bg-blue-100 border-blue-400 text-blue-700'
    };

    const notification = document.createElement('div');
    notification.className = `${colors[type]} px-4 py-3 rounded border shadow-lg`;
    notification.textContent = message;

    document.getElementById('notification-container').appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}
