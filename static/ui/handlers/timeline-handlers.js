import { log, showLoading, showStatus } from '../utils/dom-utils.js';
import { timelineUtils } from '../utils/timeline-utils.js';
import { TimelineManager } from '../components/timeline-manager.js';
import api from '../../api';

let timelineManager;

export function setupTimelineHandlers() {
    timelineManager = new TimelineManager();
    setupTimelineDragAndDrop();
    setupTimelineControls();
    setupTimelineEventListeners();
    setupTimelinePlayback();
    log('🎬 Timeline handlers initialized', 'success');
}

function setupTimelineDragAndDrop() {
    const timelineTracks = document.querySelectorAll('.track-content');
    const fileItems = document.querySelectorAll('.file-item');

    fileItems.forEach(item => {
        item.setAttribute('draggable', 'true');
        item.addEventListener('dragstart', (e) => {
            timelineManager.isDragging = true;
            timelineManager.dragSource = item;
            const filePath = item.dataset.path || '';
            const fileType = getFileTypeFromElement(item);
            e.dataTransfer.setData('text/plain', JSON.stringify({
                path: filePath,
                type: fileType
            }));
            item.classList.add('dragging');
        });
        item.addEventListener('dragend', () => {
            timelineManager.isDragging = false;
            timelineManager.dragSource = null;
            item.classList.remove('dragging');
        });
    });

    timelineTracks.forEach(track => {
        track.addEventListener('dragover', (e) => {
            e.preventDefault();
            track.classList.add('drag-over');
        });
        track.addEventListener('dragleave', () => track.classList.remove('drag-over'));
        track.addEventListener('drop', (e) => {
            e.preventDefault();
            track.classList.remove('drag-over');
            const data = e.dataTransfer.getData('text/plain');
            if (data) {
                try {
                    const { path, type } = JSON.parse(data);
                    const trackId = track.id;

                    if (trackId.includes('video') && type !== 'video') {
                        showStatus('❌ Chỉ có thể kéo file video vào track video', 'error');
                        return;
                    }
                    if (trackId.includes('audio') && type !== 'audio') {
                        showStatus('❌ Chỉ có thể kéo file audio vào track âm thanh', 'error');
                        return;
                    }

                    if (path) {
                        addFileToTimeline(path, type, trackId);
                    }
                } catch (error) {
                    console.error('Error parsing drag data:', error);
                }
            }
        });
    });
}

function getFileTypeFromElement(element) {
    const icon = element.querySelector('.file-icon');
    if (icon) {
        if (icon.textContent.includes('🎬')) return 'video';
        if (icon.textContent.includes('🎵')) return 'audio';
        if (icon.textContent.includes('🖼️')) return 'image';
    }
    return 'video';
}

function setupTimelineControls() {
    const playhead = document.getElementById('playhead');
    if (playhead) {
        let isDraggingPlayhead = false;
        playhead.addEventListener('mousedown', (e) => {
            isDraggingPlayhead = true;
            document.body.style.cursor = 'grabbing';
            e.stopPropagation();
        });
        document.addEventListener('mousemove', (e) => {
            if (!isDraggingPlayhead) return;
            const timelineSection = document.querySelector('.timeline-section');
            const rect = timelineSection.getBoundingClientRect();
            const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
            updatePlayheadPosition(x);
        });
        document.addEventListener('mouseup', () => {
            isDraggingPlayhead = false;
            document.body.style.cursor = '';
        });
    }
}

function setupTimelineEventListeners() {
    const tracks = document.querySelectorAll('.track-content');
    tracks.forEach(track => {
        track.addEventListener('click', (e) => {
            if (e.target.classList.contains('timeline-clip')) return;
            const rect = track.getBoundingClientRect();
            const x = e.clientX - rect.left;
            seekToPosition(x);
        });
    });
}

function setupTimelinePlayback() {
    const playPauseBtn = document.getElementById('timelinePlayPause');
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', toggleTimelinePlayback);
    }

    const seekStartBtn = document.querySelector('[onclick="seekToStart()"]');
    const seekEndBtn = document.querySelector('[onclick="seekToEnd()"]');

    if (seekStartBtn) {
        seekStartBtn.addEventListener('click', seekToStart);
    }
    if (seekEndBtn) {
        seekEndBtn.addEventListener('click', seekToEnd);
    }

    log('⏯️ Timeline playback handlers initialized', 'success');
}

// Timeline functions
window.toggleTimelinePlayback = async function() {
    const playPauseBtn = document.getElementById('timelinePlayPause');
    const statusElement = document.getElementById('timelineStatus');

    if (timelineManager.playbackState.isPlaying) {
        const result = await api.timeline.pauseTimeline();
        if (result.success) {
            timelineManager.playbackState.isPlaying = false;
            if (playPauseBtn) {
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i> Phát';
            }
            if (timelineManager.playbackInterval) {
                clearInterval(timelineManager.playbackInterval);
                timelineManager.playbackInterval = null;
            }
            showStatus('⏸️ Timeline đã tạm dừng', 'info', 'timelineStatus');
        }
    } else {
        if (timelineManager.currentTimelineData.length === 0) {
            showStatus('❌ Không có clip nào trong timeline để phát', 'error', 'timelineStatus');
            return;
        }

        const result = await api.timeline.playTimeline();
        if (result.success) {
            timelineManager.playbackState.isPlaying = true;
            if (playPauseBtn) {
                playPauseBtn.innerHTML = '<i class="fas fa-pause"></i> Tạm dừng';
            }

            timelineManager.playbackInterval = setInterval(updateTimelinePlayback, 100);
            showStatus('▶️ Timeline đang phát', 'info', 'timelineStatus');
        } else {
            showStatus(`❌ Không thể phát timeline: ${result.error}`, 'error', 'timelineStatus');
        }
    }
};

async function updateTimelinePlayback() {
    try {
        const status = await api.timeline.getTimelineStatus();
        if (status.success) {
            const summary = status.timeline_summary;
            timelineManager.playbackState.currentTime = summary.current_time;
            timelineManager.playbackState.totalDuration = summary.total_duration;
            timelineManager.playbackState.isPlaying = summary.is_playing;

            const pixelPosition = timelineUtils.timeToPixels(summary.current_time, timelineManager.pixelsPerSecond, timelineManager.zoom);
            updatePlayheadPosition(pixelPosition);

            const timelineCurrentTime = document.getElementById('timelineCurrentTime');
            const timelineTotalTime = document.getElementById('timelineTotalTime');

            if (timelineCurrentTime) {
                timelineCurrentTime.textContent = timelineUtils.formatTimeForDisplay(summary.current_time);
            }
            if (timelineTotalTime) {
                timelineTotalTime.textContent = timelineUtils.formatTimeForDisplay(summary.total_duration);
            }

            if (summary.current_frame && summary.current_frame.file) {
                if (window.previewFile) window.previewFile(summary.current_frame.file);
            }

            updateTimelineProperties(summary);

            if (summary.current_time >= summary.total_duration && timelineManager.playbackState.isPlaying) {
                toggleTimelinePlayback();
                seekToStart();
            }
        }
    } catch (error) {
        console.error('Error updating timeline playback:', error);
    }
}

function updatePlayheadPosition(pixelPosition) {
    const playhead = document.getElementById('playhead');
    if (!playhead) return;

    const timelineSection = document.querySelector('.timeline-section');
    const rect = timelineSection.getBoundingClientRect();
    const position = Math.max(0, Math.min(pixelPosition, rect.width));

    playhead.style.left = position + 'px';
    timelineManager.currentPlayheadPosition = position;

    const timeInSeconds = timelineUtils.pixelsToTime(position, timelineManager.pixelsPerSecond, timelineManager.zoom);
    updatePlayheadTimeDisplay(timeInSeconds);

    const timelineCurrentTime = document.getElementById('timelineCurrentTime');
    if (timelineCurrentTime) {
        timelineCurrentTime.textContent = timelineUtils.formatTimeForDisplay(timeInSeconds);
    }
}

function updatePlayheadTimeDisplay(timeInSeconds) {
    const timeDisplay = document.getElementById('playhead')?.querySelector('.playhead-time');
    if (timeDisplay) {
        timeDisplay.textContent = timelineUtils.formatTimeForDisplay(timeInSeconds);
    }
}

function seekToPosition(x) {
    updatePlayheadPosition(x);
    const timeInSeconds = timelineUtils.pixelsToTime(x, timelineManager.pixelsPerSecond, timelineManager.zoom);
    api.seekTimeline(timeInSeconds).then(result => {
        if (result.success && result.current_frame) {
            if (result.current_frame.file && window.previewFile) {
                window.previewFile(result.current_frame.file);
            }
        }
    });
}

window.seekToStart = function() {
    updatePlayheadPosition(0);
    api.timeline.seekTimeline(0);
};

window.seekToEnd = function() {
    const timelineSection = document.querySelector('.timeline-section');
    if (timelineSection) {
        const rect = timelineSection.getBoundingClientRect();
        updatePlayheadPosition(rect.width);
        const timeInSeconds = timelineUtils.pixelsToTime(rect.width, timelineManager.pixelsPerSecond, timelineManager.zoom);
        api.timeline.seekTimeline(timeInSeconds);
    }
};

window.zoomInTimeline = function() {
    timelineManager.zoomTimeline(1.2);
};

window.zoomOutTimeline = function() {
    timelineManager.zoomTimeline(0.8);
};

window.fitTimeline = function() {
    timelineManager.zoom = 1.0;
    const tracks = document.querySelectorAll('.track-content');
    tracks.forEach(track => track.style.minWidth = '100%');
    log('📐 Timeline fitted to view', 'info');
    updateTimelineProperties(timelineManager.playbackState);
};

window.toggleSnap = function() {
    const snapEnabled = document.body.classList.toggle('snap-enabled');
    const snapToggle = document.getElementById('timelineSnapToggle');
    if (snapToggle) {
        snapToggle.classList.toggle('active', snapEnabled);
    }
    log(`🧲 Snap to grid ${snapEnabled ? 'enabled' : 'disabled'}`, 'info');
};

window.splitAtPlayhead = function() {
    log('✂️ Split at playhead', 'info');
};

window.clearTimeline = async function() {
    if (confirm('Bạn có chắc chắn muốn xóa timeline? Hành động này không thể hoàn tác.')) {
        const result = await api.timeline.clearTimeline();
        if (result.success) {
            timelineManager.clearTimeline();
            showStatus('🗑️ Timeline đã được xóa', 'info', 'timelineStatus');
            updateTimelineProperties(timelineManager.playbackState);
        } else {
            showStatus(`❌ Không thể xóa timeline: ${result.error}`, 'error', 'timelineStatus');
        }
    }
};

window.exportTimeline = async function() {
    const outputName = document.getElementById('exportFilename').value || 'timeline_export.mp4';
    if (timelineManager.currentTimelineData.length === 0) {
        showStatus('❌ Không có clip nào trong timeline để xuất', 'error', 'timelineStatus');
        return;
    }
    const button = document.querySelector('#timelineTab .btn-primary');
    showLoading(button, true);
    try {
        const result = await api.timeline.export(outputName);
        if (result.success) {
            showStatus(`✅ Timeline đã xuất: ${outputName}`, 'success', 'timelineStatus');
            if (window.refreshFiles) refreshFiles();
        } else {
            showStatus(`❌ Xuất thất bại: ${result.error}`, 'error', 'timelineStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi xuất: ${error.message}`, 'error', 'timelineStatus');
    } finally { showLoading(button, false); }
};

function updateTimelineProperties(summary) {
    const propClips = document.getElementById('propClips');
    const propTotalDuration = document.getElementById('propTotalDuration');
    const propZoom = document.getElementById('propZoom');

    if (propClips) propClips.textContent = summary.total_clips || 0;
    if (propTotalDuration) propTotalDuration.textContent = timelineUtils.formatTimeForDisplay(summary.total_duration);
    if (propZoom) propZoom.textContent = Math.round(timelineManager.zoom * 100) + '%';
}

// Export timeline functions to window
window.addFileToTimeline = addFileToTimeline;
window.refreshTimeline = refreshTimeline;

async function addFileToTimeline(filePath, type = 'video', trackId = null) {
    const allFiles = [
        ...(window.currentFiles?.downloads || []),
        ...(window.currentFiles?.outputs || []),
        ...(window.currentFiles?.music || [])
    ];

    const fileData = allFiles.find(file => file.path === filePath);
    if (fileData) {
        try {
            let result;
            if (type === 'video') {
                const timelineLogo = document.getElementById('timelineLogo')?.value;
                const logoPosition = document.getElementById('logoPosition')?.value;

                const effectsConfig = {};
                if (timelineLogo) {
                    effectsConfig.logo_path = timelineLogo;
                    effectsConfig.logo_position = logoPosition;
                }

                result = await api.timeline.addClipToTimeline(filePath, 0, null, trackId === 'videoTrack2' ? 1 : 0);
            } else {
                result = await api.timeline.addAudioToTimeline(filePath);
            }

            if (result.success) {
                showStatus(`✅ Đã thêm "${fileData.name}" vào timeline`, 'success');
                refreshTimeline();
                updateTimelineProperties(result.timeline_summary);
            } else {
                showStatus(`❌ Không thể thêm vào timeline: ${result.error}`, 'error');
            }
        } catch (error) {
            showStatus(`❌ Lỗi khi thêm vào timeline: ${error.message}`, 'error');
        }
    } else {
        showStatus('❌ Không tìm thấy file', 'error');
    }
}

async function refreshTimeline() {
    try {
        const result = await api.timeline.getTimelineStatus();
        if (result.success) {
            timelineManager.currentTimelineData = result.timeline_data || [];
            timelineManager.updateTimelineUI();
        }
    } catch (error) {
        console.error('Error refreshing timeline:', error);
    }
}