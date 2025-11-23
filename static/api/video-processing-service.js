class VideoProcessingService {
    constructor(apiService) {
        this.api = apiService;
    }

    async processVideoWithEffects(videoFile, outputName, effectsConfig = {}) {
        const payload = {
            videoFile: videoFile,
            outputName: outputName,
            effects: effectsConfig
        };

        return await this.api._makeRequest('/api/process-video', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async extractAudioFromVideo(videoFile, outputName) {
        const payload = {
            videoFile: videoFile,
            outputName: outputName
        };

        return await this.api._makeRequest('/api/extract-audio', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async mergeVideos(videoFiles, outputName, options = {}) {
        const payload = {
            videoFiles: videoFiles,
            outputName: outputName,
            options: options
        };

        console.log('Sending merge request to /api/merge-videos');
        return await this.api._makeRequest('/api/merge-videos', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }
}

export default VideoProcessingService;