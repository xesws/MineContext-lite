/**
 * TodoManager - Main controller for TODO management UI
 */

const TodoManager = {
    // State
    state: {
        todos: [],
        selectedTodoId: null,
        filter: 'all',
        editingTodoId: null,
        pendingSuggestions: [],
        decomposedSubtasks: []
    },

    /**
     * Initialize the TODO manager
     */
    async init() {
        console.log('Initializing TodoManager...');

        // Set up event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadTodos();
    },

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadTodos();
        });

        // New TODO button
        document.getElementById('new-todo-btn').addEventListener('click', () => {
            this.showCreateModal();
        });

        // Filter select
        document.getElementById('filter-status').addEventListener('change', (e) => {
            this.state.filter = e.target.value;
            this.renderTodoTree();
        });

        // Modal form
        document.getElementById('todo-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTodo();
        });

        // Modal cancel button
        document.getElementById('cancel-modal-btn').addEventListener('click', () => {
            this.hideModal();
        });

        // Edit button
        document.getElementById('edit-todo-btn').addEventListener('click', () => {
            if (this.state.selectedTodoId) {
                this.showEditModal(this.state.selectedTodoId);
            }
        });

        // Delete button
        document.getElementById('delete-todo-btn').addEventListener('click', () => {
            if (this.state.selectedTodoId) {
                this.deleteTodo(this.state.selectedTodoId);
            }
        });

        // Reanalyze button
        document.getElementById('reanalyze-btn').addEventListener('click', async () => {
            if (this.state.selectedTodoId) {
                await this.analyzeTodo(this.state.selectedTodoId, true);
            }
        });

        // Close screenshot modal
        document.getElementById('close-screenshot-modal').addEventListener('click', () => {
            document.getElementById('screenshot-modal').classList.remove('active');
        });

        // Close modal on background click
        document.getElementById('todo-modal').addEventListener('click', (e) => {
            if (e.target.id === 'todo-modal') {
                this.hideModal();
            }
        });

        document.getElementById('screenshot-modal').addEventListener('click', (e) => {
            if (e.target.id === 'screenshot-modal') {
                document.getElementById('screenshot-modal').classList.remove('active');
            }
        });

        // Export/Import handlers
        // Export dropdown toggle
        document.getElementById('export-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('export-menu').classList.toggle('hidden');
        });

        // Close export menu when clicking outside
        document.addEventListener('click', () => {
            document.getElementById('export-menu').classList.add('hidden');
        });

        // Export Markdown
        document.getElementById('export-markdown-btn').addEventListener('click', async () => {
            const status = this.state.filter === 'all' ? null : this.state.filter;
            await TodoAPI.exportMarkdown(status);
            document.getElementById('export-menu').classList.add('hidden');
            TodoComponents.showToast('Exporting TODOs as Markdown...', 'info');
        });

        // Export JSON
        document.getElementById('export-json-btn').addEventListener('click', async () => {
            const status = this.state.filter === 'all' ? null : this.state.filter;
            await TodoAPI.exportJSON(status);
            document.getElementById('export-menu').classList.add('hidden');
            TodoComponents.showToast('Exporting TODOs as JSON...', 'info');
        });

        // Import button
        document.getElementById('import-btn').addEventListener('click', () => {
            document.getElementById('import-modal').classList.add('active');
        });

        // Import modal cancel
        document.getElementById('cancel-import-btn').addEventListener('click', () => {
            this.hideImportModal();
        });

        // Import modal confirm
        document.getElementById('confirm-import-btn').addEventListener('click', () => {
            this.importTodos();
        });

        // Import file handler
        document.getElementById('import-file').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                const content = await file.text();
                document.getElementById('import-content').value = content;
            }
        });

        // Close import modal on background click
        document.getElementById('import-modal').addEventListener('click', (e) => {
            if (e.target.id === 'import-modal') {
                this.hideImportModal();
            }
        });

        // Smart analyze button
        document.getElementById('smart-analyze-btn').addEventListener('click', async () => {
            if (this.state.selectedTodoId) {
                await this.smartAnalyze(this.state.selectedTodoId);
            }
        });

        // AI decompose button (in create form)
        document.getElementById('ai-decompose-btn').addEventListener('click', async () => {
            await this.previewDecompose();
        });

        // Suggestions modal handlers
        document.getElementById('close-suggestions-modal').addEventListener('click', () => {
            document.getElementById('suggestions-modal').classList.remove('active');
        });

        document.getElementById('cancel-suggestions-btn').addEventListener('click', () => {
            document.getElementById('suggestions-modal').classList.remove('active');
        });

        document.getElementById('apply-suggestions-btn').addEventListener('click', async () => {
            await this.applySuggestions();
        });

        // Close suggestions modal on background click
        document.getElementById('suggestions-modal').addEventListener('click', (e) => {
            if (e.target.id === 'suggestions-modal') {
                document.getElementById('suggestions-modal').classList.remove('active');
            }
        });
    },

    /**
     * Load all TODOs from API
     */
    async loadTodos() {
        try {
            TodoComponents.showLoading('todo-tree');

            const response = await TodoAPI.getTodos({ tree: false });
            this.state.todos = response.todos || [];

            console.log('Loaded TODOs:', this.state.todos.length);
            this.renderTodoTree();

        } catch (error) {
            console.error('Error loading TODOs:', error);
            TodoComponents.showError('todo-tree', 'Failed to load TODOs');
            TodoComponents.showToast('Failed to load TODOs', 'error');
        }
    },

    /**
     * Render TODO tree
     */
    renderTodoTree() {
        const container = document.getElementById('todo-tree');

        // Filter TODOs
        let filteredTodos = this.state.todos;
        if (this.state.filter !== 'all') {
            filteredTodos = this.state.todos.filter(todo => todo.status === this.state.filter);
        }

        if (filteredTodos.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500 py-8">No TODOs found</div>';
            return;
        }

        // Render TODO items
        container.innerHTML = filteredTodos
            .map(todo => TodoComponents.renderTodoItem(todo, todo.id === this.state.selectedTodoId))
            .join('');

        // Add click event listeners
        container.querySelectorAll('.todo-tree-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const todoId = parseInt(item.dataset.todoId);
                this.selectTodo(todoId);
            });
        });
    },

    /**
     * Select a TODO and load its details
     */
    async selectTodo(todoId) {
        this.state.selectedTodoId = todoId;
        this.renderTodoTree(); // Re-render to update selection
        await this.loadTodoDetails(todoId);
    },

    /**
     * Load TODO details
     */
    async loadTodoDetails(todoId) {
        try {
            // Show loading
            document.getElementById('empty-state').classList.add('hidden');
            document.getElementById('details-content').classList.remove('hidden');

            // Load TODO details
            const todo = await TodoAPI.getTodo(todoId);

            // Update basic info
            document.getElementById('detail-title').textContent = todo.title;
            document.getElementById('detail-status').innerHTML = TodoComponents.getStatusBadge(todo.status);
            document.getElementById('detail-priority').innerHTML = TodoComponents.getPriorityDisplay(todo.priority);
            document.getElementById('detail-time').textContent = TodoComponents.formatTime(todo.total_time_spent);
            document.getElementById('detail-description').textContent = todo.description || 'No description';

            // Update progress
            const progress = todo.completion_percentage || 0;
            document.getElementById('detail-progress-percent').textContent = `${progress}%`;
            document.getElementById('detail-progress-fill').style.width = `${progress}%`;

            // Render progress analysis if available
            if (todo.latest_progress) {
                document.getElementById('progress-analysis-section').classList.remove('hidden');
                const analysisHtml = TodoComponents.renderProgressAnalysis(todo.latest_progress);
                document.getElementById('progress-analysis-section').querySelector('.space-y-4').innerHTML = analysisHtml;
            } else {
                document.getElementById('progress-analysis-section').classList.add('hidden');
            }

            // Render activities
            const activitiesContainer = document.getElementById('activity-timeline');
            if (todo.activities && todo.activities.length > 0) {
                activitiesContainer.innerHTML = todo.activities
                    .map(activity => TodoComponents.renderActivityItem(activity))
                    .join('');

                // Add screenshot view handlers
                activitiesContainer.querySelectorAll('.view-screenshot').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        const screenshotId = btn.dataset.screenshotId;
                        this.viewScreenshot(screenshotId);
                    });
                });
            } else {
                activitiesContainer.innerHTML = '<div class="text-center text-gray-500 py-4">No activities yet</div>';
            }

        } catch (error) {
            console.error('Error loading TODO details:', error);
            TodoComponents.showToast('Failed to load TODO details', 'error');
        }
    },

    /**
     * Show create modal
     */
    showCreateModal() {
        this.state.editingTodoId = null;
        document.getElementById('modal-title').textContent = 'Create New TODO';
        document.getElementById('todo-form').reset();
        document.getElementById('todo-modal').classList.add('active');
    },

    /**
     * Show edit modal
     */
    async showEditModal(todoId) {
        try {
            this.state.editingTodoId = todoId;
            document.getElementById('modal-title').textContent = 'Edit TODO';

            const todo = await TodoAPI.getTodo(todoId);

            document.getElementById('todo-title').value = todo.title;
            document.getElementById('todo-description').value = todo.description || '';
            document.getElementById('todo-priority').value = todo.priority;
            document.getElementById('todo-estimated-hours').value = todo.estimated_hours || '';
            document.getElementById('todo-tags').value = todo.tags || '';

            document.getElementById('todo-modal').classList.add('active');
        } catch (error) {
            console.error('Error loading TODO for editing:', error);
            TodoComponents.showToast('Failed to load TODO', 'error');
        }
    },

    /**
     * Hide modal
     */
    hideModal() {
        document.getElementById('todo-modal').classList.remove('active');
        document.getElementById('todo-form').reset();
        this.state.editingTodoId = null;
    },

    /**
     * Save TODO (create or update)
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

            if (this.state.editingTodoId) {
                // Update existing TODO
                await TodoAPI.updateTodo(this.state.editingTodoId, formData);
                TodoComponents.showToast('TODO updated successfully', 'success');
            } else {
                // Create new TODO
                const result = await TodoAPI.createTodo(formData);
                TodoComponents.showToast('TODO created successfully', 'success');
                this.state.selectedTodoId = result.id;
            }

            this.hideModal();
            await this.loadTodos();

            if (this.state.selectedTodoId) {
                await this.loadTodoDetails(this.state.selectedTodoId);
            }

        } catch (error) {
            console.error('Error saving TODO:', error);
            TodoComponents.showToast('Failed to save TODO', 'error');
        }
    },

    /**
     * Delete TODO
     */
    async deleteTodo(todoId) {
        if (!confirm('Are you sure you want to delete this TODO? This will also delete all associated activities.')) {
            return;
        }

        try {
            await TodoAPI.deleteTodo(todoId);
            TodoComponents.showToast('TODO deleted successfully', 'success');

            this.state.selectedTodoId = null;
            document.getElementById('empty-state').classList.remove('hidden');
            document.getElementById('details-content').classList.add('hidden');

            await this.loadTodos();
        } catch (error) {
            console.error('Error deleting TODO:', error);
            TodoComponents.showToast('Failed to delete TODO', 'error');
        }
    },

    /**
     * Trigger AI progress analysis
     */
    async analyzeTodo(todoId, forceReanalysis = false) {
        try {
            TodoComponents.showToast('Analyzing TODO progress...', 'info');

            const progress = await TodoAPI.analyzeTodo(todoId, forceReanalysis);

            TodoComponents.showToast('Analysis complete', 'success');

            // Reload details to show updated analysis
            await this.loadTodoDetails(todoId);

        } catch (error) {
            console.error('Error analyzing TODO:', error);
            TodoComponents.showToast('Failed to analyze TODO', 'error');
        }
    },

    /**
     * View screenshot in modal
     */
    async viewScreenshot(screenshotId) {
        try {
            const modal = document.getElementById('screenshot-modal');
            const content = document.getElementById('screenshot-content');

            content.innerHTML = '<div class="text-center py-8">Loading...</div>';
            modal.classList.add('active');

            // Fetch screenshot details from main API
            const response = await fetch(`/api/screenshots/${screenshotId}`);
            const screenshot = await response.json();

            content.innerHTML = `
                <div class="space-y-4">
                    <img src="/${screenshot.filepath}" alt="Screenshot" class="w-full rounded-lg shadow">
                    <div class="text-sm text-gray-600">
                        <p><strong>Timestamp:</strong> ${TodoComponents.formatDate(screenshot.timestamp)}</p>
                        <p><strong>Description:</strong> ${screenshot.description || 'No description'}</p>
                    </div>
                </div>
            `;

        } catch (error) {
            console.error('Error loading screenshot:', error);
            document.getElementById('screenshot-content').innerHTML =
                '<div class="text-center text-red-600 py-8">Failed to load screenshot</div>';
        }
    },

    /**
     * Hide import modal
     */
    hideImportModal() {
        document.getElementById('import-modal').classList.remove('active');
        document.getElementById('import-file').value = '';
        document.getElementById('import-content').value = '';
    },

    /**
     * Import TODOs from file or text
     */
    async importTodos() {
        try {
            const content = document.getElementById('import-content').value.trim();
            const format = document.querySelector('input[name="import-format"]:checked').value;

            if (!content) {
                TodoComponents.showToast('Please provide content to import', 'error');
                return;
            }

            TodoComponents.showToast('Importing TODOs...', 'info');

            let result;
            if (format === 'markdown') {
                result = await TodoAPI.importMarkdown(content);
            } else if (format === 'json') {
                try {
                    const jsonData = JSON.parse(content);
                    result = await TodoAPI.importJSON(jsonData);
                } catch (e) {
                    TodoComponents.showToast('Invalid JSON format', 'error');
                    return;
                }
            }

            // Show result
            if (result.success) {
                TodoComponents.showToast(`Successfully imported ${result.imported_count} TODOs`, 'success');
                this.hideImportModal();
                await this.loadTodos();
            } else {
                const errorMsg = result.errors.length > 0
                    ? `Import completed with ${result.errors.length} errors`
                    : 'Import failed';
                TodoComponents.showToast(errorMsg, 'error');
                console.error('Import errors:', result.errors);
            }

        } catch (error) {
            console.error('Error importing TODOs:', error);
            TodoComponents.showToast('Failed to import TODOs', 'error');
        }
    },

    // ===== Smart Analyze Functions =====

    /**
     * Smart analyze TODO
     */
    async smartAnalyze(todoId) {
        try {
            TodoComponents.showToast('Analyzing...', 'info');

            const result = await TodoAPI.smartAnalyze(todoId);

            // Save suggestions to state
            this.state.pendingSuggestions = result.suggestions || [];

            // Show suggestions modal
            this.showSuggestionsModal(result);

            // Refresh TODO details to show auto-updates
            await this.loadTodoDetails(todoId);

        } catch (error) {
            console.error('Smart analyze error:', error);
            TodoComponents.showToast('Analysis failed: ' + error.message, 'error');
        }
    },

    /**
     * Show suggestions modal
     */
    showSuggestionsModal(result) {
        const modal = document.getElementById('suggestions-modal');

        // Show auto-applied updates
        if (result.auto_applied && result.auto_applied.length > 0) {
            const autoSection = document.getElementById('auto-updates-section');
            const autoList = document.getElementById('auto-updates-list');

            autoList.innerHTML = result.auto_applied.map(update => `
                <div class="p-2 bg-green-50 rounded text-sm text-gray-700">
                    ✓ ${this.escapeHtml(update.reason)}
                </div>
            `).join('');

            autoSection.classList.remove('hidden');
        } else {
            document.getElementById('auto-updates-section').classList.add('hidden');
        }

        // Show suggestions list
        const suggestionsList = document.getElementById('suggestions-list');

        if (result.suggestions && result.suggestions.length > 0) {
            suggestionsList.innerHTML = result.suggestions.map((suggestion, index) => {
                const icon = this.getSuggestionIcon(suggestion.type);
                const title = this.getSuggestionTitle(suggestion);

                return `
                    <div class="suggestion-item p-3 border rounded hover:bg-gray-50">
                        <label class="flex items-start cursor-pointer">
                            <input type="checkbox" checked class="mt-1 mr-3" data-index="${index}">
                            <div class="flex-1">
                                <div class="font-medium text-gray-900">
                                    ${icon} ${this.escapeHtml(title)}
                                </div>
                                <div class="text-sm text-gray-600 mt-1">${this.escapeHtml(suggestion.reason)}</div>
                                ${suggestion.confidence ? `<div class="text-xs text-gray-400 mt-1">
                                    Confidence: ${(suggestion.confidence * 100).toFixed(0)}%
                                </div>` : ''}
                            </div>
                        </label>
                    </div>
                `;
            }).join('');
        } else {
            suggestionsList.innerHTML = '<div class="text-center text-gray-500 py-4">No suggestions</div>';
        }

        modal.classList.add('active');
    },

    /**
     * Get suggestion icon
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
     * Get suggestion title
     */
    getSuggestionTitle(suggestion) {
        switch (suggestion.type) {
            case 'mark_complete':
                return 'Mark as Completed';
            case 'create_subtask':
                return `Create Subtask: ${suggestion.data.title}`;
            case 'update_status':
                return `Update Status to: ${suggestion.data.status}`;
            case 'update_progress':
                return `Update Progress to: ${suggestion.data.percentage}%`;
            default:
                return 'Apply Suggestion';
        }
    },

    /**
     * Apply selected suggestions
     */
    async applySuggestions() {
        try {
            // Get selected suggestions
            const checkboxes = document.querySelectorAll('#suggestions-list input[type="checkbox"]:checked');
            const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
            const selectedSuggestions = selectedIndices.map(i => this.state.pendingSuggestions[i]);

            if (selectedSuggestions.length === 0) {
                TodoComponents.showToast('Please select at least one suggestion', 'error');
                return;
            }

            TodoComponents.showToast('Applying suggestions...', 'info');

            // Call API
            await TodoAPI.applySuggestions(this.state.selectedTodoId, selectedSuggestions);

            // Close modal
            document.getElementById('suggestions-modal').classList.remove('active');

            // Refresh TODO
            await this.loadTodos();
            await this.loadTodoDetails(this.state.selectedTodoId);

            TodoComponents.showToast('Suggestions applied', 'success');

        } catch (error) {
            console.error('Apply suggestions error:', error);
            TodoComponents.showToast('Failed to apply: ' + error.message, 'error');
        }
    },

    /**
     * Preview task decomposition
     */
    async previewDecompose() {
        try {
            const title = document.getElementById('todo-title').value.trim();
            const description = document.getElementById('todo-description').value.trim();
            const estimatedHours = parseFloat(document.getElementById('todo-estimated-hours').value) || null;

            if (!title) {
                TodoComponents.showToast('Please enter a title first', 'error');
                return;
            }

            TodoComponents.showToast('AI is decomposing task...', 'info');

            const result = await TodoAPI.previewDecompose(title, description, estimatedHours);

            // Save subtasks to state
            this.state.decomposedSubtasks = result.suggested_subtasks || [];

            // Show preview
            this.showDecomposePreview(result.suggested_subtasks);

            TodoComponents.showToast('Decomposition complete', 'success');

        } catch (error) {
            console.error('Decompose error:', error);
            TodoComponents.showToast('Decomposition failed: ' + error.message, 'error');
        }
    },

    /**
     * Show decompose preview
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
                                ${subtask.estimated_hours ? `Est: ${subtask.estimated_hours}h` : ''}
                                ${subtask.priority ? ` | Priority: ${subtask.priority}` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

            preview.classList.remove('hidden');
        }
    },

    /**
     * Enhanced saveTodo to handle decomposed subtasks
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

            let todoId;

            // Edit or create
            if (this.state.editingTodoId) {
                // Update existing TODO
                await TodoAPI.updateTodo(this.state.editingTodoId, formData);
                todoId = this.state.editingTodoId;
                TodoComponents.showToast('TODO updated successfully', 'success');
            } else {
                // Create new TODO
                const result = await TodoAPI.createTodo(formData);
                todoId = result.id;

                // If there are decomposed subtasks, create them
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

                    TodoComponents.showToast(`TODO and ${selectedIndices.length} subtasks created`, 'success');
                } else {
                    TodoComponents.showToast('TODO created successfully', 'success');
                }
            }

            // Clear state
            this.state.decomposedSubtasks = [];
            document.getElementById('decompose-preview').classList.add('hidden');

            this.hideModal();
            await this.loadTodos();
            this.state.selectedTodoId = todoId;
            await this.loadTodoDetails(todoId);

        } catch (error) {
            console.error('Error saving TODO:', error);
            TodoComponents.showToast('Failed to save TODO: ' + error.message, 'error');
        }
    },

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TodoManager.init());
} else {
    TodoManager.init();
}

// Export
if (typeof window !== 'undefined') {
    window.TodoManager = TodoManager;
}
