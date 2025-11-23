# video_tool/uploaders/social_uploader.py
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class SocialUploader:
    """Social media uploader cho multiple platforms"""

    def __init__(self):
        self.supported_platforms = {
            'tiktok': {
                'name': 'TikTok',
                'max_duration': 180,  # 3 minutes
                'max_file_size': 500 * 1024 * 1024,  # 500MB
                'supported_formats': ['.mp4', '.mov'],
                'max_resolution': '1080x1920'  # Vertical
            },
            'instagram': {
                'name': 'Instagram',
                'max_duration': 60,  # 1 minute for feed
                'max_file_size': 100 * 1024 * 1024,  # 100MB
                'supported_formats': ['.mp4'],
                'max_resolution': '1080x1350'  # Square-ish
            },
            'facebook': {
                'name': 'Facebook',
                'max_duration': 240,  # 4 minutes
                'max_file_size': 1 * 1024 * 1024 * 1024,  # 1GB
                'supported_formats': ['.mp4', '.mov', '.avi'],
                'max_resolution': '1080x1080'
            },
            'twitter': {
                'name': 'Twitter',
                'max_duration': 140,  # 2 minutes 20 seconds
                'max_file_size': 512 * 1024 * 1024,  # 512MB
                'supported_formats': ['.mp4', '.mov'],
                'max_resolution': '1280x720'
            },
            'linkedin': {
                'name': 'LinkedIn',
                'max_duration': 600,  # 10 minutes
                'max_file_size': 5 * 1024 * 1024 * 1024,  # 5GB
                'supported_formats': ['.mp4', '.mov'],
                'max_resolution': '1920x1080'
            }
        }

        self.upload_progress_callbacks = {}

        logger.info("Social Uploader initialized")

    async def upload_to_platform(self, video_path: str, platform: str,
                                 title: str, description: str = "",
                                 tags: List[str] = None,
                                 config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload video lên social platform"""
        try:
            if platform not in self.supported_platforms:
                return {
                    'success': False,
                    'error': f'Platform not supported: {platform}'
                }

            # Validate video file
            validation_result = self._validate_video_for_platform(video_path, platform)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f'Video validation failed: {validation_result["error"]}'
                }

            logger.info(f"Uploading to {platform}: {Path(video_path).name}")

            # Platform-specific upload logic
            if platform == 'tiktok':
                return await self._upload_to_tiktok(video_path, title, description, tags, config)
            elif platform == 'instagram':
                return await self._upload_to_instagram(video_path, title, description, tags, config)
            elif platform == 'facebook':
                return await self._upload_to_facebook(video_path, title, description, tags, config)
            elif platform == 'twitter':
                return await self._upload_to_twitter(video_path, title, description, tags, config)
            elif platform == 'linkedin':
                return await self._upload_to_linkedin(video_path, title, description, tags, config)
            else:
                return {'success': False, 'error': 'Platform upload not implemented'}

        except Exception as e:
            logger.error(f"Upload to {platform} failed: {e}")
            return {'success': False, 'error': str(e)}

    async def upload_to_multiple_platforms(self, video_path: str,
                                           platforms: List[str],
                                           title: str, description: str = "",
                                           tags: List[str] = None,
                                           platform_configs: Dict[str, Dict] = None) -> Dict[str, Any]:
        """Upload video lên nhiều platforms cùng lúc"""
        try:
            if not platforms:
                return {'success': False, 'error': 'No platforms specified'}

            results = {}
            tasks = []

            for platform in platforms:
                platform_config = platform_configs.get(platform, {}) if platform_configs else {}
                task = self.upload_to_platform(
                    video_path, platform, title, description, tags, platform_config
                )
                tasks.append(task)

            # Execute all uploads concurrently
            upload_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, platform in enumerate(platforms):
                result = upload_results[i]
                if isinstance(result, Exception):
                    results[platform] = {
                        'success': False,
                        'error': str(result)
                    }
                else:
                    results[platform] = result

            # Calculate summary
            success_count = sum(1 for r in results.values() if r.get('success', False))

            return {
                'success': success_count > 0,
                'results': results,
                'summary': {
                    'total_platforms': len(platforms),
                    'successful_uploads': success_count,
                    'failed_uploads': len(platforms) - success_count
                }
            }

        except Exception as e:
            logger.error(f"Multi-platform upload failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _upload_to_tiktok(self, video_path: str, title: str, description: str,
                                tags: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Upload lên TikTok (demo implementation)"""
        try:
            # TikTok API integration would go here
            # This is a demo implementation

            platform_info = self.supported_platforms['tiktok']
            file_size = os.path.getsize(video_path)

            # Simulate upload process
            upload_time = max(3, min(30, file_size / (5 * 1024 * 1024)))  # Simulate based on file size

            logger.info(f"TikTok upload simulation: {title} ({file_size / 1024 / 1024:.1f} MB)")

            # Simulate progress
            for progress in [0, 25, 50, 75, 100]:
                await asyncio.sleep(upload_time / 4)
                self._report_progress('tiktok', progress)
                logger.debug(f"TikTok upload progress: {progress}%")

            # Generate demo post ID
            post_id = f"tiktok_{int(time.time())}"
            post_url = f"https://tiktok.com/@{config.get('username', 'user')}/video/{post_id}"

            return {
                'success': True,
                'platform': 'tiktok',
                'post_id': post_id,
                'post_url': post_url,
                'title': title,
                'description': description,
                'tags': tags or [],
                'file_size': file_size,
                'upload_time': upload_time,
                'demo_mode': True,
                'message': f'Video uploaded to TikTok: {title}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_instagram(self, video_path: str, title: str, description: str,
                                   tags: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Upload lên Instagram (demo implementation)"""
        try:
            platform_info = self.supported_platforms['instagram']
            file_size = os.path.getsize(video_path)

            # Simulate upload process
            upload_time = max(2, min(20, file_size / (3 * 1024 * 1024)))

            logger.info(f"Instagram upload simulation: {title}")

            for progress in [0, 20, 40, 60, 80, 100]:
                await asyncio.sleep(upload_time / 5)
                self._report_progress('instagram', progress)
                logger.debug(f"Instagram upload progress: {progress}%")

            post_id = f"instagram_{int(time.time())}"
            post_url = f"https://instagram.com/p/{post_id}"

            return {
                'success': True,
                'platform': 'instagram',
                'post_id': post_id,
                'post_url': post_url,
                'title': title,
                'description': description,
                'tags': tags or [],
                'file_size': file_size,
                'upload_time': upload_time,
                'demo_mode': True,
                'message': f'Video uploaded to Instagram: {title}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_facebook(self, video_path: str, title: str, description: str,
                                  tags: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Upload lên Facebook (demo implementation)"""
        try:
            platform_info = self.supported_platforms['facebook']
            file_size = os.path.getsize(video_path)

            upload_time = max(5, min(60, file_size / (2 * 1024 * 1024)))

            logger.info(f"Facebook upload simulation: {title}")

            for progress in [0, 15, 30, 45, 60, 75, 90, 100]:
                await asyncio.sleep(upload_time / 7)
                self._report_progress('facebook', progress)
                logger.debug(f"Facebook upload progress: {progress}%")

            post_id = f"facebook_{int(time.time())}"
            post_url = f"https://facebook.com/watch/?v={post_id}"

            return {
                'success': True,
                'platform': 'facebook',
                'post_id': post_id,
                'post_url': post_url,
                'title': title,
                'description': description,
                'tags': tags or [],
                'file_size': file_size,
                'upload_time': upload_time,
                'demo_mode': True,
                'message': f'Video uploaded to Facebook: {title}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_twitter(self, video_path: str, title: str, description: str,
                                 tags: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Upload lên Twitter (demo implementation)"""
        try:
            platform_info = self.supported_platforms['twitter']
            file_size = os.path.getsize(video_path)

            upload_time = max(2, min(15, file_size / (4 * 1024 * 1024)))

            logger.info(f"Twitter upload simulation: {title}")

            for progress in [0, 30, 60, 90, 100]:
                await asyncio.sleep(upload_time / 4)
                self._report_progress('twitter', progress)
                logger.debug(f"Twitter upload progress: {progress}%")

            tweet_id = f"twitter_{int(time.time())}"
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"

            return {
                'success': True,
                'platform': 'twitter',
                'tweet_id': tweet_id,
                'tweet_url': tweet_url,
                'title': title,
                'description': description,
                'tags': tags or [],
                'file_size': file_size,
                'upload_time': upload_time,
                'demo_mode': True,
                'message': f'Video uploaded to Twitter: {title}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _upload_to_linkedin(self, video_path: str, title: str, description: str,
                                  tags: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Upload lên LinkedIn (demo implementation)"""
        try:
            platform_info = self.supported_platforms['linkedin']
            file_size = os.path.getsize(video_path)

            upload_time = max(10, min(120, file_size / (1 * 1024 * 1024)))

            logger.info(f"LinkedIn upload simulation: {title}")

            for progress in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                await asyncio.sleep(upload_time / 10)
                self._report_progress('linkedin', progress)
                logger.debug(f"LinkedIn upload progress: {progress}%")

            post_id = f"linkedin_{int(time.time())}"
            post_url = f"https://linkedin.com/feed/update/{post_id}"

            return {
                'success': True,
                'platform': 'linkedin',
                'post_id': post_id,
                'post_url': post_url,
                'title': title,
                'description': description,
                'tags': tags or [],
                'file_size': file_size,
                'upload_time': upload_time,
                'demo_mode': True,
                'message': f'Video uploaded to LinkedIn: {title}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _validate_video_for_platform(self, video_path: str, platform: str) -> Dict[str, Any]:
        """Validate video cho platform cụ thể"""
        try:
            if not os.path.exists(video_path):
                return {'valid': False, 'error': 'Video file not found'}

            platform_info = self.supported_platforms[platform]
            file_size = os.path.getsize(video_path)
            file_ext = Path(video_path).suffix.lower()

            # Check file size
            if file_size > platform_info['max_file_size']:
                return {
                    'valid': False,
                    'error': f'File too large: {file_size / 1024 / 1024:.1f}MB > {platform_info["max_file_size"] / 1024 / 1024:.1f}MB'
                }

            # Check file format
            if file_ext not in platform_info['supported_formats']:
                return {
                    'valid': False,
                    'error': f'Unsupported format: {file_ext}. Supported: {platform_info["supported_formats"]}'
                }

            # Get video duration (simplified)
            try:
                import cv2
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                duration = frame_count / fps if fps > 0 else 0
                cap.release()

                if duration > platform_info['max_duration']:
                    return {
                        'valid': False,
                        'error': f'Video too long: {duration:.1f}s > {platform_info["max_duration"]}s'
                    }
            except:
                # If we can't get duration, skip duration check
                pass

            return {'valid': True, 'message': 'Video validated successfully'}

        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}

    def _report_progress(self, platform: str, progress: int):
        """Báo cáo upload progress"""
        callback = self.upload_progress_callbacks.get(platform)
        if callback:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed for {platform}: {e}")

    def set_progress_callback(self, platform: str, callback: callable):
        """Thiết lập progress callback"""
        self.upload_progress_callbacks[platform] = callback

    def get_platform_info(self, platform: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin platform"""
        return self.supported_platforms.get(platform)

    def get_all_platforms(self) -> Dict[str, Dict[str, Any]]:
        """Lấy tất cả supported platforms"""
        return self.supported_platforms.copy()

    def optimize_video_for_platform(self, video_path: str, platform: str,
                                    output_path: str) -> Dict[str, Any]:
        """Tối ưu video cho platform cụ thể"""
        try:
            platform_info = self.supported_platforms[platform]

            import ffmpeg

            # Platform-specific optimization settings
            optimization_settings = {
                'tiktok': {
                    'vf': 'scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black',
                    'c:v': 'libx264',
                    'preset': 'fast',
                    'crf': '23',
                    'c:a': 'aac',
                    'b:a': '128k'
                },
                'instagram': {
                    'vf': 'scale=1080:1350:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1350:(ow-iw)/2:(oh-ih)/2:black',
                    'c:v': 'libx264',
                    'preset': 'fast',
                    'crf': '23',
                    'c:a': 'aac',
                    'b:a': '128k'
                },
                'facebook': {
                    'vf': 'scale=1080:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black',
                    'c:v': 'libx264',
                    'preset': 'medium',
                    'crf': '21',
                    'c:a': 'aac',
                    'b:a': '192k'
                },
                'twitter': {
                    'vf': 'scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos',
                    'c:v': 'libx264',
                    'preset': 'fast',
                    'crf': '25',
                    'c:a': 'aac',
                    'b:a': '128k'
                },
                'linkedin': {
                    'vf': 'scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos',
                    'c:v': 'libx264',
                    'preset': 'medium',
                    'crf': '22',
                    'c:a': 'aac',
                    'b:a': '192k'
                }
            }

            settings = optimization_settings.get(platform, {})

            stream = ffmpeg.input(video_path)

            if 'vf' in settings:
                stream = stream.filter(**{'vf': settings['vf']})

            # Remove video filter from settings for output
            output_settings = {k: v for k, v in settings.items() if k != 'vf'}
            output_settings['y'] = None  # Overwrite output

            stream = ffmpeg.output(stream, output_path, **output_settings)
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

            if os.path.exists(output_path):
                optimized_size = os.path.getsize(output_path)
                original_size = os.path.getsize(video_path)

                return {
                    'success': True,
                    'output_path': output_path,
                    'original_size': original_size,
                    'optimized_size': optimized_size,
                    'size_reduction': original_size - optimized_size,
                    'reduction_percentage': ((
                                                         original_size - optimized_size) / original_size) * 100 if original_size > 0 else 0,
                    'platform': platform,
                    'message': f'Video optimized for {platform_info["name"]}'
                }
            else:
                return {'success': False, 'error': 'Optimization failed - output file not created'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_platform_specific_caption(self, title: str, description: str,
                                           tags: List[str], platform: str) -> str:
        """Tạo caption tối ưu cho platform"""
        platform_rules = {
            'tiktok': {
                'max_length': 150,
                'hashtag_limit': 10,
                'emoji_encouraged': True
            },
            'instagram': {
                'max_length': 2200,
                'hashtag_limit': 30,
                'emoji_encouraged': True
            },
            'facebook': {
                'max_length': 5000,
                'hashtag_limit': 5,
                'emoji_encouraged': False
            },
            'twitter': {
                'max_length': 280,
                'hashtag_limit': 3,
                'emoji_encouraged': True
            },
            'linkedin': {
                'max_length': 3000,
                'hashtag_limit': 5,
                'emoji_encouraged': False
            }
        }

        rules = platform_rules.get(platform, {})
        max_length = rules.get('max_length', 1000)
        hashtag_limit = rules.get('hashtag_limit', 10)

        # Build caption
        caption_parts = []

        if title:
            caption_parts.append(title)

        if description:
            caption_parts.append(description)

        # Add hashtags
        if tags:
            hashtags = [f"#{tag.replace(' ', '')}" for tag in tags[:hashtag_limit]]
            caption_parts.append(" ".join(hashtags))

        caption = "\n\n".join(caption_parts)

        # Truncate if necessary
        if len(caption) > max_length:
            caption = caption[:max_length - 3] + "..."

        return caption

    async def check_upload_status(self, platform: str, post_id: str) -> Dict[str, Any]:
        """Kiểm tra trạng thái upload"""
        try:
            # Simulate status check
            await asyncio.sleep(1)

            # In real implementation, this would call platform APIs
            status_options = ['processing', 'published', 'failed']
            status = status_options[int(post_id) % len(status_options)] if post_id.isdigit() else 'published'

            return {
                'success': True,
                'platform': platform,
                'post_id': post_id,
                'status': status,
                'views': 100 + (int(time.time()) % 1000),  # Simulated views
                'likes': 10 + (int(time.time()) % 100),  # Simulated likes
                'comments': 2 + (int(time.time()) % 10),  # Simulated comments
                'demo_mode': True
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}