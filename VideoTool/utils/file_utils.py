# video_tool/utils/file_utils.py
import os
import hashlib
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import fnmatch

logger = logging.getLogger(__name__)


class FileManager:
    """Quản lý file và storage với caching và optimization"""

    def __init__(self, directories: Dict[str, Path]):
        self.dirs = directories
        self.file_cache: Dict[str, Dict] = {}
        self.cache_timestamp: float = 0
        self.cache_ttl: float = 30.0  # 30 seconds cache TTL

        # Supported formats
        self.video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
        self.audio_formats = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma'}
        self.image_formats = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'}

        # Initialize cache
        self.refresh_cache()

        logger.info("File Manager initialized")

    def refresh_cache(self):
        """Refresh file cache"""
        self.file_cache.clear()
        self._build_file_cache()
        self.cache_timestamp = asyncio.get_event_loop().time()

    def _build_file_cache(self):
        """Xây dựng file cache"""
        for dir_name, dir_path in self.dirs.items():
            if not dir_path.exists():
                continue

            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    file_info = self._get_file_info(file_path)
                    if file_info:
                        cache_key = f"{dir_name}:{file_path.name}"
                        self.file_cache[cache_key] = file_info

    def _get_file_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết file"""
        try:
            stat = file_path.stat()
            file_type = self._get_file_type(file_path)

            info = {
                'name': file_path.name,
                'path': str(file_path),
                'relative_path': f"{file_path.parent.name}/{file_path.name}",
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'type': file_type,
                'extension': file_path.suffix.lower(),
                'hash': self._calculate_file_hash(file_path)
            }

            # Add media-specific information
            if file_type in ['video', 'audio']:
                media_info = self._get_media_info(file_path, file_type)
                info.update(media_info)

            return info

        except Exception as e:
            logger.warning(f"Could not get file info for {file_path}: {e}")
            return None

    def _get_file_type(self, file_path: Path) -> str:
        """Xác định loại file"""
        ext = file_path.suffix.lower()

        if ext in self.video_formats:
            return 'video'
        elif ext in self.audio_formats:
            return 'audio'
        elif ext in self.image_formats:
            return 'image'
        else:
            return 'unknown'

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Tính hash của file (optimized for large files)"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read first 8KB for quick hash
                chunk = f.read(8192)
                hasher.update(chunk)

            # Add file size and modification time to hash
            stat = file_path.stat()
            hasher.update(str(stat.st_size).encode())
            hasher.update(str(int(stat.st_mtime)).encode())

            return hasher.hexdigest()
        except:
            return 'unknown'

    def _get_media_info(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Lấy thông tin media (video/audio)"""
        try:
            if file_type == 'video':
                return self._get_video_info(file_path)
            elif file_type == 'audio':
                return self._get_audio_info(file_path)
            else:
                return {}
        except Exception as e:
            logger.debug(f"Could not get media info for {file_path}: {e}")
            return {}

    def _get_video_info(self, file_path: Path) -> Dict[str, Any]:
        """Lấy thông tin video"""
        try:
            import cv2

            cap = cv2.VideoCapture(str(file_path))
            if not cap.isOpened():
                return {}

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            codec = int(cap.get(cv2.CAP_PROP_FOURCC))

            cap.release()

            # Convert codec to readable format
            codec_str = ""
            for i in range(4):
                codec_str += chr((codec >> (8 * i)) & 0xFF)
            codec_str = codec_str.strip('\x00')

            return {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'resolution': f"{width}x{height}",
                'codec': codec_str,
                'aspect_ratio': self._calculate_aspect_ratio(width, height)
            }
        except Exception as e:
            logger.debug(f"CV2 video info failed for {file_path}: {e}")
            return {}

    def _get_audio_info(self, file_path: Path) -> Dict[str, Any]:
        """Lấy thông tin audio"""
        try:
            # For audio files, we'll use a simpler approach
            # In production, you might use libraries like pydub or mutagen
            stat = file_path.stat()
            file_size = stat.st_size

            # Estimate duration based on file size and format
            duration = self._estimate_audio_duration(file_path, file_size)

            return {
                'duration': duration,
                'bitrate': self._estimate_bitrate(file_size, duration),
                'channels': 2,  # Default assumption
                'sample_rate': 44100  # Default assumption
            }
        except Exception as e:
            logger.debug(f"Audio info failed for {file_path}: {e}")
            return {}

    def _estimate_audio_duration(self, file_path: Path, file_size: int) -> float:
        """Ước tính duration của audio file"""
        ext = file_path.suffix.lower()

        # Average bitrates for estimation
        bitrate_estimates = {
            '.mp3': 128000,  # 128 kbps
            '.wav': 1411000,  # 1411 kbps (CD quality)
            '.m4a': 256000,  # 256 kbps
            '.aac': 192000,  # 192 kbps
            '.ogg': 160000,  # 160 kbps
            '.flac': 1000000,  # 1000 kbps
        }

        bitrate = bitrate_estimates.get(ext, 128000)
        duration = (file_size * 8) / bitrate  # Convert bytes to bits

        return max(0, duration)

    def _estimate_bitrate(self, file_size: int, duration: float) -> int:
        """Ước tính bitrate"""
        if duration > 0:
            return int((file_size * 8) / duration)
        return 0

    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """Tính aspect ratio"""

        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a

        if width == 0 or height == 0:
            return "0:0"

        divisor = gcd(width, height)
        return f"{width // divisor}:{height // divisor}"

    def resolve_path(self, file_path: str) -> Optional[Path]:
        """Resolve đường dẫn file"""
        try:
            path = Path(file_path)

            # If absolute path and exists
            if path.is_absolute() and path.exists():
                return path

            # Try relative paths in all directories
            for dir_path in self.dirs.values():
                potential_path = dir_path / path.name
                if potential_path.exists():
                    return potential_path

            # Try with relative path structure
            if ':' in file_path:
                dir_name, file_name = file_path.split(':', 1)
                if dir_name in self.dirs:
                    potential_path = self.dirs[dir_name] / file_name
                    if potential_path.exists():
                        return potential_path

            return None

        except Exception as e:
            logger.warning(f"Path resolution failed for {file_path}: {e}")
            return None

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin file"""
        # Check cache first
        cache_key = self._get_cache_key(file_path)
        if cache_key in self.file_cache:
            return self.file_cache[cache_key]

        # Resolve path and get info
        resolved_path = self.resolve_path(file_path)
        if resolved_path:
            file_info = self._get_file_info(resolved_path)
            if file_info:
                self.file_cache[cache_key] = file_info
                return file_info

        return None

    def _get_cache_key(self, file_path: str) -> str:
        """Tạo cache key từ file path"""
        # Extract directory name and filename
        path = Path(file_path)
        if ':' in file_path:
            dir_name, file_name = file_path.split(':', 1)
            return f"{dir_name}:{Path(file_name).name}"
        else:
            # Try to determine directory
            for dir_name, dir_path in self.dirs.items():
                if str(path.parent) == str(dir_path):
                    return f"{dir_name}:{path.name}"

            # Fallback
            return f"unknown:{path.name}"

    def list_files(self, file_type: Optional[str] = None,
                   pattern: Optional[str] = None) -> Dict[str, Any]:
        """Liệt kê files với filtering"""
        # Refresh cache if stale
        current_time = asyncio.get_event_loop().time()
        if current_time - self.cache_timestamp > self.cache_ttl:
            self.refresh_cache()

        result = {}

        for dir_name, dir_path in self.dirs.items():
            if not dir_path.exists():
                result[dir_name] = []
                continue

            files = []
            for cache_key, file_info in self.file_cache.items():
                if cache_key.startswith(f"{dir_name}:"):
                    # Apply filters
                    if file_type and file_info['type'] != file_type:
                        continue

                    if pattern and not fnmatch.fnmatch(file_info['name'], pattern):
                        continue

                    files.append(file_info)

            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            result[dir_name] = files

        # Add summary
        total_files = sum(len(files) for files in result.values())
        total_size = sum(
            file['size']
            for files in result.values()
            for file in files
        )

        result['_summary'] = {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_human': self._format_size(total_size),
            'cache_timestamp': self.cache_timestamp
        }

        return result

    def generate_unique_filename(self, directory: str, filename: str) -> str:
        """Tạo tên file duy nhất"""
        if directory not in self.dirs:
            return filename

        dir_path = self.dirs[directory]
        path = dir_path / filename

        if not path.exists():
            return filename

        # Split filename and extension
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 1:
            base_name = name_parts[0]
            extension = ''
        else:
            base_name = name_parts[0]
            extension = name_parts[1]

        # Find unique name
        counter = 1
        while True:
            if extension:
                new_filename = f"{base_name}_{counter:03d}.{extension}"
            else:
                new_filename = f"{base_name}_{counter:03d}"

            new_path = dir_path / new_filename
            if not new_path.exists():
                return new_filename

            counter += 1

    async def cleanup(self, cleanup_type: str = 'downloads') -> Dict[str, Any]:
        """Dọn dẹp files"""
        try:
            deleted_files = []
            target_dirs = []

            if cleanup_type == 'downloads':
                target_dirs = ['downloads']
            elif cleanup_type == 'outputs':
                target_dirs = ['output']
            elif cleanup_type == 'music':
                target_dirs = ['music']
            elif cleanup_type == 'logos':
                target_dirs = ['logos']
            elif cleanup_type == 'all':
                target_dirs = ['downloads', 'output', 'music', 'logos']
            else:
                return {'success': False, 'error': f'Invalid cleanup type: {cleanup_type}'}

            total_size = 0

            for dir_name in target_dirs:
                dir_path = self.dirs.get(dir_name)
                if dir_path and dir_path.exists():
                    for file_path in dir_path.iterdir():
                        if file_path.is_file():
                            try:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                deleted_files.append({
                                    'name': file_path.name,
                                    'path': str(file_path),
                                    'size': file_size
                                })
                                total_size += file_size
                                logger.debug(f"Deleted: {file_path.name}")
                            except Exception as e:
                                logger.warning(f"Could not delete {file_path}: {e}")

            # Refresh cache after cleanup
            self.refresh_cache()

            return {
                'success': True,
                'deleted_files': deleted_files,
                'count': len(deleted_files),
                'total_size': total_size,
                'total_size_human': self._format_size(total_size),
                'cleanup_type': cleanup_type,
                'message': f'Deleted {len(deleted_files)} files ({self._format_size(total_size)})'
            }

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_storage_info(self) -> Dict[str, Any]:
        """Lấy thông tin storage"""
        storage_info = {}
        total_size = 0
        total_files = 0

        for dir_name, dir_path in self.dirs.items():
            if not dir_path.exists():
                storage_info[dir_name] = {
                    'size': 0,
                    'file_count': 0,
                    'exists': False
                }
                continue

            dir_size = 0
            dir_file_count = 0

            # Use cache for faster calculation
            for cache_key, file_info in self.file_cache.items():
                if cache_key.startswith(f"{dir_name}:"):
                    dir_size += file_info['size']
                    dir_file_count += 1

            storage_info[dir_name] = {
                'size': dir_size,
                'size_human': self._format_size(dir_size),
                'file_count': dir_file_count,
                'exists': True,
                'path': str(dir_path)
            }

            total_size += dir_size
            total_files += dir_file_count

        # Calculate available space (approximate)
        try:
            if self.dirs['downloads'].exists():
                disk_usage = shutil.disk_usage(self.dirs['downloads'])
                available_space = disk_usage.free
            else:
                available_space = 0
        except:
            available_space = 0

        return {
            'directories': storage_info,
            'total': {
                'size': total_size,
                'size_human': self._format_size(total_size),
                'file_count': total_files
            },
            'available_space': {
                'bytes': available_space,
                'human': self._format_size(available_space)
            },
            'cache_info': {
                'cached_files': len(self.file_cache),
                'cache_timestamp': self.cache_timestamp
            }
        }

    def _format_size(self, size_bytes: int) -> str:
        """Định dạng kích thước file"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0

        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024.0
            unit_index += 1

        return f"{size_bytes:.2f} {units[unit_index]}"

    def search_files(self, query: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm files"""
        results = []
        query_lower = query.lower()

        for file_info in self.file_cache.values():
            # Apply file type filter
            if file_type and file_info['type'] != file_type:
                continue

            # Search in filename and path
            if (query_lower in file_info['name'].lower() or
                    query_lower in file_info['path'].lower()):
                results.append(file_info)

        # Sort by relevance (simple implementation)
        results.sort(key=lambda x: (
            x['name'].lower().startswith(query_lower),
            x['modified']
        ), reverse=True)

        return results

    def get_recent_files(self, limit: int = 10, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy files gần đây nhất"""
        files = []

        for file_info in self.file_cache.values():
            if file_type and file_info['type'] != file_type:
                continue
            files.append(file_info)

        # Sort by modification time
        files.sort(key=lambda x: x['modified'], reverse=True)

        return files[:limit]

    def validate_file_path(self, file_path: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
        """Validate file path"""
        resolved_path = self.resolve_path(file_path)

        if not resolved_path or not resolved_path.exists():
            return {
                'valid': False,
                'error': 'File not found',
                'resolved_path': str(resolved_path) if resolved_path else None
            }

        file_info = self.get_file_info(file_path)
        if not file_info:
            return {
                'valid': False,
                'error': 'Could not read file info',
                'resolved_path': str(resolved_path)
            }

        if expected_type and file_info['type'] != expected_type:
            return {
                'valid': False,
                'error': f'Expected {expected_type} but got {file_info["type"]}',
                'file_type': file_info['type'],
                'expected_type': expected_type,
                'resolved_path': str(resolved_path)
            }

        return {
            'valid': True,
            'file_info': file_info,
            'resolved_path': str(resolved_path)
        }