// TimelineEngine.js - Enhanced Timeline Engine for 15-minute videos
import { TimelineUI } from './TimelineUI.js';
import { TimelinePlayback } from './TimelinePlayback.js';
import { ClipManager } from './ClipManager.js';
import { TimelineControls } from './TimelineControls.js';
import { NotificationManager } from './NotificationManager.js';
import { TimelineUtils } from './TimelineUtils.js';

export class TimelineEngine {
    constructor() {
        // Core state
        this.timelineClips = [];       // Video clips
        this.audioClips = [];          // Audio clips
        this.imageClips = [];          // Image clips (logos)
        this.currentVideo = null;
        this.isProcessing = false;
        this.zoomLevel = 100;
        this.selectedClipId = null;
        this.isInitialized = false;
        this.currentTime = 0;
        this.totalDuration = 0;
        this.isPlaying = false;
        this.playheadPosition = 0;
        this.currentPreviewClip = null;
        this.PIXELS_PER_SECOND = 40;   // Reduced for longer videos
        this.snapToGrid = true;
        this.snapThreshold = 8;
        this.transitionDuration = 0.5;
        this.volume = 1.0;
        this.zIndexCounter = 0;

        // Preview state
        this.previewVideo = null;
        this.isPreviewing = false;
        this.currentPreviewTime = 0;
        this.previewAudio = null;

        // DOM elements
        this.timelineContainer = null;
        this.timelineTrack = null;
        this.timelineViewport = null;
        this.playheadElement = null;

        // Performance optimization
        this.rafId = null;
        this.lastUpdateTime = 0;
        this.updateInterval = 1000 / 30; // 30fps
        this.isDragging = false;
        this.dragData = null;

        // Timeline limits for 15-minute videos
        this.MIN_TIMELINE_DURATION = 20;   // 20 seconds
        this.MAX_TIMELINE_DURATION = 900;  // 15 minutes

        // Initialize modules
        this.ui = new TimelineUI(this);
        this.playback = new TimelinePlayback(this);
        this.clipManager = new ClipManager(this);
        this.controls = new TimelineControls(this);
        this.notifications = new NotificationManager();
        this.utils = new TimelineUtils();

        this.init();
    }

    init() {
        console.log('🚀 Timeline Engine initialized for 15-minute videos');
        this.ui.createUIElements();
        this.ui.setupTimelineUI();
        this.setupGlobalEventListeners();
        this.isInitialized = true;

        // Load saved timeline if available
        this.loadSavedTimeline();
    }

    // ENHANCED: Proper duration calculation for long videos
    calculateTotalDuration() {
        // Calculate based on video clips
        const videoDuration = this.timelineClips.reduce((total, clip) => {
            const clipEnd = clip.timelineEnd || (clip.timelineStart + clip.duration);
            return Math.max(total, clipEnd);
        }, 0);

        // Calculate based on audio clips
        const audioDuration = this.audioClips.reduce((total, clip) => {
            const clipEnd = clip.timelineEnd || (clip.timelineStart + clip.duration);
            return Math.max(total, clipEnd);
        }, 0);

        // Calculate based on image clips
        const imageDuration = this.imageClips.reduce((total, clip) => {
            const clipEnd = clip.timelineEnd || (clip.timelineStart + clip.duration);
            return Math.max(total, clipEnd);
        }, 0);

        // Get the maximum duration from all
        const maxDuration = Math.max(videoDuration, audioDuration, imageDuration);

        // Apply timeline limits (20 seconds minimum, 15 minutes maximum)
        const limitedDuration = Math.max(this.MIN_TIMELINE_DURATION,
                                       Math.min(this.MAX_TIMELINE_DURATION, maxDuration));

        this.totalDuration = limitedDuration;

        console.log(`Timeline Duration: ${maxDuration}s -> Limited to: ${limitedDuration}s`);

        // Update timeline track width with better scaling
        if (this.timelineTrack) {
            const trackWidth = Math.max(800, limitedDuration * this.PIXELS_PER_SECOND);
            this.timelineTrack.style.width = trackWidth + 'px';

            // Update all tracks
            const tracks = document.querySelectorAll('.track-content');
            tracks.forEach(track => {
                if (track !== this.timelineTrack) {
                    track.style.width = trackWidth + 'px';
                }
            });
        }

        this.ui.generateTimelineRuler();
        this.ui.updateTimelineStats();
    }

    // NEW: Add image/logo to timeline
    addImageToTimeline(imagePath, duration = 10, startTime = 0, clipName = null) {
        const clip = {
            id: this.utils.generateId(),
            file: imagePath,
            name: clipName || this.utils.getFileName(imagePath),
            duration: duration,
            timelineStart: startTime,
            timelineEnd: startTime + duration,
            position: {
                x: startTime * this.PIXELS_PER_SECOND,
                y: this.getNextImageTrackPosition()
            },
            zIndex: ++this.zIndexCounter,
            type: 'image',
            track: 'image',
            opacity: 1.0,
            scale: 1.0
        };

        this.imageClips.push(clip);
        this.calculateTotalDuration();
        this.updateTimelineUI();
        this.showSuccess(`✅ Added logo "${clip.name}" to timeline`);

        return clip;
    }

    // NEW: Get next available position for image track
    getNextImageTrackPosition() {
        const positions = this.imageClips.map(clip => clip.position.y);
        if (positions.length === 0) return 0;
        const maxPosition = Math.max(...positions);
        return (maxPosition + 60) % 120;
    }

    // Delegation methods to modules
    addToTimeline(videoPath, startTime = 0, endTime = null, clipName = null) {
        const clip = this.clipManager.addToTimeline(videoPath, startTime, endTime, clipName);
        if (clip) {
            this.calculateTotalDuration();
        }
        return clip;
    }

    addAudioToTimeline(audioPath, clipName = null) {
        const clip = this.clipManager.addAudioToTimeline(audioPath, clipName);
        if (clip) {
            this.calculateTotalDuration();
        }
        return clip;
    }

    removeFromTimeline(clipId) {
        let removedClip = null;

        // Remove from video clips
        const videoIndex = this.timelineClips.findIndex(clip => clip.id === clipId);
        if (videoIndex !== -1) {
            removedClip = this.timelineClips.splice(videoIndex, 1)[0];
        }

        // Remove from audio clips
        const audioIndex = this.audioClips.findIndex(clip => clip.id === clipId);
        if (audioIndex !== -1) {
            removedClip = this.audioClips.splice(audioIndex, 1)[0];
        }

        // Remove from image clips
        const imageIndex = this.imageClips.findIndex(clip => clip.id === clipId);
        if (imageIndex !== -1) {
            removedClip = this.imageClips.splice(imageIndex, 1)[0];
        }

        if (removedClip) {
            this.showSuccess(`🗑️ Removed "${removedClip.name}" from timeline`);
        }

        // Clear selection if removed clip was selected
        if (this.selectedClipId === clipId) {
            this.selectedClipId = null;
            this.ui.hideClipProperties();
        }

        this.calculateTotalDuration();
        this.updateTimelineUI();

        return removedClip;
    }

    // Enhanced preview functionality for long videos
    previewClip(clipId) {
        const clip = this.timelineClips.find(c => c.id === clipId) ||
                    this.audioClips.find(c => c.id === clipId) ||
                    this.imageClips.find(c => c.id === clipId);

        if (!clip) return;

        this.stopPlayback();
        this.isPreviewing = true;
        this.currentPreviewClip = clipId;

        if (clip.type === 'video') {
            this.previewVideoClip(clip);
        } else if (clip.type === 'audio') {
            this.previewAudioClip(clip);
        } else if (clip.type === 'image') {
            this.previewImageClip(clip);
        }
    }

    previewVideoClip(clip) {
        if (!this.previewVideo) {
            this.createPreviewContainer();
        }

        this.previewVideo.src = clip.file;
        this.previewVideo.currentTime = 0;
        this.previewVideo.volume = clip.volume || 1.0;
        this.previewVideo.playbackRate = clip.speed || 1.0;

        // Apply video effects
        this.applyVideoEffects(clip);

        this.previewVideo.play().catch(e => {
            console.log('Preview play failed:', e);
        });

        this.showSuccess(`Previewing: ${clip.name}`);
    }

    previewAudioClip(clip) {
        if (this.previewAudio) {
            this.previewAudio.pause();
        }

        this.previewAudio = new Audio(clip.file);
        this.previewAudio.volume = clip.volume || 1.0;
        this.previewAudio.play().catch(e => {
            console.log('Audio preview play failed:', e);
        });

        this.showSuccess(`Playing audio: ${clip.name}`);
    }

    previewImageClip(clip) {
        if (!this.previewVideo) {
            this.createPreviewContainer();
        }

        // For image preview, we'll show the image in the preview container
        const previewContainer = document.getElementById('previewContainer');
        if (previewContainer) {
            const img = document.createElement('img');
            img.src = clip.file;
            img.style.maxWidth = '100%';
            img.style.maxHeight = '400px';
            img.style.display = 'block';
            img.style.margin = '0 auto';

            previewContainer.innerHTML = '';
            previewContainer.appendChild(img);
            previewContainer.style.display = 'block';
        }

        this.showSuccess(`Showing image: ${clip.name}`);
    }

    applyVideoEffects(clip) {
        if (!this.previewVideo) return;

        let transform = '';
        if (clip.flip) {
            transform += 'scaleX(-1) ';
        }
        if (clip.rotate) {
            transform += `rotate(${clip.rotate}deg) `;
        }

        this.previewVideo.style.transform = transform.trim();
    }

    createPreviewContainer() {
        let previewContainer = document.getElementById('previewContainer');
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.id = 'previewContainer';
            previewContainer.style.cssText = `
                padding: 15px;
                border: 1px solid #ccc;
                margin: 10px 0;
                border-radius: 8px;
                background: #2d3748;
                text-align: center;
            `;

            this.previewVideo = document.createElement('video');
            this.previewVideo.controls = true;
            this.previewVideo.style.maxWidth = '100%';
            this.previewVideo.style.maxHeight = '400px';
            this.previewVideo.style.background = '#000';

            previewContainer.appendChild(this.previewVideo);

            if (this.timelineContainer) {
                this.timelineContainer.parentNode.insertBefore(previewContainer, this.timelineContainer);
            } else {
                document.body.appendChild(previewContainer);
            }
        }

        previewContainer.style.display = 'block';
        return previewContainer;
    }

    stopPreview() {
        if (this.previewVideo) {
            this.previewVideo.pause();
            this.previewVideo.currentTime = 0;
        }
        if (this.previewAudio) {
            this.previewAudio.pause();
            this.previewAudio.currentTime = 0;
        }
        this.isPreviewing = false;
        this.currentPreviewClip = null;

        const previewContainer = document.getElementById('previewContainer');
        if (previewContainer) {
            previewContainer.style.display = 'none';
        }
    }

    // Enhanced playback for full timeline
    startTimelinePlayback() {
        if (this.timelineClips.length === 0 && this.audioClips.length === 0 && this.imageClips.length === 0) {
            this.showWarning('⚠️ No clips in timeline to play');
            return;
        }

        this.playback.startTimelinePlayback();
    }

    stopPlayback() {
        this.playback.stopPlayback();
    }

    toggleTimelinePlayback() {
        if (this.isPlaying) {
            this.stopPlayback();
        } else {
            this.startTimelinePlayback();
        }
    }

    // Rest of the methods remain similar but enhanced for longer videos...
    selectClip(clipId) {
        this.selectedClipId = clipId;
        const clip = this.timelineClips.find(c => c.id === clipId) ||
                    this.audioClips.find(c => c.id === clipId) ||
                    this.imageClips.find(c => c.id === clipId);
        if (clip) {
            this.ui.showClipProperties(clip);
            this.updateTimelineUI();
        }
    }

    updateTimelineUI() {
        this.ui.updateTimelineUI();
    }

    // Notification methods
    showSuccess(message) {
        this.notifications.showSuccess(message);
    }

    showError(message) {
        this.notifications.showError(message);
    }

    showWarning(message) {
        this.notifications.showWarning(message);
    }

    showInfo(message) {
        this.notifications.showInfo(message);
    }

    // Global event listeners
    setupGlobalEventListeners() {
        // ... existing event listeners enhanced for longer videos
    }

    // Save/Load timeline
    saveTimeline() {
        const project = {
            version: '3.0',
            timestamp: new Date().toISOString(),
            clips: this.timelineClips,
            audioClips: this.audioClips,
            imageClips: this.imageClips,
            totalDuration: this.totalDuration,
            zoomLevel: this.zoomLevel,
            playheadPosition: this.playheadPosition
        };

        localStorage.setItem('timelineProject', JSON.stringify(project));
        this.showSuccess('💾 Timeline project saved');
        return project;
    }

    loadSavedTimeline() {
        try {
            const saved = localStorage.getItem('timelineProject');
            if (!saved) return false;

            const project = JSON.parse(saved);

            if (project.version === '3.0') {
                this.timelineClips = project.clips || [];
                this.audioClips = project.audioClips || [];
                this.imageClips = project.imageClips || [];
            } else {
                // Migrate from older versions
                this.timelineClips = project.clips || [];
                this.audioClips = project.audioClips || [];
                this.imageClips = [];
            }

            this.zoomLevel = project.zoomLevel || 100;
            this.playheadPosition = project.playheadPosition || 0;
            this.PIXELS_PER_SECOND = (40 * this.zoomLevel) / 100;

            this.calculateTotalDuration();
            this.updateTimelineUI();

            this.showSuccess('📁 Timeline project loaded');
            return true;

        } catch (error) {
            console.warn('Failed to load saved timeline:', error);
            return false;
        }
    }

    // Cleanup
    cleanup() {
        this.stopPlayback();
        this.stopPreview();

        if (this.previewVideo) {
            this.previewVideo.pause();
            this.previewVideo.src = '';
            if (this.previewVideo.parentNode) {
                this.previewVideo.parentNode.removeChild(this.previewVideo);
            }
        }

        if (this.previewAudio) {
            this.previewAudio.pause();
            this.previewAudio.src = '';
        }

        // Cleanup blob URLs
        [...this.timelineClips, ...this.audioClips, ...this.imageClips].forEach(clip => {
            if (clip.file.startsWith('blob:')) {
                URL.revokeObjectURL(clip.file);
            }
        });

        this.saveTimeline();
    }

    // Utility methods
    getStats() {
        return {
            totalClips: this.timelineClips.length + this.audioClips.length + this.imageClips.length,
            videoClips: this.timelineClips.length,
            audioClips: this.audioClips.length,
            imageClips: this.imageClips.length,
            totalDuration: this.totalDuration,
            zoomLevel: this.zoomLevel,
            isPlaying: this.isPlaying
        };
    }

    // Reset engine
    reset() {
        this.timelineClips = [];
        this.audioClips = [];
        this.imageClips = [];
        this.selectedClipId = null;
        this.zIndexCounter = 0;
        this.totalDuration = this.MIN_TIMELINE_DURATION;
        this.playheadPosition = 0;
        this.zoomLevel = 100;
        this.PIXELS_PER_SECOND = 40;

        this.stopPlayback();
        this.stopPreview();
        this.ui.hideClipProperties();
        this.updateTimelineUI();

        localStorage.removeItem('timelineProject');
        this.showSuccess('🔄 Timeline reset');
    }

    // Delegate to controls
    zoomIn() { this.controls.zoomIn(); }
    zoomOut() { this.controls.zoomOut(); }
    fitTimeline() { this.controls.fitTimeline(); }
    toggleSnap() { this.controls.toggleSnap(); }
    splitAtPlayhead() { this.controls.splitAtPlayhead(); }
    seekToStart() { this.controls.seekToStart(); }
    seekToEnd() { this.controls.seekToEnd(); }
    clearTimeline() { this.controls.clearTimeline(); }
    exportTimeline() { this.controls.exportTimeline(); }
}

// Make available globally
window.TimelineEngine = TimelineEngine;
export default TimelineEngine;