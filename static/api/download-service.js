// static/ui/js/download-service.js
class DownloadService {
    constructor(apiService) {
        this.api = apiService;
        this.endpoints = {
            download: '/api/download',
            downloadMultiple: '/api/download-multiple',
            downloadAndMerge: '/api/download-and-merge',
            downloadAudio: '/api/download-audio',
            supportedPlatforms: '/api/supported-platforms',
            platformInfo: '/api/platform-info'
        };
    }

    async downloadVideo(url, filename = null, quality = 'best') {
        const payload = {
            urls: [url],
            quality: quality
        };

        if (filename) {
            payload.filename = filename;
        }

        return await this.api._makeRequest(this.endpoints.download, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async downloadMultipleVideos(urls, filenames = [], quality = 'best') {
        const payload = {
            urls: urls,
            quality: quality
        };

        if (filenames.length > 0) {
            payload.filenames = filenames;
        }

        return await this.api._makeRequest(this.endpoints.downloadMultiple, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async downloadAndMergeVideos(urls, outputFilename, options = {}) {
        const payload = {
            urls: urls,
            output_filename: outputFilename,
            quality: options.quality || 'best[height<=1080]',
            transition_type: options.transitionType || 'none',
            keep_originals: options.keepOriginals || false
        };

        return await this.api._makeRequest(this.endpoints.downloadAndMerge, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async downloadAudio(url, filename = null, format = 'mp3', quality = '192') {
        const payload = {
            url: url,
            format: format,
            quality: quality
        };

        if (filename) {
            payload.filename = filename;
        }

        return await this.api._makeRequest(this.endpoints.downloadAudio, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async getSupportedPlatforms() {
        return await this.api._makeRequest(this.endpoints.supportedPlatforms, {
            method: 'GET'
        });
    }

    async getPlatformInfo(url) {
        return await this.api._makeRequest(this.endpoints.platformInfo, {
            method: 'POST',
            body: JSON.stringify({ url })
        });
    }

    // Enhanced method with progress tracking
    async downloadWithProgress(urls, options = {}) {
        const isMultiple = Array.isArray(urls) && urls.length > 1;
        const endpoint = isMultiple ? this.endpoints.downloadMultiple : this.endpoints.download;

        const payload = {
            urls: Array.isArray(urls) ? urls : [urls],
            quality: options.quality || 'best[height<=1080]'
        };

        if (options.filename) {
            payload.filename = options.filename;
        }

        if (options.filenames) {
            payload.filenames = options.filenames;
        }

        try {
            const result = await this.api._makeRequest(endpoint, {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            // Call progress callback if provided
            if (options.onProgress) {
                options.onProgress({
                    stage: 'complete',
                    progress: 100,
                    result: result
                });
            }

            return result;
        } catch (error) {
            if (options.onProgress) {
                options.onProgress({
                    stage: 'error',
                    progress: 0,
                    error: error.message
                });
            }
            throw error;
        }
    }
}

export default DownloadService;