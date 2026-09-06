// AMD.AI Dashboard - Alpine.js Components & Global Store
// This file is loaded in base.html

// Global Toast Store
document.addEventListener('alpine:init', () => {
    Alpine.store('toasts', {
        list: [],
        push(toast) { this.list.push(toast); },
        remove(id) { this.list = this.list.filter(t => t.id !== id); }
    });
    
    // Global dashboard store
    Alpine.store('dashboard', {
        activeTab: 'models',
        darkMode: false,
        backendStatus: 'Verificando...',
        
        init() {
            this.loadDarkMode();
            this.checkBackends();
        },
        
        loadDarkMode() {
            this.darkMode = localStorage.getItem('darkMode') === 'true';
            document.documentElement.classList.toggle('dark', this.darkMode);
        },
        
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
            localStorage.setItem('darkMode', this.darkMode);
        },
        
        async checkBackends() {
            try {
                const res = await fetch('/api/backends');
                const data = await res.json();
                const names = data.backends.map(b => b.name.toUpperCase()).join(', ');
                this.backendStatus = `Backends: ${names || 'Ninguno'}`;
            } catch (e) {
                this.backendStatus = "Error verificando backends";
            }
        }
    });
});

// Utility functions
window.dashboardUtils = {
    // Format number with commas
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    },
    
    // Format bytes to human readable
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Format duration
    formatDuration(ms) {
        if (ms < 1000) return ms + 'ms';
        if (ms < 60000) return (ms / 1000).toFixed(1) + 's';
        if (ms < 3600000) return (ms / 60000).toFixed(1) + 'm';
        return (ms / 3600000).toFixed(1) + 'h';
    },
    
    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copiado al portapapeles', 'success');
        } catch (e) {
            this.showToast('Error copiando: ' + e.message, 'error');
        }
    },
    
    // Show toast notification
    showToast(message, type = 'info') {
        if (window.Alpine) {
            const store = Alpine.store('toasts');
            store.push({ 
                id: Date.now(), 
                message, 
                type: `toast-${type}` 
            });
        }
    },
    
    // Format date
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
};

// Global HTMX configuration
document.addEventListener('htmx:configRequest', (evt) => {
    // Add CSRF token if needed
    // evt.detail.headers['X-CSRF-Token'] = 'token';
});

// Global error handling for HTMX
document.addEventListener('htmx:responseError', (evt) => {
    console.error('HTMX Error:', evt.detail);
    window.dashboardUtils.showToast('Error en la petición: ' + evt.detail.xhr.status, 'error');
});

// WebSocket reconnection helper
window.wsHelper = {
    connections: new Map(),
    
    connect(jobId, onMessage, onClose) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/progress/${jobId}`);
        
        ws.onopen = () => {
            console.log('WebSocket connected for job:', jobId);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                console.error('WS parse error:', e);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket closed for job:', jobId);
            if (onClose) onClose();
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.connections.set(jobId, ws);
        return ws;
    },
    
    disconnect(jobId) {
        const ws = this.connections.get(jobId);
        if (ws) {
            ws.close();
            this.connections.delete(jobId);
        }
    },
    
    disconnectAll() {
        for (const [jobId, ws] of this.connections) {
            ws.close();
        }
        this.connections.clear();
    }
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    window.wsHelper.disconnectAll();
});

// Initialize Alpine store when ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize dark mode from localStorage
    const darkMode = localStorage.getItem('darkMode') === 'true';
    document.documentElement.classList.toggle('dark', darkMode);
    
    // Initialize tooltips if needed
    // Initialize any other global components
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { dashboardUtils, wsHelper };
}