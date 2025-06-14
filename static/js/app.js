// B1T Web Analyzer JavaScript

// Global variables
let statusUpdateInterval = null;
let isAnalysisRunning = false;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Start status monitoring
    startStatusMonitoring();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize auto-refresh for running jobs
    initializeAutoRefresh();
    
    // Add fade-in animation to cards
    addFadeInAnimations();
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Status monitoring
function startStatusMonitoring() {
    updateStatus();
    statusUpdateInterval = setInterval(updateStatus, 3000); // Update every 3 seconds
}

function updateStatus() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateStatusIndicators(data);
            updateProgressBars(data);
            
            // Check if analysis state changed
            if (isAnalysisRunning !== data.running) {
                isAnalysisRunning = data.running;
                handleAnalysisStateChange(data.running);
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            updateStatusIndicators({
                running: false,
                progress: 0,
                current_block: 'N/A',
                total_blocks: 'N/A',
                error: 'Connection Error'
            });
        });
}

function updateStatusIndicators(data) {
    // Update navbar status indicator
    const navbarStatus = document.getElementById('status-indicator');
    if (navbarStatus) {
        if (data.running) {
            navbarStatus.innerHTML = '<i class="fas fa-spinner fa-spin me-1 text-warning"></i>Analysis Running';
        } else if (data.error) {
            navbarStatus.innerHTML = '<i class="fas fa-exclamation-triangle me-1 text-danger"></i>Error';
        } else {
            navbarStatus.innerHTML = '<i class="fas fa-circle text-success me-1"></i>Ready';
        }
    }
    
    // Update dashboard status cards
    updateElement('current-status', data.running ?
            '<i class="fas fa-spinner fa-spin me-1"></i>Running' :
            '<i class="fas fa-check-circle me-1"></i>Ready'
    );
    updateElement('progress-text', `${data.progress || 0}%`);
    updateElement('current-block', data.current_block || 'N/A');
    updateElement('total-blocks', data.total_blocks || 'N/A');
}

function updateProgressBars(data) {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const progress = data.progress || 0;
        bar.style.width = `${progress}%`;
        bar.textContent = `${progress}%`;
        
        if (data.running) {
            bar.classList.add('progress-bar-striped', 'progress-bar-animated');
        } else {
            bar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        }
    });
    
    // Update progress details
    const progressDetails = document.querySelectorAll('#progress-details');
    progressDetails.forEach(detail => {
        if (data.running && data.current_block && data.total_blocks) {
            detail.textContent = `Block ${data.current_block} von ${data.total_blocks}`;
        }
    });
}

function handleAnalysisStateChange(isRunning) {
    if (!isRunning) {
        // Analysis completed or stopped
        setTimeout(() => {
            // Reload page to show updated results
            if (window.location.pathname.includes('/job/') || window.location.pathname === '/') {
                window.location.reload();
            }
        }, 2000);
    }
}

// Form validations
function initializeFormValidations() {
    // Analysis form validation
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', validateAnalysisForm);
    }
    
    // Config form validation
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', validateConfigForm);
    }
}

function validateAnalysisForm(event) {
    const form = event.target;
    const startBlock = parseInt(form.start_block.value);
    const endBlock = parseInt(form.end_block.value);
    const batchSize = parseInt(form.batch_size.value);
    
    // Validate block range
    if (startBlock >= endBlock) {
        event.preventDefault();
        showAlert('Der Start-Block muss kleiner als der End-Block sein!', 'danger');
        return false;
    }
    
    // Validate batch size
    if (batchSize < 1 || batchSize > 10000) {
        event.preventDefault();
        showAlert('Die Batch-Größe muss zwischen 1 und 10.000 liegen!', 'danger');
        return false;
    }
    
    // Warn for large ranges
    const blockCount = endBlock - startBlock + 1;
    if (blockCount > 100000) {
        if (!confirm(`You want to analyze ${blockCount.toLocaleString()} blocks. This may take a very long time. Continue?`)) {
            event.preventDefault();
            return false;
        }
    }
    
    // Disable submit button to prevent double submission
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Starting...';
    }
    
    return true;
}

function validateConfigForm(event) {
    const form = event.target;
    const host = form.host.value.trim();
    const port = parseInt(form.port.value);
    const username = form.username.value.trim();
    const password = form.password.value;
    
    if (!host || !username || !password) {
        event.preventDefault();
        showAlert('Please fill in all required fields.', 'danger');
        return false;
    }
    
    if (port < 1 || port > 65535) {
        event.preventDefault();
        showAlert('Port muss zwischen 1 und 65535 liegen.', 'danger');
        return false;
    }
    
    return true;
}

// Auto-refresh for pages with running jobs
function initializeAutoRefresh() {
    // Auto-refresh job list if there are running jobs
    const runningJobs = document.querySelectorAll('tr[data-status="running"]');
    if (runningJobs.length > 0) {
        setTimeout(() => {
            window.location.reload();
        }, 15000); // Refresh every 15 seconds
    }
}

// Animations
function addFadeInAnimations() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
}

// Utility functions
function updateElement(id, content) {
    const element = document.getElementById(id);
    if (element) {
        element.innerHTML = content;
    }
}

function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container');
    if (!alertContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds} Sekunde${seconds !== 1 ? 'n' : ''}`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        return `${minutes} Minute${minutes !== 1 ? 'n' : ''}`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

function formatNumber(num) {
    return num.toLocaleString('de-DE');
}

// Export functions for use in templates
window.B1TAnalyzer = {
    updateStatus,
    showAlert,
    formatDuration,
    formatNumber
};

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, reduce update frequency
        if (statusUpdateInterval) {
            clearInterval(statusUpdateInterval);
            statusUpdateInterval = setInterval(updateStatus, 10000); // Update every 10 seconds
        }
    } else {
        // Page is visible, restore normal update frequency
        if (statusUpdateInterval) {
            clearInterval(statusUpdateInterval);
            statusUpdateInterval = setInterval(updateStatus, 3000); // Update every 3 seconds
        }
    }
});

// Handle window beforeunload
window.addEventListener('beforeunload', function() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl+N or Cmd+N for new job
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault();
        window.location.href = '/new_job';
    }
    
    // Ctrl+R or Cmd+R for refresh (allow default behavior but also update status)
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        updateStatus();
    }
});

// Console welcome message
console.log('%cB1T Web Analyzer', 'color: #007bff; font-size: 24px; font-weight: bold;');
console.log('%cBlockchain Analysis Tool', 'color: #6c757d; font-size: 14px;');
console.log('Version: 1.0.0');