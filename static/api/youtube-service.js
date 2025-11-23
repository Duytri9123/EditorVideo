class YouTubeService {
    constructor(apiService) {
        this.api = apiService;
    }

    async uploadToYouTube(videoFile, title, description = '', privacyStatus = 'private') {
        const payload = {
            videoFile: videoFile,
            title: title,
            description: description,
            privacyStatus: privacyStatus
        };

        return await this.api._makeRequest(this.api.endpoints.uploadYouTube, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }
}

export default YouTubeService;