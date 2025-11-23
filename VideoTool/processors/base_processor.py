# video_tool/processors/base_processor.py
import os
import abc
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
import tempfile

logger = logging.getLogger(__name__)


class BaseVideoProcessor(abc.ABC):
    """Abstract base class cho tất cả video processors"""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "video_tool"
        self.temp_dir.mkdir(exist_ok=True)
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        self.max_file_size = 128 * 1024 * 1024 * 1024  # 128GB

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Kiểm tra processor có khả dụng không"""
        pass

    @abc.abstractmethod
    async def process_video(self, input_file: str, output_file: str,
                            effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video với hiệu ứng - Async version"""
        pass

    @abc.abstractmethod
    def process_video_sync(self, input_file: str, output_file: str,
                           effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video sync version cho thread pool"""
        pass

    @abc.abstractmethod
    async def download_video(self, url: str, filename: Optional[str] = None,
                             quality: str = 'best') -> Dict[str, Any]:
        """Tải video từ URL"""
        pass

    @abc.abstractmethod
    async def download_audio(self, url: str, filename: Optional[str] = None,
                             format: str = 'mp3', quality: str = '192') -> Dict[str, Any]:
        """Tải audio từ URL video"""
        pass

    @abc.abstractmethod
    async def extract_audio(self, video_file: str, output_file: str) -> Dict[str, Any]:
        """Trích xuất audio từ video"""
        pass

    @abc.abstractmethod
    def export_timeline_sync(self, timeline_data: Dict, output_path: str,
                             config: Optional[Dict] = None) -> Dict[str, Any]:
        """Export timeline thành video"""
        pass

    # === COMMON VALIDATION METHODS ===
    def _validate_input_file(self, input_file: str) -> Optional[str]:
        """Validate input file"""
        if not os.path.exists(input_file):
            return f"Input file not found: {input_file}"

        if not os.path.isfile(input_file):
            return f"Input path is not a file: {input_file}"

        file_size = os.path.getsize(input_file)
        if file_size > self.max_file_size:
            return f"File too large: {file_size / 1024 / 1024 / 1024:.1f}GB > {self.max_file_size / 1024 / 1024 / 1024}GB"

        file_ext = Path(input_file).suffix.lower()
        if file_ext not in self.supported_formats:
            return f"Unsupported format: {file_ext}. Supported: {self.supported_formats}"

        return None

    def _validate_output_path(self, output_file: str) -> Optional[str]:
        """Validate output path"""
        output_dir = Path(output_file).parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"Cannot create output directory: {e}"

        if not os.access(output_dir, os.W_OK):
            return f"Output directory not writable: {output_dir}"

        return None

    def _validate_effects_config(self, effects_config: Dict) -> Optional[str]:
        """Validate effects configuration"""
        if not isinstance(effects_config, dict):
            return "Effects config must be a dictionary"

        # Validate numeric values
        numeric_fields = ['brightness', 'contrast', 'saturation', 'rotate', 'logo_size', 'logo_opacity']
        for field in numeric_fields:
            if field in effects_config:
                try:
                    value = float(effects_config[field])
                    if field in ['brightness', 'contrast', 'saturation'] and (value < 0.1 or value > 5.0):
                        return f"{field} must be between 0.1 and 5.0"
                    if field == 'rotate' and (value < -360 or value > 360):
                        return "rotate must be between -360 and 360"
                    if field == 'logo_size' and (value < 10 or value > 500):
                        return "logo_size must be between 10 and 500"
                    if field == 'logo_opacity' and (value < 0 or value > 1):
                        return "logo_opacity must be between 0 and 1"
                except (ValueError, TypeError):
                    return f"{field} must be a number"

        # Validate boolean fields
        boolean_fields = ['flip_horizontal', 'flip_vertical']
        for field in boolean_fields:
            if field in effects_config and not isinstance(effects_config[field], bool):
                return f"{field} must be boolean"

        # Validate logo path
        logo_path = effects_config.get('logo_path')
        if logo_path and not os.path.exists(logo_path):
            return f"Logo file not found: {logo_path}"

        return None

    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Lấy thông tin video cơ bản"""
        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            cap.release()

            return {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'resolution': f"{width}x{height}",
                'file_size': os.path.getsize(video_path)
            }
        except Exception as e:
            logger.warning(f"Could not get video info for {video_path}: {e}")
            return {}

    def _create_temp_file(self, suffix: str = '.mp4') -> str:
        """Tạo temporary file"""
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        return temp_path

    def _cleanup_temp_files(self):
        """Dọn dẹp temporary files"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.warning(f"Temp cleanup failed: {e}")

    def _format_duration(self, seconds: float) -> str:
        """Định dạng thời lượng"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{minutes:02d}:{secs:02d}"

    def _format_file_size(self, size_bytes: int) -> str:
        """Định dạng kích thước file"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def get_capabilities(self) -> Dict[str, Any]:
        """Lấy thông tin capabilities của processor"""
        return {
            'name': self.__class__.__name__,
            'available': self.is_available(),
            'supported_formats': self.supported_formats,
            'max_file_size': self.max_file_size,
            'temp_directory': str(self.temp_dir)
        }

    def __del__(self):
        """Cleanup khi object bị destroy"""
        self._cleanup_temp_files()