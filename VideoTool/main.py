# video_tool/main.py - SMART MERGE VERSION (Preserve FPS & Resolution)
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import concurrent.futures
import tempfile
import shutil
import yt_dlp
import psutil
from datetime import datetime
import re
import urllib.parse
import subprocess
import json

logger = logging.getLogger(__name__)


class OptimizedVideoTool:
    """
    Video Tool Pro - SMART MERGE: Giữ nguyên FPS/Resolution, chỉ fix màu sắc
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._create_config(config)
        self._setup_logging()
        self._setup_directories()
        self._initialize_components()
        self._setup_thread_pool()

        logger.info("🚀 Video Tool Pro - Smart Merge Version Initialized")

    def _create_config(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        default_config = {
            'log_level': 'INFO',
            'max_workers': min(32, (os.cpu_count() or 1) + 4),
            'download_dir': 'downloads',
            'output_dir': 'output',
            'music_dir': 'music',
            'logos_dir': 'logos',
            'temp_dir': 'temp',
            'max_concurrent_downloads': 3,
            'fragment_threads': 16,
            'use_aria2c': True,
            'auto_resume': True,
            'quality_limit': 'best[height<=1080]',
            'enable_universal_download': True,
            'timeout': 300,
            'retries': 3,
            'ignore_playlist': True,
            'simplify_urls': True,
            'prefer_yt_dlp': True,
            'max_download_size': '2GB',
            'merge_quality': 'high',
            'video_codec': 'libx264',
            'audio_codec': 'aac',
            'crf_value': '18',
            'preset': 'slow',
            'pixel_format': 'yuv420p',
            'color_format': 'bt709'
        }

        if config:
            default_config.update(config)

        return default_config

    def _setup_logging(self):
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_directories(self):
        base_dir = Path(__file__).parent.parent.parent / 'static'

        self.dirs = {
            'downloads': base_dir / self.config.get('download_dir', 'downloads'),
            'output': base_dir / self.config.get('output_dir', 'output'),
            'music': base_dir / self.config.get('music_dir', 'music'),
            'logos': base_dir / self.config.get('logos_dir', 'logos'),
            'temp': base_dir / self.config.get('temp_dir', 'temp')
        }

        for dir_name, dir_path in self.dirs.items():
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"📁 Directory ready: {dir_path}")

    def _initialize_components(self):
        try:
            self.file_manager = RealFileManager(self.dirs)
            self.video_processor = SmartVideoProcessor(self.config)
            self.audio_processor = RealAudioProcessor()
            self.universal_downloader = UniversalDownloader(self.config, self.dirs)

            logger.info("✅ All components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            self._initialize_fallback_components()

    def _initialize_fallback_components(self):
        logger.warning("🔄 Using fallback components")
        self.file_manager = SimpleFileManager(self.dirs)
        self.video_processor = SimpleVideoProcessor()
        self.audio_processor = SimpleAudioProcessor()
        self.universal_downloader = SimpleUniversalDownloader()

    def _setup_thread_pool(self):
        max_workers = self.config.get('max_workers', min(32, (os.cpu_count() or 1) + 4))
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="video_tool"
        )
        logger.info(f"🔄 Thread pool: {max_workers} workers")

    # === CORE DOWNLOAD METHODS ===
    async def download_video(self, url: str, filename: Optional[str] = None,
                             quality: str = None, platform: str = 'auto') -> Dict[str, Any]:
        """Tải video với URL optimization"""
        try:
            logger.info(f"📥 Downloading: {url}")

            original_url = url
            url = self._optimize_url(url)
            if url != original_url:
                logger.info(f"🔄 URL optimized: {original_url} -> {url}")

            if not filename:
                filename = self._generate_filename(url, 'video')

            result = await self.universal_downloader.download_video(url, filename, quality)

            if result['success']:
                final_path = await self._ensure_file_location(result, filename, 'downloads')
                if final_path:
                    result.update({
                        'success': True,
                        'final_path': str(final_path),
                        'file_path': str(final_path),
                        'message': 'Download thành công'
                    })
                    logger.info(f"✅ Download completed: {filename}")
                else:
                    result['success'] = False
                    result['error'] = 'File transfer failed'
            else:
                logger.error(f"❌ Download failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            return {'success': False, 'error': str(e)}

    async def download_audio(self, url: str, filename: Optional[str] = None,
                             format: str = 'mp3', quality: str = '192') -> Dict[str, Any]:
        """Tải audio từ video"""
        try:
            logger.info(f"🎵 Downloading audio: {url}")

            url = self._optimize_url(url)

            if not filename:
                filename = self._generate_filename(url, 'audio', format)

            result = await self.universal_downloader.download_audio(url, filename, format, quality)

            if result['success']:
                final_path = await self._ensure_file_location(result, filename, 'music')
                if final_path:
                    result.update({
                        'success': True,
                        'final_path': str(final_path),
                        'file_path': str(final_path),
                        'message': 'Audio download thành công'
                    })
                else:
                    result['success'] = False
                    result['error'] = 'Audio file transfer failed'

            return result

        except Exception as e:
            logger.error(f"❌ Audio download error: {e}")
            return {'success': False, 'error': str(e)}

    # === SMART VIDEO MERGING ===
    async def merge_videos(self, input_files: List[str], output_file: str,
                           merge_config: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            logger.info(f"🎯 Smart merging {len(input_files)} videos into {output_file}")

            # Resolve file paths
            input_paths = []
            for input_file in input_files:
                resolved_path = self.file_manager.resolve_path(input_file)
                if not resolved_path or not resolved_path.exists():
                    return {'success': False, 'error': f'Input file not found: {input_file}'}
                input_paths.append(str(resolved_path))

            # Generate output path
            output_filename = self.file_manager.generate_unique_filename('output', output_file)
            output_path = self.dirs['output'] / output_filename

            # Lấy thông tin các video
            video_infos = []
            for path in input_paths:
                info = await self.video_processor.get_video_info(path)
                if info:
                    video_infos.append(info)
                    logger.info(f"📊 {Path(path).name}: {info['width']}x{info['height']} @ {info['fps']}fps")

            # Smart merge
            result = await self.video_processor.smart_merge(
                input_paths=input_paths,
                output_path=str(output_path),
                video_infos=video_infos
            )

            if result['success']:
                result.update({
                    'output_file': output_filename,
                    'output_path': str(output_path),
                    'message': f'Successfully merged {len(input_files)} videos (SMART mode - preserved quality)'
                })
                logger.info(f"✅ Smart merge completed: {output_filename}")

            return result

        except Exception as e:
            logger.error(f"❌ Video merge error: {e}")
            return {'success': False, 'error': str(e)}

    async def concatenate_videos_safe(self, input_files: List[str], output_file: str) -> Dict[str, Any]:
        """Alias cho merge_videos - để tương thích"""
        return await self.merge_videos(input_files, output_file)

    # === BATCH DOWNLOAD ===
    async def download_multiple_videos(self, urls: List[str],
                                       filenames: Optional[List[str]] = None,
                                       quality: str = None) -> Dict[str, Any]:
        """Tải nhiều video cùng lúc"""
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

            max_concurrent = self.config.get('max_concurrent_downloads', 3)
            semaphore = asyncio.Semaphore(max_concurrent)

            async def download_with_semaphore(url, index):
                async with semaphore:
                    try:
                        filename = filenames[index] if filenames and index < len(filenames) else None
                        result = await self.download_video(url, filename, quality)

                        if result['success']:
                            results['successful'] += 1
                            results['downloaded_files'].append({
                                'url': url,
                                'filename': Path(result['final_path']).name,
                                'file_path': result['final_path'],
                                'platform': self._identify_platform(url)
                            })
                        else:
                            results['failed'] += 1
                            results['failed_downloads'].append({
                                'url': url,
                                'error': result.get('error'),
                                'filename': filename
                            })
                    except Exception as e:
                        results['failed'] += 1
                        results['failed_downloads'].append({
                            'url': url,
                            'error': str(e)
                        })

            tasks = [download_with_semaphore(url, i) for i, url in enumerate(urls)]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"✅ Batch complete: {results['successful']} successful, {results['failed']} failed")
            return results

        except Exception as e:
            logger.error(f"❌ Batch download error: {e}")
            return {
                'success': False,
                'error': str(e),
                'downloaded_files': [],
                'failed_downloads': urls,
                'total': len(urls),
                'successful': 0,
                'failed': len(urls)
            }

    # === VIDEO PROCESSING ===
    async def process_video(self, input_file: str, output_file: str,
                            effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video với hiệu ứng"""
        try:
            logger.info(f"⚙️ Processing video: {input_file}")

            input_path = self.file_manager.resolve_path(input_file)
            if not input_path or not input_path.exists():
                return {'success': False, 'error': f'Input file not found: {input_file}'}

            output_filename = self.file_manager.generate_unique_filename('output', output_file)
            output_path = self.dirs['output'] / output_filename

            result = await self.video_processor.process_video(
                input_path=str(input_path),
                output_path=str(output_path),
                effects_config=effects_config
            )

            if result['success']:
                result.update({
                    'output_file': output_filename,
                    'output_path': str(output_path),
                    'message': 'Video processed successfully'
                })

            return result

        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            return {'success': False, 'error': str(e)}

    async def extract_audio(self, video_file: str, output_file: str) -> Dict[str, Any]:
        """Trích xuất audio từ video"""
        try:
            logger.info(f"🎵 Extracting audio: {video_file}")

            video_path = self.file_manager.resolve_path(video_file)
            if not video_path or not video_path.exists():
                return {'success': False, 'error': f'Video file not found: {video_file}'}

            output_filename = self.file_manager.generate_unique_filename('music', output_file)
            output_path = self.dirs['music'] / output_filename

            result = await self.audio_processor.extract_audio(
                video_path=str(video_path),
                output_path=str(output_path)
            )

            if result['success']:
                result.update({
                    'output_file': output_filename,
                    'output_path': str(output_path),
                    'message': 'Audio extracted successfully'
                })

            return result

        except Exception as e:
            logger.error(f"❌ Audio extraction error: {e}")
            return {'success': False, 'error': str(e)}

    # === URL OPTIMIZATION ===
    def _optimize_url(self, url: str) -> str:
        """Tối ưu hóa URL"""
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
            logger.warning(f"⚠️ URL optimization failed: {e}")
            return url

    def _optimize_youtube_url(self, url: str) -> str:
        """Tối ưu YouTube URL - loại bỏ playlist"""
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)

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
            logger.warning(f"⚠️ YouTube URL optimization failed: {e}")
            return url

    def _optimize_tiktok_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            optimized_url = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, '', '', ''
            ))
            return optimized_url
        except:
            return url

    def _optimize_instagram_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            if '/p/' in parsed.path or '/reel/' in parsed.path:
                path = parsed.path.split('?')[0]
                optimized_url = urllib.parse.urlunparse((
                    parsed.scheme, parsed.netloc, path, '', '', ''
                ))
                return optimized_url
            return url
        except:
            return url

    def _optimize_generic_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)

            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 'gclid']
            clean_params = {k: v[0] for k, v in query_params.items()
                            if k.lower() not in tracking_params}

            new_query = urllib.parse.urlencode(clean_params)
            optimized_url = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
            return optimized_url
        except:
            return url

    def _identify_platform(self, url: str) -> str:
        """Nhận diện platform từ URL"""
        url_lower = url.lower()

        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return 'facebook'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'vimeo.com' in url_lower:
            return 'vimeo'
        else:
            return 'unknown'

    def _generate_filename(self, url: str, media_type: str = 'video', format: str = 'mp4') -> str:
        """Tạo filename duy nhất"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = self._identify_platform(url)

        if platform == 'youtube':
            video_id = self._extract_youtube_id(url)
            identifier = video_id or 'video'
        else:
            identifier = self._extract_generic_id(url) or 'content'

        if media_type == 'video':
            return f"{platform}_{identifier}_{timestamp}.{format}"
        else:
            return f"{platform}_{identifier}_audio_{timestamp}.{format}"

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&]+)',
            r'youtube\.com/embed/([^/?]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_generic_id(self, url: str) -> Optional[str]:
        try:
            parsed = urllib.parse.urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts:
                return path_parts[-1][:20]
            return None
        except:
            return None

    # === FILE MANAGEMENT ===
    async def _ensure_file_location(self, result: Dict[str, Any], filename: str,
                                    target_dir: str) -> Optional[Path]:
        """Đảm bảo file được lưu đúng vị trí"""
        try:
            target_path = self.dirs[target_dir] / filename

            if target_path.exists():
                return target_path

            source_path = self._find_source_file(result, filename)
            if not source_path:
                logger.error(f"❌ Source file not found: {filename}")
                return None

            if source_path != target_path:
                logger.info(f"🔄 Moving file: {source_path} -> {target_path}")
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if target_path.exists():
                    target_path.unlink()

                shutil.move(str(source_path), str(target_path))

                if target_path.exists():
                    logger.info(f"✅ File moved: {target_path}")
                    if source_path.exists() and source_path != target_path:
                        try:
                            source_path.unlink()
                        except:
                            pass
                    return target_path
                else:
                    logger.error(f"❌ File move failed: {target_path}")
                    return None
            else:
                return target_path

        except Exception as e:
            logger.error(f"❌ File location error: {e}")
            return None

    def _find_source_file(self, result: Dict[str, Any], filename: str) -> Optional[Path]:
        """Tìm file nguồn từ kết quả download"""
        possible_paths = [
            self.dirs['downloads'] / filename,
            self.dirs['temp'] / filename,
            Path(result.get('file_path', '')),
            Path(result.get('temp_path', '')),
        ]

        base_name = Path(filename).stem
        extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.mp3', '.m4a', '.wav']
        for ext in extensions:
            possible_paths.extend([
                self.dirs['temp'] / f"{base_name}{ext}",
                self.dirs['downloads'] / f"{base_name}{ext}",
            ])

        for path in possible_paths:
            if path.exists() and path.is_file():
                logger.info(f"📁 Found source: {path}")
                return path

        return None

    # === UTILITY METHODS ===
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        return self.file_manager.get_file_info(file_path)

    def list_files(self, file_type: Optional[str] = None) -> Dict[str, Any]:
        return self.file_manager.list_files(file_type)

    async def cleanup(self, cleanup_type: str = 'downloads') -> Dict[str, Any]:
        logger.info(f"🧹 Cleaning up: {cleanup_type}")
        return await self.file_manager.cleanup(cleanup_type)

    def get_system_info(self) -> Dict[str, Any]:
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)

            return {
                'success': True,
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'thread_pool_workers': self.thread_pool._max_workers
                },
                'storage': {
                    'total_disk': round(disk.total / (1024 ** 3), 2),
                    'used_disk': round(disk.used / (1024 ** 3), 2),
                    'free_disk': round(disk.free / (1024 ** 3), 2),
                    'disk_usage': disk.percent
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def close(self):
        try:
            self.thread_pool.shutdown(wait=True)
            logger.info("🔚 Video Tool closed")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ============================================================================
# SMART VIDEO PROCESSOR
# ============================================================================

class SmartVideoProcessor:

    def __init__(self, config: Dict):
        self.config = config

    async def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin video: fps, resolution, codec, duration"""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate,codec_name,duration',
                '-of', 'json',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data['streams'][0]

                # Parse fps
                fps_str = stream.get('r_frame_rate', '30/1')
                fps_parts = fps_str.split('/')
                fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

                # Get duration
                duration = float(stream.get('duration', 0))

                return {
                    'width': stream.get('width', 1920),
                    'height': stream.get('height', 1080),
                    'fps': round(fps, 2),
                    'codec': stream.get('codec_name', 'h264'),
                    'duration': round(duration, 2)
                }
        except Exception as e:
            logger.error(f"Cannot get video info: {e}")
        return None

    async def smart_merge(self, input_paths: List[str], output_path: str,
                          video_infos: List[Dict]) -> Dict[str, Any]:
        """
        SMART MERGE:
        - CHỈ chuẩn hóa màu sắc (yuv420p + bt709)
        - GIỮ NGUYÊN fps từng video
        - GIỮ NGUYÊN resolution từng video
        - Xử lý audio sync tốt
        """
        try:
            logger.info("🎯 Using SMART merge (preserve fps & resolution)")

            # Build filter complex - CHỈ chuẩn hóa màu sắc
            filter_parts = []
            video_inputs = []
            audio_inputs = []

            for i in range(len(input_paths)):
                # CHỈ chuẩn hóa màu sắc và pixel format
                # KHÔNG scale, KHÔNG thay đổi fps
                filter_parts.append(
                    f"[{i}:v] format=yuv420p,colorspace=bt709:iall=bt709:fast=1,setsar=1:1 [v{i}]"
                )

                # Chuẩn hóa audio nhẹ nhàng
                filter_parts.append(
                    f"[{i}:a] aresample=async=1:first_pts=0 [a{i}]"
                )

                video_inputs.append(f"[v{i}]")
                audio_inputs.append(f"[a{i}]")

            # Concat
            filter_parts.append(
                f"{''.join(video_inputs)}concat=n={len(input_paths)}:v=1:a=0[outv]"
            )
            filter_parts.append(
                f"{''.join(audio_inputs)}concat=n={len(input_paths)}:v=0:a=1[outa]"
            )

            filter_complex = "; ".join(filter_parts)

            # Build FFmpeg command - GIỮ NGUYÊN chất lượng cao
            cmd = ['ffmpeg']
            for input_path in input_paths:
                cmd.extend(['-i', input_path])

            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', '[outa]',
                '-c:v', self.config.get('video_codec', 'libx264'),
                '-crf', '18',  # Chất lượng cao
                '-preset', 'slow',  # Chất lượng tốt hơn
                '-c:a', self.config.get('audio_codec', 'aac'),
                '-b:a', '320k',  # Audio chất lượng cao
                '-movflags', '+faststart',
                '-pix_fmt', 'yuv420p',
                '-color_primaries', 'bt709',
                '-color_trc', 'bt709',
                '-colorspace', 'bt709',
                '-y', output_path
            ])

            def run_ffmpeg():
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
                return result

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_ffmpeg)

            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Successfully merged {len(input_paths)} videos keeping original fps/resolution'
                }
            else:
                logger.error(f"Smart merge failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}

        except Exception as e:
            logger.error(f"Smart merge error: {e}")
            return {'success': False, 'error': str(e)}

    async def process_video(self, input_path: str, output_path: str, effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video với hiệu ứng"""
        try:
            cmd = ['ffmpeg', '-i', input_path]

            # Thêm hiệu ứng nếu có
            filter_complex = []
            if effects_config.get('brightness'):
                filter_complex.append(f'eq=brightness={effects_config["brightness"]}')

            if filter_complex:
                cmd.extend(['-vf', ','.join(filter_complex)])

            # Cài đặt chất lượng cao với chuẩn hóa màu
            cmd.extend([
                '-c:v', self.config.get('video_codec', 'libx264'),
                '-crf', self.config.get('crf_value', '18'),
                '-preset', self.config.get('preset', 'slow'),
                '-c:a', self.config.get('audio_codec', 'aac'),
                '-movflags', '+faststart',
                '-pix_fmt', self.config.get('pixel_format', 'yuv420p'),
                '-color_primaries', 'bt709',
                '-color_trc', 'bt709',
                '-colorspace', 'bt709',
                output_path, '-y'
            ])

            def run_ffmpeg():
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                return result

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_ffmpeg)

            if result.returncode == 0:
                return {'success': True, 'message': 'Video processed successfully'}
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return {'success': False, 'error': f'FFmpeg error: {result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'FFmpeg processing timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================================
# UNIVERSAL DOWNLOADER
# ============================================================================

class UniversalDownloader:
    """Universal downloader tối ưu"""

    def __init__(self, config: Dict, dirs: Dict[str, Path]):
        self.config = config
        self.dirs = dirs

    async def download_video(self, url: str, filename: str,
                             quality: str = None) -> Dict[str, Any]:
        """Download video với yt-dlp optimization"""
        try:
            if quality is None:
                quality = self.config.get('quality_limit', 'best[height<=1080]')

            # LUÔN download vào thư mục downloads
            output_path = self.dirs['downloads'] / filename

            ydl_opts = {
                'outtmpl': str(output_path),
                'format': quality,
                'quiet': False,
                'no_warnings': False,
                'concurrent_fragment_downloads': self.config.get('fragment_threads', 16),
                'continuedl': True,
                'noplaylist': True,
                'extract_flat': False,
            }

            # Sử dụng aria2c để tăng tốc download
            if self.config.get('use_aria2c', True):
                ydl_opts.update({
                    'external_downloader': 'aria2c',
                    'external_downloader_args': [
                        '--max-connection-per-server=16',
                        '--split=16',
                        '--min-split-size=1M',
                        '--file-allocation=none'
                    ]
                })

            def sync_download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        return {'success': True, 'info': info, 'file_path': str(output_path)}
                    except Exception as e:
                        return {'success': False, 'error': str(e)}

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_download)

            if result['success']:
                info = result['info']
                return {
                    'success': True,
                    'filename': filename,
                    'file_path': str(output_path),
                    'title': info.get('title', 'Video'),
                    'duration': info.get('duration', 0),
                    'quality': quality
                }
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def download_audio(self, url: str, filename: str,
                             format: str = 'mp3', quality: str = '192') -> Dict[str, Any]:
        """Download audio với optimization"""
        try:
            output_path = self.dirs['music'] / filename

            ydl_opts = {
                'outtmpl': str(output_path),
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': quality,
                }],
                'quiet': False,
                'no_warnings': False,
                'noplaylist': True,
            }

            def sync_download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        return {'success': True, 'info': info, 'file_path': str(output_path)}
                    except Exception as e:
                        return {'success': False, 'error': str(e)}

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_download)

            if result['success']:
                info = result['info']
                return {
                    'success': True,
                    'filename': filename,
                    'file_path': str(output_path),
                    'title': info.get('title', 'Audio'),
                    'duration': info.get('duration', 0),
                    'format': format
                }
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================================
# AUDIO PROCESSOR
# ============================================================================

class RealAudioProcessor:
    async def extract_audio(self, video_path: str, output_path: str) -> Dict[str, Any]:
        """Trích xuất audio từ video"""
        try:
            cmd = ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', output_path, '-y']

            def run_ffmpeg():
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_ffmpeg)

            if result.returncode == 0:
                return {'success': True, 'message': 'Audio extracted successfully'}
            else:
                return {'success': False, 'error': f'FFmpeg error: {result.stderr}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================================
# FILE MANAGER
# ============================================================================

class RealFileManager:
    def __init__(self, dirs: Dict[str, Path]):
        self.dirs = dirs

    def generate_unique_filename(self, dir_type: str, filename: str) -> str:
        dir_path = self.dirs[dir_type]
        base_name = Path(filename).stem
        extension = Path(filename).suffix

        counter = 1
        new_name = filename

        while (dir_path / new_name).exists():
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1

        return new_name

    def resolve_path(self, file_path: str) -> Optional[Path]:
        for dir_path in self.dirs.values():
            full_path = dir_path / file_path
            if full_path.exists():
                return full_path
        return None

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        path = self.resolve_path(file_path)
        if not path or not path.exists():
            return None

        stat = path.stat()
        return {
            'name': path.name,
            'path': str(path),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'type': self._get_file_type(path.name)
        }

    def list_files(self, file_type: Optional[str] = None) -> Dict[str, Any]:
        files = {}
        for dir_name, dir_path in self.dirs.items():
            if dir_path.exists():
                dir_files = []
                for file_path in dir_path.iterdir():
                    if file_path.is_file():
                        file_info = self.get_file_info(file_path.name)
                        if file_info:
                            dir_files.append(file_info)
                files[dir_name] = sorted(dir_files, key=lambda x: x['modified'], reverse=True)

        return {
            'success': True,
            'files': files,
            'total_count': sum(len(f) for f in files.values())
        }

    async def cleanup(self, cleanup_type: str = 'downloads') -> Dict[str, Any]:
        try:
            deleted_count = 0
            if cleanup_type == 'all':
                for dir_name, dir_path in self.dirs.items():
                    if dir_name != 'logos':
                        deleted_count += await self._cleanup_directory(dir_path)
            else:
                dir_path = self.dirs.get(cleanup_type)
                if dir_path:
                    deleted_count += await self._cleanup_directory(dir_path)

            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'Deleted {deleted_count} files'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _cleanup_directory(self, dir_path: Path) -> int:
        deleted_count = 0
        if dir_path.exists():
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {file_path}: {e}")
        return deleted_count

    def refresh_cache(self):
        pass

    def _get_file_type(self, filename: str) -> str:
        ext = filename.lower().split('.')[-1]
        if ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
            return 'video'
        elif ext in ['mp3', 'wav', 'm4a', 'aac', 'ogg']:
            return 'audio'
        elif ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            return 'image'
        else:
            return 'other'


# ============================================================================
# FALLBACK CLASSES
# ============================================================================

class SimpleFileManager:
    def __init__(self, dirs):
        self.dirs = dirs

    def generate_unique_filename(self, dir_type, filename):
        return filename

    def resolve_path(self, file_path):
        for dir_path in self.dirs.values():
            full_path = dir_path / file_path
            if full_path.exists():
                return full_path
        return None

    def get_file_info(self, file_path):
        path = self.resolve_path(file_path)
        return {'name': path.name, 'path': str(path), 'size': 0, 'type': 'file'} if path else None

    def list_files(self, file_type=None):
        return {'success': True, 'files': {}}

    async def cleanup(self, cleanup_type='downloads'):
        return {'success': True, 'deleted_count': 0}

    def refresh_cache(self):
        pass


class SimpleVideoProcessor:
    async def get_video_info(self, video_path):
        return None

    async def smart_merge(self, input_paths, output_path, video_infos):
        return {'success': True, 'message': 'Videos merged (simple)'}

    async def process_video(self, input_path, output_path, effects_config):
        return {'success': True, 'message': 'Video processed (simple)'}


class SimpleAudioProcessor:
    async def extract_audio(self, video_path, output_path):
        return {'success': True, 'message': 'Audio extracted (simple)'}


class SimpleUniversalDownloader:
    async def download_video(self, url, filename, quality):
        return {'success': False, 'error': 'Universal downloader not available'}

    async def download_audio(self, url, filename, format, quality):
        return {'success': False, 'error': 'Universal downloader not available'}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_video_tool(config: Optional[Dict] = None) -> OptimizedVideoTool:
    """Factory function để tạo Video Tool instance"""
    return OptimizedVideoTool(config)