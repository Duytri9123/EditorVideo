// ClipManager.js - Enhanced Clip Management for 15-minute videos
import { TimelineUtils } from './TimelineUtils.js';

export class ClipManager {
    constructor(engine) {
        this.engine = engine;
        this.utils = new TimelineUtils();
    }

    addToTimeline(videoPath, startTime = 0, endTime = null, clipName = null) {
        const duration = this.getVideoDuration(videoPath);

        const clip = {
            id: this.utils.generateId(),
            file: videoPath,
            name: clipName || this.utils.getFileName(videoPath),
            duration: duration,
            timelineStart: startTime,
            timelineEnd: startTime + duration,
            position: {
                x: startTime * this.engine.PIXELS_PER_SECOND,
                y: this.getNextTrackPosition()
            },
            zIndex: ++this.engine.zIndexCounter,
            speed: 1.0,
            volume: 1.0,
            flip: false,
            type: 'video',
            track: this.getNextVideoTrack()
        };

        this.engine.timelineClips.push(clip);
        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.showSuccess(`✅ Added "${clip.name}" to timeline`);

        return clip;
    }

    addAudioToTimeline(audioPath, clipName = null) {
        const duration = this.getAudioDuration(audioPath);

        const clip = {
            id: this.utils.generateId(),
            file: audioPath,
            name: clipName || this.utils.getFileName(audioPath),
            duration: duration,
            timelineStart: 0,
            timelineEnd: duration,
            position: {
                x: 0,
                y: 0
            },
            volume: 1.0,
            fadeIn: false,
            fadeOut: false,
            type: 'audio',
            track: 'audio'
        };

        this.engine.audioClips.push(clip);
        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.showSuccess(`✅ Added audio "${clip.name}" to timeline`);

        return clip;
    }

    removeFromTimeline(clipId) {
        let removedClip = null;

        const videoIndex = this.engine.timelineClips.findIndex(clip => clip.id === clipId);
        if (videoIndex !== -1) {
            removedClip = this.engine.timelineClips.splice(videoIndex, 1)[0];
        }

        const audioIndex = this.engine.audioClips.findIndex(clip => clip.id === clipId);
        if (audioIndex !== -1) {
            removedClip = this.engine.audioClips.splice(audioIndex, 1)[0];
        }

        if (removedClip) {
            this.engine.showSuccess(`🗑️ Removed "${removedClip.name}" from timeline`);
        }

        if (this.engine.selectedClipId === clipId) {
            this.engine.selectedClipId = null;
            this.engine.ui.hideClipProperties();
        }

        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();

        return removedClip;
    }

    duplicateClip(clipId) {
        const originalClip = this.engine.timelineClips.find(clip => clip.id === clipId) ||
                           this.engine.audioClips.find(clip => clip.id === clipId);

        if (!originalClip) {
            this.engine.showWarning('⚠️ Clip not found for duplication');
            return null;
        }

        const duplicatedClip = {
            ...originalClip,
            id: this.utils.generateId(),
            position: {
                x: originalClip.position.x + 50,
                y: originalClip.position.y
            },
            name: `${originalClip.name} (copy)`
        };

        if (originalClip.type === 'video') {
            this.engine.timelineClips.push(duplicatedClip);
        } else {
            this.engine.audioClips.push(duplicatedClip);
        }

        this.engine.calculateTotalDuration();
        this.engine.updateTimelineUI();
        this.engine.showSuccess(`📋 Duplicated "${originalClip.name}"`);

        return duplicatedClip;
    }

    getNextTrackPosition() {
        const positions = this.engine.timelineClips.map(clip => clip.position.y);
        if (positions.length === 0) return 0;

        const maxPosition = Math.max(...positions);
        return (maxPosition + 80) % 160;
    }

    getNextVideoTrack() {
        const tracks = this.engine.timelineClips.map(clip => clip.track);
        if (tracks.length === 0) return 'video1';

        const trackCounts = { video1: 0, video2: 0 };
        tracks.forEach(track => {
            if (trackCounts[track] !== undefined) {
                trackCounts[track]++;
            }
        });

        return trackCounts.video1 <= trackCounts.video2 ? 'video1' : 'video2';
    }

    getVideoDuration(videoPath) {
        const mockDurations = {
            'short': 5,
            'medium': 30,
            'long': 300,
            'verylong': 600
        };

        const fileName = videoPath.toLowerCase();
        let durationType = 'medium';

        if (fileName.includes('short') || fileName.includes('clip')) {
            durationType = 'short';
        } else if (fileName.includes('long') || fileName.includes('full')) {
            durationType = 'long';
        } else if (fileName.includes('verylong') || fileName.includes('movie')) {
            durationType = 'verylong';
        }

        const baseDuration = mockDurations[durationType];
        const variation = baseDuration * 0.2;
        const randomVariation = (Math.random() * variation * 2) - variation;

        return Math.max(1, baseDuration + randomVariation);
    }

    getAudioDuration(audioPath) {
        const mockDurations = {
            'short': 30,
            'medium': 180,
            'long': 600
        };

        const fileName = audioPath.toLowerCase();
        let durationType = 'medium';

        if (fileName.includes('short') || fileName.includes('effect')) {
            durationType = 'short';
        } else if (fileName.includes('long') || fileName.includes('podcast')) {
            durationType = 'long';
        }

        const baseDuration = mockDurations[durationType];
        const variation = baseDuration * 0.15;
        const randomVariation = (Math.random() * variation * 2) - variation;

        return Math.max(1, baseDuration + randomVariation);
    }

    updateClipProperties(clipId, updates) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId) ||
                    this.engine.audioClips.find(c => c.id === clipId);

        if (!clip) return false;

        Object.assign(clip, updates);
        this.engine.updateTimelineUI();

        if (this.engine.selectedClipId === clipId) {
            this.engine.ui.showClipProperties(clip);
        }

        return true;
    }

    moveClipToTrack(clipId, targetTrack) {
        const clip = this.engine.timelineClips.find(c => c.id === clipId);
        if (!clip || clip.type !== 'video') return false;

        const validTracks = ['video1', 'video2'];
        if (!validTracks.includes(targetTrack)) return false;

        clip.track = targetTrack;
        this.engine.updateTimelineUI();
        return true;
    }

    getAllClips() {
        return {
            video: [...this.engine.timelineClips],
            audio: [...this.engine.audioClips]
        };
    }

    getClipById(clipId) {
        return this.engine.timelineClips.find(c => c.id === clipId) ||
               this.engine.audioClips.find(c => c.id === clipId);
    }

    isPositionAvailable(startTime, duration, track = 'video1') {
        const endTime = startTime + duration;

        const conflictingClips = this.engine.timelineClips.filter(clip => {
            if (clip.track !== track) return false;

            return (startTime < clip.timelineEnd && endTime > clip.timelineStart);
        });

        return conflictingClips.length === 0;
    }

    findAvailablePosition(duration, track = 'video1') {
        let position = 0;
        const maxAttempts = 100;
        let attempts = 0;

        while (attempts < maxAttempts) {
            if (this.isPositionAvailable(position, duration, track)) {
                return position;
            }
            position += 1;
            attempts++;
        }

        const clipsInTrack = this.engine.timelineClips
            .filter(clip => clip.track === track)
            .map(clip => clip.timelineEnd);

        return clipsInTrack.length > 0 ? Math.max(...clipsInTrack) : 0;
    }

    autoArrangeClips() {
        const tracks = {
            video1: this.engine.timelineClips.filter(clip => clip.track === 'video1'),
            video2: this.engine.timelineClips.filter(clip => clip.track === 'video2')
        };

        let changesMade = false;

        Object.keys(tracks).forEach(track => {
            const clips = tracks[track].sort((a, b) => a.timelineStart - b.timelineStart);
            let currentTime = 0;

            clips.forEach(clip => {
                if (clip.timelineStart < currentTime) {
                    clip.timelineStart = currentTime;
                    clip.timelineEnd = currentTime + clip.duration;
                    clip.position.x = currentTime * this.engine.PIXELS_PER_SECOND;
                    changesMade = true;
                }
                currentTime = clip.timelineEnd + 0.1;
            });
        });

        if (changesMade) {
            this.engine.calculateTotalDuration();
            this.engine.updateTimelineUI();
            this.engine.showSuccess('🔀 Clips auto-arranged to avoid overlaps');
        } else {
            this.engine.showInfo('✅ Clips are already well arranged');
        }

        return changesMade;
    }
}

export default ClipManager;