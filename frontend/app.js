// MineContext-v2 Frontend Application

// Configuration
const API_BASE = '/api';
const ITEMS_PER_PAGE = 20;

// State
let state = {
    currentView: 'gallery',
    currentPage: 1,
    totalScreenshots: 0,
    screenshots: [],
    searchQuery: '',
    isSemanticSearch: false,
    currentLightboxIndex: -1,
    captureStatus: {
        is_running: false,
        interval_seconds: 5,
        screenshots_captured: 0,
        last_capture_time: null
    },
    embeddingStats: {
        with_embeddings: 0,
        pending_embeddings: 0
    }
};

// API Client
const API = {
    async getScreenshots(limit = ITEMS_PER_PAGE, offset = 0) {
        const response = await fetch(`${API_BASE}/screenshots?limit=${limit}&offset=${offset}`);
        if (!response.ok) throw new Error('Failed to fetch screenshots');
        return await response.json();
    },

    async getScreenshot(id) {
        const response = await fetch(`${API_BASE}/screenshots/${id}`);
        if (!response.ok) throw new Error('Failed to fetch screenshot');
        return await response.json();
    },

    async updateScreenshot(id, data) {
        const response = await fetch(`${API_BASE}/screenshots/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update screenshot');
        return await response.json();
    },

    async deleteScreenshot(id) {
        const response = await fetch(`${API_BASE}/screenshots/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete screenshot');
        return await response.json();
    },

    async searchScreenshots(query, limit = ITEMS_PER_PAGE, offset = 0) {
        const response = await fetch(`${API_BASE}/screenshots/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limit, offset })
        });
        if (!response.ok) throw new Error('Failed to search screenshots');
        return await response.json();
    },

    async getTimeline(limit = 100) {
        const response = await fetch(`${API_BASE}/timeline?limit=${limit}`);
        if (!response.ok) throw new Error('Failed to fetch timeline');
        return await response.json();
    },

    async startCapture() {
        const response = await fetch(`${API_BASE}/capture/start`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to start capture');
        return await response.json();
    },

    async stopCapture() {
        const response = await fetch(`${API_BASE}/capture/stop`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to stop capture');
        return await response.json();
    },

    async getCaptureStatus() {
        const response = await fetch(`${API_BASE}/capture/status`);
        if (!response.ok) throw new Error('Failed to get capture status');
        return await response.json();
    },

    async captureNow() {
        const response = await fetch(`${API_BASE}/capture/now`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to capture screenshot');
        return await response.json();
    },

    async getHealth() {
        const response = await fetch('/health');
        if (!response.ok) throw new Error('Health check failed');
        return await response.json();
    },

    async analyzeScreenshot(id, forceReanalysis = false) {
        const response = await fetch(`${API_BASE}/screenshots/${id}/analyze?force_reanalysis=${forceReanalysis}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to analyze screenshot');
        return await response.json();
    },

    async analyzeBatch(limit = 10) {
        const response = await fetch(`${API_BASE}/screenshots/analyze-batch?limit=${limit}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to analyze batch');
        return await response.json();
    },

    async extractTodos(screenshotId) {
        const response = await fetch(`${API_BASE}/screenshots/${screenshotId}/extract-todos`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to extract TODOs');
        return await response.json();
    },

    async extractTodosBatch(limit = 10, days = 7) {
        const response = await fetch(`${API_BASE}/todos/extract-batch?limit=${limit}&days=${days}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to extract TODOs in batch');
        return await response.json();
    },

    async semanticSearch(query, topK = 10, minSimilarity = null) {
        const body = { query, top_k: topK };
        if (minSimilarity !== null) body.min_similarity = minSimilarity;

        const response = await fetch(`${API_BASE}/search/semantic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error('Failed to perform semantic search');
        return await response.json();
    },

    async getSimilarScreenshots(screenshotId, topK = 10) {
        const response = await fetch(`${API_BASE}/screenshots/${screenshotId}/similar?top_k=${topK}`);
        if (!response.ok) throw new Error('Failed to get similar screenshots');
        return await response.json();
    },

    async getRelatedContexts(screenshotId, maxResults = 5) {
        const response = await fetch(`${API_BASE}/screenshots/${screenshotId}/related?max_results=${maxResults}`);
        if (!response.ok) throw new Error('Failed to get related contexts');
        return await response.json();
    },

    async generateEmbeddingsBatch(allUnprocessed = true, batchSize = null) {
        const body = { all_unprocessed: allUnprocessed };
        if (batchSize !== null) body.batch_size = batchSize;

        const response = await fetch(`${API_BASE}/embeddings/generate-batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error('Failed to generate embeddings');
        return await response.json();
    },

    async getEmbeddingStats() {
        const response = await fetch(`${API_BASE}/embeddings/stats`);
        if (!response.ok) throw new Error('Failed to get embedding stats');
        return await response.json();
    }
};

// UI Helpers
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    const bgColor = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500'
    }[type] || 'bg-gray-500';

    toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => container.removeChild(toast), 300);
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return '';
    // Add 'Z' suffix if timestamp doesn't have timezone info
    // This ensures JS treats it as UTC and converts to local time
    let isoString = dateString;
    if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
        isoString = dateString + 'Z';
    }
    const date = new Date(isoString);
    return date.toLocaleString();
}

function formatRelativeDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('gallery-view').classList.add('hidden');
    document.getElementById('timeline-view').classList.add('hidden');
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('pagination').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// Gallery View
function renderGalleryView() {
    const container = document.getElementById('gallery-view');
    container.innerHTML = '';

    if (state.screenshots.length === 0) {
        document.getElementById('empty-state').classList.remove('hidden');
        document.getElementById('pagination').classList.add('hidden');
        return;
    }

    document.getElementById('empty-state').classList.add('hidden');
    container.classList.remove('hidden');

    state.screenshots.forEach((screenshot, index) => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow cursor-pointer';
        card.onclick = () => openLightbox(index);

        const img = document.createElement('img');
        img.src = `/${screenshot.filepath}`;
        img.alt = screenshot.description || 'Screenshot';
        img.className = 'w-full h-48 object-cover';
        img.onerror = () => {
            img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
        };

        const content = document.createElement('div');
        content.className = 'p-4';

        const time = document.createElement('p');
        time.className = 'text-xs text-gray-500 mb-2';
        time.textContent = formatRelativeDate(screenshot.timestamp);

        const description = document.createElement('p');
        description.className = 'text-sm text-gray-700 line-clamp-2';
        description.textContent = screenshot.description || screenshot.window_title || 'No description';

        // Show similarity score if available (for semantic search results)
        if (screenshot.similarity !== undefined) {
            const similarity = document.createElement('div');
            similarity.className = 'mt-2 mb-1 flex items-center';
            const similarityBadge = document.createElement('span');
            similarityBadge.className = 'px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-800';
            similarityBadge.textContent = `${(screenshot.similarity * 100).toFixed(1)}% match`;
            similarity.appendChild(similarityBadge);
            content.appendChild(similarity);
        }

        if (screenshot.tags) {
            const tags = document.createElement('div');
            tags.className = 'mt-2 flex flex-wrap gap-1';
            screenshot.tags.split(',').forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded';
                tagSpan.textContent = tag.trim();
                tags.appendChild(tagSpan);
            });
            content.appendChild(tags);
        }

        content.appendChild(time);
        content.appendChild(description);
        card.appendChild(img);
        card.appendChild(content);
        container.appendChild(card);
    });

    updatePagination();
}

// Timeline View
function renderTimelineView() {
    const container = document.getElementById('timeline-view');
    container.innerHTML = '';

    showLoading();
    API.getTimeline().then(timeline => {
        hideLoading();

        if (timeline.length === 0) {
            document.getElementById('empty-state').classList.remove('hidden');
            return;
        }

        document.getElementById('empty-state').classList.add('hidden');
        container.classList.remove('hidden');

        timeline.forEach(day => {
            const daySection = document.createElement('div');
            daySection.className = 'space-y-4';

            const dayHeader = document.createElement('h2');
            dayHeader.className = 'text-xl font-bold text-gray-900 sticky top-16 bg-gray-50 py-2 z-10';
            dayHeader.textContent = new Date(day.date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            const count = document.createElement('span');
            count.className = 'ml-2 text-sm font-normal text-gray-500';
            count.textContent = `(${day.count} screenshot${day.count > 1 ? 's' : ''})`;
            dayHeader.appendChild(count);

            const grid = document.createElement('div');
            grid.className = 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4';

            day.screenshots.forEach(screenshot => {
                const item = document.createElement('div');
                item.className = 'bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow cursor-pointer';
                item.onclick = () => {
                    state.screenshots = day.screenshots;
                    const index = day.screenshots.findIndex(s => s.id === screenshot.id);
                    openLightbox(index);
                };

                const img = document.createElement('img');
                img.src = `/${screenshot.filepath}`;
                img.alt = screenshot.description || 'Screenshot';
                img.className = 'w-full h-32 object-cover';
                img.onerror = () => {
                    img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                };

                const time = document.createElement('p');
                time.className = 'text-xs text-gray-500 p-2';
                time.textContent = new Date(screenshot.timestamp).toLocaleTimeString();

                item.appendChild(img);
                item.appendChild(time);
                grid.appendChild(item);
            });

            daySection.appendChild(dayHeader);
            daySection.appendChild(grid);
            container.appendChild(daySection);
        });
    }).catch(error => {
        hideLoading();
        showToast('Failed to load timeline: ' + error.message, 'error');
    });
}

// Lightbox
function openLightbox(index) {
    state.currentLightboxIndex = index;
    updateLightbox();
    document.getElementById('lightbox').classList.remove('hidden');
}

function closeLightbox() {
    document.getElementById('lightbox').classList.add('hidden');
}

function updateLightbox() {
    const screenshot = state.screenshots[state.currentLightboxIndex];
    if (!screenshot) return;

    document.getElementById('lightbox-image').src = `/${screenshot.filepath}`;
    document.getElementById('lightbox-time').textContent = formatDate(screenshot.timestamp);
    document.getElementById('lightbox-description').textContent = screenshot.description || 'No description';
    document.getElementById('lightbox-tags').textContent = screenshot.tags || 'No tags';
    document.getElementById('lightbox-edit-description').value = screenshot.description || '';
}

function lightboxNext() {
    if (state.currentLightboxIndex < state.screenshots.length - 1) {
        state.currentLightboxIndex++;
        updateLightbox();
    }
}

function lightboxPrev() {
    if (state.currentLightboxIndex > 0) {
        state.currentLightboxIndex--;
        updateLightbox();
    }
}

async function lightboxSave() {
    const screenshot = state.screenshots[state.currentLightboxIndex];
    const description = document.getElementById('lightbox-edit-description').value;

    try {
        await API.updateScreenshot(screenshot.id, { description });
        screenshot.description = description;
        showToast('Screenshot updated successfully', 'success');
        updateLightbox();
        if (state.currentView === 'gallery') {
            renderGalleryView();
        }
    } catch (error) {
        showToast('Failed to update screenshot: ' + error.message, 'error');
    }
}

async function lightboxDelete() {
    if (!confirm('Are you sure you want to delete this screenshot?')) return;

    const screenshot = state.screenshots[state.currentLightboxIndex];

    try {
        await API.deleteScreenshot(screenshot.id);
        showToast('Screenshot deleted successfully', 'success');
        state.screenshots.splice(state.currentLightboxIndex, 1);
        closeLightbox();
        await loadScreenshots();
    } catch (error) {
        showToast('Failed to delete screenshot: ' + error.message, 'error');
    }
}

async function lightboxAnalyze() {
    const screenshot = state.screenshots[state.currentLightboxIndex];
    const analyzeBtn = document.getElementById('lightbox-analyze');

    try {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        showToast('Analyzing screenshot with AI...', 'info');

        const result = await API.analyzeScreenshot(screenshot.id, false);

        if (result.success) {
            screenshot.description = result.description;
            screenshot.tags = result.tags;
            screenshot.analyzed = true;
            showToast('Screenshot analyzed successfully!', 'success');
            updateLightbox();
            if (state.currentView === 'gallery') {
                renderGalleryView();
            }
        } else {
            showToast('AI analysis failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Failed to analyze screenshot: ' + error.message, 'error');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze with AI';
    }
}

async function analyzeBatch() {
    const analyzeBtn = document.getElementById('btn-analyze-batch');

    try {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        showToast('Starting batch AI analysis...', 'info');

        const result = await API.analyzeBatch(10);

        if (result.success) {
            showToast(
                `Batch analysis complete! Analyzed: ${result.analyzed_count}, Failed: ${result.failed_count}`,
                result.failed_count === 0 ? 'success' : 'warning'
            );
            await loadScreenshots();
        } else {
            showToast('Batch analysis failed', 'error');
        }
    } catch (error) {
        showToast('Failed to start batch analysis: ' + error.message, 'error');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Batch (AI)';
    }
}

async function generateEmbeddings() {
    const generateBtn = document.getElementById('btn-generate-embeddings');

    try {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        showToast('Generating embeddings for analyzed screenshots...', 'info');

        const result = await API.generateEmbeddingsBatch(true);

        if (result.success) {
            showToast(
                `Embeddings generated! Processed: ${result.processed_count}, Failed: ${result.failed_count}`,
                result.failed_count === 0 ? 'success' : 'warning'
            );
            await updateEmbeddingStats();
        } else {
            showToast('Embedding generation failed: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Failed to generate embeddings: ' + error.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Embeddings';
    }
}

async function updateEmbeddingStats() {
    try {
        const stats = await API.getEmbeddingStats();
        state.embeddingStats = stats;
        document.getElementById('embedding-count').textContent =
            `${stats.with_embeddings}/${stats.analyzed_screenshots}`;
    } catch (error) {
        console.error('Failed to update embedding stats:', error);
    }
}

async function extractTodosBatch() {
    const extractBtn = document.getElementById('btn-extract-todos');

    try {
        extractBtn.disabled = true;
        extractBtn.textContent = 'Extracting...';
        showToast('Extracting TODOs from recent screenshots...', 'info');

        const result = await API.extractTodosBatch(10, 7);

        if (result.success) {
            showToast(
                `TODO extraction complete! Found ${result.total_todos_extracted} TODOs from ${result.processed_screenshots} screenshots`,
                result.total_todos_extracted > 0 ? 'success' : 'info'
            );
        } else {
            showToast('TODO extraction failed', 'error');
        }
    } catch (error) {
        showToast('Failed to extract TODOs: ' + error.message, 'error');
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract TODOs (AI)';
    }
}

async function lightboxExtractTodos() {
    const screenshot = state.screenshots[state.currentLightboxIndex];
    const extractBtn = document.getElementById('lightbox-extract-todos');

    try {
        extractBtn.disabled = true;
        extractBtn.textContent = 'Extracting...';
        showToast('Extracting TODOs from screenshot...', 'info');

        const result = await API.extractTodos(screenshot.id);

        if (result.success) {
            if (result.stored_count > 0) {
                showToast(
                    `Found and saved ${result.stored_count} TODO(s)! Check the TODOs page to view them.`,
                    'success'
                );
            } else {
                showToast('No TODOs found in this screenshot', 'info');
            }
        } else {
            showToast('TODO extraction failed: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('Failed to extract TODOs: ' + error.message, 'error');
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract TODOs';
    }
}

async function lightboxFindSimilar() {
    const screenshot = state.screenshots[state.currentLightboxIndex];
    const findSimilarBtn = document.getElementById('lightbox-find-similar');
    const relatedSection = document.getElementById('lightbox-related-section');
    const relatedContainer = document.getElementById('lightbox-related-contexts');

    try {
        findSimilarBtn.disabled = true;
        findSimilarBtn.textContent = 'Finding...';
        showToast('Finding similar screenshots...', 'info');

        const similar = await API.getSimilarScreenshots(screenshot.id, 5);

        if (similar.length === 0) {
            showToast('No similar screenshots found. Try generating embeddings first.', 'warning');
            return;
        }

        // Clear previous results
        relatedContainer.innerHTML = '';

        // Render similar screenshots
        similar.forEach(item => {
            const relatedItem = document.createElement('div');
            relatedItem.className = 'p-2 bg-gray-800 rounded cursor-pointer hover:bg-gray-700 transition-colors';
            relatedItem.onclick = async () => {
                // Load the similar screenshot
                const similarScreenshot = await API.getScreenshot(item.screenshot_id);
                // Find it in current screenshots or add it
                const existingIndex = state.screenshots.findIndex(s => s.id === item.screenshot_id);
                if (existingIndex !== -1) {
                    state.currentLightboxIndex = existingIndex;
                } else {
                    state.screenshots.push(similarScreenshot);
                    state.currentLightboxIndex = state.screenshots.length - 1;
                }
                updateLightbox();
            };

            const similarity = document.createElement('div');
            similarity.className = 'flex items-center justify-between mb-1';

            const similarityBadge = document.createElement('span');
            similarityBadge.className = 'text-xs font-medium text-green-400';
            similarityBadge.textContent = `${(item.similarity * 100).toFixed(1)}% match`;

            const timestamp = document.createElement('span');
            timestamp.className = 'text-xs text-gray-400';
            timestamp.textContent = item.timestamp ? formatRelativeDate(item.timestamp) : '';

            similarity.appendChild(similarityBadge);
            similarity.appendChild(timestamp);

            const desc = document.createElement('p');
            desc.className = 'text-xs text-gray-300 line-clamp-2';
            desc.textContent = item.description || 'No description';

            relatedItem.appendChild(similarity);
            relatedItem.appendChild(desc);
            relatedContainer.appendChild(relatedItem);
        });

        relatedSection.classList.remove('hidden');
        showToast(`Found ${similar.length} similar screenshots`, 'success');

    } catch (error) {
        showToast('Failed to find similar screenshots: ' + error.message, 'error');
    } finally {
        findSimilarBtn.disabled = false;
        findSimilarBtn.textContent = 'Find Similar';
    }
}

// Pagination
function updatePagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(state.totalScreenshots / ITEMS_PER_PAGE);

    if (totalPages <= 1) {
        pagination.classList.add('hidden');
        return;
    }

    pagination.classList.remove('hidden');
    document.getElementById('page-info').textContent = `Page ${state.currentPage} of ${totalPages}`;
    document.getElementById('btn-prev-page').disabled = state.currentPage === 1;
    document.getElementById('btn-next-page').disabled = state.currentPage >= totalPages;
}

async function goToPage(page) {
    state.currentPage = page;
    await loadScreenshots();
}

// Load Screenshots
async function loadScreenshots() {
    showLoading();

    try {
        let data;
        const offset = (state.currentPage - 1) * ITEMS_PER_PAGE;

        if (state.searchQuery && state.isSemanticSearch) {
            // Semantic search
            const result = await API.semanticSearch(state.searchQuery, ITEMS_PER_PAGE);
            // Transform semantic search results to match screenshot format
            const screenshotIds = result.results.map(r => r.screenshot_id);

            // Fetch full screenshot details for each result
            const screenshots = await Promise.all(
                result.results.map(async (r) => {
                    const screenshot = await API.getScreenshot(r.screenshot_id);
                    screenshot.similarity = r.similarity; // Add similarity score
                    return screenshot;
                })
            );

            state.screenshots = screenshots;
            state.totalScreenshots = result.count;
        } else if (state.searchQuery) {
            // Regular text search
            data = await API.searchScreenshots(state.searchQuery, ITEMS_PER_PAGE, offset);
            state.screenshots = data.screenshots;
            state.totalScreenshots = data.total;
        } else {
            // No search - load all
            data = await API.getScreenshots(ITEMS_PER_PAGE, offset);
            state.screenshots = data.screenshots;
            state.totalScreenshots = data.total;
        }

        hideLoading();

        if (state.currentView === 'gallery') {
            renderGalleryView();
        } else {
            renderTimelineView();
        }

        document.getElementById('screenshot-count').textContent = state.totalScreenshots;
    } catch (error) {
        hideLoading();
        showToast('Failed to load screenshots: ' + error.message, 'error');
    }
}

// Capture Controls
async function updateCaptureStatus() {
    try {
        state.captureStatus = await API.getCaptureStatus();

        const statusBadge = document.getElementById('status-badge');
        const statusText = document.getElementById('capture-status');
        const startBtn = document.getElementById('btn-start-capture');
        const stopBtn = document.getElementById('btn-stop-capture');

        if (state.captureStatus.is_running) {
            statusBadge.textContent = 'Capturing';
            statusBadge.className = 'ml-3 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800';
            statusText.textContent = 'Running';
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusBadge.textContent = 'Stopped';
            statusBadge.className = 'ml-3 px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800';
            statusText.textContent = 'Stopped';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    } catch (error) {
        console.error('Failed to update capture status:', error);
    }
}

async function startCapture() {
    try {
        await API.startCapture();
        showToast('Screenshot capture started', 'success');
        await updateCaptureStatus();
    } catch (error) {
        showToast('Failed to start capture: ' + error.message, 'error');
    }
}

async function stopCapture() {
    try {
        await API.stopCapture();
        showToast('Screenshot capture stopped', 'success');
        await updateCaptureStatus();
    } catch (error) {
        showToast('Failed to stop capture: ' + error.message, 'error');
    }
}

async function captureNow() {
    try {
        const result = await API.captureNow();
        if (result.success) {
            showToast('Screenshot captured successfully', 'success');
            setTimeout(() => loadScreenshots(), 1000);
        } else {
            showToast('Failed to capture screenshot', 'error');
        }
    } catch (error) {
        showToast('Failed to capture screenshot: ' + error.message, 'error');
    }
}

// Search
function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    const isSemanticSearch = document.getElementById('semantic-search-toggle').checked;

    state.searchQuery = query;
    state.isSemanticSearch = isSemanticSearch;
    state.currentPage = 1;

    if (query) {
        showToast(
            isSemanticSearch ? 'Performing semantic search...' : 'Searching...',
            'info'
        );
    }

    loadScreenshots();
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    document.getElementById('semantic-search-toggle').checked = false;
    state.searchQuery = '';
    state.isSemanticSearch = false;
    state.currentPage = 1;
    loadScreenshots();
}

// View Switching
function switchView(view) {
    state.currentView = view;

    const galleryBtn = document.getElementById('view-gallery');
    const timelineBtn = document.getElementById('view-timeline');
    const galleryView = document.getElementById('gallery-view');
    const timelineView = document.getElementById('timeline-view');

    if (view === 'gallery') {
        galleryBtn.classList.add('border-blue-500');
        galleryBtn.classList.remove('border-transparent');
        timelineBtn.classList.remove('border-blue-500');
        timelineBtn.classList.add('border-transparent');
        timelineView.classList.add('hidden');
        galleryView.classList.remove('hidden');
        renderGalleryView();
    } else {
        timelineBtn.classList.add('border-blue-500');
        timelineBtn.classList.remove('border-transparent');
        galleryBtn.classList.remove('border-blue-500');
        galleryBtn.classList.add('border-transparent');
        galleryView.classList.add('hidden');
        timelineView.classList.remove('hidden');
        renderTimelineView();
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // View switching
    document.getElementById('view-gallery').addEventListener('click', () => switchView('gallery'));
    document.getElementById('view-timeline').addEventListener('click', () => switchView('timeline'));

    // Capture controls
    document.getElementById('btn-start-capture').addEventListener('click', startCapture);
    document.getElementById('btn-stop-capture').addEventListener('click', stopCapture);
    document.getElementById('btn-capture-now').addEventListener('click', captureNow);
    document.getElementById('btn-analyze-batch').addEventListener('click', analyzeBatch);
    document.getElementById('btn-generate-embeddings').addEventListener('click', generateEmbeddings);
    document.getElementById('btn-extract-todos').addEventListener('click', extractTodosBatch);

    // Search
    document.getElementById('btn-search').addEventListener('click', performSearch);
    document.getElementById('btn-clear-search').addEventListener('click', clearSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    // Pagination
    document.getElementById('btn-prev-page').addEventListener('click', () => {
        if (state.currentPage > 1) goToPage(state.currentPage - 1);
    });
    document.getElementById('btn-next-page').addEventListener('click', () => {
        goToPage(state.currentPage + 1);
    });

    // Lightbox
    document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
    document.getElementById('lightbox-next').addEventListener('click', lightboxNext);
    document.getElementById('lightbox-prev').addEventListener('click', lightboxPrev);
    document.getElementById('lightbox-save').addEventListener('click', lightboxSave);
    document.getElementById('lightbox-delete').addEventListener('click', lightboxDelete);
    document.getElementById('lightbox-analyze').addEventListener('click', lightboxAnalyze);
    document.getElementById('lightbox-extract-todos').addEventListener('click', lightboxExtractTodos);
    document.getElementById('lightbox-find-similar').addEventListener('click', lightboxFindSimilar);

    // Close lightbox on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !document.getElementById('lightbox').classList.contains('hidden')) {
            closeLightbox();
        }
        if (!document.getElementById('lightbox').classList.contains('hidden')) {
            if (e.key === 'ArrowRight') lightboxNext();
            if (e.key === 'ArrowLeft') lightboxPrev();
        }
    });

    // Close lightbox on background click
    document.getElementById('lightbox').addEventListener('click', (e) => {
        if (e.target.id === 'lightbox') closeLightbox();
    });

    // Initial load
    loadScreenshots();
    updateCaptureStatus();
    updateEmbeddingStats();

    // Auto-refresh status every 5 seconds
    setInterval(updateCaptureStatus, 5000);
    setInterval(updateEmbeddingStats, 10000);

    // Auto-refresh screenshots every 30 seconds if capture is running
    setInterval(() => {
        if (state.captureStatus.is_running) {
            loadScreenshots();
        }
    }, 30000);
});
