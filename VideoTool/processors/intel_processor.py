# video_tool/processors/intel_processor.py
import os
import asyncio
import subprocess
import tempfile
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
import logging
import shutil

logger = logging.getLogger(__name__)


class IntelOptimizedProcessor:
    """Processor tối ưu cho Intel CPUs với Quick Sync và OpenCL"""

    def __init__(self):
        self.supported_accelerations = self._detect_intel_features()
        self.vaapi_available = self._check_vaapi_support()
        self.opencl_available = self._check_opencl_support()
        self.temp_dir = Path(tempfile.gettempdir()) / "video_tool_intel"
        self.temp_dir.mkdir(exist_ok=True)

        logger.info(f"Intel Processor initialized: {self.supported_accelerations}")

    def _detect_intel_features(self) -> Dict[str, bool]:
        """Phát hiện tính năng Intel"""
        features = {
            'quick_sync': False,
            'opencl': False,
            'avx512': False,
            'media_sdk': False,
            'openvino': False
        }

        try:
            # Kiểm tra Intel Media SDK (VAAPI)
            result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=10)
            features['quick_sync'] = result.returncode == 0

            # Kiểm tra OpenCL
            try:
                import cv2
                features['opencl'] = cv2.ocl.haveOpenCL()
                if features['opencl']:
                    cv2.ocl.setUseOpenCL(True)
            except ImportError:
                features['opencl'] = False

            # Kiểm tra CPU features
            try:
                import cpuinfo
                info = cpuinfo.get_cpu_info()
                features['avx512'] = 'avx512' in info.get('flags', [])
            except (ImportError, AttributeError):
                features['avx512'] = False

            # Kiểm tra OpenVINO
            try:
                import openvino.runtime as ov
                features['openvino'] = True
            except ImportError:
                features['openvino'] = False

        except Exception as e:
            logger.warning(f"Intel feature detection failed: {e}")

        return features

    def _check_vaapi_support(self) -> bool:
        """Kiểm tra VAAPI support"""
        try:
            result = subprocess.run(['vainfo'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def _check_opencl_support(self) -> bool:
        """Kiểm tra OpenCL support"""
        try:
            import cv2
            return cv2.ocl.haveOpenCL()
        except (ImportError, AttributeError):
            return False

    def is_available(self) -> bool:
        """Kiểm tra processor có khả dụng không"""
        return any([
            self.vaapi_available,
            self.opencl_available,
            self.supported_accelerations['avx512']
        ])

    def get_acceleration_info(self) -> Dict[str, Any]:
        """Thông tin acceleration chi tiết"""
        return {
            **self.supported_accelerations,
            'vaapi_available': self.vaapi_available,
            'opencl_available': self.opencl_available,
            'recommended_method': 'vaapi' if self.vaapi_available else
            'opencl' if self.opencl_available else 'software'
        }

    async def process_video(self, input_file: str, output_file: str,
                            effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video với Intel optimization - Async version"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.process_video_sync, input_file, output_file, effects_config
            )
            return result
        except Exception as e:
            logger.error(f"Async video processing failed: {e}")
            return {'success': False, 'error': str(e)}

    def process_video_sync(self, input_file: str, output_file: str,
                           effects_config: Dict) -> Dict[str, Any]:
        """Xử lý video sync version cho thread pool"""
        try:
            logger.info(f"Intel processing: {Path(input_file).name} -> {Path(output_file).name}")

            if self.vaapi_available and self._should_use_vaapi(effects_config):
                return self._process_with_vaapi(input_file, output_file, effects_config)
            elif self.opencl_available:
                return self._process_with_opencl(input_file, output_file, effects_config)
            else:
                return self._process_with_software(input_file, output_file, effects_config)

        except Exception as e:
            logger.error(f"Intel processing failed: {e}")
            return {'success': False, 'error': str(e)}

    def _should_use_vaapi(self, effects_config: Dict) -> bool:
        """Xác định có nên dùng VAAPI không"""
        # VAAPI tốt cho các effect đơn giản, không tốt cho complex effects
        complex_effects = any([
            effects_config.get('rotation', 0) not in [0, 90, 180, 270],
            effects_config.get('border_width', 0) > 0,
            effects_config.get('logo_path') is not None,
            effects_config.get('blur_strength', 0) > 0,
            effects_config.get('watermark_text') is not None
        ])
        return not complex_effects

    def _process_with_vaapi(self, input_file: str, output_file: str,
                            effects_config: Dict) -> Dict[str, Any]:
        """Xử lý với VAAPI hardware acceleration"""
        try:
            import ffmpeg

            # Build filter chain
            filter_chain = []

            # Basic effects supported by VAAPI
            if effects_config.get('flip_horizontal'):
                filter_chain.append('hflip')
            if effects_config.get('flip_vertical'):
                filter_chain.append('vflip')

            # Color adjustments
            brightness = effects_config.get('brightness', 1.0)
            contrast = effects_config.get('contrast', 1.0)
            saturation = effects_config.get('saturation', 1.0)

            color_filters = []
            if brightness != 1.0:
                color_filters.append(f'brightness={brightness - 1:.2f}')
            if contrast != 1.0:
                color_filters.append(f'contrast={contrast:.2f}')
            if saturation != 1.0:
                color_filters.append(f'saturation={saturation:.2f}')

            if color_filters:
                filter_chain.append(f'eq={":".join(color_filters)}')

            # Build stream
            stream = ffmpeg.input(input_file)

            if filter_chain:
                stream = stream.filter(*filter_chain)

            # VAAPI encoding parameters
            encode_params = {
                'c:v': 'h264_vaapi',
                'vf': 'format=nv12|vaapi,hwupload',
                'quality': 23,
                'preset': 'fast',
                'c:a': 'aac',
                'b:a': '192k',
                'y': None  # Overwrite output
            }

            # Add resolution scaling if specified
            scale_width = effects_config.get('scale_width')
            scale_height = effects_config.get('scale_height')
            if scale_width and scale_height:
                encode_params['vf'] = f'scale={scale_width}:{scale_height},format=nv12|vaapi,hwupload'

            # Run conversion
            stream = ffmpeg.output(stream, output_file, **encode_params)
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

            logger.info("✅ VAAPI processing completed")
            return {'success': True, 'output': output_file, 'method': 'vaapi'}

        except ImportError:
            logger.warning("FFmpeg Python package not available, falling back to software")
            return self._process_with_software(input_file, output_file, effects_config)
        except Exception as e:
            logger.warning(f"VAAPI processing failed, falling back to software: {e}")
            return self._process_with_software(input_file, output_file, effects_config)

    def _process_with_opencl(self, input_file: str, output_file: str,
                             effects_config: Dict) -> Dict[str, Any]:
        """Xử lý với OpenCL acceleration"""
        try:
            import cv2

            # Use OpenCL if available
            cv2.ocl.setUseOpenCL(True)

            cap = cv2.VideoCapture(input_file)
            if not cap.isOpened():
                return {'success': False, 'error': 'Cannot open input video'}

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Setup writer with appropriate codec
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

            if not out.isOpened():
                cap.release()
                return {'success': False, 'error': 'Cannot create output video writer'}

            # Process frames with OpenCL
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Upload to GPU (UMat) and apply effects
                umat = cv2.UMat(frame)
                processed_umat = self._apply_effects_gpu(umat, effects_config)

                # Download back to CPU for writing
                processed_frame = processed_umat.get()
                out.write(processed_frame)

                frame_count += 1
                if frame_count % 30 == 0:
                    logger.debug(f"OpenCL processed {frame_count}/{total_frames} frames")

            cap.release()
            out.release()

            logger.info("✅ OpenCL processing completed")
            return {'success': True, 'output': output_file, 'method': 'opencl'}

        except Exception as e:
            logger.warning(f"OpenCL processing failed, falling back to software: {e}")
            return self._process_with_software(input_file, output_file, effects_config)

    def _apply_effects_gpu(self, umat: 'cv2.UMat', effects_config: Dict) -> 'cv2.UMat':
        """Áp dụng hiệu ứng trên GPU với OpenCL"""
        processed = umat

        # Flip operations on GPU
        if effects_config.get('flip_horizontal'):
            processed = cv2.flip(processed, 1)
        if effects_config.get('flip_vertical'):
            processed = cv2.flip(processed, 0)

        # Color adjustments on GPU
        brightness = effects_config.get('brightness', 1.0)
        contrast = effects_config.get('contrast', 1.0)

        if brightness != 1.0 or contrast != 1.0:
            processed = cv2.convertScaleAbs(processed, alpha=contrast, beta=(brightness - 1) * 128)

        # Rotation on GPU
        rotate_angle = effects_config.get('rotate', 0)
        if rotate_angle != 0:
            center = (processed.cols() // 2, processed.rows() // 2)
            matrix = cv2.getRotationMatrix2D(center, rotate_angle, 1.0)
            processed = cv2.warpAffine(processed, matrix, (processed.cols(), processed.rows()))

        return processed

    def _process_with_software(self, input_file: str, output_file: str,
                               effects_config: Dict) -> Dict[str, Any]:
        """Xử lý với software optimization và AVX instructions"""
        try:
            import cv2

            cap = cv2.VideoCapture(input_file)
            if not cap.isOpened():
                return {'success': False, 'error': 'Cannot open input video'}

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Setup writer
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

            if not out.isOpened():
                cap.release()
                return {'success': False, 'error': 'Cannot create output video writer'}

            # Process frames with optimized NumPy operations
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Apply effects with optimized operations
                processed_frame = self._apply_effects_optimized(frame, effects_config)
                out.write(processed_frame)

                frame_count += 1
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.debug(f"Software processed {frame_count}/{total_frames} frames ({progress:.1f}%)")

            cap.release()
            out.release()

            logger.info("✅ Software processing completed")
            return {'success': True, 'output': output_file, 'method': 'software'}

        except Exception as e:
            logger.error(f"Software processing failed: {e}")
            return {'success': False, 'error': str(e)}

    def _apply_effects_optimized(self, frame: np.ndarray, effects_config: Dict) -> np.ndarray:
        """Áp dụng hiệu ứng với optimized NumPy operations"""
        processed = frame.copy()

        # Flip operations
        if effects_config.get('flip_horizontal'):
            processed = np.fliplr(processed)
        if effects_config.get('flip_vertical'):
            processed = np.flipud(processed)

        # Color adjustments with vectorized operations
        brightness = effects_config.get('brightness', 1.0)
        contrast = effects_config.get('contrast', 1.0)
        saturation = effects_config.get('saturation', 1.0)

        if brightness != 1.0 or contrast != 1.0:
            # Vectorized brightness/contrast adjustment
            processed = np.clip(contrast * (processed * brightness), 0, 255).astype(np.uint8)

        # Saturation adjustment
        if saturation != 1.0:
            # Convert to HSV for saturation adjustment
            hsv = cv2.cvtColor(processed, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
            processed = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Rotation
        rotate_angle = effects_config.get('rotate', 0)
        if rotate_angle != 0:
            center = (processed.shape[1] // 2, processed.shape[0] // 2)
            matrix = cv2.getRotationMatrix2D(center, rotate_angle, 1.0)
            processed = cv2.warpAffine(processed, matrix, (processed.shape[1], processed.shape[0]))

        # Add logo if specified
        logo_path = effects_config.get('logo_path')
        if logo_path and os.path.exists(logo_path):
            processed = self._add_logo_optimized(processed, logo_path, effects_config)

        # Add watermark text if specified
        watermark_text = effects_config.get('watermark_text')
        if watermark_text:
            processed = self._add_watermark_text(processed, watermark_text, effects_config)

        return processed

    def _add_logo_optimized(self, frame: np.ndarray, logo_path: str,
                            effects_config: Dict) -> np.ndarray:
        """Thêm logo với optimized operations"""
        try:
            logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
            if logo is None:
                return frame

            # Resize logo
            logo_size = effects_config.get('logo_size', 80)
            logo_opacity = effects_config.get('logo_opacity', 0.8)

            # Calculate aspect ratio
            h, w = logo.shape[:2]
            aspect_ratio = w / h
            new_height = logo_size
            new_width = int(new_height * aspect_ratio)

            logo_resized = cv2.resize(logo, (new_width, new_height))

            # Position logo
            position = effects_config.get('logo_position', 'top-left')
            margin = 10

            if position == 'top-right':
                x = frame.shape[1] - new_width - margin
                y = margin
            elif position == 'bottom-left':
                x = margin
                y = frame.shape[0] - new_height - margin
            elif position == 'bottom-right':
                x = frame.shape[1] - new_width - margin
                y = frame.shape[0] - new_height - margin
            else:  # top-left
                x = margin
                y = margin

            # Blend logo with frame
            if logo_resized.shape[2] == 4:  # PNG with alpha channel
                # Extract alpha channel
                logo_rgb = logo_resized[:, :, :3]
                alpha = logo_resized[:, :, 3] / 255.0 * logo_opacity

                # Get region of interest
                roi = frame[y:y + new_height, x:x + new_width]

                # Blend using alpha
                for c in range(3):
                    roi[:, :, c] = roi[:, :, c] * (1 - alpha) + logo_rgb[:, :, c] * alpha

                frame[y:y + new_height, x:x + new_width] = roi
            else:
                # Simple overlay for non-transparent images
                roi = frame[y:y + new_height, x:x + new_width]
                cv2.addWeighted(logo_resized, logo_opacity, roi, 1 - logo_opacity, 0, roi)

            return frame

        except Exception as e:
            logger.warning(f"Logo addition failed: {e}")
            return frame

    def _add_watermark_text(self, frame: np.ndarray, text: str,
                            effects_config: Dict) -> np.ndarray:
        """Thêm watermark text"""
        try:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = effects_config.get('watermark_font_scale', 1.0)
            font_color = effects_config.get('watermark_color', (255, 255, 255))
            thickness = effects_config.get('watermark_thickness', 2)
            opacity = effects_config.get('watermark_opacity', 0.7)

            # Get text size
            (text_width, text_height), baseline = cv2.getTextSize(
                text, font, font_scale, thickness
            )

            # Position (default bottom-right)
            position = effects_config.get('watermark_position', 'bottom-right')
            margin = 10

            if position == 'top-left':
                x = margin
                y = text_height + margin
            elif position == 'top-right':
                x = frame.shape[1] - text_width - margin
                y = text_height + margin
            elif position == 'bottom-left':
                x = margin
                y = frame.shape[0] - margin
            else:  # bottom-right
                x = frame.shape[1] - text_width - margin
                y = frame.shape[0] - margin

            # Create overlay with text
            overlay = frame.copy()
            cv2.putText(overlay, text, (x, y), font, font_scale, font_color, thickness)

            # Blend with original frame
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

            return frame
        except Exception as e:
            logger.warning(f"Watermark text addition failed: {e}")
            return frame

    async def download_video(self, url: str, filename: Optional[str] = None,
                             quality: str = 'best') -> Dict[str, Any]:
        """Tải video với yt-dlp và optimization"""
        try:
            import yt_dlp

            ydl_opts = {
                'outtmpl': filename or '%(title)s.%(ext)s',
                'format': self._get_best_format(quality),
                'quiet': False,
                'no_warnings': False,
                'extractaudio': False,
                'format_sort': ['res:1080', 'ext:mp4:m4a'],
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                actual_filename = ydl.prepare_filename(info)

                # Get video duration and resolution
                duration = info.get('duration', 0)
                width = info.get('width', 0)
                height = info.get('height', 0)

                return {
                    'success': True,
                    'filename': actual_filename,
                    'title': info.get('title', ''),
                    'duration': duration,
                    'width': width,
                    'height': height,
                    'filesize': os.path.getsize(actual_filename) if os.path.exists(actual_filename) else 0
                }

        except ImportError:
            error_msg = "yt-dlp package not available for video download"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Video download failed: {e}")
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
                'quiet': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                original_filename = ydl.prepare_filename(info)
                actual_filename = Path(original_filename).with_suffix(f'.{format}')

                return {
                    'success': True,
                    'filename': str(actual_filename),
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'filesize': actual_filename.stat().st_size if actual_filename.exists() else 0
                }

        except ImportError:
            error_msg = "yt-dlp package not available for audio download"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Audio download failed: {e}")
            return {'success': False, 'error': str(e)}

    async def extract_audio(self, video_file: str, output_file: str) -> Dict[str, Any]:
        """Trích xuất audio từ video với FFmpeg optimization"""
        try:
            import ffmpeg

            # Use hardware acceleration if available
            if self.vaapi_available:
                # Decode with VAAPI for faster processing
                stream = ffmpeg.input(video_file)
                stream = ffmpeg.output(
                    stream,
                    output_file,
                    **{
                        'c:a': 'aac',
                        'b:a': '192k',
                        'vn': None,  # No video
                        'y': None
                    }
                )
            else:
                # Standard software extraction
                stream = ffmpeg.input(video_file)
                stream = ffmpeg.output(stream, output_file, **{'q:a': 0, 'map': 'a', 'y': None})

            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

            if os.path.exists(output_file):
                return {
                    'success': True,
                    'output': output_file,
                    'filesize': os.path.getsize(output_file)
                }
            else:
                return {'success': False, 'error': 'Output file not created'}

        except ImportError:
            error_msg = "FFmpeg Python package not available for audio extraction"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return {'success': False, 'error': str(e)}

    def _get_best_format(self, quality: str) -> str:
        """Chọn format tối ưu dựa trên chất lượng"""
        format_map = {
            'best': 'best[height<=1080]',
            '1080': 'best[height<=1080]',
            '720': 'best[height<=720]',
            '480': 'best[height<=480]',
            '360': 'best[height<=360]'
        }
        return format_map.get(quality, 'best[height<=1080]')

    def export_timeline_sync(self, timeline_data: Dict, output_path: str,
                             config: Optional[Dict] = None) -> Dict[str, Any]:
        """Export timeline với hardware acceleration"""
        try:
            if not timeline_data.get('clips'):
                return {'success': False, 'error': 'No clips in timeline'}

            # Use FFmpeg concat với hardware acceleration
            return self._export_with_ffmpeg_concat(timeline_data, output_path, config)

        except Exception as e:
            logger.error(f"Timeline export failed: {e}")
            return {'success': False, 'error': str(e)}

    async def export_timeline(self, timeline_data: Dict, output_path: str,
                              config: Optional[Dict] = None) -> Dict[str, Any]:
        """Export timeline async version"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.export_timeline_sync, timeline_data, output_path, config
            )
            return result
        except Exception as e:
            logger.error(f"Async timeline export failed: {e}")
            return {'success': False, 'error': str(e)}

    def _export_with_ffmpeg_concat(self, timeline_data: Dict, output_path: str,
                                   config: Optional[Dict]) -> Dict[str, Any]:
        """Export timeline sử dụng FFmpeg concat"""
        try:
            import ffmpeg

            # Tạo file list cho concat
            concat_file = self.temp_dir / "concat_list.txt"
            with open(concat_file, 'w', encoding='utf-8') as f:
                for clip in timeline_data['clips']:
                    file_path = clip.get('file_path', '')
                    if os.path.exists(file_path):
                        f.write(f"file '{file_path}'\n")

            if self.vaapi_available:
                # Hardware accelerated concat
                stream = ffmpeg.input(str(concat_file), format='concat', safe=0)
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    **{
                        'c:v': 'h264_vaapi',
                        'vf': 'format=nv12|vaapi,hwupload',
                        'c:a': 'aac',
                        'b:a': '192k',
                        'y': None
                    }
                )
            else:
                # Software concat
                stream = ffmpeg.input(str(concat_file), format='concat', safe=0)
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    **{
                        'c:v': 'libx264',
                        'preset': 'fast',
                        'c:a': 'aac',
                        'b:a': '192k',
                        'y': None
                    }
                )

            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

            # Cleanup
            concat_file.unlink(missing_ok=True)

            if os.path.exists(output_path):
                return {
                    'success': True,
                    'output': output_path,
                    'filesize': os.path.getsize(output_path)
                }
            else:
                return {'success': False, 'error': 'Export failed - output file not created'}

        except ImportError:
            error_msg = "FFmpeg Python package not available for timeline export"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            logger.error(f"FFmpeg concat export failed: {e}")
            # Cleanup on error
            concat_file = self.temp_dir / "concat_list.txt"
            concat_file.unlink(missing_ok=True)
            return {'success': False, 'error': str(e)}

    def cleanup(self):
        """Dọn dẹp temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("Intel processor temp files cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def __del__(self):
        """Cleanup temp files khi object bị destroy"""
        self.cleanup()


# Factory function để tạo processor
def create_intel_processor() -> Optional[IntelOptimizedProcessor]:
    """Tạo Intel optimized processor nếu available"""
    try:
        processor = IntelOptimizedProcessor()
        if processor.is_available():
            logger.info("Intel optimized processor created successfully")
            return processor
        else:
            logger.warning("Intel optimized processor not available on this system")
            return None
    except Exception as e:
        logger.error(f"Failed to create Intel processor: {e}")
        return None