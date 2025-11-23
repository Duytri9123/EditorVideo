# video_tool/editors/timeline_editor.py
import uuid
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TimelineClip:
    """Đại diện cho một clip trong timeline"""

    id: str
    file_path: str
    file_type: str  # 'video', 'audio', 'image'
    start_time: float = 0.0
    end_time: Optional[float] = None
    position: float = 0.0  # Vị trí trong timeline (giây)
    duration: float = 0.0
    volume: float = 1.0
    speed: float = 1.0
    effects: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.effects is None:
            self.effects = {}
        if self.metadata is None:
            self.metadata = {}
        if self.end_time is None:
            self.end_time = self.start_time + self.duration

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành dictionary"""
        return asdict(self)


@dataclass
class AudioTrack:
    """Đại diện cho audio track"""

    id: str
    file_path: str
    start_time: float = 0.0
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    effects: Dict[str, Any] = None

    def __post_init__(self):
        if self.effects is None:
            self.effects = {}

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành dictionary"""
        return asdict(self)


class TimelineEditor:
    """Quản lý timeline video với multi-track support"""

    def __init__(self):
        self.video_tracks: List[List[TimelineClip]] = [[]]  # Multiple video tracks
        self.audio_tracks: List[AudioTrack] = []  # Multiple audio tracks
        self.transitions: List[Dict] = []
        self.effects: List[Dict] = []

        self.current_time: float = 0.0
        self.total_duration: float = 0.0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0

        self._update_total_duration()

        logger.info("Timeline Editor initialized")

    def add_clip(self, file_path: str, start_time: float = 0.0,
                 end_time: Optional[float] = None, track: int = 0) -> Dict[str, Any]:
        """Thêm clip vào timeline"""
        try:
            # Validate track
            if track < 0:
                return {'success': False, 'error': 'Track index cannot be negative'}

            # Ensure we have enough tracks
            while len(self.video_tracks) <= track:
                self.video_tracks.append([])

            # Determine file type
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                file_type = 'video'
            elif file_ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg']:
                file_type = 'audio'
                return self.add_audio(file_path, start_time)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                file_type = 'image'
            else:
                return {'success': False, 'error': f'Unsupported file type: {file_ext}'}

            # Get clip duration (simplified - in real implementation, read from file)
            duration = self._estimate_clip_duration(file_path, file_type)
            if end_time is None:
                end_time = start_time + duration

            # Create clip
            clip = TimelineClip(
                id=str(uuid.uuid4()),
                file_path=file_path,
                file_type=file_type,
                start_time=start_time,
                end_time=end_time,
                position=self._find_next_position(track, duration),
                duration=duration,
                metadata={
                    'filename': Path(file_path).name,
                    'added_at': time.time()
                }
            )

            # Add to track
            self.video_tracks[track].append(clip)
            self._update_total_duration()

            logger.info(f"Added clip to track {track}: {Path(file_path).name}")

            return {
                'success': True,
                'clip_id': clip.id,
                'track': track,
                'position': clip.position,
                'duration': clip.duration,
                'message': f'Added {file_type} clip to timeline'
            }

        except Exception as e:
            logger.error(f"Failed to add clip: {e}")
            return {'success': False, 'error': str(e)}

    def add_audio(self, audio_path: str, start_time: float = 0.0) -> Dict[str, Any]:
        """Thêm audio track"""
        try:
            duration = self._estimate_clip_duration(audio_path, 'audio')

            audio_track = AudioTrack(
                id=str(uuid.uuid4()),
                file_path=audio_path,
                start_time=start_time,
                volume=1.0,
                metadata={
                    'filename': Path(audio_path).name,
                    'added_at': time.time()
                }
            )

            self.audio_tracks.append(audio_track)
            self._update_total_duration()

            logger.info(f"Added audio track: {Path(audio_path).name}")

            return {
                'success': True,
                'audio_id': audio_track.id,
                'start_time': start_time,
                'duration': duration,
                'message': 'Added audio to timeline'
            }

        except Exception as e:
            logger.error(f"Failed to add audio: {e}")
            return {'success': False, 'error': str(e)}

    def remove_clip(self, clip_id: str) -> Dict[str, Any]:
        """Xóa clip khỏi timeline"""
        try:
            for track_index, track in enumerate(self.video_tracks):
                for i, clip in enumerate(track):
                    if clip.id == clip_id:
                        removed_clip = track.pop(i)
                        self._update_total_duration()

                        logger.info(f"Removed clip: {removed_clip.metadata.get('filename')}")

                        return {
                            'success': True,
                            'clip_id': clip_id,
                            'track': track_index,
                            'message': 'Clip removed from timeline'
                        }

            return {'success': False, 'error': 'Clip not found'}

        except Exception as e:
            logger.error(f"Failed to remove clip: {e}")
            return {'success': False, 'error': str(e)}

    def remove_audio(self, audio_id: str) -> Dict[str, Any]:
        """Xóa audio track"""
        try:
            for i, audio_track in enumerate(self.audio_tracks):
                if audio_track.id == audio_id:
                    removed_audio = self.audio_tracks.pop(i)
                    self._update_total_duration()

                    logger.info(f"Removed audio track: {removed_audio.file_path}")

                    return {
                        'success': True,
                        'audio_id': audio_id,
                        'message': 'Audio track removed'
                    }

            return {'success': False, 'error': 'Audio track not found'}

        except Exception as e:
            logger.error(f"Failed to remove audio: {e}")
            return {'success': False, 'error': str(e)}

    def move_clip(self, clip_id: str, new_position: float, new_track: Optional[int] = None) -> Dict[str, Any]:
        """Di chuyển clip đến vị trí mới"""
        try:
            clip = None
            old_track_index = -1

            # Find clip
            for track_index, track in enumerate(self.video_tracks):
                for c in track:
                    if c.id == clip_id:
                        clip = c
                        old_track_index = track_index
                        break
                if clip:
                    break

            if not clip:
                return {'success': False, 'error': 'Clip not found'}

            # Remove from old track
            self.video_tracks[old_track_index] = [c for c in self.video_tracks[old_track_index] if c.id != clip_id]

            # Determine target track
            target_track = new_track if new_track is not None else old_track_index
            if target_track >= len(self.video_tracks):
                # Add new track if needed
                while len(self.video_tracks) <= target_track:
                    self.video_tracks.append([])

            # Update clip position and add to new track
            clip.position = new_position
            self.video_tracks[target_track].append(clip)

            # Sort clips in track by position
            self.video_tracks[target_track].sort(key=lambda x: x.position)

            self._update_total_duration()

            logger.info(f"Moved clip {clip_id} to position {new_position} in track {target_track}")

            return {
                'success': True,
                'clip_id': clip_id,
                'old_track': old_track_index,
                'new_track': target_track,
                'new_position': new_position,
                'message': 'Clip moved successfully'
            }

        except Exception as e:
            logger.error(f"Failed to move clip: {e}")
            return {'success': False, 'error': str(e)}

    def apply_effect_to_clip(self, clip_id: str, effect_type: str, effect_config: Dict) -> Dict[str, Any]:
        """Áp dụng hiệu ứng cho clip"""
        try:
            clip = self._find_clip_by_id(clip_id)
            if not clip:
                return {'success': False, 'error': 'Clip not found'}

            clip.effects[effect_type] = effect_config

            logger.info(f"Applied effect {effect_type} to clip {clip_id}")

            return {
                'success': True,
                'clip_id': clip_id,
                'effect_type': effect_type,
                'message': f'Effect {effect_type} applied to clip'
            }

        except Exception as e:
            logger.error(f"Failed to apply effect: {e}")
            return {'success': False, 'error': str(e)}

    def clear_timeline(self) -> Dict[str, Any]:
        """Xóa toàn bộ timeline"""
        try:
            clip_count = sum(len(track) for track in self.video_tracks)
            audio_count = len(self.audio_tracks)

            self.video_tracks = [[]]
            self.audio_tracks = []
            self.transitions = []
            self.effects = []
            self.current_time = 0.0
            self.total_duration = 0.0
            self.is_playing = False

            logger.info(f"Cleared timeline: {clip_count} clips, {audio_count} audio tracks")

            return {
                'success': True,
                'clips_removed': clip_count,
                'audio_tracks_removed': audio_count,
                'message': 'Timeline cleared'
            }

        except Exception as e:
            logger.error(f"Failed to clear timeline: {e}")
            return {'success': False, 'error': str(e)}

    def _find_clip_by_id(self, clip_id: str) -> Optional[TimelineClip]:
        """Tìm clip bằng ID"""
        for track in self.video_tracks:
            for clip in track:
                if clip.id == clip_id:
                    return clip
        return None

    def _estimate_clip_duration(self, file_path: str, file_type: str) -> float:
        """Ước tính duration của clip (simplified)"""
        # Trong implementation thực tế, sẽ đọc từ file metadata
        duration_map = {
            'video': 30.0,  # 30 seconds default for videos
            'audio': 180.0,  # 3 minutes default for audio
            'image': 5.0  # 5 seconds for images
        }
        return duration_map.get(file_type, 10.0)

    def _find_next_position(self, track: int, duration: float) -> float:
        """Tìm vị trí tiếp theo trong track"""
        if not self.video_tracks[track]:
            return 0.0

        # Find the end of the last clip in track
        last_clip = max(self.video_tracks[track], key=lambda x: x.position + x.duration)
        return last_clip.position + last_clip.duration

    def _update_total_duration(self):
        """Cập nhật tổng duration của timeline"""
        max_duration = 0.0

        # Check video tracks
        for track in self.video_tracks:
            for clip in track:
                clip_end = clip.position + clip.duration
                if clip_end > max_duration:
                    max_duration = clip_end

        # Check audio tracks
        for audio in self.audio_tracks:
            # Simplified audio duration estimation
            audio_duration = self._estimate_clip_duration(audio.file_path, 'audio')
            audio_end = audio.start_time + audio_duration
            if audio_end > max_duration:
                max_duration = audio_end

        self.total_duration = max_duration

    def get_timeline_data(self) -> Dict[str, Any]:
        """Lấy toàn bộ dữ liệu timeline"""
        return {
            'video_tracks': [
                [clip.to_dict() for clip in track]
                for track in self.video_tracks
            ],
            'audio_tracks': [audio.to_dict() for audio in self.audio_tracks],
            'transitions': self.transitions,
            'effects': self.effects,
            'current_time': self.current_time,
            'total_duration': self.total_duration,
            'is_playing': self.is_playing,
            'playback_speed': self.playback_speed
        }

    def get_status(self) -> Dict[str, Any]:
        """Trạng thái timeline"""
        total_clips = sum(len(track) for track in self.video_tracks)

        return {
            'total_clips': total_clips,
            'audio_track_count': len(self.audio_tracks),
            'video_track_count': len(self.video_tracks),
            'total_duration': self.total_duration,
            'current_time': self.current_time,
            'is_playing': self.is_playing,
            'playback_speed': self.playback_speed,
            'has_transitions': len(self.transitions) > 0,
            'has_effects': len(self.effects) > 0
        }

    def seek(self, time_seconds: float) -> Dict[str, Any]:
        """Di chuyển đến thời điểm cụ thể"""
        try:
            if time_seconds < 0:
                time_seconds = 0
            elif time_seconds > self.total_duration:
                time_seconds = self.total_duration

            self.current_time = time_seconds

            return {
                'success': True,
                'current_time': self.current_time,
                'message': f'Seeked to {time_seconds:.1f}s'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def play(self) -> Dict[str, Any]:
        """Bắt đầu playback"""
        self.is_playing = True
        return {'success': True, 'is_playing': True, 'message': 'Playback started'}

    def pause(self) -> Dict[str, Any]:
        """Tạm dừng playback"""
        self.is_playing = False
        return {'success': True, 'is_playing': False, 'message': 'Playback paused'}

    def stop(self) -> Dict[str, Any]:
        """Dừng playback"""
        self.is_playing = False
        self.current_time = 0.0
        return {'success': True, 'is_playing': False, 'current_time': 0.0, 'message': 'Playback stopped'}