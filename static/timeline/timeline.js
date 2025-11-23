// timeline-service.js
import { log, fetchAPI } from './api_service.js';

let timelineData = [];
let currentVideo = null;
let videoPlayer = null;
let isPlaying = false;
let currentTime = 0;
let selectedClipIndex = -1;
let inPoint = 0;
let outPoint = 0;

export function initTimelineEditor() {
    const container = document.getElementById('timelineEditor');
    if (!container) return;

    container.innerHTML = `
        <div class="video-editor-container">
            <!-- Video Preview Section -->
            <div class="video-preview-section">
                <div class="video-controls">
                    <button id="playPauseBtn" class="btn btn-sm">⏯️ Phát</button>
                    <button id="markInBtn" class="btn btn-sm">🎬 Điểm bắt đầu</button>
                    <button id="markOutBtn" class="btn btn-sm">⏹️ Điểm kết thúc</button>
                    <button id="addClipBtn" class="btn btn-sm btn-success">➕ Thêm clip</button>
                    <span class="time-display">00:00 / 00:00</span>
                </div>
                
                <!-- Video Player -->
                <div class="video-player-wrapper">
                    <video id="mainVideoPlayer" controls style="width: 100%; max-height: 400px; background: #000;">
                        Trình duyệt của bạn không hỗ trợ video.
                    </video>
                    <div class="scrubber-container">
                        <div class="scrubber-bar" id="scrubberBar">
                            <div class="scrubber-progress" id="scrubberProgress"></div>
                            <div class="scrubber-handle" id="scrubberHandle"></div>
                            <div class="in-point-marker" id="inPointMarker"></div>
                            <div class="out-point-marker" id="outPointMarker"></div>
                        </div>
                    </div>
                </div>

                <!-- Current Selection Info -->
                <div class="selection-info">
                    <div>🎬 In: <span id="inPointDisplay">0.00s</span></div>
                    <div>⏹️ Out: <span id="outPointDisplay">0.00s</span></div>
                    <div>⏱️ Duration: <span id="selectionDuration">0.00s</span></div>
                </div>
            </div>

            <!-- Timeline Tracks -->
            <div class="timeline-section">
                <h4>🎬 Timeline</h4>
                <div class="timeline-header">
                    <div class="timeline-ruler" id="timelineRuler">
                        <!-- Timeline ruler marks will be generated here -->
                    </div>
                </div>
                <div class="timeline-track" id="timelineTrack">
                    <div class="timeline-clips" id="timelineClips">
                        <!-- Clips will be added here -->
                    </div>
                    <div class="playhead" id="playhead"></div>
                </div>
            </div>

            <!-- Clip Properties Panel -->
            <div class="clip-properties" id="clipProperties" style="display: none;">
                <h4>⚙️ Thuộc tính Clip</h4>
                <div class="property-grid">
                    <div class="form-group">
                        <label>Thời gian bắt đầu (s):</label>
                        <input type="number" id="clipStart" class="form-control" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label>Thời gian kết thúc (s):</label>
                        <input type="number" id="clipEnd" class="form-control" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label>Tốc độ:</label>
                        <select id="clipSpeed" class="form-control">
                            <option value="0.25">0.25x (Rất chậm)</option>
                            <option value="0.5">0.5x (Chậm)</option>
                            <option value="0.75">0.75x (Hơi chậm)</option>
                            <option value="1" selected>1x (Bình thường)</option>
                            <option value="1.25">1.25x (Hơi nhanh)</option>
                            <option value="1.5">1.5x (Nhanh)</option>
                            <option value="2">2x (Rất nhanh)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Âm lượng:</label>
                        <input type="range" id="clipVolume" class="form-control" min="0" max="200" value="100">
                        <span id="volumeValue">100%</span>
                    </div>
                </div>
                <div class="property-actions">
                    <button class="btn btn-danger" onclick="removeSelectedClip()">🗑️ Xóa clip</button>
                    <button class="btn btn-secondary" onclick="splitClip()">✂️ Chia clip</button>
                </div>
            </div>
        </div>
    `;

    initializeVideoPlayer();
    initializeEventListeners();
    generateTimelineRuler();
}

function generateTimelineRuler() {
    const ruler = document.getElementById('timelineRuler');
    if (!ruler) return;

    ruler.innerHTML = '';

    // Generate ruler marks every 5 seconds up to 5 minutes
    for (let i = 0; i <= 300; i += 5) {
        const mark = document.createElement('div');
        mark.className = 'ruler-mark';
        mark.style.left = `${(i / 300) * 100}%`;

        const minutes = Math.floor(i / 60);
        const seconds = i % 60;

        if (i % 30 === 0) { // Major mark every 30 seconds
            mark.className += ' major-mark';
            mark.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else {
            mark.textContent = seconds === 0 ? `${minutes}:00` : '';
        }

        ruler.appendChild(mark);
    }
}

function initializeVideoPlayer() {
    videoPlayer = document.getElementById('mainVideoPlayer');
    if (!videoPlayer) return;

    videoPlayer.addEventListener('loadedmetadata', function() {
        updateTimeDisplay();
        generateTimelineRuler();
    });

    videoPlayer.addEventListener('timeupdate', function() {
        currentTime = videoPlayer.currentTime;
        updateTimeDisplay();
        updateScrubber();
        updatePlayhead();
    });

    videoPlayer.addEventListener('play', function() {
        isPlaying = true;
        updatePlayButton();
    });

    videoPlayer.addEventListener('pause', function() {
        isPlaying = false;
        updatePlayButton();
    });

    videoPlayer.addEventListener('seeked', function() {
        currentTime = videoPlayer.currentTime;
        updateScrubber();
        updatePlayhead();
    });
}

function initializeEventListeners() {
    // Play/Pause button
    document.getElementById('playPauseBtn').addEventListener('click', togglePlayPause);

    // Mark In/Out buttons
    document.getElementById('markInBtn').addEventListener('click', markInPoint);
    document.getElementById('markOutBtn').addEventListener('click', markOutPoint);

    // Add Clip button
    document.getElementById('addClipBtn').addEventListener('click', addClipFromCurrentSelection);

    // Volume slider
    document.getElementById('clipVolume').addEventListener('input', function(e) {
        document.getElementById('volumeValue').textContent = e.target.value + '%';
        updateSelectedClip();
    });

    // Clip property inputs
    document.getElementById('clipStart').addEventListener('change', updateSelectedClip);
    document.getElementById('clipEnd').addEventListener('change', updateSelectedClip);
    document.getElementById('clipSpeed').addEventListener('change', updateSelectedClip);

    // Scrubber interaction
    setupScrubberInteractions();
}

function setupScrubberInteractions() {
    const scrubberBar = document.getElementById('scrubberBar');
    if (!scrubberBar) return;

    scrubberBar.addEventListener('click', function(e) {
        const rect = scrubberBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;

        if (videoPlayer) {
            videoPlayer.currentTime = percentage * (videoPlayer.duration || 0);
        }
    });

    // Drag for in/out points
    let isSettingInPoint = false;
    let isSettingOutPoint = false;

    document.getElementById('inPointMarker').addEventListener('mousedown', function() {
        isSettingInPoint = true;
    });

    document.getElementById('outPointMarker').addEventListener('mousedown', function() {
        isSettingOutPoint = true;
    });

    scrubberBar.addEventListener('mousemove', function(e) {
        if (!isSettingInPoint && !isSettingOutPoint) return;

        const rect = scrubberBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(1, clickX / rect.width));
        const time = percentage * (videoPlayer?.duration || 0);

        if (isSettingInPoint) {
            setInPoint(time);
        } else if (isSettingOutPoint) {
            setOutPoint(time);
        }
    });

    document.addEventListener('mouseup', function() {
        isSettingInPoint = false;
        isSettingOutPoint = false;
    });
}

function togglePlayPause() {
    if (!videoPlayer) return;

    if (isPlaying) {
        videoPlayer.pause();
    } else {
        videoPlayer.play();
    }
}

function updatePlayButton() {
    const button = document.getElementById('playPauseBtn');
    if (button) {
        button.textContent = isPlaying ? '⏸️ Tạm dừng' : '⏯️ Phát';
    }
}

function markInPoint() {
    if (!videoPlayer) return;
    setInPoint(currentTime);
}

function markOutPoint() {
    if (!videoPlayer) return;
    setOutPoint(currentTime);
}

function setInPoint(time) {
    inPoint = Math.max(0, time);
    if (outPoint > 0 && inPoint >= outPoint) {
        outPoint = inPoint + 1;
    }
    updateSelectionMarkers();
    updateSelectionInfo();
}

function setOutPoint(time) {
    if (!videoPlayer) return;
    const duration = videoPlayer.duration || 0;
    outPoint = Math.min(duration, time);
    if (inPoint >= outPoint) {
        inPoint = Math.max(0, outPoint - 1);
    }
    updateSelectionMarkers();
    updateSelectionInfo();
}

function updateSelectionMarkers() {
    const inMarker = document.getElementById('inPointMarker');
    const outMarker = document.getElementById('outPointMarker');
    const scrubberBar = document.getElementById('scrubberBar');

    if (!inMarker || !outMarker || !scrubberBar || !videoPlayer) return;

    const duration = videoPlayer.duration || 1;

    inMarker.style.left = `${(inPoint / duration) * 100}%`;
    outMarker.style.left = `${(outPoint / duration) * 100}%`;
}

function updateSelectionInfo() {
    document.getElementById('inPointDisplay').textContent = inPoint.toFixed(2) + 's';
    document.getElementById('outPointDisplay').textContent = outPoint.toFixed(2) + 's';

    const duration = outPoint - inPoint;
    document.getElementById('selectionDuration').textContent = duration.toFixed(2) + 's';
}

function addClipFromCurrentSelection() {
    if (!currentVideo) {
        alert('Vui lòng chọn video trước!');
        return;
    }

    if (outPoint <= inPoint) {
        alert('Điểm kết thúc phải sau điểm bắt đầu!');
        return;
    }

    const speed = parseFloat(document.getElementById('clipSpeed').value) || 1;
    const volume = parseInt(document.getElementById('clipVolume').value) || 100;

    const clip = {
        type: 'cut',
        file: currentVideo,
        start: inPoint,
        end: outPoint,
        speed: speed,
        volume: volume / 100,
        position: timelineData.length
    };

    timelineData.push(clip);
    renderTimelineClips();

    log(`✅ Đã thêm clip: ${inPoint.toFixed(2)}s - ${outPoint.toFixed(2)}s`, 'success');
}

function renderTimelineClips() {
    const container = document.getElementById('timelineClips');
    if (!container) return;

    container.innerHTML = '';

    const videoDuration = videoPlayer?.duration || 60;

    timelineData.forEach((clip, index) => {
        const clipElement = document.createElement('div');
        clipElement.className = `timeline-clip ${selectedClipIndex === index ? 'selected' : ''}`;
        clipElement.style.left = `${(clip.start / videoDuration) * 100}%`;
        clipElement.style.width = `${((clip.end - clip.start) / videoDuration) * 100}%`;

        clipElement.innerHTML = `
            <div class="clip-content">
                <span class="clip-label">Clip ${index + 1}</span>
                <span class="clip-duration">${(clip.end - clip.start).toFixed(1)}s</span>
                ${clip.speed !== 1 ? `<span class="clip-speed">${clip.speed}x</span>` : ''}
                <div class="clip-handle left"></div>
                <div class="clip-handle right"></div>
            </div>
        `;

        clipElement.addEventListener('click', (e) => {
            e.stopPropagation();
            selectClip(index);
        });

        // Make clip draggable and resizable
        makeClipInteractive(clipElement, index);

        container.appendChild(clipElement);
    });
}

function makeClipInteractive(clipElement, index) {
    let isDragging = false;
    let isResizing = false;
    let resizeDirection = '';
    let startX = 0;
    let startLeft = 0;
    let startWidth = 0;

    const handles = clipElement.querySelectorAll('.clip-handle');

    handles[0].addEventListener('mousedown', (e) => { // Left handle
        e.stopPropagation();
        isResizing = true;
        resizeDirection = 'left';
        startX = e.clientX;
        startLeft = parseFloat(clipElement.style.left);
        startWidth = parseFloat(clipElement.style.width);
    });

    handles[1].addEventListener('mousedown', (e) => { // Right handle
        e.stopPropagation();
        isResizing = true;
        resizeDirection = 'right';
        startX = e.clientX;
        startLeft = parseFloat(clipElement.style.left);
        startWidth = parseFloat(clipElement.style.width);
    });

    clipElement.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('clip-handle')) return;
        isDragging = true;
        startX = e.clientX;
        startLeft = parseFloat(clipElement.style.left);
        selectClip(index);
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging && !isResizing) return;

        const timelineTrack = document.getElementById('timelineTrack');
        const rect = timelineTrack.getBoundingClientRect();
        const deltaX = e.clientX - startX;
        const deltaPercent = (deltaX / rect.width) * 100;
        const videoDuration = videoPlayer?.duration || 60;

        if (isDragging) {
            const newLeft = Math.max(0, Math.min(100 - parseFloat(clipElement.style.width), startLeft + deltaPercent));
            clipElement.style.left = newLeft + '%';

            const clip = timelineData[index];
            const duration = clip.end - clip.start;
            clip.start = (newLeft / 100) * videoDuration;
            clip.end = clip.start + duration;
        } else if (isResizing) {
            const clip = timelineData[index];

            if (resizeDirection === 'left') {
                const newLeft = Math.max(0, Math.min(startLeft + deltaPercent,
                    (clip.end / videoDuration) * 100 - 1));
                const newWidth = startWidth - (newLeft - startLeft);

                if (newWidth > 1 && newLeft >= 0) {
                    clipElement.style.left = newLeft + '%';
                    clipElement.style.width = newWidth + '%';
                    clip.start = (newLeft / 100) * videoDuration;
                }
            } else { // right
                const newWidth = Math.max(1, startWidth + deltaPercent);
                if (newWidth <= 100 - startLeft) {
                    clipElement.style.width = newWidth + '%';
                    clip.end = ((startLeft + newWidth) / 100) * videoDuration;
                }
            }
        }

        updateClipProperties();
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        isResizing = false;
        renderTimelineClips(); // Re-render to ensure proper positioning
    });
}

function selectClip(index) {
    selectedClipIndex = index;
    renderTimelineClips();
    updateClipProperties();
    showClipProperties();

    // Set in/out points to match selected clip
    const clip = timelineData[index];
    setInPoint(clip.start);
    setOutPoint(clip.end);

    // Seek video to clip start
    if (videoPlayer) {
        videoPlayer.currentTime = clip.start;
    }
}

function updateClipProperties() {
    if (selectedClipIndex === -1 || !timelineData[selectedClipIndex]) return;

    const clip = timelineData[selectedClipIndex];
    document.getElementById('clipStart').value = clip.start.toFixed(2);
    document.getElementById('clipEnd').value = clip.end.toFixed(2);
    document.getElementById('clipSpeed').value = clip.speed;
    document.getElementById('clipVolume').value = Math.round(clip.volume * 100);
    document.getElementById('volumeValue').textContent = Math.round(clip.volume * 100) + '%';
}

function updateSelectedClip() {
    if (selectedClipIndex === -1) return;

    const clip = timelineData[selectedClipIndex];
    const newStart = parseFloat(document.getElementById('clipStart').value) || 0;
    const newEnd = parseFloat(document.getElementById('clipEnd').value) || newStart + 1;
    const newSpeed = parseFloat(document.getElementById('clipSpeed').value) || 1;
    const newVolume = parseInt(document.getElementById('clipVolume').value) / 100 || 1;

    if (newEnd <= newStart) {
        alert('Thời gian kết thúc phải sau thời gian bắt đầu!');
        return;
    }

    clip.start = newStart;
    clip.end = newEnd;
    clip.speed = newSpeed;
    clip.volume = newVolume;

    renderTimelineClips();
    setInPoint(newStart);
    setOutPoint(newEnd);
}

function removeSelectedClip() {
    if (selectedClipIndex === -1) return;

    timelineData.splice(selectedClipIndex, 1);
    selectedClipIndex = -1;
    renderTimelineClips();
    hideClipProperties();
    log('🗑️ Đã xóa clip', 'info');
}

function splitClip() {
    if (selectedClipIndex === -1 || !videoPlayer) return;

    const clip = timelineData[selectedClipIndex];
    const splitTime = videoPlayer.currentTime;

    if (splitTime <= clip.start || splitTime >= clip.end) {
        alert('Thời điểm chia phải nằm trong khoảng thời gian của clip!');
        return;
    }

    // Create new clip from the second part
    const newClip = {
        ...clip,
        start: splitTime,
        position: selectedClipIndex + 1
    };

    // Update original clip end time
    clip.end = splitTime;

    // Insert new clip
    timelineData.splice(selectedClipIndex + 1, 0, newClip);

    renderTimelineClips();
    selectClip(selectedClipIndex + 1);
    log(`✂️ Đã chia clip tại ${splitTime.toFixed(2)}s`, 'success');
}

function showClipProperties() {
    document.getElementById('clipProperties').style.display = 'block';
}

function hideClipProperties() {
    document.getElementById('clipProperties').style.display = 'none';
}

function updateTimeDisplay() {
    if (!videoPlayer) return;

    const timeDisplay = document.querySelector('.time-display');
    if (timeDisplay) {
        const current = formatTime(currentTime);
        const duration = formatTime(videoPlayer.duration || 0);
        timeDisplay.textContent = `${current} / ${duration}`;
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function updateScrubber() {
    if (!videoPlayer) return;

    const progress = document.getElementById('scrubberProgress');
    const handle = document.getElementById('scrubberHandle');

    if (progress && handle) {
        const duration = videoPlayer.duration || 1;
        const percentage = (currentTime / duration) * 100;

        progress.style.width = percentage + '%';
        handle.style.left = percentage + '%';
    }
}

function updatePlayhead() {
    const playhead = document.getElementById('playhead');
    if (!playhead || !videoPlayer) return;

    const duration = videoPlayer.duration || 1;
    const percentage = (currentTime / duration) * 100;
    playhead.style.left = percentage + '%';
}

// Export functions for external use
export function loadVideoForEditing(videoPath) {
    currentVideo = videoPath;
    if (videoPlayer) {
        videoPlayer.src = videoPath;
        log(`🎬 Đã tải video: ${videoPath}`, 'success');
    }
}

export function getTimelineData() {
    return timelineData;
}

export function clearTimeline() {
    timelineData = [];
    selectedClipIndex = -1;
    renderTimelineClips();
    hideClipProperties();
    log('🗑️ Đã xóa toàn bộ timeline', 'info');
}

// Make functions available globally
window.removeSelectedClip = removeSelectedClip;
window.splitClip = splitClip;