# video_tool/processors/ffmpeg_processor.py
import os
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FFmpegProcessor:
    """FFmpeg-based processor với software optimization"""

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.temp_dir = Path(tempfile.gettempdir()) / "video_tool_ffmpeg"
        self.temp_dir.mkdir(exist_ok=True)

        logger.info("FFmpeg Processor initialized")

    def _find_ffmpeg(self) -> str:
        """Tìm FFmpeg executable"""
        # Check common paths
        possible_paths = [
            'ffmpeg',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            'C:\\ffmpeg\\bin\\ffmpeg.exe'
        ]

        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Found FFmpeg at: {path}")
                    return path
            except:
                continue

        # Fallback to ffmpeg in PATH
        return 'ffmpeg'

    def is_available(self) -> bool:
        """Kiểm tra FFmpeg có khả dụng không"""
        try:
            result = subprocess.run([self.ffmpeg_path, '-version'],
                                    capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    async def process_video(self, input_file: str, output_file: str,
                            effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video với FFmpeg - Async version"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.process_video_sync, input_file, output_file, effects_config
            )
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def process_video_sync(self, input_file: str, output_file: str,
                           effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video sync version"""
        try:
            logger.info(f"FFmpeg processing: {Path(input_file).name} -> {Path(output_file).name}")

            # Build FFmpeg command
            cmd = [self.ffmpeg_path, '-i', input_file, '-y']  # -y to overwrite

            # Add effects filters
            filter_parts = []

            # Flip effects
            if effects_config.get('flip_horizontal'):
                filter_parts.append('hflip')
            if effects_config.get('flip_vertical'):
                filter_parts.append('vflip')

            # Color adjustments
            brightness = effects_config.get('brightness', 1.0)
            contrast = effects_config.get('contrast', 1.0)
            saturation = effects_config.get('saturation', 1.0)

            if brightness != 1.0 or contrast != 1.0 or saturation != 1.0:
                eq_filter = f'eq=brightness={brightness - 1:.2f}:contrast={contrast:.2f}:saturation={saturation:.2f}'
                filter_parts.append(eq_filter)

            # Rotation
            rotate_angle = effects_config.get('rotate', 0)
            if rotate_angle != 0:
                filter_parts.append(f'rotate={rotate_angle}*PI/180')

            # Add filter complex if we have filters
            if filter_parts:
                cmd.extend(['-vf', ','.join(filter_parts)])

            # Add logo if specified
            logo_path = effects_config.get('logo_path')
            if logo_path and os.path.exists(logo_path):
                cmd = self._add_logo_to_command(cmd, logo_path, effects_config)

            # Output settings
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                output_file
            ])

            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info("✅ FFmpeg processing completed")
                return {'success': True, 'output': output_file, 'method': 'ffmpeg'}
            else:
                error_msg = result.stderr.split('\n')[-2] if result.stderr else 'Unknown error'
                return {'success': False, 'error': f'FFmpeg failed: {error_msg}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'FFmpeg processing timeout'}
        except Exception as e:
            logger.error(f"FFmpeg processing failed: {e}")
            return {'success': False, 'error': str(e)}

    def _add_logo_to_command(self, cmd: list, logo_path: str,
                             effects_config: Dict) -> list:
        """Thêm logo vào FFmpeg command"""
        try:
            logo_position = effects_config.get('logo_position', 'top-left')
            logo_size = effects_config.get('logo_size', 80)
            logo_opacity = effects_config.get('logo_opacity', 0.8)

            # Map position to FFmpeg coordinates
            position_map = {
                'top-left': f'10:10',
                'top-right': f'main_w-overlay_w-10:10',
                'bottom-left': f'10:main_h-overlay_h-10',
                'bottom-right': f'main_w-overlay_w-10:main_h-overlay_h-10',
                'center': f'(main_w-overlay_w)/2:(main_h-overlay_h)/2'
            }

            position = position_map.get(logo_position, '10:10')

            # Create complex filter for overlay
            current_filters = []
            if '-vf' in cmd:
                vf_index = cmd.index('-vf') + 1
                current_filters = cmd[vf_index].split(',')
                cmd.pop(vf_index)
                cmd.pop(cmd.index('-vf'))

            # Add logo overlay filter
            overlay_filter = (
                f"[1]scale={logo_size}:-1[logo];"
                f"[0][logo]overlay={position}:enable='between(t,0,1e6)':format=auto"
            )

            if current_filters:
                # Combine with existing filters
                combined_filter = f"{','.join(current_filters)},{overlay_filter}"
            else:
                combined_filter = overlay_filter

            # Insert logo input and filter
            cmd.insert(1, '-i')
            cmd.insert(2, logo_path)
            cmd.insert(3, '-filter_complex')
            cmd.insert(4, combined_filter)
            cmd.insert(5, '-map')
            cmd.insert(6, '[v]')
            cmd.insert(7, '-map')
            cmd.insert(8, '0:a?')  # Map audio if exists

            return cmd

        except Exception as e:
            logger.warning(f"Logo addition to command failed: {e}")
            return cmd

    async def download_video(self, url: str, filename: Optional[str] = None,
                             quality: str = 'best') -> Dict[str, Any]:
        """Tải video - FFmpeg processor sử dụng yt-dlp"""
        try:
            import yt_dlp

            ydl_opts = {
                'outtmpl': filename or '%(title)s.%(ext)s',
                'format': self._get_best_format(quality),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                actual_filename = ydl.prepare_filename(info)

                return {
                    'success': True,
                    'filename': actual_filename,
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0)
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def download_audio(self, url: str, filename: Optional[str] = None,
                             format: str = 'mp3', quality: str = '192') -> Dict[str, Any]:
        """Tải audio từ video"""
        try:
            import yt_dlp

            ydl_opts = {
                'outtmpl': filename or '%(title)s',
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': quality,
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                original_filename = ydl.prepare_filename(info)
                actual_filename = Path(original_filename).with_suffix(f'.{format}')

                return {
                    'success': True,
                    'filename': str(actual_filename),
                    'title': info.get('title', '')
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def extract_audio(self, video_file: str, output_file: str) -> Dict[str, Any]:
        """Trích xuất audio từ video với FFmpeg"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_file,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',  # Overwrite
                output_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0 and os.path.exists(output_file):
                return {
                    'success': True,
                    'output': output_file,
                    'filesize': os.path.getsize(output_file)
                }
            else:
                error_msg = result.stderr.split('\n')[-2] if result.stderr else 'Unknown error'
                return {'success': False, 'error': f'FFmpeg failed: {error_msg}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_best_format(self, quality: str) -> str:
        """Chọn format tối ưu"""
        format_map = {
            'best': 'best[height<=1080]',
            '1080': 'best[height<=1080]',
            '720': 'best[height<=720]',
            '480': 'best[height<=480]',
        }
        return format_map.get(quality, 'best[height<=1080]')

    def export_timeline_sync(self, timeline_data: Dict, output_path: str,
                             config: Optional[Dict] = None) -> Dict[str, Any]:
        """Export timeline với FFmpeg concat"""
        try:
            if not timeline_data.get('clips'):
                return {'success': False, 'error': 'No clips in timeline'}

            # Create concat file
            concat_file = self.temp_dir / "ffmpeg_concat.txt"
            with open(concat_file, 'w') as f:
                for clip in timeline_data['clips']:
                    file_path = clip['file_path']
                    if os.path.exists(file_path):
                        f.write(f"file '{file_path}'\n")

            # FFmpeg concat command
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',  # Stream copy for fastest processing
                '-y',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Cleanup
            concat_file.unlink(missing_ok=True)

            if result.returncode == 0 and os.path.exists(output_path):
                return {
                    'success': True,
                    'output': output_path,
                    'filesize': os.path.getsize(output_path)
                }
            else:
                error_msg = result.stderr.split('\n')[-2] if result.stderr else 'Unknown error'
                return {'success': False, 'error': f'Concat failed: {error_msg}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def __del__(self):
        """Cleanup"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except:
            pass