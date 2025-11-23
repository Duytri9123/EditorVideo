class TimelineService {
    constructor(apiService) {
        this.api = apiService;
    }

    async addClipToTimeline(videoFile, startTime = 0, endTime = null, position = 0) {
        const payload = {
            videoFile: videoFile,
            startTime: startTime,
            endTime: endTime,
            position: position
        };

        return await this.api._makeRequest(this.api.endpoints.timeline.addClip, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async addAudioToTimeline(audioFile, startTime = 0, volume = 1.0) {
        const payload = {
            audioFile: audioFile,
            startTime: startTime,
            volume: volume
        };

        return await this.api._makeRequest(this.api.endpoints.timeline.addAudio, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async playTimeline() {
        return await this.api._makeRequest(this.api.endpoints.timeline.play, {
            method: 'POST'
        });
    }

    async pauseTimeline() {
        return await this.api._makeRequest(this.api.endpoints.timeline.pause, {
            method: 'POST'
        });
    }

    async stopTimeline() {
        return await this.api._makeRequest(this.api.endpoints.timeline.stop, {
            method: 'POST'
        });
    }

    async seekTimeline(time) {
        return await this.api._makeRequest(this.api.endpoints.timeline.seek, {
            method: 'POST',
            body: JSON.stringify({ time })
        });
    }

    async getTimelineStatus() {
        return await this.api._makeRequest(this.api.endpoints.timeline.status, {
            method: 'GET'
        });
    }

    async clearTimeline() {
        return await this.api._makeRequest(this.api.endpoints.timeline.clear, {
            method: 'POST'
        });
    }

    async flipClip(clipId, direction = 'horizontal') {
        return await this.api._makeRequest(this.api.endpoints.timeline.flipClip, {
            method: 'POST',
            body: JSON.stringify({ clipId, direction })
        });
    }

    async rotateClip(clipId, degrees = 90) {
        return await this.api._makeRequest(this.api.endpoints.timeline.rotateClip, {
            method: 'POST',
            body: JSON.stringify({ clipId, degrees })
        });
    }

    async extractAudioFromClip(clipId, outputName) {
        return await this.api._makeRequest(this.api.endpoints.timeline.extractAudio, {
            method: 'POST',
            body: JSON.stringify({ clipId, outputName })
        });
    }

    async exportTimeline(outputName, format = 'mp4', quality = 'high') {
        return await this.api._makeRequest(this.api.endpoints.timeline.export, {
            method: 'POST',
            body: JSON.stringify({ outputName, format, quality })
        });
    }
}

export default TimelineService;