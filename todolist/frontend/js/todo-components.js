/**
 * TodoComponents - Reusable UI components for TodoList
 */

const TodoComponents = {
    /**
     * Render TODO tree item
     */
    renderTodoItem(todo, isSelected = false) {
        const statusIcons = {
            'pending': '⚪',
            'in_progress': '🔵',
            'completed': '✅',
            'archived': '📦'
        };

        const priorityColors = {
            'low': 'text-gray-500',
            'medium': 'text-yellow-500',
            'high': 'text-red-500'
        };

        const statusIcon = statusIcons[todo.status] || '⚪';
        const priorityClass = priorityColors[todo.priority] || 'text-gray-500';

        const hasChildren = todo.children && todo.children.length > 0;
        const childrenHtml = hasChildren
            ? `<div class="ml-6 mt-1 space-y-1">${todo.children.map(child => this.renderTodoItem(child)).join('')}</div>`
            : '';

        return `
            <div class="todo-tree-item ${isSelected ? 'selected' : ''} rounded p-2 cursor-pointer" data-todo-id="${todo.id}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2 flex-1 min-w-0">
                        <span class="text-lg">${statusIcon}</span>
                        <span class="font-medium truncate">${this.escapeHtml(todo.title)}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="${priorityClass} text-xs">●</span>
                        ${todo.completion_percentage > 0 ? `<span class="text-xs text-gray-500">${todo.completion_percentage}%</span>` : ''}
                    </div>
                </div>
                ${childrenHtml}
            </div>
        `;
    },

    /**
     * Render activity timeline item
     */
    renderActivityItem(activity) {
        const activityIcons = {
            'reading': '📖',
            'coding': '💻',
            'video': '🎥',
            'browsing': '🌐',
            'communication': '💬',
            'design': '🎨',
            'general': '📄'
        };

        const icon = activityIcons[activity.activity_type] || '📄';
        // Add 'Z' suffix to treat as UTC if no timezone info
        let timestamp = activity.screenshot_timestamp;
        if (timestamp && !timestamp.endsWith('Z') && !timestamp.includes('+') && !timestamp.includes('-', 10)) {
            timestamp = timestamp + 'Z';
        }
        const timestampDisplay = new Date(timestamp).toLocaleString();
        const duration = activity.duration_minutes || 0;

        return `
            <div class="activity-timeline-item">
                <div class="activity-icon">${icon}</div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs text-gray-500">${timestampDisplay}</span>
                        <span class="text-xs text-gray-500">${duration}min</span>
                    </div>
                    <p class="text-sm text-gray-700 mb-2">${this.escapeHtml(activity.activity_description || activity.screenshot_description || 'No description')}</p>
                    ${activity.screenshot_filepath ? `
                        <button class="text-xs text-blue-600 hover:text-blue-800 view-screenshot" data-screenshot-id="${activity.screenshot_id}">
                            View Screenshot →
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * Render progress analysis section
     */
    renderProgressAnalysis(progress) {
        let html = '';

        // Summary
        if (progress.summary) {
            html += `<div id="analysis-summary" class="p-3 bg-blue-50 rounded-lg text-sm text-gray-700">${this.escapeHtml(progress.summary)}</div>`;
        }

        // Completed aspects
        if (progress.completed_aspects && progress.completed_aspects.length > 0) {
            html += `
                <div id="completed-aspects-container">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">✅ Completed</h4>
                    <ul id="completed-aspects-list" class="space-y-1">
                        ${progress.completed_aspects.map(aspect =>
                            `<li class="text-sm text-gray-600 flex items-start">
                                <span class="text-green-500 mr-2">•</span>
                                <span>${this.escapeHtml(aspect)}</span>
                            </li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }

        // Remaining aspects
        if (progress.remaining_aspects && progress.remaining_aspects.length > 0) {
            html += `
                <div id="remaining-aspects-container">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">⏳ Remaining</h4>
                    <ul id="remaining-aspects-list" class="space-y-1">
                        ${progress.remaining_aspects.map(aspect =>
                            `<li class="text-sm text-gray-600 flex items-start">
                                <span class="text-gray-400 mr-2">•</span>
                                <span>${this.escapeHtml(aspect)}</span>
                            </li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }

        // Next steps
        if (progress.next_steps && progress.next_steps.length > 0) {
            html += `
                <div id="next-steps-container">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">💡 Next Steps</h4>
                    <ul id="next-steps-list" class="space-y-1">
                        ${progress.next_steps.map(step =>
                            `<li class="text-sm text-gray-600 flex items-start">
                                <span class="text-blue-500 mr-2">→</span>
                                <span>${this.escapeHtml(step)}</span>
                            </li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }

        return html;
    },

    /**
     * Get status badge HTML
     */
    getStatusBadge(status) {
        const statusConfig = {
            'pending': { class: 'bg-gray-100 text-gray-700', text: 'Pending' },
            'in_progress': { class: 'bg-blue-100 text-blue-700', text: 'In Progress' },
            'completed': { class: 'bg-green-100 text-green-700', text: 'Completed' },
            'archived': { class: 'bg-purple-100 text-purple-700', text: 'Archived' }
        };

        const config = statusConfig[status] || statusConfig.pending;
        return `<span class="px-2 py-1 rounded-full ${config.class}">${config.text}</span>`;
    },

    /**
     * Get priority display
     */
    getPriorityDisplay(priority) {
        const priorityConfig = {
            'low': { icon: '🟢', text: 'Low Priority' },
            'medium': { icon: '🟡', text: 'Medium Priority' },
            'high': { icon: '🔴', text: 'High Priority' }
        };

        const config = priorityConfig[priority] || priorityConfig.medium;
        return `<span>${config.icon} ${config.text}</span>`;
    },

    /**
     * Format time display
     */
    formatTime(minutes) {
        if (!minutes) return '0 min';
        if (minutes < 60) return `${minutes} min`;
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
    },

    /**
     * Format date display
     */
    formatDate(dateString) {
        if (!dateString) return '';
        // Add 'Z' suffix to treat as UTC if no timezone info
        let isoString = dateString;
        if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
            isoString = dateString + 'Z';
        }
        const date = new Date(isoString);
        return date.toLocaleString();
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Show loading spinner
     */
    showLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600"></div>
                    <p class="text-gray-500 mt-2">Loading...</p>
                </div>
            `;
        }
    },

    /**
     * Show error message
     */
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8 text-red-600">
                    <div class="text-4xl mb-2">⚠️</div>
                    <p>${this.escapeHtml(message)}</p>
                </div>
            `;
        }
    },

    /**
     * Show success toast
     */
    showToast(message, type = 'success') {
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        };

        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

// Export
if (typeof window !== 'undefined') {
    window.TodoComponents = TodoComponents;
}
