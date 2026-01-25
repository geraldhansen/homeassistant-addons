// S3 Backup Web UI JavaScript

// Global state
let appState = {
    status: 'unknown',
    lastUpdate: null,
    refreshInterval: null
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('Initializing S3 Backup Web UI...');
    
    // Update status indicator initially
    updateStatusIndicator('unknown', 'Loading...');
    
    // Set up auto-refresh if on dashboard or backups page
    const currentPage = window.location.pathname;
    if (currentPage === '/' || currentPage === '/backups') {
        startAutoRefresh();
    }
    
    // Set up global error handling
    window.addEventListener('unhandledrejection', handleGlobalError);
    window.addEventListener('error', handleGlobalError);
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        initializeTooltips();
    }
}

function updateStatusIndicator(status, message) {
    const indicator = document.getElementById('status-indicator');
    if (!indicator) return;
    
    const statusClasses = {
        success: 'bg-success',
        error: 'bg-danger',
        warning: 'bg-warning',
        info: 'bg-info',
        unknown: 'bg-secondary'
    };
    
    const statusIcons = {
        success: 'bi-check-circle',
        error: 'bi-x-circle',
        warning: 'bi-exclamation-triangle',
        info: 'bi-info-circle',
        unknown: 'bi-question-circle'
    };
    
    // Remove all status classes
    Object.values(statusClasses).forEach(cls => indicator.classList.remove(cls));
    
    // Add current status class
    indicator.className = `badge ${statusClasses[status] || statusClasses.unknown}`;
    
    // Update content
    const icon = statusIcons[status] || statusIcons.unknown;
    indicator.innerHTML = `<i class="bi ${icon}"></i> ${message}`;
    
    // Update global state
    appState.status = status;
    appState.lastUpdate = new Date();
}

function startAutoRefresh() {
    // Clear existing interval
    if (appState.refreshInterval) {
        clearInterval(appState.refreshInterval);
    }
    
    // Set up new interval (every 30 seconds)
    appState.refreshInterval = setInterval(() => {
        refreshData();
    }, 30000);
    
    console.log('Auto-refresh started');
}

function stopAutoRefresh() {
    if (appState.refreshInterval) {
        clearInterval(appState.refreshInterval);
        appState.refreshInterval = null;
    }
    console.log('Auto-refresh stopped');
}

function refreshData() {
    // This function will be overridden by page-specific scripts
    // but provides a fallback for status checking
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const status = data.s3_connected ? 'success' : 'error';
            const message = data.s3_connected ? 'Connected' : 'S3 Error';
            updateStatusIndicator(status, message);
        })
        .catch(error => {
            console.error('Error refreshing data:', error);
            updateStatusIndicator('error', 'Connection Error');
        });
}

function handleGlobalError(event) {
    console.error('Global error:', event.error || event.reason);
    updateStatusIndicator('error', 'Application Error');
}

function initializeTooltips() {
    try {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } catch (error) {
        console.warn('Could not initialize tooltips:', error);
    }
}

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return {
            short: date.toLocaleDateString(),
            long: date.toLocaleString(),
            iso: date.toISOString(),
            relative: getRelativeTime(date)
        };
    } catch (error) {
        return {
            short: 'Invalid Date',
            long: 'Invalid Date',
            iso: '',
            relative: 'Unknown'
        };
    }
}

function getRelativeTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    const diffWeeks = Math.floor(diffDays / 7);
    const diffMonths = Math.floor(diffDays / 30);
    
    if (diffMonths > 0) return `${diffMonths} month${diffMonths > 1 ? 's' : ''} ago`;
    if (diffWeeks > 0) return `${diffWeeks} week${diffWeeks > 1 ? 's' : ''} ago`;
    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffMins > 0) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    return 'Just now';
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(endpoint, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error(`API call failed for ${endpoint}:`, error);
        return { success: false, error: error.message };
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(notification, container.firstChild);
    }
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Loading state management
function setLoading(elementId, isLoading = true) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (isLoading) {
        element.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">Loading...</p>
            </div>
        `;
    }
}

// Form validation helpers
function validateRequired(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

function clearValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const fields = form.querySelectorAll('.is-invalid');
    fields.forEach(field => field.classList.remove('is-invalid'));
}

// Modal helpers
function showModal(modalId, options = {}) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return null;
    
    const modal = new bootstrap.Modal(modalElement, options);
    modal.show();
    return modal;
}

function hideModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    
    const modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
        modal.hide();
    }
}

// Confirmation dialog
function confirmAction(message, callback, options = {}) {
    const defaults = {
        title: 'Confirm Action',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        confirmClass: 'btn-primary'
    };
    
    const settings = { ...defaults, ...options };
    
    if (confirm(`${settings.title}\n\n${message}`)) {
        callback();
    }
}

// Export utility functions to global scope
window.S3Backup = {
    updateStatusIndicator,
    startAutoRefresh,
    stopAutoRefresh,
    refreshData,
    formatBytes,
    formatDate,
    getRelativeTime,
    apiCall,
    showNotification,
    setLoading,
    validateRequired,
    clearValidation,
    showModal,
    hideModal,
    confirmAction
};

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});

console.log('S3 Backup Web UI initialized');