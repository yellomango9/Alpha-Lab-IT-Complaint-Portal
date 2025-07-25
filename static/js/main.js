/**
 * Alpha Lab IT Complaint Portal - Main JavaScript
 * Provides enhanced functionality for the complaint portal
 */

// Global variables
let charts = {};
let currentFilters = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form enhancements
    initializeFormEnhancements();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize charts if on dashboard
    if (document.querySelector('.chart-container')) {
        initializeCharts();
    }
    
    // Initialize file upload
    initializeFileUpload();
    
    // Initialize filters
    initializeFilters();
    
    // Initialize auto-refresh for dashboard
    initializeAutoRefresh();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form enhancements
 */
function initializeFormEnhancements() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
    
    // Form validation feedback
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Character counter for text inputs
    const textInputs = document.querySelectorAll('input[maxlength], textarea[maxlength]');
    textInputs.forEach(input => {
        const maxLength = input.getAttribute('maxlength');
        const counter = document.createElement('small');
        counter.className = 'form-text text-muted';
        counter.innerHTML = `<span class="char-count">0</span>/${maxLength} characters`;
        
        input.parentNode.appendChild(counter);
        
        input.addEventListener('input', function() {
            const currentLength = this.value.length;
            const charCountSpan = counter.querySelector('.char-count');
            charCountSpan.textContent = currentLength;
            
            if (currentLength > maxLength * 0.9) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                if (query.length >= 2 || query.length === 0) {
                    performSearch(query);
                }
            }, 300);
        });
    });
}

/**
 * Perform search operation
 */
function performSearch(query) {
    // Show loading state
    showLoadingSpinner();
    
    // Update URL with search parameter
    const url = new URL(window.location);
    if (query) {
        url.searchParams.set('search', query);
    } else {
        url.searchParams.delete('search');
    }
    
    // Update browser history and reload
    window.location.href = url.toString();
}

/**
 * Initialize charts for dashboard
 */
function initializeCharts() {
    // Status distribution chart
    const statusChart = document.getElementById('statusChart');
    if (statusChart) {
        loadChartData('status_distribution', statusChart);
    }
    
    // Monthly trends chart
    const trendsChart = document.getElementById('trendsChart');
    if (trendsChart) {
        loadChartData('monthly_trends', trendsChart);
    }
    
    // Department stats chart
    const departmentChart = document.getElementById('departmentChart');
    if (departmentChart) {
        loadChartData('department_stats', departmentChart);
    }
    
    // Urgency breakdown chart
    const urgencyChart = document.getElementById('urgencyChart');
    if (urgencyChart) {
        loadChartData('urgency_breakdown', urgencyChart);
    }
}

/**
 * Load chart data from API
 */
function loadChartData(chartType, canvas) {
    fetch(`/dashboard/api/chart-data/?type=${chartType}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Chart data error:', data.error);
                return;
            }
            
            createChart(canvas, data);
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
        });
}

/**
 * Create chart using Chart.js
 */
function createChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const chartId = canvas.id;
    
    // Destroy existing chart if it exists
    if (charts[chartId]) {
        charts[chartId].destroy();
    }
    
    let config = {
        type: data.type,
        data: {
            labels: data.labels,
            datasets: data.datasets || [{
                data: data.data,
                backgroundColor: data.backgroundColor || [
                    '#667eea', '#764ba2', '#f093fb', '#f5576c',
                    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    };
    
    // Customize options based on chart type
    if (data.type === 'line') {
        config.options.scales = {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0,0,0,0.1)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        };
    } else if (data.type === 'bar') {
        config.options.scales = {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0,0,0,0.1)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        };
    }
    
    charts[chartId] = new Chart(ctx, config);
}

/**
 * Initialize file upload functionality
 */
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const dropZone = input.closest('.file-upload-area');
        if (!dropZone) return;
        
        // Drag and drop functionality
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            input.files = files;
            updateFileList(input, files);
        });
        
        // File selection
        input.addEventListener('change', function() {
            updateFileList(this, this.files);
        });
    });
}

/**
 * Update file list display
 */
function updateFileList(input, files) {
    const fileList = input.parentNode.querySelector('.file-list');
    if (!fileList) return;
    
    fileList.innerHTML = '';
    
    Array.from(files).forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex justify-content-between align-items-center p-2 border rounded mb-2';
        
        fileItem.innerHTML = `
            <div>
                <i class="fas fa-file me-2"></i>
                <span class="file-name">${file.name}</span>
                <small class="text-muted ms-2">(${formatFileSize(file.size)})</small>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${index}">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        fileList.appendChild(fileItem);
    });
    
    // Add remove file functionality
    fileList.querySelectorAll('.remove-file').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.dataset.index);
            removeFile(input, index);
        });
    });
}

/**
 * Remove file from input
 */
function removeFile(input, index) {
    const dt = new DataTransfer();
    const files = input.files;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    input.files = dt.files;
    updateFileList(input, input.files);
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize filters
 */
function initializeFilters() {
    const filterForm = document.querySelector('.filter-form');
    if (!filterForm) return;
    
    const filterInputs = filterForm.querySelectorAll('select, input');
    
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Auto-submit filter form
            setTimeout(() => {
                filterForm.submit();
            }, 100);
        });
    });
    
    // Clear filters button
    const clearFiltersBtn = document.querySelector('.clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Clear all filter inputs
            filterInputs.forEach(input => {
                if (input.type === 'select-one') {
                    input.selectedIndex = 0;
                } else {
                    input.value = '';
                }
            });
            
            // Submit form to clear filters
            filterForm.submit();
        });
    }
}

/**
 * Initialize auto-refresh for dashboard
 */
function initializeAutoRefresh() {
    const dashboard = document.querySelector('.dashboard-container');
    if (!dashboard) return;
    
    // Auto-refresh every 5 minutes
    setInterval(() => {
        refreshDashboardData();
    }, 300000);
}

/**
 * Refresh dashboard data
 */
function refreshDashboardData() {
    // Refresh metric cards
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(card => {
        card.classList.add('loading');
    });
    
    // Refresh charts
    Object.keys(charts).forEach(chartId => {
        const canvas = document.getElementById(chartId);
        if (canvas) {
            const chartType = canvas.dataset.chartType;
            if (chartType) {
                loadChartData(chartType, canvas);
            }
        }
    });
    
    // Remove loading state after 2 seconds
    setTimeout(() => {
        metricCards.forEach(card => {
            card.classList.remove('loading');
        });
    }, 2000);
}

/**
 * Show loading spinner
 */
function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="spinner-border spinner-border-custom" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    
    document.body.appendChild(spinner);
    
    // Remove spinner after 3 seconds max
    setTimeout(() => {
        if (spinner.parentNode) {
            spinner.parentNode.removeChild(spinner);
        }
    }, 3000);
}

/**
 * Hide loading spinner
 */
function hideLoadingSpinner() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.parentNode.removeChild(spinner);
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 150);
        }
    }, 5000);
}

/**
 * Confirm action with modal
 */
function confirmAction(message, callback) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Action</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary confirm-btn">Confirm</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    modal.querySelector('.confirm-btn').addEventListener('click', function() {
        callback();
        bootstrapModal.hide();
    });
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

/**
 * Export table data as CSV
 */
function exportTableAsCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(col => {
            let cellData = col.textContent.trim();
            // Escape quotes and wrap in quotes if contains comma
            if (cellData.includes(',') || cellData.includes('"')) {
                cellData = '"' + cellData.replace(/"/g, '""') + '"';
            }
            rowData.push(cellData);
        });
        
        csv.push(rowData.join(','));
    });
    
    // Download CSV
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

/**
 * Print current page
 */
function printPage() {
    window.print();
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy to clipboard', 'error');
    });
}

// Expose functions globally for use in templates
window.AlphaLabPortal = {
    showNotification,
    confirmAction,
    exportTableAsCSV,
    printPage,
    copyToClipboard,
    showLoadingSpinner,
    hideLoadingSpinner
};