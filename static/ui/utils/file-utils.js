export const fileUtils = {
    getFileIcon(filename) {
        if (!filename) return '📄';

        if (filename.match(/\.(mp4|avi|mov|mkv|webm|flv|wmv)$/i)) return '🎬';
        if (filename.match(/\.(mp3|wav|aac|m4a|ogg|flac)$/i)) return '🎵';
        if (filename.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i)) return '🖼️';
        return '📄';
    },

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatDuration(seconds) {
        if (isNaN(seconds)) return '00:00';

        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    },

    sanitizeFilename(filename) {
        if (!filename) return 'file';
        return filename.replace(/[^a-zA-Z0-9.-]/g, '_');
    },

    getFileExtension(filename) {
        if (!filename) return '';
        return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
    },

    isValidVideoFile(filename) {
        if (!filename) return false;
        const videoExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'];
        return videoExtensions.includes(this.getFileExtension(filename));
    },

    isValidAudioFile(filename) {
        if (!filename) return false;
        const audioExtensions = ['mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'];
        return audioExtensions.includes(this.getFileExtension(filename));
    },

    isValidImageFile(filename) {
        if (!filename) return false;
        const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'];
        return imageExtensions.includes(this.getFileExtension(filename));
    },

    getUniqueFilename(desiredName, existingFiles) {
        if (!existingFiles.some(file => file.name === desiredName)) {
            return desiredName;
        }

        const nameParts = desiredName.split('.');
        const baseName = nameParts.slice(0, -1).join('.');
        const extension = nameParts.length > 1 ? nameParts.pop() : '';

        let counter = 1;
        let newName;
        do {
            newName = extension ? `${baseName} (${counter}).${extension}` : `${baseName} (${counter})`;
            counter++;
        } while (existingFiles.some(file => file.name === newName));

        return newName;
    }
};