# video_tool/utils/audio_utils.py
import os
import numpy as np
from typing import Dict, Optional, Any, List
import logging

logger = logging.getLogger(__name__)


class AudioUtils:
    """Audio utilities cho xử lý âm thanh"""

    def __init__(self):
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
        logger.info("Audio Utils initialized")

    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """Lấy thông tin audio file"""
        try:
            # Try using pydub if available
            try:
                from pydub import AudioSegment
                return self._get_audio_info_pydub(audio_path)
            except ImportError:
                pass

            # Fallback to basic file info
            return self._get_audio_info_basic(audio_path)

        except Exception as e:
            logger.error(f"Audio info extraction failed: {e}")
            return {'success': False, 'error': str(e)}

    def _get_audio_info_pydub(self, audio_path: str) -> Dict[str, Any]:
        """Lấy thông tin audio với pydub"""
        from pydub import AudioSegment

        audio = AudioSegment.from_file(audio_path)
        file_size = os.path.getsize(audio_path)

        return {
            'success': True,
            'duration': len(audio) / 1000.0,  # Convert to seconds
            'channels': audio.channels,
            'sample_width': audio.sample_width,
            'frame_rate': audio.frame_rate,
            'frame_count': audio.frame_count(),
            'file_size': file_size,
            'file_size_formatted': self._format_file_size(file_size),
            'bitrate': self._calculate_bitrate(file_size, len(audio) / 1000.0),
            'format': audio_path.split('.')[-1].upper()
        }

    def _get_audio_info_basic(self, audio_path: str) -> Dict[str, Any]:
        """Lấy thông tin audio cơ bản"""
        file_size = os.path.getsize(audio_path)
        file_ext = os.path.splitext(audio_path)[1].lower()

        # Estimate duration based on file size and format
        duration = self._estimate_duration(file_size, file_ext)

        return {
            'success': True,
            'duration': duration,
            'duration_formatted': self._format_duration(duration),
            'file_size': file_size,
            'file_size_formatted': self._format_file_size(file_size),
            'bitrate': self._calculate_bitrate(file_size, duration),
            'format': file_ext[1:].upper() if file_ext else 'UNKNOWN',
            'channels': 2,  # Default assumption
            'sample_rate': 44100  # Default assumption
        }

    def _estimate_duration(self, file_size: int, file_ext: str) -> float:
        """Ước tính duration dựa trên file size và format"""
        # Average bitrates for common formats
        bitrate_estimates = {
            '.mp3': 128000,  # 128 kbps
            '.wav': 1411000,  # 1411 kbps (CD quality)
            '.m4a': 256000,  # 256 kbps
            '.aac': 192000,  # 192 kbps
            '.ogg': 160000,  # 160 kbps
            '.flac': 1000000,  # 1000 kbps
        }

        bitrate = bitrate_estimates.get(file_ext, 128000)
        duration = (file_size * 8) / bitrate  # Convert bytes to bits

        return max(0, duration)

    def _calculate_bitrate(self, file_size: int, duration: float) -> int:
        """Tính bitrate"""
        if duration > 0:
            return int((file_size * 8) / duration)
        return 0

    def extract_audio_segment(self, audio_path: str, start_time: float,
                              end_time: float, output_path: str) -> Dict[str, Any]:
        """Trích xuất segment audio"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)
            segment = audio[start_time * 1000:end_time * 1000]  # pydub uses milliseconds

            # Export segment
            format = output_path.split('.')[-1]
            segment.export(output_path, format=format)

            return {
                'success': True,
                'output_path': output_path,
                'duration': len(segment) / 1000.0,
                'file_size': os.path.getsize(output_path)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def merge_audio_files(self, audio_files: List[str], output_path: str) -> Dict[str, Any]:
        """Merge nhiều audio files"""
        try:
            from pydub import AudioSegment

            if not audio_files:
                return {'success': False, 'error': 'No audio files provided'}

            merged = None

            for audio_file in audio_files:
                if not os.path.exists(audio_file):
                    return {'success': False, 'error': f'Audio file not found: {audio_file}'}

                audio = AudioSegment.from_file(audio_file)

                if merged is None:
                    merged = audio
                else:
                    merged = merged.append(audio, crossfade=0)

            if merged is not None:
                format = output_path.split('.')[-1]
                merged.export(output_path, format=format)

                return {
                    'success': True,
                    'output_path': output_path,
                    'duration': len(merged) / 1000.0,
                    'file_size': os.path.getsize(output_path),
                    'merged_files': len(audio_files)
                }
            else:
                return {'success': False, 'error': 'No audio to merge'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def adjust_volume(self, audio_path: str, volume_change: float,
                      output_path: str) -> Dict[str, Any]:
        """Điều chỉnh volume"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)

            # volume_change in dB: positive for louder, negative for quieter
            adjusted = audio + volume_change

            format = output_path.split('.')[-1]
            adjusted.export(output_path, format=format)

            return {
                'success': True,
                'output_path': output_path,
                'volume_change': volume_change,
                'file_size': os.path.getsize(output_path)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_fade(self, audio_path: str, fade_in: float = 0, fade_out: float = 0,
                 output_path: str = None) -> Dict[str, Any]:
        """Thêm fade in/out"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)

            # Apply fades (duration in seconds)
            if fade_in > 0:
                audio = audio.fade_in(int(fade_in * 1000))  # Convert to milliseconds

            if fade_out > 0:
                audio = audio.fade_out(int(fade_out * 1000))

            if output_path is None:
                output_path = audio_path

            format = output_path.split('.')[-1]
            audio.export(output_path, format=format)

            return {
                'success': True,
                'output_path': output_path,
                'fade_in': fade_in,
                'fade_out': fade_out,
                'file_size': os.path.getsize(output_path)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def convert_format(self, audio_path: str, output_path: str,
                       quality: str = '192k') -> Dict[str, Any]:
        """Chuyển đổi định dạng audio"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)
            output_format = output_path.split('.')[-1]

            # Set parameters based on quality
            parameters = {}
            if output_format == 'mp3':
                parameters['bitrate'] = quality

            audio.export(output_path, format=output_format, **parameters)

            return {
                'success': True,
                'output_path': output_path,
                'original_format': audio_path.split('.')[-1],
                'target_format': output_format,
                'quality': quality,
                'file_size': os.path.getsize(output_path)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def analyze_audio_levels(self, audio_path: str) -> Dict[str, Any]:
        """Phân tích audio levels"""
        try:
            from pydub import AudioSegment
            import numpy as np

            audio = AudioSegment.from_file(audio_path)
            samples = np.array(audio.get_array_of_samples())

            if audio.channels == 2:
                # Stereo - separate channels
                left_channel = samples[0::2]
                right_channel = samples[1::2]

                left_rms = np.sqrt(np.mean(left_channel ** 2))
                right_rms = np.sqrt(np.mean(right_channel ** 2))
                overall_rms = np.sqrt(np.mean(samples ** 2))
            else:
                # Mono
                overall_rms = np.sqrt(np.mean(samples ** 2))
                left_rms = overall_rms
                right_rms = overall_rms

            # Convert to dB
            max_possible = 2 ** (audio.sample_width * 8 - 1)
            left_db = 20 * np.log10(left_rms / max_possible) if left_rms > 0 else -float('inf')
            right_db = 20 * np.log10(right_rms / max_possible) if right_rms > 0 else -float('inf')
            overall_db = 20 * np.log10(overall_rms / max_possible) if overall_rms > 0 else -float('inf')

            # Peak detection
            peak_left = np.max(np.abs(left_channel)) if audio.channels == 2 else np.max(np.abs(samples))
            peak_right = np.max(np.abs(right_channel)) if audio.channels == 2 else peak_left
            peak_overall = np.max(np.abs(samples))

            peak_db_left = 20 * np.log10(peak_left / max_possible) if peak_left > 0 else -float('inf')
            peak_db_right = 20 * np.log10(peak_right / max_possible) if peak_right > 0 else -float('inf')
            peak_db_overall = 20 * np.log10(peak_overall / max_possible) if peak_overall > 0 else -float('inf')

            return {
                'success': True,
                'rms_levels': {
                    'left': float(left_db),
                    'right': float(right_db),
                    'overall': float(overall_db)
                },
                'peak_levels': {
                    'left': float(peak_db_left),
                    'right': float(peak_db_right),
                    'overall': float(peak_db_overall)
                },
                'dynamic_range': {
                    'left': float(peak_db_left - left_db),
                    'right': float(peak_db_right - right_db),
                    'overall': float(peak_db_overall - overall_db)
                },
                'loudness': self._calculate_loudness(samples, audio.sample_width)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _calculate_loudness(self, samples: np.ndarray, sample_width: int) -> float:
        """Tính loudness (simplified LUFS)"""
        try:
            # Simple loudness calculation (not true LUFS)
            max_possible = 2 ** (sample_width * 8 - 1)
            normalized = samples.astype(np.float64) / max_possible
            rms = np.sqrt(np.mean(normalized ** 2))
            loudness = 20 * np.log10(rms) if rms > 0 else -float('inf')
            return float(loudness)
        except:
            return 0.0

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