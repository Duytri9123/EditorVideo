// static/ui/js/index.js
import ApiService from './base.js';
import DownloadService from './download-service.js';
import TimelineService from './timeline-service.js';
import VideoProcessingService from './video-processing-service.js';
import YouTubeService from './youtube-service.js';
import FileManagementService from './file-management-service.js';

class CompleteApiService extends ApiService {
    constructor() {
        super();

        // Initialize service modules
        this.download = new DownloadService(this);
        this.timeline = new TimelineService(this);
        this.videoProcessing = new VideoProcessingService(this);
        this.youtube = new YouTubeService(this);
        this.fileManagement = new FileManagementService(this);

        // System methods
        this.system = {
            getStatus: () => this.getSystemStatus(),
            getStorageInfo: () => this.getStorageInfo()
        };
    }

    // System status methods
    async getSystemStatus() {
        try {
            return await this._makeRequest('/api/system/status', {
                method: 'GET'
            });
        } catch (error) {
            console.error('System status error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getStorageInfo() {
        try {
            return await this._makeRequest('/api/system/storage', {
                method: 'GET'
            });
        } catch (error) {
            console.error('Storage info error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Platform information
    async getPlatformInfo(url) {
        try {
            return await this._makeRequest('/api/platform-info', {
                method: 'POST',
                body: JSON.stringify({ url })
            });
        } catch (error) {
            console.error('Platform info error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getSupportedPlatforms() {
        try {
            return await this._makeRequest('/api/supported-platforms', {
                method: 'GET'
            });
        } catch (error) {
            console.error('Supported platforms error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Download methods - main interface
    async downloadVideo(url, filename = null, quality = 'best') {
        return await this.download.downloadVideo(url, filename, quality);
    }

    async downloadMultipleVideos(urls, filenames = [], quality = 'best') {
        return await this.download.downloadMultipleVideos(urls, filenames, quality);
    }

    async downloadAndMergeVideos(urls, outputFilename, options = {}) {
        return await this.download.downloadAndMergeVideos(urls, outputFilename, options);
    }

    async downloadAudio(url, filename = null, format = 'mp3', quality = '192') {
        return await this.download.downloadAudio(url, filename, format, quality);
    }

    // Backward compatibility methods
    async downloadVideos(urls, customFilename = null, quality = 'best[height<=1080]') {
        if (Array.isArray(urls) && urls.length > 1) {
            const filenames = customFilename ? [customFilename] : [];
            return await this.downloadMultipleVideos(urls, filenames, quality);
        } else {
            const url = Array.isArray(urls) ? urls[0] : urls;
            return await this.downloadVideo(url, customFilename, quality);
        }
    }

    // File management
    async listFiles() {
        return await this.fileManagement.listFiles();
    }

    async deleteFile(filename) {
        return await this.fileManagement.deleteFile(filename);
    }

    async uploadFile(file, fileType = 'logo') {
        return await this.fileManagement.uploadFile(file, fileType);
    }

    async cleanup(cleanupType = 'downloads') {
        return await this.fileManagement.cleanup(cleanupType);
    }

    // Video processing
    async processVideoWithEffects(videoFile, outputName, effectsConfig = {}) {
        return await this.videoProcessing.processVideoWithEffects(videoFile, outputName, effectsConfig);
    }

    async extractAudioFromVideo(videoFile, outputName) {
        return await this.videoProcessing.extractAudioFromVideo(videoFile, outputName);
    }

    async mergeVideos(videoFiles, outputName, options = {}) {
        return await this.videoProcessing.mergeVideos(videoFiles, outputName, options);
    }

    // YouTube
    async uploadToYouTube(videoFile, title, description = '', privacyStatus = 'private') {
        return await this.youtube.uploadToYouTube(videoFile, title, description, privacyStatus);
    }
}

// Create and export singleton instance
const api = new CompleteApiService();

// Export for both ES6 modules and global usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
} else {
    window.api = api;
}

export default api;