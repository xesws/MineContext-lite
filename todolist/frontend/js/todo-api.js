/**
 * TodoAPI - API client for TodoList module
 */

const TodoAPI = {
    baseURL: '/api/todolist',

    /**
     * Generic API call wrapper
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    // ===== TODO Management =====

    /**
     * Get all TODOs
     */
    async getTodos(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/todos${queryString ? '?' + queryString : ''}`;
        return await this.request(endpoint);
    },

    /**
     * Get single TODO with details
     */
    async getTodo(todoId) {
        return await this.request(`/todos/${todoId}`);
    },

    /**
     * Create new TODO
     */
    async createTodo(data) {
        return await this.request('/todos', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * Update TODO
     */
    async updateTodo(todoId, data) {
        return await this.request(`/todos/${todoId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * Delete TODO
     */
    async deleteTodo(todoId) {
        return await this.request(`/todos/${todoId}`, {
            method: 'DELETE'
        });
    },

    // ===== Progress Analysis =====

    /**
     * Get TODO progress analysis
     */
    async getTodoProgress(todoId, forceReanalysis = false) {
        const endpoint = `/todos/${todoId}/progress${forceReanalysis ? '?force_reanalysis=true' : ''}`;
        return await this.request(endpoint);
    },

    /**
     * Trigger AI progress analysis
     */
    async analyzeTodo(todoId, forceReanalysis = false) {
        const endpoint = `/todos/${todoId}/analyze${forceReanalysis ? '?force_reanalysis=true' : ''}`;
        return await this.request(endpoint, {
            method: 'POST'
        });
    },

    /**
     * Get TODO activities timeline
     */
    async getTodoActivities(todoId, limit = null) {
        const endpoint = `/todos/${todoId}/activities${limit ? '?limit=' + limit : ''}`;
        return await this.request(endpoint);
    },

    // ===== Activity Management =====

    /**
     * Manually link screenshot to TODO
     */
    async linkActivity(data) {
        return await this.request('/activities/link', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * Unlink activity
     */
    async unlinkActivity(activityId) {
        return await this.request(`/activities/${activityId}`, {
            method: 'DELETE'
        });
    },

    /**
     * Get TODOs associated with screenshot
     */
    async getScreenshotTodos(screenshotId) {
        return await this.request(`/screenshots/${screenshotId}/todos`);
    },

    // ===== Statistics =====

    /**
     * Get TODO statistics
     */
    async getStats() {
        return await this.request('/stats');
    },

    // ===== Import/Export =====

    /**
     * Export TODOs to Markdown format
     */
    async exportMarkdown(status = null) {
        const endpoint = `/export/markdown${status ? '?status=' + status : ''}`;
        window.location.href = this.baseURL + endpoint;
    },

    /**
     * Export TODOs to JSON format
     */
    async exportJSON(status = null) {
        const endpoint = `/export/json${status ? '?status=' + status : ''}`;
        window.location.href = this.baseURL + endpoint;
    },

    /**
     * Import TODOs from Markdown
     */
    async importMarkdown(content) {
        return await this.request('/import/markdown', {
            method: 'POST',
            body: JSON.stringify({ content: content })
        });
    },

    /**
     * Import TODOs from JSON
     */
    async importJSON(data) {
        return await this.request('/import/json', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // ===== Smart Analyze Methods =====

    /**
     * Smart analyze TODO
     */
    async smartAnalyze(todoId) {
        return await this.request(`/todos/${todoId}/smart-analyze`, {
            method: 'POST'
        });
    },

    /**
     * Apply suggestions
     */
    async applySuggestions(todoId, suggestions) {
        return await this.request(`/todos/${todoId}/apply-suggestions`, {
            method: 'POST',
            body: JSON.stringify({ suggestions: suggestions })
        });
    },

    /**
     * AI decompose existing TODO
     */
    async decomposeTodo(todoId) {
        return await this.request(`/todos/${todoId}/decompose`, {
            method: 'POST'
        });
    },

    /**
     * Preview task decomposition (during creation)
     */
    async previewDecompose(title, description, estimatedHours) {
        return await this.request('/todos/preview-decompose', {
            method: 'POST',
            body: JSON.stringify({
                title: title,
                description: description || null,
                estimated_hours: estimatedHours || null
            })
        });
    }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.TodoAPI = TodoAPI;
}
