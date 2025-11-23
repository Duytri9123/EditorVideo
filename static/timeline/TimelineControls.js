// TimelineControls.js - Enhanced Timeline Control Management
export class TimelineControls {
    constructor(engine) {
        this.engine = engine;
    }

    zoomIn() {
        this.engine.zoomLevel = Math.min(200, this.engine.zoomLevel + 10);
        this.engine.PIXELS_PER_SECOND = (40 * this.engine.zoomLevel) / 100;
        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.ui.generateTimelineRuler();
        this.engine.showInfo(`🔍 Zoom: ${this.engine.zoomLevel}%`);
    }

    zoomOut() {
        this.engine.zoomLevel = Math.max(50, this.engine.zoomLevel - 10);
        this.engine.PIXELS_PER_SECOND = (40 * this.engine.zoomLevel) / 100;
        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.ui.generateTimelineRuler();
        this.engine.showInfo(`🔍 Zoom: ${this.engine.zoomLevel}%`);
    }

    fitTimeline() {
        const totalSeconds = this.engine.totalDuration;
        const viewportWidth = this.engine.timelineTrack?.parentElement?.clientWidth || 800;

        if (totalSeconds > 0) {
            const targetPixelsPerSecond = (viewportWidth * 0.9) / totalSeconds;
            this.engine.zoomLevel = Math.max(50, Math.min(200, (targetPixelsPerSecond / 40) * 100));
            this.engine.PIXELS_PER_SECOND = (40 * this.engine.zoomLevel) / 100;
            this.engine.calculateTotalDuration();
            this.engine.updateTimelineUI();
            this.engine.ui.generateTimelineRuler();
            this.engine.showInfo(`🔍 Fit to view: ${this.engine.zoomLevel}%`);
        }
    }

    toggleSnap() {
        this.engine.snapToGrid = !this.engine.snapToGrid;
        this.updateSnapButton();
        this.engine.showInfo(this.engine.snapToGrid ? '🧲 Snap enabled' : '🧲 Snap disabled');
    }

    updateSnapButton() {
        const snapButton = document.getElementById('snapToggle');
        const timelineSnapButton = document.getElementById('timelineSnapToggle');

        const isActive = this.engine.snapToGrid;

        if (snapButton) {
            if (isActive) {
                snapButton.classList.add('active');
                snapButton.title = 'Snap: ON';
            } else {
                snapButton.classList.remove('active');
                snapButton.title = 'Snap: OFF';
            }
        }

        if (timelineSnapButton) {
            if (isActive) {
                timelineSnapButton.classList.add('active');
                timelineSnapButton.title = 'Snap: ON';
            } else {
                timelineSnapButton.classList.remove('active');
                timelineSnapButton.title = 'Snap: OFF';
            }
        }
    }

    splitAtPlayhead() {
        if (!this.engine.selectedClipId) {
            this.engine.showWarning('⚠️ Please select a clip first');
            return;
        }

        const clip = this.engine.timelineClips.find(c => c.id === this.engine.selectedClipId);
        if (!clip) {
            this.engine.showWarning('⚠️ Selected clip not found');
            return;
        }

        const splitTime = this.engine.playheadPosition;
        if (splitTime <= clip.timelineStart || splitTime >= clip.timelineEnd) {
            this.engine.showWarning('⚠️ Playhead must be within the selected clip');
            return;
        }

        const newClip = {
            ...clip,
            id: this.engine.utils.generateId(),
            timelineStart: splitTime,
            position: {
                x: splitTime * this.engine.PIXELS_PER_SECOND,
                y: clip.position.y
            },
            duration: clip.timelineEnd - splitTime
        };

        clip.timelineEnd = splitTime;
        clip.duration = splitTime - clip.timelineStart;

        this.engine.timelineClips.push(newClip);
        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.showSuccess('✂️ Clip split successfully');
    }

    seekToStart() {
        this.engine.playheadPosition = 0;
        this.engine.ui.updatePlayhead();
        this.engine.ui.updateTimelineTimeDisplay();
        this.engine.playback.updateVideoPreview();
    }

    seekToEnd() {
        this.engine.playheadPosition = this.engine.totalDuration;
        this.engine.ui.updatePlayhead();
        this.engine.ui.updateTimelineTimeDisplay();
        this.engine.playback.updateVideoPreview();
    }

    clearTimeline() {
        if (this.engine.timelineClips.length === 0 && this.engine.audioClips.length === 0) return;

        if (confirm('Are you sure you want to clear the entire timeline?')) {
            this.engine.timelineClips = [];
            this.engine.audioClips = [];
            this.engine.selectedClipId = null;
            this.engine.zIndexCounter = 0;
            this.engine.totalDuration = 0;
            this.engine.playheadPosition = 0;
            this.engine.stopPlayback();
            this.engine.ui.hideClipProperties();
            this.engine.updateTimelineUI();
            this.engine.showSuccess('🗑️ Timeline cleared');
        }
    }

    exportTimeline() {
        if (this.engine.timelineClips.length === 0 && this.engine.audioClips.length === 0) {
            this.engine.showWarning('⚠️ No clips in timeline to export');
            return;
        }

        const project = {
            version: '2.0',
            timestamp: new Date().toISOString(),
            clips: this.engine.timelineClips,
            audioClips: this.engine.audioClips,
            totalDuration: this.engine.totalDuration,
            zoomLevel: this.engine.zoomLevel,
            exportSettings: {
                format: document.getElementById('exportFormat')?.value || 'mp4',
                quality: document.getElementById('exportQuality')?.value || 'high',
                resolution: document.getElementById('exportResolution')?.value || 'original'
            }
        };

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(project, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `timeline_project_${Date.now()}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();

        this.engine.showSuccess('📤 Timeline project exported successfully');
    }

    toggleClipFlip(clipId) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId);
        if (clip) {
            clip.flip = !clip.flip;
            this.engine.updateTimelineUI();
            this.engine.selectClip(clipId);
            this.engine.showInfo(`Video ${clip.flip ? 'flipped' : 'unflipped'}`);
        }
    }

    moveLayer(clipId, direction) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId);
        if (!clip) return;

        const currentIndex = this.engine.timelineClips.indexOf(clip);
        let newIndex;

        if (direction === 'up') {
            newIndex = Math.min(this.engine.timelineClips.length - 1, currentIndex + 1);
        } else {
            newIndex = Math.max(0, currentIndex - 1);
        }

        if (newIndex !== currentIndex) {
            const tempZ = clip.zIndex;
            clip.zIndex = this.engine.timelineClips[newIndex].zIndex;
            this.engine.timelineClips[newIndex].zIndex = tempZ;

            [this.engine.timelineClips[currentIndex], this.engine.timelineClips[newIndex]] =
            [this.engine.timelineClips[newIndex], this.engine.timelineClips[currentIndex]];

            this.engine.updateTimelineUI();
            this.engine.selectClip(clipId);
            this.engine.showSuccess(`🔄 Moved clip ${direction}`);
        }
    }

    bringToFront(clipId) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId);
        if (!clip) return;

        this.engine.zIndexCounter++;
        clip.zIndex = this.engine.zIndexCounter;

        const index = this.engine.timelineClips.indexOf(clip);
        this.engine.timelineClips.splice(index, 1);
        this.engine.timelineClips.push(clip);

        this.engine.updateTimelineUI();
        this.engine.selectClip(clipId);
        this.engine.showSuccess('🎯 Brought clip to front');
    }

    sendToBack(clipId) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId);
        if (!clip) return;

        clip.zIndex = 1;

        const index = this.engine.timelineClips.indexOf(clip);
        this.engine.timelineClips.splice(index, 1);
        this.engine.timelineClips.unshift(clip);

        this.engine.timelineClips.forEach((c, i) => {
            c.zIndex = i + 1;
        });
        this.engine.zIndexCounter = this.engine.timelineClips.length;

        this.engine.updateTimelineUI();
        this.engine.selectClip(clipId);
        this.engine.showSuccess('⏮️ Sent clip to back');
    }

    moveClipTime(clipId, direction) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                    this.engine.audioClips.find(c => c.id === clipId);
        if (!clip) return;

        const shiftAmount = 1;
        const pixelShift = shiftAmount * this.engine.PIXELS_PER_SECOND;

        if (direction === 'left') {
            clip.timelineStart = Math.max(0, clip.timelineStart - shiftAmount);
            clip.timelineEnd = clip.timelineStart + clip.duration;
            clip.position.x = Math.max(0, clip.position.x - pixelShift);
        } else if (direction === 'right') {
            clip.timelineStart += shiftAmount;
            clip.timelineEnd = clip.timelineStart + clip.duration;
            clip.position.x += pixelShift;
        }

        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.selectClip(clipId);
        this.engine.showInfo(`Moved clip ${direction}`);
    }

    playPauseClip(clipId) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                    this.engine.audioClips.find(c => c.id === clipId);
        if (!clip) return;

        if (this.engine.currentPreviewClip === clipId && this.engine.isPreviewing) {
            this.engine.stopPreview();
        } else {
            this.engine.previewClip(clipId);
        }
    }

    jumpToClip(clipId) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                    this.engine.audioClips.find(c => c.id === clipId);
        if (!clip) return;

        this.engine.playheadPosition = clip.timelineStart;
        this.engine.ui.updatePlayhead();
        this.engine.ui.updateTimelineTimeDisplay();
        this.engine.playback.updateVideoPreview();
        this.engine.showInfo(`Jumped to clip: ${clip.name}`);
    }

    deleteClip(clipId) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                    this.engine.audioClips.find(c => c.id === clipId);
        if (!clip) return;

        if (confirm(`Are you sure you want to delete "${clip.name}"?`)) {
            this.engine.removeFromTimeline(clipId);
        }
    }

    adjustClipSpeed(clipId, speedChange) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId);
        if (!clip || clip.type === 'audio') return;

        const newSpeed = Math.max(0.25, Math.min(4, clip.speed + speedChange));
        clip.speed = newSpeed;

        this.engine.updateTimelineUI();
        this.engine.selectClip(clipId);
        this.engine.showInfo(`Speed: ${newSpeed}x`);
    }

    adjustClipVolume(clipId, volumeChange) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                    this.engine.audioClips.find(c => c.id === clipId);
        if (!clip) return;

        const newVolume = Math.max(0, Math.min(2, clip.volume + volumeChange));
        clip.volume = newVolume;

        this.engine.updateTimelineUI();
        this.engine.selectClip(clipId);
        this.engine.showInfo(`Volume: ${Math.round(newVolume * 100)}%`);
    }

    fadeInAudio(clipId) {
        const clip = this.engine.audioClips.find(c => c.id === clipId);
        if (clip) {
            clip.fadeIn = true;
            clip.fadeOut = false;
            this.engine.showInfo('Fade in effect applied to audio');
        }
    }

    fadeOutAudio(clipId) {
        const clip = this.engine.audioClips.find(c => c.id === clipId);
        if (clip) {
            clip.fadeOut = true;
            clip.fadeIn = false;
            this.engine.showInfo('Fade out effect applied to audio');
        }
    }
}

export default TimelineControls;