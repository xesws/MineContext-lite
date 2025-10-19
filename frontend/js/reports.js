/**
 * Reports JavaScript for MineContext-v2
 */

const API_BASE = window.location.origin + '/api';

let currentReportContent = '';

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadRecentReports();
    setDefaultDate();
});

function setDefaultDate() {
    const dateInput = document.getElementById('report-date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
}

function setupEventListeners() {
    document.getElementById('generate-btn').addEventListener('click', generateReport);
    document.getElementById('download-btn').addEventListener('click', downloadReport);
}

async function generateReport() {
    const reportType = document.getElementById('report-type').value;
    const reportDate = document.getElementById('report-date').value;

    if (!reportDate) {
        showNotification('Please select a date', 'error');
        return;
    }

    const generateBtn = document.getElementById('generate-btn');
    const loadingEl = document.getElementById('generate-loading');

    generateBtn.classList.add('hidden');
    loadingEl.classList.remove('hidden');

    try {
        const endpoint = reportType === 'daily' ? '/reports/daily' : '/reports/weekly';
        const params = new URLSearchParams({ date: reportDate });

        const response = await fetch(`${API_BASE}${endpoint}?${params}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to generate report');
        }

        const data = await response.json();

        displayReport(data.content);
        currentReportContent = data.content;

        if (data.cached) {
            showNotification('Loaded cached report', 'success');
        } else {
            showNotification('Report generated successfully', 'success');
        }

        // Refresh recent reports list
        loadRecentReports();

    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('Failed to generate report', 'error');
    } finally {
        generateBtn.classList.remove('hidden');
        loadingEl.classList.add('hidden');
    }
}

function displayReport(markdownContent) {
    const contentEl = document.getElementById('report-content');
    const downloadBtn = document.getElementById('download-btn');

    // Convert Markdown to HTML using marked.js
    contentEl.innerHTML = marked.parse(markdownContent);

    // Show download button
    downloadBtn.classList.remove('hidden');
}

async function loadRecentReports() {
    try {
        const response = await fetch(`${API_BASE}/reports/list?limit=10`);

        if (!response.ok) {
            throw new Error('Failed to fetch reports');
        }

        const data = await response.json();

        const listEl = document.getElementById('reports-list');

        if (data.reports.length === 0) {
            listEl.innerHTML = '<p class="text-sm text-gray-500">No reports generated yet</p>';
            return;
        }

        listEl.innerHTML = data.reports.map(report => `
            <div class="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                 onclick="loadReport(${report.id})">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-900">
                            ${report.report_type === 'daily' ? '📅' : '📊'}
                            ${report.report_type.charAt(0).toUpperCase() + report.report_type.slice(1)} Report
                        </p>
                        <p class="text-xs text-gray-500">${report.period_start}</p>
                    </div>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading recent reports:', error);
    }
}

async function loadReport(reportId) {
    try {
        const response = await fetch(`${API_BASE}/reports/${reportId}`);

        if (!response.ok) {
            throw new Error('Failed to load report');
        }

        const report = await response.json();

        displayReport(report.content);
        currentReportContent = report.content;

        showNotification('Report loaded', 'success');

    } catch (error) {
        console.error('Error loading report:', error);
        showNotification('Failed to load report', 'error');
    }
}

function downloadReport() {
    if (!currentReportContent) {
        showNotification('No report to download', 'error');
        return;
    }

    const blob = new Blob([currentReportContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);

    showNotification('Report downloaded', 'success');
}

function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-100 border-green-400 text-green-700',
        error: 'bg-red-100 border-red-400 text-red-700',
        info: 'bg-blue-100 border-blue-400 text-blue-700'
    };

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} px-4 py-3 rounded border z-50`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}
