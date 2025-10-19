/**
 * Dashboard JavaScript for MineContext-v2
 * Handles analytics visualization and data fetching
 */

const API_BASE = window.location.origin + '/api';

// Chart instances
let activityChart = null;
let hourlyChart = null;
let appsChart = null;
let productivityTrendChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    setupEventListeners();
    loadDashboardData();
    loadTodoWidget();
});

function setupEventListeners() {
    const periodType = document.getElementById('period-type');
    const refreshBtn = document.getElementById('refresh-btn');
    const customDate = document.getElementById('custom-date');

    periodType.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            customDate.classList.remove('hidden');
        } else {
            customDate.classList.add('hidden');
            loadDashboardData();
        }
    });

    customDate.addEventListener('change', () => {
        loadDashboardData();
    });

    refreshBtn.addEventListener('click', () => {
        loadDashboardData();
        loadTodoWidget();
    });

    // Quick add TODO form
    const quickAddForm = document.getElementById('quick-add-todo-form');
    if (quickAddForm) {
        quickAddForm.addEventListener('submit', handleQuickAddTodo);
    }
}

async function loadDashboardData() {
    const periodType = document.getElementById('period-type').value;
    const customDate = document.getElementById('custom-date').value;

    let endpoint = '/analytics/daily';
    let params = {};

    switch (periodType) {
        case 'today':
            endpoint = '/analytics/daily';
            break;
        case 'yesterday':
            endpoint = '/analytics/daily';
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            params.date = yesterday.toISOString().split('T')[0];
            break;
        case 'week':
            endpoint = '/analytics/weekly';
            break;
        case 'custom':
            if (customDate) {
                endpoint = '/analytics/daily';
                params.date = customDate;
            }
            break;
    }

    try {
        // Build query string
        const queryString = new URLSearchParams(params).toString();
        const url = `${API_BASE}${endpoint}${queryString ? '?' + queryString : ''}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch analytics data');

        const data = await response.json();

        updateStats(data.statistics, data.productivity_score);
        updateActivityChart(data.activity_breakdown);
        updateHourlyChart(data.hourly_distribution);
        updateAppsChart(data.app_usage);
        updateSessionsTable(data.sessions);

        // Load productivity trend
        loadProductivityTrend();

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load analytics data');
    }
}

function updateStats(stats, productivity) {
    document.getElementById('stat-screenshots').textContent = stats.total_screenshots || 0;
    document.getElementById('stat-sessions').textContent = stats.work_sessions || 0;
    document.getElementById('stat-productivity').textContent = productivity?.toFixed(1) || '0.0';
    document.getElementById('stat-switches').textContent = stats.app_switches || 0;
}

function initializeCharts() {
    // Activity Breakdown Pie Chart
    const activityCtx = document.getElementById('activity-chart').getContext('2d');
    activityChart = new Chart(activityCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
                    '#8B5CF6', '#EC4899', '#6366F1', '#14B8A6'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Hourly Distribution Bar Chart
    const hourlyCtx = document.getElementById('hourly-chart').getContext('2d');
    hourlyChart = new Chart(hourlyCtx, {
        type: 'bar',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Screenshots',
                data: Array(24).fill(0),
                backgroundColor: '#3B82F6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Top Apps Horizontal Bar Chart
    const appsCtx = document.getElementById('apps-chart').getContext('2d');
    appsChart = new Chart(appsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Screenshots',
                data: [],
                backgroundColor: '#10B981'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });

    // Productivity Trend Line Chart
    const trendCtx = document.getElementById('productivity-trend-chart').getContext('2d');
    productivityTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Productivity Score',
                data: [],
                borderColor: '#8B5CF6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function updateActivityChart(activityBreakdown) {
    if (!activityBreakdown || Object.keys(activityBreakdown).length === 0) {
        activityChart.data.labels = ['No Data'];
        activityChart.data.datasets[0].data = [1];
    } else {
        activityChart.data.labels = Object.keys(activityBreakdown).map(k => k.charAt(0).toUpperCase() + k.slice(1));
        activityChart.data.datasets[0].data = Object.values(activityBreakdown);
    }
    activityChart.update();
}

function updateHourlyChart(hourlyDistribution) {
    const hourlyData = Array(24).fill(0);

    if (hourlyDistribution) {
        Object.entries(hourlyDistribution).forEach(([hour, count]) => {
            hourlyData[parseInt(hour)] = count;
        });
    }

    hourlyChart.data.datasets[0].data = hourlyData;
    hourlyChart.update();
}

function updateAppsChart(appUsage) {
    if (!appUsage || Object.keys(appUsage).length === 0) {
        appsChart.data.labels = ['No Data'];
        appsChart.data.datasets[0].data = [1];
    } else {
        // Take top 10 apps
        const sorted = Object.entries(appUsage)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        appsChart.data.labels = sorted.map(([app]) => app);
        appsChart.data.datasets[0].data = sorted.map(([, count]) => count);
    }
    appsChart.update();
}

async function loadProductivityTrend() {
    try {
        const response = await fetch(`${API_BASE}/analytics/productivity?days=7`);
        if (!response.ok) throw new Error('Failed to fetch productivity trend');

        const data = await response.json();

        productivityTrendChart.data.labels = data.daily_scores.map(d => d.date);
        productivityTrendChart.data.datasets[0].data = data.daily_scores.map(d => d.productivity_score);
        productivityTrendChart.update();

    } catch (error) {
        console.error('Error loading productivity trend:', error);
    }
}

function updateSessionsTable(sessions) {
    const tbody = document.getElementById('sessions-table');

    if (!sessions || sessions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No sessions found</td></tr>';
        return;
    }

    tbody.innerHTML = sessions.map(session => {
        const startTime = new Date(session.start_time).toLocaleTimeString();
        const duration = formatDuration(session.duration_seconds);

        return `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${startTime}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${duration}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${session.screenshot_count}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        ${session.dominant_activity}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

function showError(message) {
    // Simple error notification
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// ===== TODO Widget Functions =====

async function loadTodoWidget() {
    try {
        // Load stats
        const [pendingRes, completedRes, upcomingRes] = await Promise.all([
            fetch(`${API_BASE}/todos?status=pending&limit=1000`),
            fetch(`${API_BASE}/todos?status=completed&limit=1000`),
            fetch(`${API_BASE}/todos/upcoming/deadline?days=3`)
        ]);

        const pending = await pendingRes.json();
        const completed = await completedRes.json();
        const upcoming = await upcomingRes.json();

        // Update counts
        document.getElementById('todo-pending-count').textContent = pending.length;
        document.getElementById('todo-completed-count').textContent = completed.length;
        document.getElementById('todo-upcoming-count').textContent = upcoming.length;

        // Display upcoming TODOs
        displayUpcomingTodos(upcoming);

    } catch (error) {
        console.error('Error loading TODO widget:', error);
    }
}

function displayUpcomingTodos(todos) {
    const container = document.getElementById('upcoming-todos-list');
    const emptyState = document.getElementById('no-upcoming-todos');

    if (todos.length === 0) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    container.classList.remove('hidden');
    emptyState.classList.add('hidden');

    // Sort by due date (earliest first) and priority
    todos.sort((a, b) => {
        if (a.due_date && b.due_date) {
            return new Date(a.due_date) - new Date(b.due_date);
        }
        if (a.due_date) return -1;
        if (b.due_date) return 1;
        return 0;
    });

    // Show only top 5
    const topTodos = todos.slice(0, 5);

    container.innerHTML = topTodos.map(todo => {
        const priorityColors = {
            high: 'bg-red-100 text-red-700',
            medium: 'bg-yellow-100 text-yellow-700',
            low: 'bg-green-100 text-green-700'
        };

        const now = new Date();
        const dueDate = new Date(todo.due_date);
        const diffHours = (dueDate - now) / (1000 * 60 * 60);
        const isUrgent = diffHours < 24;

        return `
            <div class="flex items-start justify-between p-3 border border-gray-200 rounded-md hover:bg-gray-50 ${isUrgent ? 'border-red-300 bg-red-50' : ''}">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-2 mb-1">
                        ${todo.title ? `<p class="text-sm font-medium text-gray-900 truncate">${escapeHtml(todo.title)}</p>` : ''}
                        <span class="px-2 py-0.5 text-xs font-medium rounded ${priorityColors[todo.priority]}">
                            ${todo.priority}
                        </span>
                    </div>
                    <p class="text-sm text-gray-600 truncate">${escapeHtml(todo.todo_text)}</p>
                    <p class="text-xs text-gray-500 mt-1">
                        ${isUrgent ? '⚠️ ' : '📅 '}${formatDateTime(todo.due_date)}
                    </p>
                </div>
                <button
                    onclick="completeTodoFromWidget(${todo.id})"
                    class="ml-2 px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                    title="Mark as complete"
                >
                    ✓
                </button>
            </div>
        `;
    }).join('');
}

async function handleQuickAddTodo(e) {
    e.preventDefault();

    const input = document.getElementById('quick-todo-text');
    const todoText = input.value.trim();

    if (!todoText) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/todos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                todo_text: todoText,
                priority: 'medium',
                created_by: 'manual'
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create TODO');
        }

        input.value = '';
        showNotification('TODO created successfully', 'success');
        loadTodoWidget();

    } catch (error) {
        console.error('Error creating TODO:', error);
        showNotification('Failed to create TODO', 'error');
    }
}

async function completeTodoFromWidget(todoId) {
    try {
        const response = await fetch(`${API_BASE}/todos/${todoId}/complete`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to complete TODO');
        }

        showNotification('TODO completed', 'success');
        loadTodoWidget();

    } catch (error) {
        console.error('Error completing TODO:', error);
        showNotification('Failed to complete TODO', 'error');
    }
}

function formatDateTime(isoString) {
    if (!isoString) return '';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = date - now;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    const formatted = date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    // Add relative time for upcoming deadlines
    if (diffHours < 0) {
        return `${formatted} (overdue)`;
    } else if (diffHours < 2) {
        return `${formatted} (in ${diffHours}h)`;
    } else if (diffDays === 0) {
        return `${formatted} (today)`;
    } else if (diffDays === 1) {
        return `${formatted} (tomorrow)`;
    } else if (diffDays <= 3) {
        return `${formatted} (in ${diffDays} days)`;
    }

    return formatted;
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
