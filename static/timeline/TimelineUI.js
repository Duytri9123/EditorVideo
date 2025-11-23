// TimelineUI.js - Complete Timeline UI Management for 15-minute videos with images
import { TimelineUtils } from './TimelineUtils.js';

export class TimelineUI {
    constructor(engine) {
        this.engine = engine;
        this.utils = new TimelineUtils();
        this.isDragging = false;
        this.currentDragClip = null;
        this.dragStartX = 0;
        this.dragStartLeft = 0;
        this.resizeData = null;
    }

    createUIElements() {
        // Find timeline elements in DOM
        this.engine.timelineTrack = document.getElementById('videoTrack');
        this.engine.timelineTrack2 = document.getElementById('videoTrack2');
        this.engine.audioTrack = document.getElementById('audioTrack');
        this.engine.imageTrack = document.getElementById('imageTrack');

        if (!this.engine.timelineTrack) {
            console.error('❌ Timeline track not found');
            return;
        }

        this.setupTimelineDragAndDrop();
        this.createPlayhead();
        this.updateSourceFiles();
        this.setupTimelineClickEvents();
        this.setupTimelineControls();
    }

    setupTimelineUI() {
        this.updateTimelineUI();
        this.generateTimelineRuler();
        this.updateSourceFiles();
        this.updateTimelineStats();
        this.setupKeyboardShortcuts();
    }

    setupTimelineControls() {
        // Setup zoom controls
        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');
        const fitTimelineBtn = document.getElementById('fitTimelineBtn');
        const snapToggleBtn = document.getElementById('snapToggleBtn');

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.engine.zoomIn());
        }
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.engine.zoomOut());
        }
        if (fitTimelineBtn) {
            fitTimelineBtn.addEventListener('click', () => this.engine.fitTimeline());
        }
        if (snapToggleBtn) {
            snapToggleBtn.addEventListener('click', () => this.engine.toggleSnap());
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '=':
                        e.preventDefault();
                        this.engine.zoomIn();
                        break;
                    case '-':
                        e.preventDefault();
                        this.engine.zoomOut();
                        break;
                    case '0':
                        e.preventDefault();
                        this.engine.fitTimeline();
                        break;
                }
            }

            // Space bar for play/pause
            if (e.code === 'Space' && !e.target.matches('input, textarea, select')) {
                e.preventDefault();
                this.engine.toggleTimelinePlayback();
            }
        });
    }

    setupTimelineClickEvents() {
        const tracks = [this.engine.timelineTrack, this.engine.timelineTrack2, this.engine.audioTrack, this.engine.imageTrack];

        tracks.forEach(track => {
            if (track) {
                track.addEventListener('click', (e) => {
                    if (!e.target.closest('.timeline-clip')) {
                        this.handleTimelineClick(e);
                    }
                });

                // Double click to add marker or split
                track.addEventListener('dblclick', (e) => {
                    if (!e.target.closest('.timeline-clip')) {
                        this.handleTimelineDoubleClick(e);
                    }
                });
            }
        });
    }

    handleTimelineClick(e) {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
        const totalSeconds = this.engine.totalDuration;
        this.engine.playheadPosition = (x / rect.width) * totalSeconds;

        this.updatePlayhead();
        this.updateTimelineTimeDisplay();
        this.engine.showInfo(`Seek to: ${this.utils.formatTime(this.engine.playheadPosition)}`);
    }

    handleTimelineDoubleClick(e) {
        if (this.engine.selectedClipId) {
            this.engine.controls.splitAtPlayhead();
        } else {
            this.handleTimelineClick(e);
        }
    }

    // ========== SOURCE FILES MANAGEMENT ==========

    updateSourceFiles() {
        const filesList = document.getElementById('filesList');
        if (!filesList) {
            console.warn('⚠️ Files list container not found');
            return;
        }

        const allFiles = [
            ...(window.currentFiles?.downloads || []),
            ...(window.currentFiles?.outputs || []),
            ...(window.currentFiles?.music || []),
            ...(window.currentFiles?.logos || [])
        ];

        if (allFiles.length === 0) {
            filesList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📁</div>
                    <p>No media files</p>
                    <small>Download videos to get started</small>
                </div>
            `;
            return;
        }

        filesList.innerHTML = allFiles.map(file => `
            <div class="file-item" 
                 data-path="${file.path}"
                 data-type="${file.type || 'video'}"
                 draggable="true"
                 ondragstart="window.timelineEngine.ui.handleFileDragStart(event)"
                 ondragend="window.timelineEngine.ui.handleFileDragEnd(event)">
                <div class="file-icon">${this.getFileIcon(file.name, file.type)}</div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-details">
                        ${file.duration ? this.utils.formatTime(file.duration) + ' • ' : ''}
                        ${file.width && file.height ? file.width + 'x' + file.height + ' • ' : ''}
                        ${this.formatFileSize(file.size || 0)}
                    </div>
                </div>
                <div class="file-actions">
                    <button class="file-action-btn" onclick="event.stopPropagation(); window.previewFile('${file.path}')" title="Preview">👁️</button>
                    <button class="file-action-btn" onclick="event.stopPropagation(); window.addFileToTimeline('${file.path}')" title="Add to Timeline">➕</button>
                </div>
            </div>
        `).join('');

        // Add drag and drop listeners to new file items
        this.setupFileDragAndDrop();
    }

    getFileIcon(filename, fileType = 'video') {
        if (fileType === 'audio' || filename.match(/\.(mp3|wav|aac|m4a|ogg|flac)$/i)) {
            return '🎵';
        } else if (fileType === 'image' || filename.match(/\.(png|jpg|jpeg|gif|bmp|webp|svg)$/i)) {
            return '🖼️';
        } else {
            return '🎬';
        }
    }

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    setupFileDragAndDrop() {
        const fileItems = document.querySelectorAll('.file-item');
        fileItems.forEach(item => {
            item.addEventListener('dragstart', (e) => this.handleFileDragStart(e));
            item.addEventListener('dragend', (e) => this.handleFileDragEnd(e));
        });
    }

    handleFileDragStart(e) {
        const fileItem = e.target.closest('.file-item');
        if (fileItem) {
            const filePath = fileItem.getAttribute('data-path');
            const fileType = fileItem.getAttribute('data-type') || 'video';

            e.dataTransfer.setData('text/plain', filePath);
            e.dataTransfer.setData('application/file-type', fileType);
            e.dataTransfer.effectAllowed = 'copy';

            fileItem.classList.add('dragging');
            this.engine.showInfo(`Dragging: ${fileItem.querySelector('.file-name').textContent}`);
        }
    }

    handleFileDragEnd(e) {
        const fileItem = e.target.closest('.file-item');
        if (fileItem) {
            fileItem.classList.remove('dragging');
        }
    }

    // ========== TIMELINE DRAG & DROP ==========

    setupTimelineDragAndDrop() {
        const tracks = [
            this.engine.timelineTrack,
            this.engine.timelineTrack2,
            this.engine.audioTrack,
            this.engine.imageTrack
        ];

        tracks.forEach((track, index) => {
            if (track) {
                const trackType = index === 2 ? 'audio' : index === 3 ? 'image' : 'video';
                this.setupTrackDropZone(track, trackType);
            }
        });
    }

    setupTrackDropZone(trackElement, type) {
        trackElement.addEventListener('dragover', (e) => {
            e.preventDefault();
            trackElement.classList.add('drag-over');
            e.dataTransfer.dropEffect = 'copy';
        });

        trackElement.addEventListener('dragleave', () => {
            trackElement.classList.remove('drag-over');
        });

        trackElement.addEventListener('drop', (e) => {
            e.preventDefault();
            trackElement.classList.remove('drag-over');

            const filePath = e.dataTransfer.getData('text/plain');
            const fileType = e.dataTransfer.getData('application/file-type') || type;

            if (filePath) {
                this.addFileToTimeline(filePath, fileType, e);
            }
        });
    }

    addFileToTimeline(filePath, fileType = 'video', dropEvent = null) {
        const allFiles = [
            ...(window.currentFiles?.downloads || []),
            ...(window.currentFiles?.outputs || []),
            ...(window.currentFiles?.music || []),
            ...(window.currentFiles?.logos || [])
        ];

        const fileData = allFiles.find(file => file.path === filePath);

        if (fileData) {
            let startTime = 0;

            // Calculate drop position for start time
            if (dropEvent) {
                const track = dropEvent.currentTarget;
                const rect = track.getBoundingClientRect();
                const x = Math.max(0, Math.min(dropEvent.clientX - rect.left, rect.width));
                startTime = (x / rect.width) * this.engine.totalDuration;

                // Snap to grid if enabled
                if (this.engine.snapToGrid) {
                    startTime = Math.round(startTime / 0.5) * 0.5; // Snap to 0.5 second intervals
                }
            }

            switch (fileType) {
                case 'audio':
                    this.engine.addAudioToTimeline(filePath, fileData.name);
                    break;
                case 'image':
                    this.engine.addImageToTimeline(filePath, 10, startTime, fileData.name);
                    break;
                default:
                    this.engine.addToTimeline(filePath, startTime, null, fileData.name);
            }

            this.engine.showSuccess(`✅ Added "${fileData.name}" to timeline`);
        } else {
            this.engine.showError('❌ File not found in library');
        }
    }

    // ========== TIMELINE RENDERING ==========

    updateTimelineUI() {
        const tracks = {
            video: this.engine.timelineTrack,
            video2: this.engine.timelineTrack2,
            audio: this.engine.audioTrack,
            image: this.engine.imageTrack
        };

        // Clear all tracks
        Object.values(tracks).forEach(track => {
            if (track) track.innerHTML = '';
        });

        // Check if timeline is empty
        if (this.engine.timelineClips.length === 0 &&
            this.engine.audioClips.length === 0 &&
            this.engine.imageClips.length === 0) {

            this.showEmptyTimelineStates(tracks);
            return;
        }

        // Render video clips to tracks (distribute between video tracks)
        this.engine.timelineClips.forEach((clip, index) => {
            const targetTrack = index % 2 === 0 ? tracks.video : tracks.video2;
            if (targetTrack) {
                const clipElement = this.createClipElement(clip, 'video');
                targetTrack.appendChild(clipElement);
            }
        });

        // Render audio clips
        this.engine.audioClips.forEach(clip => {
            if (tracks.audio) {
                const clipElement = this.createClipElement(clip, 'audio');
                tracks.audio.appendChild(clipElement);
            }
        });

        // Render image clips
        this.engine.imageClips.forEach(clip => {
            if (tracks.image) {
                const clipElement = this.createClipElement(clip, 'image');
                tracks.image.appendChild(clipElement);
            }
        });

        this.createPlayhead();
        this.updatePlayhead();
        this.updateTimelineStats();
    }

    showEmptyTimelineStates(tracks) {
        if (tracks.video) {
            tracks.video.innerHTML = `
                <div class="empty-timeline">
                    <div class="empty-icon">🎬</div>
                    <p>Drag video files here to start editing</p>
                    <small>Supports videos up to 15 minutes</small>
                </div>
            `;
        }
        if (tracks.audio) {
            tracks.audio.innerHTML = `
                <div class="empty-timeline">
                    <div class="empty-icon">🎵</div>
                    <p>Drag audio files here</p>
                    <small>Background music, sound effects</small>
                </div>
            `;
        }
        if (tracks.image) {
            tracks.image.innerHTML = `
                <div class="empty-timeline">
                    <div class="empty-icon">🖼️</div>
                    <p>Drag logo/images here</p>
                    <small>Watermarks, overlays, branding</small>
                </div>
            `;
        }
    }

    createClipElement(clip, type) {
        const clipElement = document.createElement('div');
        clipElement.className = `timeline-clip ${type}-clip ${clip.flip ? 'flipped' : ''} ${clip.id === this.engine.selectedClipId ? 'selected' : ''}`;
        clipElement.setAttribute('data-clip-id', clip.id);
        clipElement.setAttribute('data-clip-type', type);

        const clipWidth = Math.max(60, clip.duration * this.engine.PIXELS_PER_SECOND);
        const clipHeight = type === 'audio' ? 60 : type === 'image' ? 50 : 80;

        clipElement.style.width = `${clipWidth}px`;
        clipElement.style.height = `${clipHeight}px`;
        clipElement.style.left = `${clip.position.x}px`;

        if (type !== 'image') {
            clipElement.style.top = `${clip.position.y}px`;
        }

        if (type === 'video') {
            clipElement.style.zIndex = clip.zIndex || 1;
        }

        const isAudio = type === 'audio';
        const isImage = type === 'image';
        const flipIcon = clip.flip ? '🔄' : '↔️';
        const flipTitle = clip.flip ? 'Unflip Video' : 'Flip Video';

        clipElement.innerHTML = `
            <div class="clip-content">
                <div class="clip-thumbnail">
                    <div class="clip-thumbnail-placeholder">
                        ${isAudio ? '🎵' : isImage ? '🖼️' : '🎬'}
                    </div>
                    ${!isAudio && !isImage ? `<div class="clip-layer">${clip.zIndex || 1}</div>` : ''}
                    ${clip.flip ? '<div class="clip-flip-indicator">🔄</div>' : ''}
                </div>
                <div class="clip-info">
                    <div class="clip-name" title="${clip.name}">${this.utils.extractFileName(clip.name)}</div>
                    <div class="clip-duration">${this.utils.formatTime(clip.duration)}</div>
                    ${!isAudio && !isImage ? `<div class="clip-speed">${clip.speed}x</div>` : ''}
                    ${isAudio ? `<div class="clip-volume">${Math.round(clip.volume * 100)}%</div>` : ''}
                    ${isImage ? `<div class="clip-opacity">${Math.round((clip.opacity || 1) * 100)}%</div>` : ''}
                </div>
                <div class="clip-controls">
                    <button class="clip-btn preview-btn" data-clip-id="${clip.id}" title="Preview Clip">▶️</button>
                    ${!isAudio && !isImage ? `
                        <button class="clip-btn flip-btn" data-clip-id="${clip.id}" title="${flipTitle}">${flipIcon}</button>
                    ` : ''}
                    <button class="clip-btn delete-btn" data-clip-id="${clip.id}" title="Delete Clip">🗑️</button>
                </div>
            </div>
            ${!isAudio ? `
                <div class="clip-resize-handle left" data-clip-id="${clip.id}" title="Resize Start"></div>
                <div class="clip-resize-handle right" data-clip-id="${clip.id}" title="Resize End"></div>
            ` : ''}
        `;

        this.setupClipInteractions(clipElement, clip.id, type);
        return clipElement;
    }

    setupClipInteractions(clipElement, clipId, type) {
        // Click to select
        clipElement.addEventListener('click', (e) => {
            if (!e.target.classList.contains('clip-btn')) {
                this.engine.selectClip(clipId);
            }
        });

        // Button events
        clipElement.querySelector('.preview-btn')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.engine.previewClip(clipId);
        });

        clipElement.querySelector('.flip-btn')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.engine.controls.toggleClipFlip(clipId);
        });

        clipElement.querySelector('.delete-btn')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.engine.removeFromTimeline(clipId);
        });

        // Drag functionality
        this.makeClipDraggable(clipElement, clipId, type);

        // Resize functionality (video and image only)
        if (type !== 'audio') {
            this.makeClipResizable(clipElement, clipId, type);
        }
    }

    makeClipDraggable(clipElement, clipId, type) {
        clipElement.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('clip-btn') ||
                e.target.classList.contains('clip-resize-handle')) {
                return;
            }

            e.preventDefault();
            this.isDragging = true;
            this.currentDragClip = clipId;
            this.dragStartX = e.clientX;
            this.dragStartLeft = parseFloat(clipElement.style.left) || 0;

            this.engine.selectClip(clipId);

            const mouseMoveHandler = (e) => {
                if (!this.isDragging) return;

                const deltaX = e.clientX - this.dragStartX;
                let newLeft = Math.max(0, this.dragStartLeft + deltaX);

                // Snap to grid if enabled
                if (this.engine.snapToGrid) {
                    newLeft = Math.round(newLeft / this.engine.snapThreshold) * this.engine.snapThreshold;
                }

                clipElement.style.left = newLeft + 'px';

                const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                            this.engine.audioClips.find(c => c.id === clipId) ||
                            this.engine.imageClips.find(c => c.id === clipId);

                if (clip) {
                    clip.position.x = newLeft;
                    clip.timelineStart = newLeft / this.engine.PIXELS_PER_SECOND;
                    clip.timelineEnd = clip.timelineStart + clip.duration;
                }
            };

            const mouseUpHandler = () => {
                this.isDragging = false;
                this.currentDragClip = null;
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
                document.body.style.cursor = '';

                this.engine.calculateTotalDuration();
                this.engine.updateTimelineUI();
                this.engine.showInfo(`Moved clip to ${this.utils.formatTime(clipElement.style.left / this.engine.PIXELS_PER_SECOND)}`);
            };

            document.body.style.cursor = 'grabbing';
            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        });
    }

    makeClipResizable(clipElement, clipId, type) {
        const setupResizeHandle = (handle, side) => {
            handle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                e.preventDefault();

                this.isDragging = true;
                const startX = e.clientX;
                const startLeft = parseFloat(clipElement.style.left);
                const startWidth = parseFloat(clipElement.style.width);
                const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                            this.engine.imageClips.find(c => c.id === clipId);

                const mouseMoveHandler = (e) => {
                    if (!this.isDragging || !clip) return;

                    const deltaX = e.clientX - startX;

                    if (side === 'left') {
                        const newLeft = Math.max(0, startLeft + deltaX);
                        const newWidth = Math.max(60, startWidth - deltaX);

                        clipElement.style.left = newLeft + 'px';
                        clipElement.style.width = newWidth + 'px';

                        clip.position.x = newLeft;
                        clip.duration = newWidth / this.engine.PIXELS_PER_SECOND;
                        clip.timelineStart = newLeft / this.engine.PIXELS_PER_SECOND;
                        clip.timelineEnd = clip.timelineStart + clip.duration;
                    } else {
                        const newWidth = Math.max(60, startWidth + deltaX);
                        clipElement.style.width = newWidth + 'px';

                        clip.duration = newWidth / this.engine.PIXELS_PER_SECOND;
                        clip.timelineEnd = clip.timelineStart + clip.duration;
                    }
                };

                const mouseUpHandler = () => {
                    this.isDragging = false;
                    document.removeEventListener('mousemove', mouseMoveHandler);
                    document.removeEventListener('mouseup', mouseUpHandler);
                    document.body.style.cursor = '';

                    this.engine.calculateTotalDuration();
                    this.engine.updateTimelineUI();
                    this.engine.showInfo(`Resized clip to ${this.utils.formatTime(clip.duration)}`);
                };

                document.body.style.cursor = 'col-resize';
                document.addEventListener('mousemove', mouseMoveHandler);
                document.addEventListener('mouseup', mouseUpHandler);
            });
        };

        const leftHandle = clipElement.querySelector('.clip-resize-handle.left');
        const rightHandle = clipElement.querySelector('.clip-resize-handle.right');

        if (leftHandle) setupResizeHandle(leftHandle, 'left');
        if (rightHandle) setupResizeHandle(rightHandle, 'right');
    }

    // ========== PLAYHEAD MANAGEMENT ==========

    createPlayhead() {
        const tracks = [this.engine.timelineTrack, this.engine.timelineTrack2, this.engine.audioTrack, this.engine.imageTrack];

        tracks.forEach(track => {
            if (!track) return;

            const existingPlayhead = track.querySelector('.playhead');
            if (existingPlayhead) existingPlayhead.remove();

            const playhead = document.createElement('div');
            playhead.className = 'playhead';
            playhead.innerHTML = `
                <div class="playhead-line"></div>
                <div class="playhead-handle"></div>
                <div class="playhead-time">00:00</div>
            `;
            track.appendChild(playhead);

            if (!this.engine.playheadElement) {
                this.engine.playheadElement = playhead;
            }
        });

        this.setupPlayheadDrag();
    }

    setupPlayheadDrag() {
        if (!this.engine.playheadElement) return;

        let isDragging = false;

        const mouseMoveHandler = (e) => {
            if (!isDragging) return;

            const track = this.engine.playheadElement.parentElement;
            const rect = track.getBoundingClientRect();
            const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
            const totalSeconds = this.engine.totalDuration;
            this.engine.playheadPosition = (x / rect.width) * totalSeconds;

            this.updatePlayhead();
            this.updateTimelineTimeDisplay();
        };

        const mouseUpHandler = () => {
            isDragging = false;
            this.engine.playheadElement.classList.remove('dragging');
            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);
        };

        this.engine.playheadElement.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isDragging = true;
            this.engine.playheadElement.classList.add('dragging');

            if (this.engine.isPlaying) {
                this.engine.stopPlayback();
            }

            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        });
    }

    updatePlayhead() {
        if (!this.engine.playheadElement) return;

        const x = this.engine.playheadPosition * this.engine.PIXELS_PER_SECOND;
        this.engine.playheadElement.style.left = x + 'px';

        const timeDisplay = this.engine.playheadElement.querySelector('.playhead-time');
        if (timeDisplay) {
            timeDisplay.textContent = this.utils.formatTime(this.engine.playheadPosition);
        }

        // Update all playheads
        const allPlayheads = document.querySelectorAll('.playhead');
        allPlayheads.forEach(playhead => {
            playhead.style.left = x + 'px';
            const timeEl = playhead.querySelector('.playhead-time');
            if (timeEl) {
                timeEl.textContent = this.utils.formatTime(this.engine.playheadPosition);
            }
        });
    }

    updateTimelineTimeDisplay() {
        const currentTimeEl = document.getElementById('timelineCurrentTime');
        const totalTimeEl = document.getElementById('timelineTotalTime');

        if (currentTimeEl) {
            currentTimeEl.textContent = this.utils.formatTime(this.engine.playheadPosition);
        }
        if (totalTimeEl) {
            totalTimeEl.textContent = this.utils.formatTime(this.engine.totalDuration);
        }
    }

    // ========== TIMELINE RULER ==========

    generateTimelineRuler() {
        const ruler = document.getElementById('timelineRuler');
        if (!ruler) return;

        const totalSeconds = this.engine.totalDuration;
        const width = this.engine.totalDuration * this.engine.PIXELS_PER_SECOND;

        // Determine mark spacing based on zoom level and total duration
        let markSpacing, timeStep;

        if (totalSeconds <= 300) { // 5 minutes or less
            if (this.engine.zoomLevel <= 50) {
                markSpacing = this.engine.PIXELS_PER_SECOND * 30; // 30 seconds
                timeStep = 30;
            } else if (this.engine.zoomLevel <= 100) {
                markSpacing = this.engine.PIXELS_PER_SECOND * 10; // 10 seconds
                timeStep = 10;
            } else {
                markSpacing = this.engine.PIXELS_PER_SECOND * 5; // 5 seconds
                timeStep = 5;
            }
        } else if (totalSeconds <= 600) { // 10 minutes or less
            if (this.engine.zoomLevel <= 50) {
                markSpacing = this.engine.PIXELS_PER_SECOND * 60; // 1 minute
                timeStep = 60;
            } else if (this.engine.zoomLevel <= 100) {
                markSpacing = this.engine.PIXELS_PER_SECOND * 30; // 30 seconds
                timeStep = 30;
            } else {
                markSpacing = this.engine.PIXELS_PER_SECOND * 15; // 15 seconds
                timeStep = 15;
            }
        } else { // 15 minutes
            if (this.engine.zoomLevel <= 50) {
                markSpacing = this.engine.PIXELS_PER_SECOND * 120; // 2 minutes
                timeStep = 120;
            } else if (this.engine.zoomLevel <= 100) {
                markSpacing = this.engine.PIXELS_PER_SECOND * 60; // 1 minute
                timeStep = 60;
            } else {
                markSpacing = this.engine.PIXELS_PER_SECOND * 30; // 30 seconds
                timeStep = 30;
            }
        }

        let rulerHTML = '';
        const maxMarks = Math.ceil(width / markSpacing);

        for (let i = 0; i <= maxMarks; i++) {
            const x = i * markSpacing;
            const seconds = i * timeStep;

            if (x > width) break;

            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.floor(seconds % 60);

            // Major marks every minute or based on zoom
            const isMajorMark = seconds % 60 === 0 || (timeStep >= 30 && seconds % 60 === 0);
            const isMinuteMark = seconds % 60 === 0;

            rulerHTML += `
                <div class="timeline-ruler-mark ${isMajorMark ? 'major-mark' : 'minor-mark'} ${isMinuteMark ? 'minute-mark' : ''}" 
                     style="left: ${x}px;">
                    <div class="ruler-line ${isMajorMark ? 'major-line' : 'minor-line'}"></div>
                    ${isMajorMark ? `
                    <div class="ruler-label">${minutes}:${remainingSeconds.toString().padStart(2, '0')}</div>
                    ` : ''}
                </div>
            `;

            // Add sub-marks for high zoom levels
            if (this.engine.zoomLevel > 150 && timeStep > 5) {
                for (let j = 1; j < timeStep; j += 5) {
                    const subX = x + (j * this.engine.PIXELS_PER_SECOND);
                    if (subX > width) break;

                    rulerHTML += `
                        <div class="timeline-ruler-mark sub-mark" style="left: ${subX}px;">
                            <div class="ruler-line sub-line"></div>
                        </div>
                    `;
                }
            }
        }

        ruler.innerHTML = rulerHTML;
    }

    // ========== CLIP PROPERTIES PANEL ==========

    showClipProperties(clip) {
        const propertiesContent = document.querySelector('.right-panel .panel-content');
        if (!propertiesContent) return;

        let propertiesHTML = `
            <div class="property-group">
                <h4>📋 Clip Properties</h4>
                <div class="property-item">
                    <span class="prop-label">Name:</span>
                    <span class="prop-value">${clip.name || 'Unknown'}</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Duration:</span>
                    <span class="prop-value">${this.utils.formatTime(clip.duration)}</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Start Time:</span>
                    <span class="prop-value">${this.utils.formatTime(clip.timelineStart)}</span>
                </div>
        `;

        if (clip.type === 'video') {
            propertiesHTML += `
                <div class="property-item">
                    <span class="prop-label">Speed:</span>
                    <input type="range" class="prop-slider" value="${clip.speed * 100}" min="25" max="400" 
                           onchange="window.timelineEngine.controls.adjustClipSpeed('${clip.id}', (this.value / 100) - ${clip.speed})">
                    <span class="prop-value">${clip.speed}x</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Volume:</span>
                    <input type="range" class="prop-slider" value="${(clip.volume || 1) * 100}" min="0" max="200"
                           onchange="window.timelineEngine.controls.adjustClipVolume('${clip.id}', (this.value / 100) - ${clip.volume || 1})">
                    <span class="prop-value">${Math.round((clip.volume || 1) * 100)}%</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Flipped:</span>
                    <span class="prop-value">${clip.flip ? 'Yes' : 'No'}</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Layer:</span>
                    <span class="prop-value">${clip.zIndex || 1}</span>
                </div>
            `;
        } else if (clip.type === 'audio') {
            propertiesHTML += `
                <div class="property-item">
                    <span class="prop-label">Volume:</span>
                    <input type="range" class="prop-slider" value="${(clip.volume || 1) * 100}" min="0" max="200"
                           onchange="window.timelineEngine.controls.adjustClipVolume('${clip.id}', (this.value / 100) - ${clip.volume || 1})">
                    <span class="prop-value">${Math.round((clip.volume || 1) * 100)}%</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Fade In:</span>
                    <input type="checkbox" ${clip.fadeIn ? 'checked' : ''} 
                           onchange="window.timelineEngine.controls.fadeInAudio('${clip.id}')">
                </div>
                <div class="property-item">
                    <span class="prop-label">Fade Out:</span>
                    <input type="checkbox" ${clip.fadeOut ? 'checked' : ''}
                           onchange="window.timelineEngine.controls.fadeOutAudio('${clip.id}')">
                </div>
            `;
        } else if (clip.type === 'image') {
            propertiesHTML += `
                <div class="property-item">
                    <span class="prop-label">Opacity:</span>
                    <input type="range" class="prop-slider" value="${(clip.opacity || 1) * 100}" min="0" max="100"
                           onchange="window.timelineEngine.clipManager.updateClipProperties('${clip.id}', {opacity: this.value / 100})">
                    <span class="prop-value">${Math.round((clip.opacity || 1) * 100)}%</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Scale:</span>
                    <input type="range" class="prop-slider" value="${(clip.scale || 1) * 100}" min="10" max="200"
                           onchange="window.timelineEngine.clipManager.updateClipProperties('${clip.id}', {scale: this.value / 100})">
                    <span class="prop-value">${(clip.scale || 1).toFixed(1)}x</span>
                </div>
            `;
        }

        propertiesHTML += `
            </div>
            <div class="property-actions">
                <button class="btn btn-secondary" onclick="window.timelineEngine.previewClip('${clip.id}')">
                    ▶️ Preview Clip
                </button>
                ${clip.type === 'video' ? `
                <button class="btn btn-secondary" onclick="window.timelineEngine.controls.toggleClipFlip('${clip.id}')">
                    ${clip.flip ? '🔄 Unflip' : '↔️ Flip'} Video
                </button>
                ` : ''}
                <button class="btn btn-danger" onclick="window.timelineEngine.removeFromTimeline('${clip.id}')">
                    🗑️ Delete Clip
                </button>
            </div>
        `;

        propertiesContent.innerHTML = propertiesHTML;
    }

    hideClipProperties() {
        const propertiesContent = document.querySelector('.right-panel .panel-content');
        if (!propertiesContent) return;

        propertiesContent.innerHTML = `
            <div class="property-group">
                <h4>📊 Timeline Information</h4>
                <div class="property-item">
                    <span class="prop-label">Total Duration:</span>
                    <span class="prop-value" id="propTotalDuration">00:00</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Video Clips:</span>
                    <span class="prop-value" id="propVideoClips">0</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Audio Clips:</span>
                    <span class="prop-value" id="propAudioClips">0</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Image Clips:</span>
                    <span class="prop-value" id="propImageClips">0</span>
                </div>
                <div class="property-item">
                    <span class="prop-label">Zoom Level:</span>
                    <span class="prop-value" id="propZoom">100%</span>
                </div>
            </div>

            <div class="property-group">
                <h4>⚙️ Timeline Controls</h4>
                <div class="property-actions">
                    <button class="btn btn-primary" onclick="window.timelineEngine.toggleTimelinePlayback()">
                        ▶️ Play/Pause
                    </button>
                    <button class="btn btn-secondary" onclick="window.timelineEngine.zoomIn()">
                        🔍 Zoom In
                    </button>
                    <button class="btn btn-secondary" onclick="window.timelineEngine.zoomOut()">
                        🔍 Zoom Out
                    </button>
                    <button class="btn btn-secondary" onclick="window.timelineEngine.fitTimeline()">
                        📐 Fit Timeline
                    </button>
                </div>
            </div>
        `;

        this.updateTimelineStats();
    }

    // ========== UTILITY METHODS ==========

    updateTimelineStats() {
        const totalClips = this.engine.timelineClips.length + this.engine.audioClips.length + this.engine.imageClips.length;
        const totalDuration = this.engine.totalDuration;

        // Update properties panel
        const propTotalDuration = document.getElementById('propTotalDuration');
        const propVideoClips = document.getElementById('propVideoClips');
        const propAudioClips = document.getElementById('propAudioClips');
        const propImageClips = document.getElementById('propImageClips');
        const propZoom = document.getElementById('propZoom');

        if (propTotalDuration) propTotalDuration.textContent = this.utils.formatTime(totalDuration);
        if (propVideoClips) propVideoClips.textContent = this.engine.timelineClips.length;
        if (propAudioClips) propAudioClips.textContent = this.engine.audioClips.length;
        if (propImageClips) propImageClips.textContent = this.engine.imageClips.length;
        if (propZoom) propZoom.textContent = this.engine.zoomLevel + '%';

        // Update main timeline stats
        const timelineStats = document.getElementById('timelineStats');
        if (timelineStats) {
            timelineStats.innerHTML = `
                <span>Clips: ${totalClips}</span>
                <span>Duration: ${this.utils.formatTime(totalDuration)}</span>
                <span>Zoom: ${this.engine.zoomLevel}%</span>
            `;
        }
    }

    // Handle window resize
    handleResize() {
        this.engine.calculateTotalDuration();
        this.generateTimelineRuler();
        this.updatePlayhead();
        this.updateTimelineUI();
    }

    // Export timeline as image (for debugging)
    exportTimelineSnapshot() {
        const timelineContainer = document.querySelector('.timeline-container');
        if (!timelineContainer) return;

        html2canvas(timelineContainer).then(canvas => {
            const link = document.createElement('a');
            link.download = `timeline-snapshot-${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();
        });
    }
}

export default TimelineUI;