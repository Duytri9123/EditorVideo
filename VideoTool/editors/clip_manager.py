# video_tool/editors/clip_manager.py
import os
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ClipProperties:
    """Properties của video/audio clip"""

    # Basic properties
    duration: float = 0.0
    file_size: int = 0
    resolution: str = "0x0"
    fps: float = 0.0
    bitrate: int = 0

    # Video specific
    width: int = 0
    height: int = 0
    frame_count: int = 0
    codec: str = ""
    has_audio: bool = False

    # Audio specific
    audio_channels: int = 0
    audio_sample_rate: int = 0
    audio_bitrate: int = 0

    # Metadata
    created_time: float = 0.0
    modified_time: float = 0.0
    file_format: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành dictionary"""
        return asdict(self)


class ClipManager:
    """Quản lý clips với caching và optimization"""

    def __init__(self):
        self.clips: Dict[str, 'Clip'] = {}
        self.thumbnails: Dict[str, np.ndarray] = {}
        self.properties_cache: Dict[str, ClipProperties] = {}
        self.thumbnail_size: Tuple[int, int] = (160, 90)  # 16:9 aspect ratio

        logger.info("Clip Manager initialized")

    def add_clip(self, file_path: str, clip_id: Optional[str] = None) -> 'Clip':
        """Thêm clip mới"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Clip file not found: {file_path}")

            clip_id = clip_id or str(uuid.uuid4())

            # Create clip object
            clip = Clip(clip_id, file_path)

            # Load properties
            properties = self._load_clip_properties(file_path)
            clip.properties = properties

            # Generate thumbnail
            thumbnail = self._generate_thumbnail(file_path)
            if thumbnail is not None:
                self.thumbnails[clip_id] = thumbnail

            # Add to storage
            self.clips[clip_id] = clip
            self.properties_cache[clip_id] = properties

            logger.info(f"Added clip: {clip_id} - {Path(file_path).name}")

            return clip

        except Exception as e:
            logger.error(f"Failed to add clip {file_path}: {e}")
            raise

    def remove_clip(self, clip_id: str) -> bool:
        """Xóa clip"""
        try:
            if clip_id in self.clips:
                del self.clips[clip_id]

            if clip_id in self.thumbnails:
                del self.thumbnails[clip_id]

            if clip_id in self.properties_cache:
                del self.properties_cache[clip_id]

            logger.info(f"Removed clip: {clip_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove clip {clip_id}: {e}")
            return False

    def get_clip(self, clip_id: str) -> Optional['Clip']:
        """Lấy clip bằng ID"""
        return self.clips.get(clip_id)

    def get_clip_properties(self, clip_id: str) -> Optional[ClipProperties]:
        """Lấy properties của clip"""
        if clip_id in self.properties_cache:
            return self.properties_cache[clip_id]

        clip = self.get_clip(clip_id)
        if clip:
            return clip.properties

        return None

    def get_thumbnail(self, clip_id: str, size: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
        """Lấy thumbnail của clip"""
        try:
            thumbnail = self.thumbnails.get(clip_id)
            if thumbnail is None:
                # Generate thumbnail if not exists
                clip = self.get_clip(clip_id)
                if clip:
                    thumbnail = self._generate_thumbnail(clip.file_path)
                    if thumbnail is not None:
                        self.thumbnails[clip_id] = thumbnail

            if thumbnail is not None and size is not None:
                # Resize to requested size
                thumbnail = cv2.resize(thumbnail, size, interpolation=cv2.INTER_AREA)

            return thumbnail

        except Exception as e:
            logger.warning(f"Failed to get thumbnail for {clip_id}: {e}")
            return None

    def extract_clip_segment(self, clip_id: str, start_time: float, end_time: float,
                             output_path: str) -> Dict[str, Any]:
        """Trích xuất segment từ clip"""
        try:
            clip = self.get_clip(clip_id)
            if not clip:
                return {'success': False, 'error': 'Clip not found'}

            import ffmpeg

            # Validate time range
            if start_time < 0:
                start_time = 0
            if end_time > clip.properties.duration:
                end_time = clip.properties.duration
            if start_time >= end_time:
                return {'success': False, 'error': 'Invalid time range'}

            duration = end_time - start_time

            # Extract segment using FFmpeg
            stream = ffmpeg.input(clip.file_path, ss=start_time, t=duration)
            stream = ffmpeg.output(stream, output_path, **{'c': 'copy', 'y': None})

            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

            if os.path.exists(output_path):
                segment_size = os.path.getsize(output_path)

                return {
                    'success': True,
                    'output_path': output_path,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'file_size': segment_size
                }
            else:
                return {'success': False, 'error': 'Segment extraction failed'}

        except Exception as e:
            logger.error(f"Segment extraction failed for {clip_id}: {e}")
            return {'success': False, 'error': str(e)}

    def change_clip_speed(self, clip_id: str, speed_factor: float,
                          output_path: str) -> Dict[str, Any]:
        """Thay đổi tốc độ clip"""
        try:
            clip = self.get_clip(clip_id)
            if not clip:
                return {'success': False, 'error': 'Clip not found'}

            if speed_factor <= 0:
                return {'success': False, 'error': 'Speed factor must be positive'}

            import ffmpeg

            # Apply speed change using FFmpeg
            if speed_factor != 1.0:
                # For video speed change
                stream = ffmpeg.input(clip.file_path)

                # Set PTS (Presentation TimeStamp) to control speed
                stream = stream.filter('setpts', f'{1 / speed_factor}*PTS')

                # For audio speed change (if exists)
                if clip.properties.has_audio:
                    stream = stream.filter('atempo', speed_factor)

                stream = ffmpeg.output(stream, output_path, **{'y': None})
            else:
                # No speed change, just copy
                stream = ffmpeg.input(clip.file_path)
                stream = ffmpeg.output(stream, output_path, **{'c': 'copy', 'y': None})

            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

            if os.path.exists(output_path):
                new_duration = clip.properties.duration / speed_factor
                file_size = os.path.getsize(output_path)

                return {
                    'success': True,
                    'output_path': output_path,
                    'original_duration': clip.properties.duration,
                    'new_duration': new_duration,
                    'speed_factor': speed_factor,
                    'file_size': file_size
                }
            else:
                return {'success': False, 'error': 'Speed change failed'}

        except Exception as e:
            logger.error(f"Speed change failed for {clip_id}: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_clip_audio(self, clip_id: str) -> Dict[str, Any]:
        """Phân tích audio của clip"""
        try:
            clip = self.get_clip(clip_id)
            if not clip:
                return {'success': False, 'error': 'Clip not found'}

            if not clip.properties.has_audio:
                return {'success': False, 'error': 'Clip has no audio'}

            # Use pydub for audio analysis
            from pydub import AudioSegment
            from pydub.utils import mediainfo

            audio = AudioSegment.from_file(clip.file_path)
            samples = np.array(audio.get_array_of_samples())

            # Calculate audio levels
            rms = np.sqrt(np.mean(samples ** 2))
            peak = np.max(np.abs(samples))
            max_possible = 2 ** (audio.sample_width * 8 - 1)

            rms_db = 20 * np.log10(rms / max_possible) if rms > 0 else -float('inf')
            peak_db = 20 * np.log10(peak / max_possible) if peak > 0 else -float('inf')

            # Detect silence
            silence_threshold = -40  # dB
            silent_segments = self._detect_silence(audio, silence_threshold)

            # Frequency analysis (simplified)
            if len(samples) > 0:
                # Use FFT for basic frequency analysis
                fft = np.fft.fft(samples)
                frequencies = np.fft.fftfreq(len(fft), 1 / audio.frame_rate)

                # Find dominant frequency
                magnitude = np.abs(fft)
                dominant_freq_idx = np.argmax(magnitude[:len(magnitude) // 2])
                dominant_frequency = abs(frequencies[dominant_freq_idx])
            else:
                dominant_frequency = 0

            return {
                'success': True,
                'audio_levels': {
                    'rms_db': float(rms_db),
                    'peak_db': float(peak_db),
                    'dynamic_range': float(peak_db - rms_db)
                },
                'silence_detection': {
                    'threshold_db': silence_threshold,
                    'silent_segments': silent_segments,
                    'total_silence_duration': sum(seg['duration'] for seg in silent_segments),
                    'silence_percentage': (sum(
                        seg['duration'] for seg in silent_segments) / clip.properties.duration) * 100
                },
                'frequency_analysis': {
                    'dominant_frequency': dominant_frequency,
                    'sample_rate': audio.frame_rate,
                    'channels': audio.channels
                }
            }

        except Exception as e:
            logger.error(f"Audio analysis failed for {clip_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _detect_silence(self, audio_segment, threshold_db: float) -> List[Dict[str, Any]]:
        """Phát hiện silence trong audio"""
        try:
            from pydub import AudioSegment
            from pydub.silence import detect_silence

            # Convert threshold to pydub format (RMS in dBFS)
            silence_ranges = detect_silence(
                audio_segment,
                min_silence_len=500,  # 500ms minimum silence
                silence_thresh=threshold_db
            )

            silent_segments = []
            for start_ms, end_ms in silence_ranges:
                silent_segments.append({
                    'start_time': start_ms / 1000.0,  # Convert to seconds
                    'end_time': end_ms / 1000.0,
                    'duration': (end_ms - start_ms) / 1000.0
                })

            return silent_segments

        except Exception as e:
            logger.warning(f"Silence detection failed: {e}")
            return []

    def get_clip_waveform(self, clip_id: str, width: int = 800, height: int = 200) -> Optional[np.ndarray]:
        """Tạo waveform visualization cho clip"""
        try:
            clip = self.get_clip(clip_id)
            if not clip or not clip.properties.has_audio:
                return None

            from pydub import AudioSegment
            import matplotlib.pyplot as plt
            from io import BytesIO

            audio = AudioSegment.from_file(clip.file_path)
            samples = np.array(audio.get_array_of_samples())

            if audio.channels == 2:
                # Stereo - use left channel
                samples = samples[0::2]

            # Downsample for performance
            target_samples = min(len(samples), width * 2)
            if len(samples) > target_samples:
                step = len(samples) // target_samples
                samples = samples[::step]

            # Create waveform visualization
            plt.figure(figsize=(width / 100, height / 100), dpi=100)
            plt.plot(samples, color='blue', alpha=0.7, linewidth=0.5)
            plt.axis('off')
            plt.margins(0)
            plt.tight_layout(pad=0)

            # Convert plot to image
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            buf.seek(0)

            # Read image
            waveform_img = cv2.imdecode(np.frombuffer(buf.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            plt.close()

            return waveform_img

        except Exception as e:
            logger.warning(f"Waveform generation failed for {clip_id}: {e}")
            return None

    def _load_clip_properties(self, file_path: str) -> ClipProperties:
        """Tải properties của clip"""
        try:
            import cv2

            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                # Try as audio file
                return self._load_audio_properties(file_path)

            # Video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            codec = int(cap.get(cv2.CAP_PROP_FOURCC))

            # Convert codec to readable format
            codec_str = ""
            for i in range(4):
                codec_str += chr((codec >> (8 * i)) & 0xFF)
            codec_str = codec_str.strip('\x00')

            # Check for audio
            has_audio = cap.get(cv2.CAP_PROP_AUDIO_TOTAL_STREAMS) > 0

            cap.release()

            # File properties
            stat = os.stat(file_path)
            file_size = stat.st_size
            bitrate = int((file_size * 8) / duration) if duration > 0 else 0

            return ClipProperties(
                duration=duration,
                file_size=file_size,
                resolution=f"{width}x{height}",
                fps=fps,
                bitrate=bitrate,
                width=width,
                height=height,
                frame_count=frame_count,
                codec=codec_str,
                has_audio=has_audio,
                created_time=stat.st_ctime,
                modified_time=stat.st_mtime,
                file_format=Path(file_path).suffix.lower()
            )

        except Exception as e:
            logger.warning(f"Could not load video properties for {file_path}: {e}")
            # Return basic properties
            stat = os.stat(file_path)
            return ClipProperties(
                file_size=stat.st_size,
                created_time=stat.st_ctime,
                modified_time=stat.st_mtime,
                file_format=Path(file_path).suffix.lower()
            )

    def _load_audio_properties(self, file_path: str) -> ClipProperties:
        """Tải properties của audio file"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(file_path)
            stat = os.stat(file_path)
            file_size = stat.st_size
            duration = len(audio) / 1000.0  # Convert to seconds
            bitrate = int((file_size * 8) / duration) if duration > 0 else 0

            return ClipProperties(
                duration=duration,
                file_size=file_size,
                bitrate=bitrate,
                audio_channels=audio.channels,
                audio_sample_rate=audio.frame_rate,
                audio_bitrate=bitrate,
                created_time=stat.st_ctime,
                modified_time=stat.st_mtime,
                file_format=Path(file_path).suffix.lower()
            )

        except Exception as e:
            logger.warning(f"Could not load audio properties for {file_path}: {e}")
            # Return basic properties
            stat = os.stat(file_path)
            return ClipProperties(
                file_size=stat.st_size,
                created_time=stat.st_ctime,
                modified_time=stat.st_mtime,
                file_format=Path(file_path).suffix.lower()
            )

    def _generate_thumbnail(self, file_path: str) -> Optional[np.ndarray]:
        """Tạo thumbnail cho clip"""
        try:
            import cv2

            # Try as video first
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                # Get frame at 10% of duration
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                target_frame = max(0, min(total_frames - 1, int(total_frames * 0.1)))

                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()
                cap.release()

                if ret and frame is not None:
                    # Resize to standard thumbnail size
                    thumbnail = cv2.resize(frame, self.thumbnail_size, interpolation=cv2.INTER_AREA)
                    return thumbnail

            return None

        except Exception as e:
            logger.debug(f"Thumbnail generation failed for {file_path}: {e}")
            return None

    def get_all_clips(self) -> List['Clip']:
        """Lấy tất cả clips"""
        return list(self.clips.values())

    def search_clips(self, query: str) -> List['Clip']:
        """Tìm kiếm clips"""
        results = []
        query_lower = query.lower()

        for clip in self.clips.values():
            filename = Path(clip.file_path).name.lower()
            if (query_lower in filename or
                    query_lower in clip.id.lower()):
                results.append(clip)

        return results

    def clear_cache(self):
        """Xóa cache"""
        self.thumbnails.clear()
        self.properties_cache.clear()
        logger.info("Clip manager cache cleared")

    def get_memory_usage(self) -> Dict[str, Any]:
        """Lấy thông tin memory usage"""
        thumbnail_memory = sum(
            img.nbytes if hasattr(img, 'nbytes') else 0
            for img in self.thumbnails.values()
        )

        return {
            'total_clips': len(self.clips),
            'cached_thumbnails': len(self.thumbnails),
            'cached_properties': len(self.properties_cache),
            'thumbnail_memory_bytes': thumbnail_memory,
            'thumbnail_memory_human': self._format_size(thumbnail_memory)
        }

    def _format_size(self, size_bytes: int) -> str:
        """Định dạng kích thước"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


class Clip:
    """Đại diện cho một media clip"""

    def __init__(self, clip_id: str, file_path: str):
        self.id = clip_id
        self.file_path = file_path
        self.properties: Optional[ClipProperties] = None
        self.metadata: Dict[str, Any] = {}
        self.tags: List[str] = []
        self.created_at = time.time()

    def add_tag(self, tag: str):
        """Thêm tag cho clip"""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Xóa tag khỏi clip"""
        if tag in self.tags:
            self.tags.remove(tag)

    def set_metadata(self, key: str, value: Any):
        """Đặt metadata"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Lấy metadata"""
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành dictionary"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'properties': self.properties.to_dict() if self.properties else {},
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at,
            'filename': Path(self.file_path).name
        }