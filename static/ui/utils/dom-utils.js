export function log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const styles = {
        success: 'color: #10B981; font-weight: bold;',
        error: 'color: #EF4444; font-weight: bold;',
        warning: 'color: #F59E0B; font-weight: bold;',
        info: 'color: #3B82F6; font-weight: bold;'
    };

    console.log(`%c[${timestamp}] ${message}`, styles[type] || styles.info);

    // Optional: Show notification in UI if function exists
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    }
}

export function showLoading(button, isLoading, loadingText = 'Loading...') {
    if (!button) return;

    if (isLoading) {
        button.disabled = true;
        button.setAttribute('data-original-text', button.innerHTML);
        button.innerHTML = `<span class="loading-spinner"></span> ${loadingText}`;
        button.classList.add('loading');
    } else {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        }
        button.classList.remove('loading');
    }
}

export function showStatus(message, type = 'info', elementId = 'status') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = message;
        element.className = `status-message status-${type}`;

        // Auto-hide success messages after 8 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (element.innerHTML === message) {
                    element.innerHTML = '';
                    element.className = 'status-message';
                }
            }, 8000);
        }

        // Auto-hide info messages after 5 seconds
        if (type === 'info') {
            setTimeout(() => {
                if (element.innerHTML === message) {
                    element.innerHTML = '';
                    element.className = 'status-message';
                }
            }, 5000);
        }
    }

    log(message, type);
}

export const dataFixer = {
    fixFileData(files) {
        if (!Array.isArray(files)) return [];

        return files.map(file => ({
            name: file.name || 'Unknown',
            path: file.path || `downloads/${file.name}`,
            duration: file.duration || 0,
            width: file.width || 0,
            height: file.height || 0,
            size: file.size || 0,
            type: this.determineFileType(file.name),
            modified: file.modified || Date.now(),
            quality: file.quality || 'unknown'
        }));
    },

    determineFileType(filename) {
        if (!filename) return 'other';

        const videoExtensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'];
        const audioExtensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'];
        const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];

        const ext = filename.toLowerCase().substring(filename.lastIndexOf('.'));

        if (videoExtensions.includes(ext)) return 'video';
        if (audioExtensions.includes(ext)) return 'audio';
        if (imageExtensions.includes(ext)) return 'image';
        return 'other';
    },

    ensureNumber(value, defaultValue = 0) {
        if (value === null || value === undefined) return defaultValue;
        const num = Number(value);
        return isNaN(num) ? defaultValue : num;
    },

    ensureString(value, defaultValue = '') {
        return typeof value === 'string' ? value : defaultValue;
    },

    ensureArray(value) {
        if (Array.isArray(value)) return value;
        if (value === null || value === undefined) return [];
        return [value];
    }
};

// Format file size for display
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format time for display
export function formatTime(seconds) {
    if (isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Debounce function for performance
export function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}