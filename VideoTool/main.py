# video_tool/main_improved.py - PRODUCTION-READY VERSION
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import tempfile
import shutil
import yt_dlp
from datetime import datetime, timedelta
import re
import urllib.parse
import subprocess
import json
import hashlib
import psutil
from dataclasses import dataclass, asdict
from enum import Enum
import signal
from contextlib import asynccontextmanager
import atexit

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ProcessingProfile(Enum):
    """Processing quality profiles"""
    FAST = "fast"  # ultrafast preset, CRF 28
    BALANCED = "balanced"  # medium preset, CRF 23
    QUALITY = "quality"  # slow preset, CRF 18
    LOSSLESS = "lossless"  # veryslow preset, CRF 0


class MergeStrategy(Enum):
    """Video merge strategies"""
    SMART_CONCAT = "smart_concat"  # Use concat demuxer if possible
    REENCODE = "reencode"  # Always re-encode
    AUTO = "auto"  # Automatically choose best


@dataclass
class DownloadProgress:
    """Progress tracking for downloads"""
    url: str
    total_bytes: int = 0
    downloaded_bytes: int = 0
    speed: float = 0.0
    eta: int = 0
    status: str = "pending"
    error: Optional[str] = None

    @property
    def percentage(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class VideoInfo:
    """Video metadata"""
    width: int
    height: int
    fps: float
    codec: str
    duration: float
    bitrate: int
    has_audio: bool
    audio_codec: Optional[str] = None
    audio_bitrate: Optional[int] = None
    file_size: int = 0
    color_space: str = "unknown"

    def __eq__(self, other) -> bool:
        """Check if two videos have compatible formats"""
        if not isinstance(other, VideoInfo):
            return False
        return (
                self.width == other.width and
                self.height == other.height and
                abs(self.fps - other.fps) < 0.1 and
                self.codec == other.codec
        )


@dataclass
class ResourceLimits:
    """Resource usage limits"""
    max_file_size_mb: int = 2048  # 2GB
    max_duration_seconds: int = 7200  # 2 hours
    max_concurrent_downloads: int = 5
    max_memory_mb: int = 4096  # 4GB
    max_disk_usage_mb: int = 10240  # 10GB


# ============================================================================
# EXCEPTIONS
# ============================================================================

class VideoToolException(Exception):
    """Base exception for VideoTool"""
    pass


class ValidationError(VideoToolException):
    """Input validation error"""
    pass


class ResourceLimitError(VideoToolException):
    """Resource limit exceeded"""
    pass


class DownloadError(VideoToolException):
    """Download failed"""
    pass


class ProcessingError(VideoToolException):
    """Video processing failed"""
    pass


# ============================================================================
# INPUT VALIDATOR
# ============================================================================

class InputValidator:
    """Validates all inputs before processing"""

    @staticmethod
    def validate_url(url: str) -> str:
        """Validate and sanitize URL"""
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")

        url = url.strip()

        # Check URL format
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"Invalid URL format: {url}")

        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError(f"Only HTTP/HTTPS URLs are supported: {url}")

        # Sanitize for subprocess safety
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in url:
                raise ValidationError(f"URL contains dangerous character: {char}")

        return url

    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = False) -> Path:
        """Validate file path"""
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")

        try:
            path = Path(file_path).resolve()
        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}")

        # Check for path traversal
        if '..' in file_path:
            raise ValidationError("Path traversal detected")

        if must_exist and not path.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        return path

    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename"""
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename must be a non-empty string")

        # Remove dangerous characters
        sanitized = re.sub(r'[^\w\s\-\.]', '_', filename)
        sanitized = sanitized.strip()

        if not sanitized:
            raise ValidationError("Filename contains only invalid characters")

        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]

        return sanitized

    @staticmethod
    def validate_format(format_str: str, allowed_formats: List[str]) -> str:
        """Validate format"""
        if not format_str or not isinstance(format_str, str):
            raise ValidationError("Format must be a non-empty string")

        format_str = format_str.lower().strip()

        if format_str not in allowed_formats:
            raise ValidationError(
                f"Invalid format '{format_str}'. Allowed: {', '.join(allowed_formats)}"
            )

        return format_str


# ============================================================================
# RESOURCE MONITOR
# ============================================================================

class ResourceMonitor:
    """Monitor and enforce resource limits"""

    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.process = psutil.Process()

    async def check_memory(self) -> bool:
        """Check if memory usage is within limits"""
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            if memory_mb > self.limits.max_memory_mb:
                logger.warning(f"⚠️ Memory usage high: {memory_mb:.0f}MB / {self.limits.max_memory_mb}MB")
                return False
            return True
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return True  # Don't block on check failure

    async def check_disk_space(self, path: Path, required_mb: int = 0) -> bool:
        """Check if disk space is sufficient"""
        try:
            stat = shutil.disk_usage(path)
            free_mb = stat.free / 1024 / 1024

            if required_mb > 0 and free_mb < required_mb:
                raise ResourceLimitError(
                    f"Insufficient disk space: {free_mb:.0f}MB available, {required_mb:.0f}MB required"
                )

            if free_mb < 1024:  # Less than 1GB
                logger.warning(f"⚠️ Low disk space: {free_mb:.0f}MB")
                return False

            return True
        except ResourceLimitError:
            raise
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return True

    async def check_file_size(self, file_size_mb: int) -> bool:
        """Check if file size is within limits"""
        if file_size_mb > self.limits.max_file_size_mb:
            raise ResourceLimitError(
                f"File too large: {file_size_mb}MB exceeds limit of {self.limits.max_file_size_mb}MB"
            )
        return True


# ============================================================================
# CACHE MANAGER
# ============================================================================

class CacheManager:
    """Manage cached video info and downloads"""

    def __init__(self, cache_dir: Path, max_age_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)
        self._info_cache: Dict[str, VideoInfo] = {}

    def _get_url_hash(self, url: str) -> str:
        """Generate hash for URL"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    async def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """Get cached video info"""
        url_hash = self._get_url_hash(url)

        # Check memory cache first
        if url_hash in self._info_cache:
            return self._info_cache[url_hash]

        # Check disk cache
        cache_file = self.cache_dir / f"info_{url_hash}.json"
        if cache_file.exists():
            try:
                age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if age < self.max_age:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        info = VideoInfo(**data)
                        self._info_cache[url_hash] = info
                        return info
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")

        return None

    async def save_video_info(self, url: str, info: VideoInfo):
        """Save video info to cache"""
        url_hash = self._get_url_hash(url)
        self._info_cache[url_hash] = info

        cache_file = self.cache_dir / f"info_{url_hash}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(asdict(info), f)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def cleanup_old_cache(self):
        """Remove old cache files"""
        try:
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if age > self.max_age:
                    cache_file.unlink()
                    count += 1
            if count > 0:
                logger.info(f"🧹 Cleaned {count} old cache files")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")


# ============================================================================
# TEMP FILE MANAGER
# ============================================================================

class TempFileManager:
    """Manage temporary files with automatic cleanup"""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir:
            self.base_dir = base_dir
            self.base_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.base_dir = Path(tempfile.gettempdir()) / "video_tool"
            self.base_dir.mkdir(parents=True, exist_ok=True)

        self.session_dir = self.base_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self._tracked_files: List[Path] = []
        self._cleanup_registered = False

        logger.info(f"📁 Temp directory: {self.session_dir}")

    def get_temp_path(self, filename: str) -> Path:
        """Get path for temporary file"""
        path = self.session_dir / filename
        self._tracked_files.append(path)
        return path

    async def cleanup_session(self):
        """Clean up current session files"""
        count = 0
        for file_path in self._tracked_files:
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                        count += 1
            except Exception as e:
                logger.warning(f"Could not delete {file_path}: {e}")

        try:
            if self.session_dir.exists():
                shutil.rmtree(self.session_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Could not delete session dir: {e}")

        if count > 0:
            logger.info(f"🧹 Cleaned up {count} temporary files")

    async def cleanup_old_sessions(self, older_than_hours: int = 24):
        """Clean up old session directories"""
        try:
            count = 0
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

            for session_dir in self.base_dir.glob("session_*"):
                if not session_dir.is_dir():
                    continue

                try:
                    dir_time = datetime.fromtimestamp(session_dir.stat().st_mtime)
                    if dir_time < cutoff_time:
                        shutil.rmtree(session_dir, ignore_errors=True)
                        count += 1
                except Exception as e:
                    logger.warning(f"Could not clean {session_dir}: {e}")

            if count > 0:
                logger.info(f"🧹 Cleaned up {count} old session directories")

        except Exception as e:
            logger.error(f"Old session cleanup failed: {e}")

    def register_cleanup(self):
        """Register cleanup on exit"""
        if not self._cleanup_registered:
            atexit.register(lambda: asyncio.run(self.cleanup_session()))
            self._cleanup_registered = True


# ============================================================================
# PROGRESS TRACKER
# ============================================================================

class ProgressTracker:
    """Track progress of operations"""

    def __init__(self):
        self._progress: Dict[str, DownloadProgress] = {}
        self._callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        """Register progress callback"""
        self._callbacks.append(callback)

    def create_progress(self, url: str) -> DownloadProgress:
        """Create new progress tracker"""
        progress = DownloadProgress(url=url)
        self._progress[url] = progress
        return progress

    def update_progress(self, url: str, **kwargs):
        """Update progress"""
        if url in self._progress:
            for key, value in kwargs.items():
                if hasattr(self._progress[url], key):
                    setattr(self._progress[url], key, value)

            # Call callbacks
            for callback in self._callbacks:
                try:
                    callback(self._progress[url])
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

    def get_progress(self, url: str) -> Optional[DownloadProgress]:
        """Get progress for URL"""
        return self._progress.get(url)

    def get_all_progress(self) -> Dict[str, DownloadProgress]:
        """Get all progress"""
        return self._progress.copy()


# ============================================================================
# IMPROVED VIDEO PROCESSOR
# ============================================================================

class ImprovedVideoProcessor:
    """Enhanced video processor with smart merging"""

    def __init__(self, config: Dict, cache_manager: CacheManager):
        self.config = config
        self.cache = cache_manager

    async def get_video_info(self, video_path: str, use_cache: bool = True) -> Optional[VideoInfo]:
        """Get detailed video information"""
        try:
            # Check cache first
            if use_cache:
                cached = await self.cache.get_video_info(video_path)
                if cached:
                    return cached

            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries',
                'stream=width,height,r_frame_rate,codec_name,duration,bit_rate:format=size',
                '-of', 'json',
                video_path
            ]

            def run_ffprobe():
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False
                )
                return result

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_ffprobe)

            if result.returncode != 0:
                logger.error(f"ffprobe failed: {result.stderr}")
                return None

            data = json.loads(result.stdout)

            if not data.get('streams'):
                return None

            stream = data['streams'][0]
            format_data = data.get('format', {})

            # Parse FPS
            fps_str = stream.get('r_frame_rate', '30/1')
            fps_parts = fps_str.split('/')
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

            # Get audio info
            audio_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,bit_rate',
                '-of', 'json',
                video_path
            ]

            audio_result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(audio_cmd, capture_output=True, text=True, timeout=30, check=False)
            )

            has_audio = False
            audio_codec = None
            audio_bitrate = None

            if audio_result.returncode == 0:
                audio_data = json.loads(audio_result.stdout)
                if audio_data.get('streams'):
                    has_audio = True
                    audio_codec = audio_data['streams'][0].get('codec_name')
                    audio_bitrate = int(audio_data['streams'][0].get('bit_rate', 0))

            info = VideoInfo(
                width=int(stream.get('width', 1920)),
                height=int(stream.get('height', 1080)),
                fps=round(fps, 2),
                codec=stream.get('codec_name', 'h264'),
                duration=float(stream.get('duration', format_data.get('duration', 0))),
                bitrate=int(stream.get('bit_rate', 0)),
                has_audio=has_audio,
                audio_codec=audio_codec,
                audio_bitrate=audio_bitrate,
                file_size=int(format_data.get('size', 0)),
                color_space='bt709'  # Default assumption
            )

            # Cache the info
            if use_cache:
                await self.cache.save_video_info(video_path, info)

            return info

        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None

    async def can_use_concat_demuxer(self, video_infos: List[VideoInfo]) -> bool:
        """Check if videos can use fast concat demuxer"""
        if not video_infos or len(video_infos) < 2:
            return False

        first = video_infos[0]
        for info in video_infos[1:]:
            if first != info:
                return False

        return True

    async def merge_with_concat_demuxer(
            self,
            input_paths: List[str],
            output_path: str
    ) -> Dict[str, Any]:
        """Fast merge using concat demuxer (no re-encoding)"""
        try:
            logger.info("🚀 Using fast concat demuxer (no re-encoding)")

            # Create concat file
            concat_file = Path(output_path).parent / "concat_list.txt"
            with open(concat_file, 'w') as f:
                for path in input_paths:
                    # Escape single quotes in path
                    escaped_path = str(Path(path).absolute()).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-movflags', '+faststart',
                '-y', output_path
            ]

            def run_ffmpeg():
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600,
                    check=False
                )
                return result

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_ffmpeg)

            # Cleanup concat file
            try:
                concat_file.unlink()
            except:
                pass

            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Fast merged {len(input_paths)} videos (no re-encoding)',
                    'method': 'concat_demuxer',
                    'video_count': len(input_paths)
                }
            else:
                logger.warning(f"Concat demuxer failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}

        except Exception as e:
            logger.error(f"Concat demuxer error: {e}")
            return {'success': False, 'error': str(e)}

    async def merge_with_filter_complex(
            self,
            input_paths: List[str],
            output_path: str,
            video_infos: List[VideoInfo],
            profile: ProcessingProfile = ProcessingProfile.BALANCED
    ) -> Dict[str, Any]:
        """Merge with re-encoding using filter_complex"""
        try:
            logger.info(f"⚙️ Using filter_complex merge (re-encoding with {profile.value} profile)")

            # Get profile settings
            preset, crf = self._get_profile_settings(profile)

            # Build filter complex
            filter_parts = []
            video_inputs = []
            audio_inputs = []

            for i in range(len(input_paths)):
                # Normalize video
                filter_parts.append(
                    f"[{i}:v] format=yuv420p,colorspace=bt709:iall=bt709:fast=1,setsar=1:1 [v{i}]"
                )

                # Normalize audio if exists
                if video_infos[i].has_audio:
                    filter_parts.append(
                        f"[{i}:a] aresample=async=1:first_pts=0 [a{i}]"
                    )
                    audio_inputs.append(f"[a{i}]")

                video_inputs.append(f"[v{i}]")

            # Concat videos
            filter_parts.append(
                f"{''.join(video_inputs)}concat=n={len(input_paths)}:v=1:a=0[outv]"
            )

            # Concat audio if exists
            if audio_inputs:
                filter_parts.append(
                    f"{''.join(audio_inputs)}concat=n={len(audio_inputs)}:v=0:a=1[outa]"
                )

            filter_complex = "; ".join(filter_parts)

            # Build command
            cmd = ['ffmpeg']
            for input_path in input_paths:
                cmd.extend(['-i', input_path])

            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[outv]',
            ])

            if audio_inputs:
                cmd.extend(['-map', '[outa]'])

            cmd.extend([
                '-c:v', 'libx264',
                '-preset', preset,
                '-crf', str(crf),
                '-c:a', 'aac',
                '-b:a', '192k',
                '-movflags', '+faststart',
                '-pix_fmt', 'yuv420p',
                '-y', output_path
            ])

            def run_ffmpeg():
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=7200,
                    check=False
                )
                return result

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_ffmpeg)

            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Merged {len(input_paths)} videos with {profile.value} profile',
                    'method': 'filter_complex',
                    'video_count': len(input_paths),
                    'profile': profile.value
                }
            else:
                logger.error(f"FFmpeg merge failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}

        except Exception as e:
            logger.error(f"Filter complex merge error: {e}")
            return {'success': False, 'error': str(e)}

    def _get_profile_settings(self, profile: ProcessingProfile) -> tuple:
        """Get preset and CRF for profile"""
        settings = {
            ProcessingProfile.FAST: ('ultrafast', 28),
            ProcessingProfile.BALANCED: ('medium', 23),
            ProcessingProfile.QUALITY: ('slow', 18),
            ProcessingProfile.LOSSLESS: ('veryslow', 0)
        }
        return settings.get(profile, ('medium', 23))

    async def smart_merge(
            self,
            input_paths: List[str],
            output_path: str,
            strategy: MergeStrategy = MergeStrategy.AUTO,
            profile: ProcessingProfile = ProcessingProfile.BALANCED
    ) -> Dict[str, Any]:
        """Smart merge with automatic strategy selection"""
        try:
            # Get video info for all inputs
            video_infos = []
            for path in input_paths:
                info = await self.get_video_info(path)
                if not info:
                    return {'success': False, 'error': f'Cannot get info for {path}'}
                video_infos.append(info)

            # Determine merge strategy
            if strategy == MergeStrategy.AUTO:
                can_concat = await self.can_use_concat_demuxer(video_infos)
                if can_concat:
                    strategy = MergeStrategy.SMART_CONCAT
                else:
                    strategy = MergeStrategy.REENCODE

            # Execute merge
            if strategy == MergeStrategy.SMART_CONCAT:
                return await self.merge_with_concat_demuxer(input_paths, output_path)
            else:
                return await self.merge_with_filter_complex(
                    input_paths, output_path, video_infos, profile
                )

        except Exception as e:
            logger.error(f"Smart merge failed: {e}")
            return {'success': False, 'error': str(e)}


# ============================================================================
# MAIN VIDEO TOOL CLASS
# ============================================================================

class ImprovedVideoTool:
    """Production-ready video tool with all improvements"""

    ALLOWED_VIDEO_FORMATS = ['mp4', 'webm', 'mkv', 'avi', 'mov']
    ALLOWED_AUDIO_FORMATS = ['mp3', 'm4a', 'aac', 'wav', 'ogg']

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._create_config(config)
        self._setup_logging()

        # Initialize components
        self.limits = ResourceLimits(
            max_file_size_mb=self.config.get('max_file_size_mb', 2048),
            max_duration_seconds=self.config.get('max_duration_seconds', 7200),
            max_concurrent_downloads=self.config.get('max_concurrent_downloads', 5),
            max_memory_mb=self.config.get('max_memory_mb', 4096),
            max_disk_usage_mb=self.config.get('max_disk_usage_mb', 10240)
        )

        self.resource_monitor = ResourceMonitor(self.limits)
        self.temp_manager = TempFileManager()
        self.temp_manager.register_cleanup()

        cache_dir = Path(self.config.get('cache_dir', 'cache'))
        self.cache_manager = CacheManager(cache_dir)

        self.video_processor = ImprovedVideoProcessor(self.config, self.cache_manager)
        self.progress_tracker = ProgressTracker()

        self._download_semaphore = asyncio.Semaphore(self.limits.max_concurrent_downloads)
        self._running_tasks: List[asyncio.Task] = []

        logger.info("✅ ImprovedVideoTool initialized successfully")
        logger.info(f"📊 Limits: {self.limits.max_file_size_mb}MB file, "
                    f"{self.limits.max_concurrent_downloads} concurrent downloads")

    def _create_config(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create configuration with defaults"""
        default_config = {
            'log_level': 'INFO',
            'max_file_size_mb': 2048,
            'max_duration_seconds': 7200,
            'max_concurrent_downloads': 5,
            'max_memory_mb': 4096,
            'max_disk_usage_mb': 10240,
            'cache_dir': 'cache',
            'default_profile': ProcessingProfile.BALANCED.value,
            'default_merge_strategy': MergeStrategy.AUTO.value,
            'enable_hardware_accel': False,
            'retry_attempts': 3,
            'retry_delay': 5
        }

        if config:
            default_config.update(config)

        return default_config

    def _setup_logging(self):
        """Setup logging"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.getLogger().setLevel(log_level)

    # === DOWNLOAD WITH PROGRESS ===

    async def download_video(
            self,
            url: str,
            filename: Optional[str] = None,
            quality: str = 'best',
            format: str = 'mp4',
            progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Download video with validation and progress tracking"""
        try:
            # Validate inputs
            url = InputValidator.validate_url(url)
            format = InputValidator.validate_format(format, self.ALLOWED_VIDEO_FORMATS)

            if filename:
                filename = InputValidator.validate_filename(filename)

            # Check resources
            await self.resource_monitor.check_memory()
            await self.resource_monitor.check_disk_space(self.temp_manager.session_dir, required_mb=100)

            logger.info(f"📥 Downloading: {url}")

            # Create progress tracker
            progress = self.progress_tracker.create_progress(url)
            if progress_callback:
                self.progress_tracker.register_callback(progress_callback)

            # Generate filename
            if not filename:
                filename = self._generate_filename(url, 'video', format)

            temp_file = self.temp_manager.get_temp_path(filename)

            # Progress hook for yt-dlp
            def progress_hook(d):
                if d['status'] == 'downloading':
                    self.progress_tracker.update_progress(
                        url,
                        total_bytes=d.get('total_bytes', 0),
                        downloaded_bytes=d.get('downloaded_bytes', 0),
                        speed=d.get('speed', 0),
                        eta=d.get('eta', 0),
                        status='downloading'
                    )
                elif d['status'] == 'finished':
                    self.progress_tracker.update_progress(url, status='finished')

            # Configure yt-dlp
            ydl_opts = {
                'outtmpl': str(temp_file.with_suffix('')),
                'format': self._get_quality_format(quality, format),
                'quiet': True,
                'no_warnings': False,
                'noplaylist': True,
                'progress_hooks': [progress_hook],
                'retries': self.config.get('retry_attempts', 3),
            }

            # Use aria2c if available
            if shutil.which('aria2c'):
                ydl_opts.update({
                    'external_downloader': 'aria2c',
                    'external_downloader_args': [
                        '--max-connection-per-server=16',
                        '--split=16',
                        '--min-split-size=1M'
                    ]
                })

            # Download with retry
            attempt = 0
            max_attempts = self.config.get('retry_attempts', 3)
            last_error = None

            while attempt < max_attempts:
                try:
                    def sync_download():
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = yt_dlp.extract_info(url, download=True)
                            return {'success': True, 'info': info}

                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, sync_download)

                    if result['success']:
                        break

                except Exception as e:
                    last_error = e
                    attempt += 1
                    if attempt < max_attempts:
                        delay = self.config.get('retry_delay', 5)
                        logger.warning(f"⚠️ Download attempt {attempt} failed, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        raise DownloadError(f"Download failed after {max_attempts} attempts: {e}")

            if not result.get('success'):
                raise DownloadError(last_error or "Unknown download error")

            # Find actual file
            actual_file = await self._find_actual_file(temp_file)
            if not actual_file or not actual_file.exists():
                raise DownloadError("Downloaded file not found")

            # Validate file
            file_size_mb = actual_file.stat().st_size / 1024 / 1024
            await self.resource_monitor.check_file_size(int(file_size_mb))

            # Get video info
            info = result['info']
            video_info = await self.video_processor.get_video_info(str(actual_file))

            if video_info and video_info.duration > self.limits.max_duration_seconds:
                actual_file.unlink()
                raise ResourceLimitError(
                    f"Video too long: {video_info.duration}s exceeds limit of {self.limits.max_duration_seconds}s"
                )

            self.progress_tracker.update_progress(url, status='completed')

            return {
                'success': True,
                'filename': actual_file.name,
                'file_path': str(actual_file),
                'size': actual_file.stat().st_size,
                'size_mb': round(file_size_mb, 2),
                'duration': info.get('duration', 0),
                'quality': quality,
                'format': format,
                'title': info.get('title', 'Video'),
                'platform': self._identify_platform(url),
                'video_info': asdict(video_info) if video_info else None,
                'temp_file': True
            }

        except (ValidationError, ResourceLimitError, DownloadError) as e:
            self.progress_tracker.update_progress(url, status='failed', error=str(e))
            logger.error(f"❌ Download failed: {e}")
            return {'success': False, 'error': str(e), 'error_type': type(e).__name__}

        except Exception as e:
            self.progress_tracker.update_progress(url, status='failed', error=str(e))
            logger.error(f"❌ Unexpected download error: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'error_type': 'UnexpectedError'}

    async def download_to_file(
            self,
            url: str,
            output_path: str,
            quality: str = 'best',
            format: str = 'mp4',
            progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Download video and save to specified file"""
        try:
            output_path = InputValidator.validate_file_path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download to temp
            result = await self.download_video(url, None, quality, format, progress_callback)

            if not result['success']:
                return result

            # Move to destination
            temp_file = Path(result['file_path'])
            shutil.copy2(temp_file, output_path)

            # Cleanup temp
            temp_file.unlink(missing_ok=True)

            result['file_path'] = str(output_path)
            result['filename'] = output_path.name
            result['temp_file'] = False

            logger.info(f"✅ Downloaded to: {output_path}")
            return result

        except Exception as e:
            logger.error(f"❌ Download to file error: {e}")
            return {'success': False, 'error': str(e)}

    # === BATCH DOWNLOADS ===

    async def download_multiple_videos(
            self,
            urls: List[str],
            quality: str = 'best',
            progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Download multiple videos concurrently"""
        try:
            logger.info(f"📥 Batch downloading {len(urls)} videos")

            results = {
                'success': True,
                'downloaded_files': [],
                'failed_downloads': [],
                'total': len(urls),
                'successful': 0,
                'failed': 0
            }

            async def download_one(url: str):
                async with self._download_semaphore:
                    try:
                        result = await self.download_video(url, None, quality, 'mp4', progress_callback)

                        if result['success']:
                            results['successful'] += 1
                            results['downloaded_files'].append({
                                'url': url,
                                'filename': result['filename'],
                                'file_path': result['file_path'],
                                'size_mb': result.get('size_mb', 0)
                            })
                        else:
                            results['failed'] += 1
                            results['failed_downloads'].append({
                                'url': url,
                                'error': result.get('error')
                            })

                    except Exception as e:
                        results['failed'] += 1
                        results['failed_downloads'].append({
                            'url': url,
                            'error': str(e)
                        })

            # Create tasks
            tasks = [asyncio.create_task(download_one(url)) for url in urls]
            self._running_tasks.extend(tasks)

            # Wait for completion
            await asyncio.gather(*tasks, return_exceptions=True)

            # Remove completed tasks
            self._running_tasks = [t for t in self._running_tasks if not t.done()]

            logger.info(f"✅ Batch complete: {results['successful']}/{results['total']} successful")
            return results

        except Exception as e:
            logger.error(f"❌ Batch download error: {e}")
            return {'success': False, 'error': str(e)}

    # === MERGE VIDEOS ===

    async def merge_videos(
            self,
            video_files: List[str],
            output_filename: str,
            strategy: MergeStrategy = MergeStrategy.AUTO,
            profile: ProcessingProfile = ProcessingProfile.BALANCED
    ) -> Dict[str, Any]:
        """Merge multiple videos with smart strategy selection"""
        try:
            # Validate inputs
            if len(video_files) < 2:
                raise ValidationError("Need at least 2 videos to merge")

            if len(video_files) > 50:
                raise ValidationError("Maximum 50 videos allowed for merge")

            output_filename = InputValidator.validate_filename(output_filename)

            # Validate all input files exist
            input_paths = []
            for video_file in video_files:
                if isinstance(video_file, dict):
                    path = video_file.get('file_path')
                else:
                    path = video_file

                path = InputValidator.validate_file_path(str(path), must_exist=True)
                input_paths.append(str(path))

            logger.info(f"🎯 Merging {len(input_paths)} videos with {strategy.value} strategy")

            # Check resources
            await self.resource_monitor.check_memory()

            # Create output path
            output_path = self.temp_manager.get_temp_path(output_filename)

            # Perform merge
            result = await self.video_processor.smart_merge(
                input_paths=input_paths,
                output_path=str(output_path),
                strategy=strategy,
                profile=profile
            )

            if result['success'] and output_path.exists():
                file_size = output_path.stat().st_size
                result.update({
                    'filename': output_filename,
                    'file_path': str(output_path),
                    'size': file_size,
                    'size_mb': round(file_size / 1024 / 1024, 2),
                    'temp_file': True,
                    'input_count': len(input_paths)
                })
                logger.info(f"✅ Merge completed: {output_filename} ({result.get('method', 'unknown')})")

            return result

        except (ValidationError, ResourceLimitError) as e:
            logger.error(f"❌ Merge validation error: {e}")
            return {'success': False, 'error': str(e), 'error_type': type(e).__name__}

        except Exception as e:
            logger.error(f"❌ Merge error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def merge_and_save(
            self,
            video_files: List[str],
            output_path: str,
            strategy: MergeStrategy = MergeStrategy.AUTO,
            profile: ProcessingProfile = ProcessingProfile.BALANCED
    ) -> Dict[str, Any]:
        """Merge videos and save to specified path"""
        try:
            output_path = InputValidator.validate_file_path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Merge to temp
            temp_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            result = await self.merge_videos(video_files, temp_filename, strategy, profile)

            if not result['success']:
                return result

            # Move to destination
            temp_file = Path(result['file_path'])
            shutil.copy2(temp_file, output_path)

            # Cleanup temp
            temp_file.unlink(missing_ok=True)

            result['file_path'] = str(output_path)
            result['filename'] = output_path.name
            result['temp_file'] = False

            logger.info(f"✅ Merged video saved to: {output_path}")
            return result

        except Exception as e:
            logger.error(f"❌ Merge and save error: {e}")
            return {'success': False, 'error': str(e)}

    # === HELPER METHODS ===

    async def _find_actual_file(self, base_path: Path, audio: bool = False) -> Optional[Path]:
        """Find actual downloaded file"""
        base_dir = base_path.parent
        base_name = base_path.stem

        extensions = self.ALLOWED_AUDIO_FORMATS if audio else self.ALLOWED_VIDEO_FORMATS

        # Try exact match first
        for ext in extensions:
            possible_file = base_dir / f"{base_name}.{ext}"
            if possible_file.exists():
                return possible_file

        # Try prefix match
        for file_path in base_dir.iterdir():
            if file_path.is_file() and file_path.stem.startswith(base_name):
                return file_path

        return None

    def _generate_filename(self, url: str, media_type: str, format: str) -> str:
        """Generate safe filename from URL"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = self._identify_platform(url)

        # Get URL hash for uniqueness
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]

        return f"{platform}_{url_hash}_{timestamp}.{format}"

    def _identify_platform(self, url: str) -> str:
        """Identify platform from URL"""
        url_lower = url.lower()

        platforms = {
            'youtube': ['youtube.com', 'youtu.be'],
            'tiktok': ['tiktok.com'],
            'instagram': ['instagram.com'],
            'facebook': ['facebook.com', 'fb.watch'],
            'twitter': ['twitter.com', 'x.com'],
            'vimeo': ['vimeo.com']
        }

        for platform, domains in platforms.items():
            if any(domain in url_lower for domain in domains):
                return platform

        return 'unknown'

    def _get_quality_format(self, quality: str, format: str) -> str:
        """Convert quality to yt-dlp format"""
        if quality == 'best':
            return f'bestvideo[ext={format}]+bestaudio/best[ext={format}]/best'
        elif quality == 'worst':
            return 'worst'
        elif quality.isdigit():
            return f'bestvideo[height<={quality}]+bestaudio/best'
        else:
            return 'best'

    # === PROGRESS TRACKING ===

    def get_download_progress(self, url: str) -> Optional[Dict]:
        """Get progress for a specific download"""
        progress = self.progress_tracker.get_progress(url)
        return progress.to_dict() if progress else None

    def get_all_progress(self) -> Dict[str, Dict]:
        """Get all download progress"""
        all_progress = self.progress_tracker.get_all_progress()
        return {url: p.to_dict() for url, p in all_progress.items()}

    # === CLEANUP & MAINTENANCE ===

    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        await self.temp_manager.cleanup_session()

    async def cleanup_old_cache(self):
        """Clean up old cache files"""
        await self.cache_manager.cleanup_old_cache()

    async def cleanup_old_sessions(self, older_than_hours: int = 24):
        """Clean up old session directories"""
        await self.temp_manager.cleanup_old_sessions(older_than_hours)

    async def full_cleanup(self):
        """Perform full cleanup"""
        logger.info("🧹 Starting full cleanup...")
        await self.cleanup_temp_files()
        await self.cleanup_old_cache()
        await self.cleanup_old_sessions()
        logger.info("✅ Full cleanup completed")

    # === RESOURCE MONITORING ===

    async def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            temp_size = sum(
                f.stat().st_size for f in self.temp_manager.session_dir.rglob('*') if f.is_file()
            ) / 1024 / 1024

            disk_stat = shutil.disk_usage(self.temp_manager.session_dir)

            return {
                'memory_usage_mb': round(memory_mb, 2),
                'memory_limit_mb': self.limits.max_memory_mb,
                'memory_percent': round((memory_mb / self.limits.max_memory_mb) * 100, 2),
                'temp_size_mb': round(temp_size, 2),
                'disk_free_mb': round(disk_stat.free / 1024 / 1024, 2),
                'disk_total_mb': round(disk_stat.total / 1024 / 1024, 2),
                'active_downloads': len([t for t in self._running_tasks if not t.done()]),
                'session_dir': str(self.temp_manager.session_dir)
            }
        except Exception as e:
            logger.error(f"Failed to get resource stats: {e}")
            return {'error': str(e)}

    # === CANCEL OPERATIONS ===

    async def cancel_all_downloads(self):
        """Cancel all running downloads"""
        count = 0
        for task in self._running_tasks:
            if not task.done():
                task.cancel()
                count += 1

        if count > 0:
            logger.info(f"🛑 Cancelled {count} downloads")

        self._running_tasks.clear()

    # === CONTEXT MANAGER ===

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Clean shutdown"""
        logger.info("🔚 Shutting down ImprovedVideoTool...")

        # Cancel running tasks
        await self.cancel_all_downloads()

        # Cleanup
        await self.cleanup_temp_files()

        logger.info("✅ Shutdown complete")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_video_tool(config: Optional[Dict] = None) -> ImprovedVideoTool:
    """Factory function to create ImprovedVideoTool instance"""
    return ImprovedVideoTool(config)


# ============================================================================
# CLI HELPER (Optional)
# ============================================================================

async def main_example():
    """Example usage"""

    # Create tool with custom config
    config = {
        'max_file_size_mb': 1024,  # 1GB limit
        'max_concurrent_downloads': 3,
        'log_level': 'INFO'
    }

    async with create_video_tool(config) as tool:

        # Download single video
        result = await tool.download_video(
            url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            quality='720',
            format='mp4'
        )

        if result['success']:
            print(f"✅ Downloaded: {result['filename']} ({result['size_mb']}MB)")

            # Get resource stats
            stats = await tool.get_resource_stats()
            print(f"📊 Memory: {stats['memory_usage_mb']}MB")

        # Download multiple videos
        urls = [
            'https://www.youtube.com/watch?v=video1',
            'https://www.youtube.com/watch?v=video2'
        ]

        batch_result = await tool.download_multiple_videos(urls, quality='best')
        print(f"📦 Batch: {batch_result['successful']}/{batch_result['total']} successful")

        # Merge videos with auto strategy
        if batch_result['successful'] >= 2:
            video_files = [f['file_path'] for f in batch_result['downloaded_files'][:2]]

            merge_result = await tool.merge_videos(
                video_files=video_files,
                output_filename='merged_output.mp4',
                strategy=MergeStrategy.AUTO,
                profile=ProcessingProfile.BALANCED
            )

            if merge_result['success']:
                print(f"✅ Merged using {merge_result['method']}: {merge_result['filename']}")


if __name__ == '__main__':
    asyncio.run(main_example())