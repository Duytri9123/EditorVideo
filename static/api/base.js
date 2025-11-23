class ApiService {
    constructor() {
        this.baseURL = window.location.origin;
        this.endpoints = {
            // Download endpoints
            download: '/api/download',
            downloadAudio: '/api/download-audio',
            batchUpload: '/api/batch-upload-youtube',
            mergeVideos: '/api/merge-videos',
            // Timeline endpoints
            timeline: {
                addClip: '/api/timeline/add-clip',
                addAudio: '/api/timeline/add-audio',
                play: '/api/timeline/play',
                pause: '/api/timeline/pause',
                stop: '/api/timeline/stop',
                seek: '/api/timeline/seek',
                status: '/api/timeline/status',
                clear: '/api/timeline/clear',
                flipClip: '/api/timeline/flip-clip',
                rotateClip: '/api/timeline/rotate-clip',
                extractAudio: '/api/timeline/extract-audio',
                export: '/api/timeline/export'
            },

            // Video processing endpoints
            processVideo: '/api/process-video',
            extractAudio: '/api/extract-audio',

            // YouTube endpoints
            uploadYouTube: '/api/upload-youtube',

            // File management
            listFiles: '/api/list-files',
            fileInfo: '/api/file-info',
            cleanup: '/api/cleanup',
            uploadFile: '/api/upload-file',

            // System endpoints
            systemStatus: '/api/system/status',
            storageInfo: '/api/system/storage'
        };
    }

    async _makeRequest(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request error to ${endpoint}:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/api/health', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // System methods
    async getSystemStatus() {
        return await this._makeRequest(this.endpoints.systemStatus, {
            method: 'GET'
        });
    }

    async getStorageInfo() {
        return await this._makeRequest(this.endpoints.storageInfo, {
            method: 'GET'
        });
    }

    // Utility methods
    formatTime(seconds) {
        if (isNaN(seconds)) return '00:00';

        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    }

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    generateUniqueName(originalName, existingFiles) {
        if (!existingFiles.some(file => file.name === originalName)) {
            return originalName;
        }

        const nameParts = originalName.split('.');
        const baseName = nameParts.slice(0, -1).join('.');
        const extension = nameParts.length > 1 ? nameParts.pop() : '';

        let counter = 1;
        let newName;
        do {
            newName = extension ? `${baseName}_${counter}.${extension}` : `${baseName}_${counter}`;
            counter++;
        } while (existingFiles.some(file => file.name === newName));

        return newName;
    }
}

export default ApiService;