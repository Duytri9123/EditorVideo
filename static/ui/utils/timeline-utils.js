export const timelineUtils = {
    timeToPixels(seconds, pixelsPerSecond, zoomLevel = 1) {
        return seconds * pixelsPerSecond * zoomLevel;
    },

    pixelsToTime(pixels, pixelsPerSecond, zoomLevel = 1) {
        return pixels / (pixelsPerSecond * zoomLevel);
    },

    formatTimeForDisplay(seconds, showHours = false) {
        if (isNaN(seconds)) return '00:00';

        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (showHours || hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    },

    calculateTotalDuration(clips) {
        return clips.reduce((total, clip) => total + (clip.duration || 0), 0);
    },

    snapToGrid(value, gridSize) {
        return Math.round(value / gridSize) * gridSize;
    }
};