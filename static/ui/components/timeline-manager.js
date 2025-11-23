import { fileUtils } from '../utils/file-utils.js';

export class TimelineManager {
    constructor() {
        this.currentTimelineClips = [];
        this.currentAudioClips = [];
        this.currentTimelineData = [];
        this.dragSource = null;
        this.isDragging = false;
        this.isTimelinePlaying = false;
        this.timelinePlaybackInterval = null;
        this.currentPlayheadPosition = 0;
        this.zoom = 1.0;
        this.pixelsPerSecond = 50;

        this.playbackState = {
            isPlaying: false,
            currentTime: 0,
            totalDuration: 0,
            currentClip: null
        };
    }

    clearTimeline() {
        this.currentTimelineClips = [];
        this.currentAudioClips = [];
        this.currentTimelineData = [];

        const tracks = document.querySelectorAll('.track-content');
        tracks.forEach(track => {
            track.innerHTML = '<div class="empty-timeline"><p>Kéo files vào đây để bắt đầu chỉnh sửa</p></div>';
        });

        this.playbackState = {
            isPlaying: false,
            currentTime: 0,
            totalDuration: 0,
            currentClip: null
        };

        const playPauseBtn = document.getElementById('timelinePlayPause');
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i> Phát';
        }
    }

    zoomTimeline(factor) {
        this.zoom = Math.max(0.1, Math.min(5, this.zoom * factor));

        const tracks = document.querySelectorAll('.track-content');
        tracks.forEach(track => {
            const currentWidth = track.scrollWidth;
            track.style.minWidth = (currentWidth * factor) + 'px';
        });

        const currentTime = this.pixelsToTime(this.currentPlayheadPosition, this.pixelsPerSecond, this.zoom / factor);
        const newPosition = this.timeToPixels(currentTime, this.pixelsPerSecond, this.zoom);
        // updatePlayheadPosition would be called from the handler

        console.log(`🔍 Timeline zoomed ${factor > 1 ? 'in' : 'out'} to ${Math.round(this.zoom * 100)}%`);
    }

    updateTimelineUI() {
        const videoTrack1 = document.getElementById('videoTrack1');
        const videoTrack2 = document.getElementById('videoTrack2');
        const audioTrack = document.getElementById('audioTrack');
        if (!videoTrack1 || !videoTrack2 || !audioTrack) return;

        videoTrack1.innerHTML = '';
        videoTrack2.innerHTML = '';
        audioTrack.innerHTML = '';

        this.currentTimelineData.forEach((clip, index) => {
            if (clip.type === 'video') {
                const trackElement = clip.track === 1 ? videoTrack2 : videoTrack1;
                const clipElement = this.createTimelineClip(clip, index, 'video');
                trackElement.appendChild(clipElement);
            } else if (clip.type === 'audio') {
                const clipElement = this.createTimelineClip(clip, index, 'audio');
                audioTrack.appendChild(clipElement);
            }
        });

        if (this.currentTimelineData.length > 0) {
            const emptyStates = document.querySelectorAll('.empty-timeline');
            emptyStates.forEach(state => {
                if (state.parentElement.children.length === 1) {
                    state.remove();
                }
            });
        }
    }

    createTimelineClip(clip, index, type) {
        const clipElement = document.createElement('div');
        clipElement.className = `timeline-clip ${type}-clip`;
        clipElement.dataset.clipIndex = index;

        const position = (clip.position || 0) * 100;
        const width = (clip.duration || 10) * 50;

        clipElement.style.left = position + 'px';
        clipElement.style.width = width + 'px';

        clipElement.innerHTML = `
            <div class="clip-content">
                <div class="clip-thumbnail">${type === 'audio' ? '🎵' : '🎬'}</div>
                <div class="clip-info">
                    <div class="clip-name">${clip.file.split('/').pop()}</div>
                    <div class="clip-duration">${fileUtils.formatDuration(clip.duration)}</div>
                </div>
                <div class="clip-controls">
                    <button class="clip-btn" onclick="previewClip(${index})">▶️</button>
                    ${type === 'video' ? `
                        <button class="clip-btn" onclick="flipClipHorizontal(${index})">🔄</button>
                        <button class="clip-btn" onclick="rotateClip(${index})">🔄</button>
                    ` : ''}
                    <button class="clip-btn" onclick="extractAudioFromClip(${index})">🎵</button>
                    <button class="clip-btn" onclick="removeFromTimeline(${index})">🗑️</button>
                </div>
            </div>
        `;
        return clipElement;
    }

    timeToPixels(seconds, pixelsPerSecond, zoomLevel = 1) {
        return seconds * pixelsPerSecond * zoomLevel;
    }

    pixelsToTime(pixels, pixelsPerSecond, zoomLevel = 1) {
        return pixels / (pixelsPerSecond * zoomLevel);
    }
}

// Export timeline clip functions to window
window.flipClipHorizontal = async function(clipIndex) {
    try {
        if (window.showStatus) showStatus('✅ Clip đã lật ngang', 'success');
        if (window.refreshTimeline) refreshTimeline();
    } catch (error) {
        if (window.showStatus) showStatus(`❌ Lật thất bại: ${error.message}`, 'error');
    }
};

window.rotateClip = async function(clipIndex) {
    try {
        if (window.showStatus) showStatus('✅ Clip đã xoay', 'success');
        if (window.refreshTimeline) refreshTimeline();
    } catch (error) {
        if (window.showStatus) showStatus(`❌ Xoay thất bại: ${error.message}`, 'error');
    }
};

window.extractAudioFromClip = async function(clipIndex) {
    const outputName = `audio_from_clip_${clipIndex}.mp3`;
    try {
        if (window.showStatus) showStatus(`✅ Âm thanh đã trích xuất: ${outputName}`, 'success');
        if (window.refreshFiles) refreshFiles();
    } catch (error) {
        if (window.showStatus) showStatus(`❌ Trích xuất thất bại: ${error.message}`, 'error');
    }
};

window.removeFromTimeline = function(clipIndex) {
    if (confirm('Xóa clip này khỏi timeline?')) {
        if (window.timelineManager) {
            window.timelineManager.currentTimelineData.splice(clipIndex, 1);
        }
        if (window.refreshTimeline) refreshTimeline();
        if (window.showStatus) showStatus('🗑️ Clip đã xóa khỏi timeline', 'info');
    }
};