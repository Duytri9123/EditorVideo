// TimelinePlayback.js - Enhanced Timeline Playback with Real Preview Integration
import { TimelineUtils } from './TimelineUtils.js';

export class TimelinePlayback {
    constructor(engine) {
        this.engine = engine;
        this.utils = new TimelineUtils();
        this.isPlaying = false;
        this.playbackInterval = null;
        this.currentTime = 0;
        this.playbackSpeed = 1.0;
    }

    startTimelinePlayback() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.engine.isPlaying = true;
        this.currentTime = this.engine.playheadPosition;

        // Update UI
        this.updatePlaybackUI(true);

        // Start playback loop
        this.playbackInterval = setInterval(() => {
            this.updatePlayback();
        }, 1000 / 30); // 30fps

        this.engine.showSuccess('▶️ Timeline playback started');
    }

    stopPlayback() {
        this.isPlaying = false;
        this.engine.isPlaying = false;

        if (this.playbackInterval) {
            clearInterval(this.playbackInterval);
            this.playbackInterval = null;
        }

        // Update UI
        this.updatePlaybackUI(false);

        this.engine.showInfo('⏸️ Timeline playback stopped');
    }

    updatePlayback() {
        if (!this.isPlaying) return;

        // Increment time based on playback speed
        this.currentTime += (1 / 30) * this.playbackSpeed; // 30fps

        // Check if reached end
        if (this.currentTime >= this.engine.totalDuration) {
            this.stopPlayback();
            this.currentTime = 0;
            return;
        }

        // Update engine state
        this.engine.playheadPosition = this.currentTime;

        // Update UI
        this.engine.ui.updatePlayhead();
        this.engine.ui.updateTimelineTimeDisplay();

        // Update preview with current frame
        this.updatePreviewWithCurrentFrame();

        // Update properties panel
        this.engine.ui.updateTimelineStats();
    }

    updatePreviewWithCurrentFrame() {
        // Find the current clip at the playhead position
        const currentClip = this.findClipAtTime(this.currentTime);

        if (currentClip && currentClip.file) {
            // Update the main preview with the current clip
            const previewVideo = document.getElementById('mainPreview');
            if (previewVideo && previewVideo.src !== currentClip.file) {
                previewVideo.src = currentClip.file;
            }

            // Calculate the time within the current clip
            const clipTime = this.currentTime - currentClip.timelineStart;

            // Only seek if the time difference is significant (more than 0.5 seconds)
            if (previewVideo.currentTime === 0 || Math.abs(previewVideo.currentTime - clipTime) > 0.5) {
                previewVideo.currentTime = clipTime;
            }

            // Play the preview video if it's paused
            if (previewVideo.paused) {
                previewVideo.play().catch(e => {
                    console.log('Preview play failed:', e);
                });
            }
        }
    }

    findClipAtTime(time) {
        // Search video clips
        for (const clip of this.engine.timelineClips) {
            if (time >= clip.timelineStart && time <= clip.timelineEnd) {
                return clip;
            }
        }

        // Search audio clips
        for (const clip of this.engine.audioClips) {
            if (time >= clip.timelineStart && time <= clip.timelineEnd) {
                return clip;
            }
        }

        // Search image clips
        for (const clip of this.engine.imageClips) {
            if (time >= clip.timelineStart && time <= clip.timelineEnd) {
                return clip;
            }
        }

        return null;
    }

    updatePlaybackUI(isPlaying) {
        const playPauseBtn = document.getElementById('timelinePlayPause');
        if (playPauseBtn) {
            playPauseBtn.innerHTML = isPlaying ?
                '<i class="fas fa-pause"></i> Pause' :
                '<i class="fas fa-play"></i> Play';
        }

        // Update timeline status
        const statusElement = document.getElementById('timelineStatus');
        if (statusElement) {
            statusElement.textContent = isPlaying ?
                '▶️ Timeline playing' :
                '⏸️ Timeline paused';
            statusElement.className = `status-message ${isPlaying ? 'status-info' : 'status-warning'}`;
        }
    }

    setPlaybackSpeed(speed) {
        this.playbackSpeed = Math.max(0.25, Math.min(4.0, speed));
        this.engine.showInfo(`Playback speed: ${this.playbackSpeed}x`);
    }

    seekTo(time) {
        this.currentTime = Math.max(0, Math.min(this.engine.totalDuration, time));
        this.engine.playheadPosition = this.currentTime;

        // Update UI
        this.engine.ui.updatePlayhead();
        this.engine.ui.updateTimelineTimeDisplay();

        // Update preview
        this.updatePreviewWithCurrentFrame();
    }

    // Handle clip transitions and effects during playback
    applyClipEffects(clip, currentTime) {
        if (!clip.effects) return;

        const clipTime = currentTime - clip.timelineStart;

        // Apply fade in/out for audio
        if (clip.type === 'audio' && clipTime <= 2) {
            // Fade in first 2 seconds
            const volume = Math.min(1, clipTime / 2);
            this.setAudioVolume(clip, volume * (clip.volume || 1));
        } else if (clip.type === 'audio' && clipTime >= clip.duration - 2) {
            // Fade out last 2 seconds
            const volume = Math.min(1, (clip.duration - clipTime) / 2);
            this.setAudioVolume(clip, volume * (clip.volume || 1));
        }

        // Apply video effects
        if (clip.type === 'video') {
            this.applyVideoEffects(clip, clipTime);
        }
    }

    setAudioVolume(clip, volume) {
        // This would control the actual audio element volume
        // In a real implementation, you'd have an audio context
        console.log(`Setting volume for ${clip.name} to ${volume}`);
    }

    applyVideoEffects(clip, clipTime) {
        // Apply any time-based video effects
        // This would be handled by the video processing backend
    }

    // Cleanup
    cleanup() {
        this.stopPlayback();
    }
}

export default TimelinePlayback;