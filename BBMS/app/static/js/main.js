// Main JavaScript for Blood Bank Management System

// Utility Functions
const BBMS = {
    // Show loading spinner
    showLoading: function(element) {
        if (element) {
            element.innerHTML = '<div class="loading-spinner"></div>';
        }
    },

    // Hide loading spinner
    hideLoading: function(element, content) {
        if (element) {
            element.innerHTML = content;
        }
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    },

    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    // Format datetime
    formatDateTime: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Validate email
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validate phone number
    validatePhone: function(phone) {
        const re = /^[\+]?[1-9][\d]{0,15}$/;
        return re.test(phone.replace(/\s/g, ''));
    },

    // Confirm action
    confirmAction: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },

    // Auto-hide alerts
    autoHideAlerts: function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    },

    // Setup accessibility for dropdowns
    setupDropdownAccessibility: function() {
        const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
            });
        });
    },

    // Setup accessibility for navbar toggler
    setupNavbarAccessibility: function() {
        const navbarToggler = document.querySelector('.navbar-toggler');
        if (navbarToggler) {
            navbarToggler.addEventListener('click', function() {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
            });
        }
    }
};

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Auto-complete functionality
function setupAutocomplete(inputElement, dataUrl, displayField = 'name', valueField = 'id') {
    if (!inputElement) return;
    
    const datalist = document.createElement('datalist');
    datalist.id = inputElement.id + '-list';
    inputElement.setAttribute('list', datalist.id);
    inputElement.parentNode.appendChild(datalist);
    
    inputElement.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length < 2) return;
        
        fetch(`${dataUrl}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                datalist.innerHTML = '';
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item[displayField];
                    option.setAttribute('data-value', item[valueField]);
                    datalist.appendChild(option);
                });
            })
            .catch(error => console.error('Autocomplete error:', error));
    });
}

// Dynamic form fields
function addDynamicField(container, template, index) {
    const field = template.replace(/\{index\}/g, index);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = field;
    container.appendChild(tempDiv.firstElementChild);
}

function removeDynamicField(button) {
    button.closest('.dynamic-field').remove();
}

// File upload preview
function setupFilePreview(inputElement, previewElement) {
    if (!inputElement || !previewElement) return;
    
    inputElement.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewElement.src = e.target.result;
                    previewElement.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                previewElement.style.display = 'none';
            }
        }
    });
}

// Search functionality
function setupSearch(inputElement, tableElement) {
    if (!inputElement || !tableElement) return;
    
    inputElement.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        const rows = tableElement.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// Sort table functionality
function setupTableSort(tableElement) {
    if (!tableElement) return;
    
    const headers = tableElement.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.sort;
            const order = this.dataset.order === 'asc' ? 'desc' : 'asc';
            
            // Update all headers
            headers.forEach(h => h.dataset.order = '');
            this.dataset.order = order;
            
            // Sort table
            sortTable(tableElement, column, order);
        });
    });
}

function sortTable(table, column, order) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-${column}]`).dataset[column];
        const bValue = b.querySelector(`td[data-${column}]`).dataset[column];
        
        if (order === 'asc') {
            return aValue.localeCompare(bValue);
        } else {
            return bValue.localeCompare(aValue);
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Modal utilities
function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

// AJAX utilities
function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Chart utilities (if Chart.js is available)
function createChart(canvasId, type, data, options = {}) {
    if (typeof Chart === 'undefined') return null;
    
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: type,
        data: data,
        options: finalOptions
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts
    BBMS.autoHideAlerts();
    
    // Setup accessibility
    BBMS.setupDropdownAccessibility();
    BBMS.setupNavbarAccessibility();
    
    // Setup form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                BBMS.showToast('Please fill in all required fields.', 'warning');
            }
        });
    });
    
    // Setup search functionality
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        const tableId = input.dataset.search;
        const table = document.getElementById(tableId);
        if (table) {
            setupSearch(input, table);
        }
    });
    
    // Setup table sorting
    const sortableTables = document.querySelectorAll('table[data-sortable]');
    sortableTables.forEach(table => {
        setupTableSort(table);
    });
    
    // Setup file previews
    const fileInputs = document.querySelectorAll('input[type="file"][data-preview]');
    fileInputs.forEach(input => {
        const previewId = input.dataset.preview;
        const preview = document.getElementById(previewId);
        if (preview) {
            setupFilePreview(input, preview);
        }
    });
    
    // Setup autocomplete
    const autocompleteInputs = document.querySelectorAll('[data-autocomplete]');
    autocompleteInputs.forEach(input => {
        const url = input.dataset.autocomplete;
        const displayField = input.dataset.displayField || 'name';
        const valueField = input.dataset.valueField || 'id';
        setupAutocomplete(input, url, displayField, valueField);
    });
    
    // Setup dynamic forms
    const addButtons = document.querySelectorAll('[data-add-field]');
    addButtons.forEach(button => {
        button.addEventListener('click', function() {
            const containerId = this.dataset.addField;
            const template = this.dataset.template;
            const container = document.getElementById(containerId);
            const index = container.children.length;
            
            if (container && template) {
                addDynamicField(container, template, index);
            }
        });
    });
    
    // Remove dynamic field buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-remove-field]')) {
            removeDynamicField(e.target);
        }
    });
    
    // Print functionality
    const printButtons = document.querySelectorAll('[data-print]');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.print;
            const target = document.getElementById(targetId);
            if (target) {
                const printWindow = window.open('', '_blank');
                printWindow.document.write(`
                    <html>
                        <head>
                            <title>Print</title>
                            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                        </head>
                        <body>
                            ${target.outerHTML}
                        </body>
                    </html>
                `);
                printWindow.document.close();
                printWindow.print();
            }
        });
    });
});

// Export BBMS object for global access
window.BBMS = BBMS; 