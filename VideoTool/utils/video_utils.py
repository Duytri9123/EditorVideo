# video_tool/utils/video_utils.py
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class VideoUtils:
    """Video utilities với hardware acceleration"""

    def __init__(self):
        self.opencl_available = self._check_opencl_support()
        self.cuda_available = self._check_cuda_support()

        if self.opencl_available:
            cv2.ocl.setUseOpenCL(True)
            logger.info("OpenCL acceleration enabled")

        logger.info("Video Utils initialized")

    def _check_opencl_support(self) -> bool:
        """Kiểm tra OpenCL support"""
        try:
            return cv2.ocl.haveOpenCL()
        except:
            return False

    def _check_cuda_support(self) -> bool:
        """Kiểm tra CUDA support"""
        try:
            return cv2.cuda.getCudaEnabledDeviceCount() > 0
        except:
            return False

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Lấy thông tin video chi tiết"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'error': 'Cannot open video file'}

            # Basic properties
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

            # Get bitrate estimation
            file_size = os.path.getsize(video_path)
            bitrate = self._calculate_bitrate(file_size, duration)

            # Get first frame for additional info
            ret, first_frame = cap.read()
            color_info = {}
            if ret:
                color_info = self._analyze_frame_color(first_frame)

            cap.release()

            return {
                'success': True,
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'duration_formatted': self._format_duration(duration),
                'codec': codec_str,
                'bitrate': bitrate,
                'bitrate_formatted': self._format_bitrate(bitrate),
                'resolution': f"{width}x{height}",
                'aspect_ratio': self._calculate_aspect_ratio(width, height),
                'file_size': file_size,
                'file_size_formatted': self._format_file_size(file_size),
                'color_info': color_info,
                'has_audio': self._has_audio(video_path)
            }

        except Exception as e:
            logger.error(f"Video info extraction failed: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_bitrate(self, file_size: int, duration: float) -> int:
        """Tính bitrate"""
        if duration > 0:
            return int((file_size * 8) / duration)
        return 0

    def _analyze_frame_color(self, frame: np.ndarray) -> Dict[str, Any]:
        """Phân tích màu sắc của frame"""
        try:
            # Convert to different color spaces
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

            # Calculate statistics
            brightness = np.mean(frame) / 255.0
            saturation = np.mean(hsv[:, :, 1]) / 255.0
            contrast = np.std(frame) / 255.0

            # Dominant colors (simplified)
            pixels = frame.reshape(-1, 3)
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            dominant_color = unique_colors[np.argmax(counts)]

            return {
                'brightness': brightness,
                'saturation': saturation,
                'contrast': contrast,
                'dominant_color_bgr': dominant_color.tolist(),
                'color_variance': float(np.var(pixels))
            }
        except Exception as e:
            logger.debug(f"Color analysis failed: {e}")
            return {}

    def _has_audio(self, video_path: str) -> bool:
        """Kiểm tra video có audio không"""
        try:
            cap = cv2.VideoCapture(video_path)
            # Try to get audio stream info (simplified check)
            has_audio = cap.get(cv2.CAP_PROP_AUDIO_TOTAL_STREAMS) > 0
            cap.release()
            return has_audio
        except:
            return False

    def extract_frame(self, video_path: str, time_seconds: float,
                      quality: int = 95) -> Optional[np.ndarray]:
        """Trích xuất frame tại thời điểm cụ thể"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None

            # Calculate frame number
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(time_seconds * fps)

            # Set position
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            # Read frame
            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                # Adjust quality if needed
                if quality != 100:
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                    _, buffer = cv2.imencode('.jpg', frame, encode_param)
                    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

                return frame

            return None

        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            return None

    def extract_frames(self, video_path: str, interval: float = 1.0,
                       max_frames: int = 100) -> Dict[str, Any]:
        """Trích xuất nhiều frames với khoảng thời gian"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'success': False, 'error': 'Cannot open video'}

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_interval = int(fps * interval)

            frames = []
            frame_numbers = []
            timestamps = []

            for i in range(0, frame_count, frame_interval):
                if len(frames) >= max_frames:
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret and frame is not None:
                    frames.append(frame)
                    frame_numbers.append(i)
                    timestamps.append(i / fps)

            cap.release()

            return {
                'success': True,
                'frames': frames,
                'frame_numbers': frame_numbers,
                'timestamps': timestamps,
                'count': len(frames),
                'interval': interval
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_thumbnail(self, video_path: str, output_path: str,
                         time_seconds: float = 0, width: int = 320) -> Dict[str, Any]:
        """Tạo thumbnail từ video"""
        try:
            frame = self.extract_frame(video_path, time_seconds)
            if frame is None:
                return {'success': False, 'error': 'Could not extract frame'}

            # Resize maintaining aspect ratio
            height = int(width * frame.shape[0] / frame.shape[1])
            resized_frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

            # Save thumbnail
            success = cv2.imwrite(output_path, resized_frame)

            if success:
                return {
                    'success': True,
                    'output_path': output_path,
                    'width': width,
                    'height': height,
                    'file_size': os.path.getsize(output_path)
                }
            else:
                return {'success': False, 'error': 'Could not save thumbnail'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def compare_videos(self, video1_path: str, video2_path: str,
                       method: str = 'ssim') -> Dict[str, Any]:
        """So sánh hai videos"""
        try:
            # Get basic info
            info1 = self.get_video_info(video1_path)
            info2 = self.get_video_info(video2_path)

            if not info1.get('success') or not info2.get('success'):
                return {'success': False, 'error': 'Could not get video info'}

            # Compare properties
            resolution_match = info1['resolution'] == info2['resolution']
            duration_diff = abs(info1['duration'] - info2['duration'])
            fps_diff = abs(info1['fps'] - info2['fps'])

            # Extract sample frames for visual comparison
            sample_frames1 = self.extract_frames(video1_path, interval=2.0, max_frames=5)
            sample_frames2 = self.extract_frames(video2_path, interval=2.0, max_frames=5)

            similarity_scores = []
            if (sample_frames1['success'] and sample_frames2['success'] and
                    len(sample_frames1['frames']) == len(sample_frames2['frames'])):

                for frame1, frame2 in zip(sample_frames1['frames'], sample_frames2['frames']):
                    if frame1.shape == frame2.shape:
                        if method == 'ssim':
                            score = self._calculate_ssim(frame1, frame2)
                        else:  # mse
                            score = self._calculate_mse(frame1, frame2)
                        similarity_scores.append(score)

            avg_similarity = np.mean(similarity_scores) if similarity_scores else 0

            return {
                'success': True,
                'resolution_match': resolution_match,
                'duration_difference': duration_diff,
                'fps_difference': fps_diff,
                'similarity_scores': similarity_scores,
                'average_similarity': avg_similarity,
                'similarity_method': method,
                'video1_info': info1,
                'video2_info': info2
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Tính Structural Similarity Index"""
        try:
            from skimage.metrics import structural_similarity as ssim

            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Calculate SSIM
            score = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
            return float(score)
        except:
            return 0.0

    def _calculate_mse(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Tính Mean Squared Error"""
        try:
            err = np.sum((img1.astype("float") - img2.astype("float")) ** 2)
            err /= float(img1.shape[0] * img1.shape[1])
            return float(err)
        except:
            return float('inf')

    def detect_scene_changes(self, video_path: str, threshold: float = 0.3) -> Dict[str, Any]:
        """Phát hiện scene changes"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'success': False, 'error': 'Cannot open video'}

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            scene_changes = []
            prev_frame = None

            for i in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break

                if prev_frame is not None:
                    # Convert to grayscale
                    gray_current = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

                    # Calculate difference
                    diff = cv2.absdiff(gray_current, gray_prev)
                    mean_diff = np.mean(diff) / 255.0

                    if mean_diff > threshold:
                        scene_changes.append({
                            'frame_number': i,
                            'timestamp': i / fps,
                            'difference': mean_diff
                        })

                prev_frame = frame.copy()

            cap.release()

            return {
                'success': True,
                'scene_changes': scene_changes,
                'count': len(scene_changes),
                'threshold': threshold,
                'fps': fps
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

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

    def _format_bitrate(self, bitrate: int) -> str:
        """Định dạng bitrate"""
        if bitrate < 1000:
            return f"{bitrate} bps"
        elif bitrate < 1000000:
            return f"{bitrate / 1000:.1f} kbps"
        else:
            return f"{bitrate / 1000000:.1f} Mbps"

    def _format_file_size(self, size_bytes: int) -> str:
        """Định dạng kích thước file"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

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