class FileManagementService {
    constructor(apiService) {
        this.api = apiService;
    }

    async listFiles() {
        return await this.api._makeRequest(this.api.endpoints.listFiles, {
            method: 'GET'
        });
    }

    async getFileInfo(filePath) {
        return await this.api._makeRequest(`${this.api.endpoints.fileInfo}?path=${encodeURIComponent(filePath)}`, {
            method: 'GET'
        });
    }

    async cleanup(cleanupType = 'downloads') {
        return await this.api._makeRequest(this.api.endpoints.cleanup, {
            method: 'POST',
            body: JSON.stringify({ type: cleanupType })
        });
    }

    async uploadFile(file, fileType = 'music') {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('type', fileType);

            const response = await fetch(this.api.endpoints.uploadFile, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Upload file error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async deleteFile(filename) {
        return await this.api._makeRequest(this.api.endpoints.cleanup, {
            method: 'POST',
            body: JSON.stringify({
                type: 'file',
                filename: filename
            })
        });
    }

    async downloadFile(filename) {
        try {
            const response = await fetch(`/api/files/${encodeURIComponent(filename)}`, {
                method: 'GET'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            return { success: true };
        } catch (error) {
            console.error('Download file error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

export default FileManagementService;