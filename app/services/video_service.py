import os
import asyncio
import time
import logging
import re
import urllib.parse
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
from datetime import datetime
import aiofiles

from app.config import Config

logger = logging.getLogger(__name__)


class VideoService:
    """Optimized Video Service for direct browser downloads"""

    def __init__(self, config_class=None):
        self.config = config_class or Config()
        self._initialize_directories()
        self._initialize_components()
        logger.info("🚀 Optimized VideoService initialized - Direct Download Mode")

    def _initialize_directories(self):
        """Initialize only essential directories"""
        self.base_dir = Path(self.config.BASE_DIR)
        self.static_dir = Path(self.config.STATIC_DIR)
        
        # Only keep temp directory for processing
        self.temp_dir = self.static_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📁 Essential directories initialized")

    def _initialize_components(self):
        """Initialize video processing components"""
        try:
            # Try to import optimized components
            from VideoTool.main import OptimizedVideoTool
            video_tool_config = {
                'temp_dir': str(self.temp_dir),
                'simplify_urls': True,
                'ignore_playlist': True,
                'use_aria2c': True,
                'fragment_threads': 8,
                'max_filesize': '500M'
            }
            self.video_tool = OptimizedVideoTool(config=video_tool_config)
            self.use_optimized_tool = True
            logger.info("✅ Using OptimizedVideoTool backend")
        except ImportError as e:
            logger.warning(f"❌ OptimizedVideoTool not available: {e}")
            self.use_optimized_tool = False
            self._initialize_fallback_components()

    def _initialize_fallback_components(self):
        """Initialize yt-dlp based fallback"""
        try:
            import yt_dlp
            self.ydl = yt_dlp
            logger.info("✅ Using yt-dlp fallback backend")
        except ImportError as e:
            logger.error(f"❌ yt-dlp not available: {e}")
            self.ydl = None

    # === URL PROCESSING METHODS ===
    def _optimize_url(self, url: str) -> str:
        """Optimize URL for better download performance"""
        try:
            platform = self._identify_platform(url)
            
            if platform == 'youtube':
                return self._optimize_youtube_url(url)
            elif platform == 'tiktok':
                return self._optimize_tiktok_url(url)
            elif platform == 'instagram':
                return self._optimize_instagram_url(url)
            else:
                return self._optimize_generic_url(url)
                
        except Exception as e:
            logger.warning(f"URL optimization failed: {e}")
            return url

    def _optimize_youtube_url(self, url: str) -> str:
        """Optimize YouTube URL - remove playlist parameters"""
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)

            # Keep only video ID parameter
            clean_params = {}
            if 'v' in query_params:
                clean_params['v'] = query_params['v'][0]

            new_query = urllib.parse.urlencode(clean_params)
            optimized_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                ''
            ))

            logger.info(f"🎯 YouTube URL optimized")
            return optimized_url

        except Exception as e:
            logger.warning(f"YouTube URL optimization failed: {e}")
            return url

    def _optimize_tiktok_url(self, url: str) -> str:
        """Optimize TikTok URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            return urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                '', '', ''
            ))
        except:
            return url

    def _optimize_instagram_url(self, url: str) -> str:
        """Optimize Instagram URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            if '/p/' in parsed.path or '/reel/' in parsed.path:
                path = parsed.path.split('?')[0]
                return urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    path,
                    '', '', ''
                ))
            return url
        except:
            return url

    def _optimize_generic_url(self, url: str) -> str:
        """Optimize generic URLs"""
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)

            # Remove tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 'gclid']
            clean_params = {k: v[0] for k, v in query_params.items()
                          if k.lower() not in tracking_params}

            new_query = urllib.parse.urlencode(clean_params)
            return urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        except:
            return url

    # === CORE DOWNLOAD METHODS ===
    async def download_video(self, url: str, filename: Optional[str] = None,
                           quality: str = 'best', format: str = 'mp4') -> Dict[str, Any]:
        """Download video and return file information for browser download"""
        try:
            # Validate URL
            if not self._is_supported_url(url):
                return {
                    'success': False,
                    'error': 'URL không được hỗ trợ. Vui lòng kiểm tra lại.'
                }

            logger.info(f"📥 Downloading video: {url}")

            # Optimize URL
            original_url = url
            url = self._optimize_url(url)
            if url != original_url:
                logger.info("🔄 URL optimized")

            # Generate filename
            if not filename:
                platform = self._identify_platform(url)
                filename = self._generate_filename_from_url(url, platform, format)
            else:
                filename = self._ensure_extension(filename, format)

            # Download using available backend
            if self.use_optimized_tool:
                result = await self._download_with_optimized_tool(url, filename, quality, format)
            else:
                result = await self._download_with_ytdlp(url, filename, quality, format)

            return result

        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            return {'success': False, 'error': str(e)}

    async def download_audio(self, url: str, filename: Optional[str] = None,
                           format: str = 'mp3', quality: str = '192') -> Dict[str, Any]:
        """Download audio and return file information"""
        try:
            if not self._is_supported_url(url):
                return {'success': False, 'error': 'URL không được hỗ trợ'}

            logger.info(f"🎵 Downloading audio: {url}")

            # Optimize URL
            url = self._optimize_url(url)

            # Generate filename
            if not filename:
                platform = self._identify_platform(url)
                filename = self._generate_audio_filename_from_url(url, platform, format)
            else:
                filename = self._ensure_extension(filename, format)

            # Download audio
            if self.use_optimized_tool:
                result = await self._download_audio_with_optimized_tool(url, filename, format, quality)
            else:
                result = await self._download_audio_with_ytdlp(url, filename, format, quality)

            return result

        except Exception as e:
            logger.error(f"❌ Audio download error: {e}")
            return {'success': False, 'error': str(e)}

    # === DOWNLOAD IMPLEMENTATIONS ===
    async def _download_with_optimized_tool(self, url: str, filename: str, 
                                          quality: str, format: str) -> Dict[str, Any]:
        """Download using OptimizedVideoTool"""
        try:
            result = await self.video_tool.download_video(url, filename, quality, format)
            
            if result.get('success'):
                # Get file info for browser download
                file_path = Path(result.get('file_path', ''))
                if file_path.exists():
                    file_info = await self._get_file_info(file_path)
                    return {
                        'success': True,
                        'filename': filename,
                        'file_path': str(file_path),
                        'size': file_info['size'],
                        'duration': result.get('duration', 0),
                        'quality': quality,
                        'format': format,
                        'message': 'Video download thành công'
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Optimized tool download error: {e}")
            return {'success': False, 'error': str(e)}

    async def _download_with_ytdlp(self, url: str, filename: str, 
                                 quality: str, format: str) -> Dict[str, Any]:
        """Download using yt-dlp"""
        if not self.ydl:
            return {'success': False, 'error': 'yt-dlp not available'}

        try:
            output_path = self.temp_dir / filename

            ydl_opts = {
                'outtmpl': str(output_path.with_suffix('')),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'extract_flat': False,
                'nocheckcertificate': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }

            # Add format specific options
            if format != 'best':
                ydl_opts['format'] = f'best[ext={format}]/best'

            def sync_download():
                with self.ydl.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        return {'success': True, 'info': info, 'file_path': str(output_path)}
                    except Exception as e:
                        return {'success': False, 'error': str(e)}

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_download)

            if result['success']:
                # Find the actual downloaded file (yt-dlp might change extension)
                actual_path = await self._find_downloaded_file(output_path)
                if actual_path and actual_path.exists():
                    file_info = await self._get_file_info(actual_path)
                    info = result['info']
                    
                    return {
                        'success': True,
                        'filename': actual_path.name,
                        'file_path': str(actual_path),
                        'size': file_info['size'],
                        'duration': info.get('duration', 0),
                        'quality': quality,
                        'format': format,
                        'title': info.get('title', 'Video'),
                        'platform': self._identify_platform(url)
                    }
                else:
                    return {'success': False, 'error': 'Downloaded file not found'}
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _download_audio_with_optimized_tool(self, url: str, filename: str,
                                                format: str, quality: str) -> Dict[str, Any]:
        """Download audio using OptimizedVideoTool"""
        try:
            result = await self.video_tool.download_audio(url, filename, format, quality)
            
            if result.get('success'):
                file_path = Path(result.get('file_path', ''))
                if file_path.exists():
                    file_info = await self._get_file_info(file_path)
                    return {
                        'success': True,
                        'filename': filename,
                        'file_path': str(file_path),
                        'size': file_info['size'],
                        'duration': result.get('duration', 0),
                        'format': format,
                        'message': 'Audio download thành công'
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Optimized tool audio error: {e}")
            return {'success': False, 'error': str(e)}

    async def _download_audio_with_ytdlp(self, url: str, filename: str,
                                       format: str, quality: str) -> Dict[str, Any]:
        """Download audio using yt-dlp"""
        if not self.ydl:
            return {'success': False, 'error': 'yt-dlp not available'}

        try:
            output_path = self.temp_dir / filename

            ydl_opts = {
                'outtmpl': str(output_path.with_suffix('')),
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': quality,
                }],
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
            }

            def sync_download():
                with self.ydl.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        return {'success': True, 'info': info, 'file_path': str(output_path)}
                    except Exception as e:
                        return {'success': False, 'error': str(e)}

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_download)

            if result['success']:
                # Find the actual audio file
                actual_path = await self._find_downloaded_file(output_path, audio=True)
                if actual_path and actual_path.exists():
                    file_info = await self._get_file_info(actual_path)
                    info = result['info']
                    
                    return {
                        'success': True,
                        'filename': actual_path.name,
                        'file_path': str(actual_path),
                        'size': file_info['size'],
                        'duration': info.get('duration', 0),
                        'format': format,
                        'title': info.get('title', 'Audio'),
                        'platform': self._identify_platform(url)
                    }
                else:
                    return {'success': False, 'error': 'Downloaded audio file not found'}
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # === FILE MANAGEMENT ===
    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information"""
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"File info error: {e}")
            return {'size': 0, 'created': 0, 'modified': 0}

    async def _find_downloaded_file(self, base_path: Path, audio: bool = False) -> Optional[Path]:
        """Find the actual downloaded file (yt-dlp might change extensions)"""
        try:
            base_dir = base_path.parent
            base_name = base_path.stem
            
            # Common extensions
            if audio:
                extensions = ['.mp3', '.m4a', '.wav', '.aac', '.ogg']
            else:
                extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv']
            
            # Check for files with similar names
            for ext in extensions:
                possible_path = base_dir / f"{base_name}{ext}"
                if possible_path.exists():
                    return possible_path
            
            # Check for any file starting with base_name
            for file_path in base_dir.iterdir():
                if file_path.is_file() and file_path.stem.startswith(base_name):
                    return file_path
            
            return None
            
        except Exception as e:
            logger.error(f"Find downloaded file error: {e}")
            return None

    def _ensure_extension(self, filename: str, format: str) -> str:
        """Ensure filename has correct extension"""
        filename = Path(filename).name
        base_name = Path(filename).stem
        
        if format == 'mp3':
            return f"{base_name}.mp3"
        elif format in ['mp4', 'webm', 'avi', 'mov', 'mkv']:
            return f"{base_name}.{format}"
        else:
            return f"{base_name}.mp4"

    # === UTILITY METHODS ===
    def _is_supported_url(self, url: str) -> bool:
        """Check if URL is from supported platform"""
        supported_patterns = [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)',
            r'(https?://)?(www\.|vm\.|vt\.)?tiktok\.com',
            r'(https?://)?(www\.)?instagram\.com',
            r'(https?://)?(www\.|fb\.|m\.)?facebook\.com',
            r'(https?://)?fb\.watch',
            r'(https?://)?(www\.|mobile\.)?(twitter\.com|x\.com)',
            r'(https?://)?(www\.)?vimeo\.com',
        ]

        try:
            url_lower = url.lower()
            return any(re.search(pattern, url_lower) for pattern in supported_patterns)
        except Exception:
            return False

    def _identify_platform(self, url: str) -> str:
        """Identify platform from URL"""
        platform_patterns = {
            'youtube': [r'youtube\.com', r'youtu\.be'],
            'tiktok': [r'tiktok\.com'],
            'instagram': [r'instagram\.com'],
            'facebook': [r'facebook\.com', r'fb\.watch'],
            'twitter': [r'twitter\.com', r'x\.com'],
            'vimeo': [r'vimeo\.com'],
        }

        url_lower = url.lower()
        for platform, patterns in platform_patterns.items():
            if any(re.search(pattern, url_lower) for pattern in patterns):
                return platform
        return 'unknown'

    def _generate_filename_from_url(self, url: str, platform: str, format: str) -> str:
        """Generate meaningful filename from URL"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            identifier = self._extract_video_identifier(url, platform)
            
            if identifier:
                return f"{platform}_{identifier}_{timestamp}.{format}"
            else:
                return f"{platform}_video_{timestamp}.{format}"
        except Exception:
            return f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

    def _generate_audio_filename_from_url(self, url: str, platform: str, format: str) -> str:
        """Generate meaningful audio filename from URL"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            identifier = self._extract_video_identifier(url, platform)
            
            if identifier:
                return f"{platform}_{identifier}_audio_{timestamp}.{format}"
            else:
                return f"{platform}_audio_{timestamp}.{format}"
        except Exception:
            return f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

    def _extract_video_identifier(self, url: str, platform: str) -> Optional[str]:
        """Extract video identifier based on platform"""
        try:
            if platform == 'youtube':
                return self._extract_youtube_id(url)
            elif platform == 'tiktok':
                return self._extract_tiktok_id(url)
            elif platform == 'instagram':
                return self._extract_instagram_id(url)
            elif platform == 'facebook':
                return self._extract_facebook_id(url)
            elif platform == 'twitter':
                return self._extract_twitter_id(url)
            elif platform == 'vimeo':
                return self._extract_vimeo_id(url)
            else:
                return self._extract_generic_id(url)
        except:
            return None

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&]+)',
            r'youtube\.com/embed/([^/?]+)',
        ]
        return self._extract_with_patterns(url, patterns)

    def _extract_tiktok_id(self, url: str) -> Optional[str]:
        patterns = [
            r'tiktok\.com/.+?/video/(\d+)',
            r'tiktok\.com/@.+?/video/(\d+)',
        ]
        return self._extract_with_patterns(url, patterns)

    def _extract_instagram_id(self, url: str) -> Optional[str]:
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
        ]
        return self._extract_with_patterns(url, patterns)

    def _extract_facebook_id(self, url: str) -> Optional[str]:
        patterns = [
            r'facebook\.com/.+?/videos/(\d+)',
            r'fb\.watch/(\w+)'
        ]
        return self._extract_with_patterns(url, patterns)

    def _extract_twitter_id(self, url: str) -> Optional[str]:
        patterns = [
            r'twitter\.com/.+?/status/(\d+)',
            r'x\.com/.+?/status/(\d+)'
        ]
        return self._extract_with_patterns(url, patterns)

    def _extract_vimeo_id(self, url: str) -> Optional[str]:
        patterns = [
            r'vimeo\.com/(\d+)',
            r'vimeo\.com/.+?/(\d+)'
        ]
        return self._extract_with_patterns(url, patterns)

    def _extract_generic_id(self, url: str) -> Optional[str]:
        try:
            parsed = urllib.parse.urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts:
                return path_parts[-1][:20]
            return None
        except:
            return None

    def _extract_with_patterns(self, url: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _get_ydlp_format(self, quality: str, format: str) -> str:
        """Get yt-dlp format string"""
        if quality == 'best':
            return 'best'
        elif quality == 'worst':
            return 'worst'
        else:
            return f'best[height<={quality}]/best'

    # === FILE CLEANUP ===
    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            deleted_count = 0
            current_time = datetime.now().timestamp()
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > older_than_hours * 3600:  # Convert hours to seconds
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.warning(f"Could not delete {file_path}: {e}")
            
            logger.info(f"🧹 Cleaned up {deleted_count} temporary files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Temp cleanup error: {e}")
            return 0

    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a specific file"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return {'success': True, 'message': f'Đã xóa {path.name}'}
            return {'success': False, 'error': 'File không tồn tại'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def close(self):
        """Cleanup resources"""
        try:
            if self.use_optimized_tool:
                await self.video_tool.close()
            # Cleanup temp files on close
            await self.cleanup_temp_files(1)  # Clean files older than 1 hour
        except Exception as e:
            logger.error(f"Error closing VideoService: {e}")

    async def download_video_with_progress(self, url: str, filename: Optional[str] = None,
                                        quality: str = 'best', format: str = 'mp4',
                                        progress_callback=None, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """Download video with progress tracking and optional move to target directory"""
        try:
            if not self._is_supported_url(url):
                return {'success': False, 'error': 'URL không được hỗ trợ'}

            # Optimize URL
            url = self._optimize_url(url)

            # Generate filename
            if not filename:
                platform = self._identify_platform(url)
                filename = self._generate_filename_from_url(url, platform, format)
            else:
                filename = self._ensure_extension(filename, format)

            # Use yt-dlp with progress hooks for real progress tracking
            if self.ydl:
                return await self._download_with_ytdlp_progress(url, filename, quality, format, progress_callback, target_dir)
            else:
                # Fallback to normal download
                result = await self.download_video(url, filename, quality, format)
                if result.get('success') and target_dir:
                    return await self._move_to_target_dir(result, target_dir)
                return result

        except Exception as e:
            logger.error(f"❌ Download with progress error: {e}")
            return {'success': False, 'error': str(e)}

    async def _download_with_ytdlp_progress(self, url: str, filename: str, 
                                        quality: str, format: str, 
                                        progress_callback=None, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """Download using yt-dlp with progress hooks and optional move"""
        output_path = self.temp_dir / filename
        try:
            def progress_hook(d):
                if progress_callback and d.get('status'):
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    progress_data = {
                        'status': d.get('status', 'downloading'),
                        'stage': 'Downloading video data' if d.get('status') == 'downloading' else d.get('status'),
                        'percent': 0,
                        'downloaded_bytes': downloaded,
                        'total_bytes': total,
                        'speed': d.get('speed', 0),
                        'eta': d.get('eta', 0)
                    }
                    
                    # Calculate percentage
                    if total > 0:
                        progress_data['percent'] = (downloaded / total) * 100
                    
                    progress_callback(progress_data)

            ydl_opts = {
                'outtmpl': str(output_path.with_suffix('')),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
            }

            def sync_download():
                with self.ydl.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        return {'success': True, 'info': info, 'file_path': str(output_path)}
                    except Exception as e:
                        return {'success': False, 'error': str(e)}

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_download)

            if result['success']:
                actual_path = await self._find_downloaded_file(output_path)
                if actual_path and actual_path.exists():
                    file_info = await self._get_file_info(actual_path)
                    info = result['info']
                    
                    download_result = {
                        'success': True,
                        'filename': actual_path.name,
                        'file_path': str(actual_path),
                        'size': file_info['size'],
                        'duration': info.get('duration', 0),
                        'quality': quality,
                        'format': format,
                        'title': info.get('title', 'Video')
                    }

                    # IF target_dir is provided, move the file
                    if target_dir:
                        if progress_callback:
                            progress_callback({'status': 'finalizing', 'stage': 'Moving to destination folder...', 'percent': 99})
                        return await self._move_to_target_dir(download_result, target_dir)
                    
                    return download_result
                else:
                    return {'success': False, 'error': 'Downloaded file not found'}
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            # Cleanup partial files if failed
            self._cleanup_partial_files(output_path)

    async def _move_to_target_dir(self, result: Dict[str, Any], target_dir: str) -> Dict[str, Any]:
        """Move downloaded file to target directory and cleanup temp"""
        try:
            src_path = Path(result['file_path'])
            dst_dir = Path(target_dir)
            
            if not dst_dir.exists():
                try:
                    dst_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Cannot create directory {target_dir}: {e}")
                    return {**result, 'warning': f'Không thể tạo thư mục lưu trữ. Lưu tại mặc định. Lỗi: {e}'}

            dst_path = dst_dir / src_path.name
            
            # Copy then remove to ensure clean move
            shutil.copy2(src_path, dst_path)
            src_path.unlink()
            
            logger.info(f"✅ File moved to: {dst_path}")
            return {
                **result,
                'file_path': str(dst_path),
                'saved_to_custom_dir': True,
                'target_dir': str(dst_dir)
            }
        except Exception as e:
            logger.error(f"❌ Move file error: {e}")
            return {**result, 'warning': f'Không thể chuyển file tới thư mục đích: {e}'}

    def _cleanup_partial_files(self, base_path: Path):
        """Clean up yt-dlp partial files (.part, .ytdl, etc)"""
        try:
            base_dir = base_path.parent
            base_name = base_path.name
            for file_path in base_dir.iterdir():
                if file_path.is_file() and (file_path.name.startswith(base_name) or base_name in file_path.name):
                    if file_path.suffix in ['.part', '.ytdl', '.temp']:
                        try:
                            file_path.unlink()
                            logger.info(f"🗑️ Deleted partial file: {file_path.name}")
                        except:
                            pass
        except:
            pass

    async def merge_videos(self, video_paths: List[str], output_filename: str, cleanup_sources: bool = True) -> Dict[str, Any]:
        """Merge multiple videos using ffmpeg with robust transcoding"""
        try:
            if not video_paths:
                return {'success': False, 'error': 'No videos to merge'}

            output_path = self.temp_dir / output_filename
            
            # Construct robust filter_complex for different resolutions/codecs
            # We normalize everything to 720p (1280x720) for consistency
            inputs = []
            filters = ""
            concat_parts = ""
            
            for i, path in enumerate(video_paths):
                inputs.extend(['-i', str(Path(path).absolute())])
                # Scale and pad to 1280x720 while preserving aspect ratio
                # setsar=1 to ensure square pixels
                filters += (
                    f"[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
                    f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];"
                    f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}];"
                )
                concat_parts += f"[v{i}][a{i}]"
            
            filters += f"{concat_parts}concat=n={len(video_paths)}:v=1:a=1[outv][outa]"
            
            cmd = [
                'ffmpeg', '-y'
            ] + inputs + [
                '-filter_complex', filters,
                '-map', '[outv]',
                '-map', '[outa]',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                str(output_path)
            ]
            
            logger.info(f"🎬 Running robust merge: {' '.join(cmd[:10])}...")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                file_info = await self._get_file_info(output_path)
                
                # Cleanup source files if requested
                if cleanup_sources:
                    for path in video_paths:
                        try:
                            p = Path(path)
                            if p.exists():
                                p.unlink()
                                logger.info(f"🗑️ Cleaned up source file: {p.name}")
                        except Exception as e:
                            logger.error(f"Error cleaning up {path}: {e}")

                return {
                    'success': True,
                    'filename': output_path.name,
                    'file_path': str(output_path),
                    'size': file_info['size']
                }
            else:
                error_msg = stderr.decode()
                logger.error(f"❌ FFmpeg merge error: {error_msg}")
                return {'success': False, 'error': f'FFmpeg error: {error_msg}'}

        except Exception as e:
            logger.error(f"❌ Merge videos robust error: {e}")
            return {'success': False, 'error': str(e)}


# Fallback processor for compatibility
class FallbackVideoProcessor:
    """Simple fallback processor"""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def download_video(self, url: str, filename: str, quality: str = 'best', format: str = 'mp4'):
        """Simple fallback download"""
        await asyncio.sleep(1)  # Simulate download
        file_path = self.temp_dir / filename
        file_path.touch()  # Create empty file
        
        return {
            'success': True,
            'filename': filename,
            'file_path': str(file_path),
            'size': 1024,  # Mock size
            'duration': 120.5,
            'quality': quality,
            'format': format
        }

    async def download_audio(self, url: str, filename: str, format: str = 'mp3', quality: str = '192'):
        """Simple fallback audio download"""
        await asyncio.sleep(1)
        file_path = self.temp_dir / filename
        file_path.touch()
        
        return {
            'success': True,
            'filename': filename,
            'file_path': str(file_path),
            'size': 512,  # Mock size
            'duration': 120.5,
            'format': format
        }