import { log } from '../utils/dom-utils.js';
import { timelineUtils } from '../utils/timeline-utils.js';
import { fileUtils } from '../utils/file-utils.js';

export function setupPreviewHandlers() {
    const previewVideo = document.getElementById('mainPreview');
    if (previewVideo) {
        previewVideo.addEventListener('loadedmetadata', function() {
            updateVideoInfo(this);
            if (window.timelineManager && window.timelineManager.playbackState.totalDuration === 0 && this.duration) {
                window.timelineManager.playbackState.totalDuration = this.duration;
                const timelineTotalTime = document.getElementById('timelineTotalTime');
                if (timelineTotalTime) {
                    timelineTotalTime.textContent = timelineUtils.formatTimeForDisplay(this.duration);
                }
            }
        });
        previewVideo.addEventListener('timeupdate', function() {
            updatePlaybackProgress(this);
        });
        previewVideo.addEventListener('ended', function() {
            if (window.timelineManager && window.timelineManager.playbackState.isPlaying) {
                // Timeline playback ended
            }
        });
    }
    log('👁️ Preview handlers initialized', 'success');
}

window.previewFile = function(filePath) {
    const allFiles = [
        ...(window.currentFiles?.downloads || []),
        ...(window.currentFiles?.outputs || []),
        ...(window.currentFiles?.music || [])
    ];

    const file = allFiles.find(f => f.path === filePath);
    if (file) {
        const preview = document.getElementById('mainPreview');
        if (preview) {
            preview.src = file.path;
            preview.load();
            updateVideoInfo(preview);
            log(`👁️ Đang xem trước: ${file.name}`, 'info');
        }
    }
};

window.previewClip = function(clipIndex) {
    if (window.timelineManager) {
        const clip = window.timelineManager.currentTimelineData[clipIndex];
        if (clip) previewFile(clip.file);
    }
};

window.playPreview = function() {
    const preview = document.getElementById('mainPreview');
    if (preview) {
        preview.play().catch(e => {
            log('❌ Không thể phát video: ' + e.message, 'error');
            if (window.showStatus) showStatus('❌ Không thể phát video: ' + e.message, 'error');
        });
    }
};

window.pausePreview = function() {
    const preview = document.getElementById('mainPreview');
    if (preview) preview.pause();
};

window.stopPreview = function() {
    const preview = document.getElementById('mainPreview');
    if (preview) {
        preview.pause();
        preview.currentTime = 0;
    }
};

window.togglePlayPause = function() {
    const preview = document.getElementById('mainPreview');
    if (preview) {
        if (preview.paused) {
            preview.play().catch(e => {
                log('❌ Không thể phát video: ' + e.message, 'error');
                if (window.showStatus) showStatus('❌ Không thể phát video: ' + e.message, 'error');
            });
        } else {
            preview.pause();
        }
    }
};

window.toggleMute = function() {
    const preview = document.getElementById('mainPreview');
    if (preview) {
        preview.muted = !preview.muted;
        const muteBtn = document.querySelector('[onclick="toggleMute()"]');
        if (muteBtn) {
            muteBtn.innerHTML = preview.muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
        }
        log(preview.muted ? '🔇 Đã tắt tiếng' : '🔊 Đã bật tiếng', 'info');
    }
};

window.changeVolume = function(value) {
    const preview = document.getElementById('mainPreview');
    if (preview) {
        preview.volume = value / 100;
        document.getElementById('volumeText').textContent = value + '%';
    }
};

function updateVideoInfo(video) {
    const durationEl = document.getElementById('vidDuration');
    const resolutionEl = document.getElementById('vidResolution');
    const sizeEl = document.getElementById('vidSize');

    if (durationEl) durationEl.textContent = fileUtils.formatDuration(video.duration);
    if (resolutionEl) resolutionEl.textContent = `${video.videoWidth}x${video.videoHeight}`;
    if (sizeEl) sizeEl.textContent = fileUtils.formatFileSize(0);
}

function updatePlaybackProgress(video) {
    const currentTimeEl = document.getElementById('currentTime');
    const totalTimeEl = document.getElementById('totalTime');

    if (currentTimeEl) currentTimeEl.textContent = timelineUtils.formatTimeForDisplay(video.currentTime);
    if (totalTimeEl) totalTimeEl.textContent = timelineUtils.formatTimeForDisplay(video.duration);
}