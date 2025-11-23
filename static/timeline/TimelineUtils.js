// TimelineUtils.js - Enhanced Utility Functions for Timeline
export class TimelineUtils {
    constructor() {
        this.cache = new Map();
    }

    generateId(prefix = 'clip') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getFileName(path) {
        if (!path) return 'unknown';
        return path.split('/').pop() || path.split('\\').pop() || 'clip';
    }

    formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return '00:00';

        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    }

    formatTimeWithMs(seconds) {
        if (isNaN(seconds)) return '00:00.000';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);

        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }

    extractFileName(path) {
        const fileName = this.getFileName(path);
        return fileName.split('.').slice(0, -1).join('.') || fileName;
    }

    getFileExtension(path) {
        const fileName = this.getFileName(path);
        return fileName.split('.').pop()?.toLowerCase() || '';
    }

    encodeVideoPath(videoPath) {
        if (videoPath.startsWith('blob:')) return videoPath;
        if (videoPath.startsWith('http')) return videoPath;

        const parts = videoPath.split('/');
        const encodedParts = parts.map(part => encodeURIComponent(part));
        return encodedParts.join('/');
    }

    generateUniqueId(prefix = 'item') {
        const timestamp = Date.now().toString(36);
        const randomStr = Math.random().toString(36).substr(2, 9);
        return `${prefix}_${timestamp}_${randomStr}`;
    }

    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    snapToGrid(value, gridSize) {
        return Math.round(value / gridSize) * gridSize;
    }

    debounce(func, wait, immediate = false) {
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

    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    parseTime(timeString) {
        if (typeof timeString === 'number') return timeString;

        const parts = timeString.split(':');

        if (parts.length === 3) {
            const hours = parseInt(parts[0]) || 0;
            const mins = parseInt(parts[1]) || 0;
            const secs = parseInt(parts[2]) || 0;
            return hours * 3600 + mins * 60 + secs;
        } else if (parts.length === 2) {
            const mins = parseInt(parts[0]) || 0;
            const secs = parseInt(parts[1]) || 0;
            return mins * 60 + secs;
        } else {
            return parseFloat(timeString) || 0;
        }
    }

    downloadJSON(data, filename) {
        try {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", filename);
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
            return true;
        } catch (error) {
            console.error('Failed to download JSON:', error);
            return false;
        }
    }

    uploadJSON(callback) {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';

            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) {
                    resolve(null);
                    return;
                }

                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        const data = JSON.parse(event.target.result);
                        if (callback) callback(data);
                        resolve(data);
                    } catch (error) {
                        console.error('Failed to parse JSON file:', error);
                        if (callback) callback(null, error);
                        resolve(null);
                    }
                };
                reader.readAsText(file);
            };

            input.click();
        });
    }

    isValidVideoFile(filename) {
        const videoExtensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v'];
        return videoExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    }

    isValidAudioFile(filename) {
        const audioExtensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma'];
        return audioExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    }

    isValidImageFile(filename) {
        const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'];
        return imageExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    }

    bytesToSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';

        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    calculateAspectRatio(width, height) {
        if (!width || !height) return 'Unknown';

        const gcd = (a, b) => b ? gcd(b, a % b) : a;
        const divisor = gcd(width, height);

        return `${width / divisor}:${height / divisor}`;
    }

    stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }

        let color = '#';
        for (let i = 0; i < 3; i++) {
            const value = (hash >> (i * 8)) & 0xFF;
            color += ('00' + value.toString(16)).substr(-2);
        }

        return color;
    }

    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (obj instanceof Object) {
            const clonedObj = {};
            for (let key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }

    deepMerge(target, source) {
        const output = this.deepClone(target);

        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }

        return output;
    }

    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    randomIntInRange(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substr(0, maxLength - 3) + '...';
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    getTimestamp(format = 'iso') {
        const now = new Date();

        switch (format) {
            case 'iso':
                return now.toISOString();
            case 'locale':
                return now.toLocaleString();
            case 'time':
                return now.toLocaleTimeString();
            case 'date':
                return now.toLocaleDateString();
            case 'unix':
                return Math.floor(now.getTime() / 1000);
            default:
                return now.toISOString();
        }
    }

    calculateFPS() {
        let lastTime = performance.now();
        let frameCount = 0;
        let fps = 0;

        return function() {
            frameCount++;
            const currentTime = performance.now();

            if (currentTime - lastTime >= 1000) {
                fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                frameCount = 0;
                lastTime = currentTime;
            }

            return fps;
        };
    }

    getMemoryUsage() {
        if (performance.memory) {
            return {
                used: this.bytesToSize(performance.memory.usedJSHeapSize),
                total: this.bytesToSize(performance.memory.totalJSHeapSize),
                limit: this.bytesToSize(performance.memory.jsHeapSizeLimit)
            };
        }
        return null;
    }
}

export default TimelineUtils;