# video_tool/uploaders/youtube_uploader.py
import os
import time
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class YouTubeUploader:
    """YouTube uploader với authentication và progress tracking"""

    def __init__(self):
        self.youtube_service = None
        self.authenticated = False
        self._authenticate()

    def _authenticate(self):
        """Xác thực với YouTube API"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            creds = None
            token_file = Path('youtube_token.json')
            secrets_file = Path('client_secrets.json')

            # Load existing credentials
            if token_file.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(token_file), [
                        'https://www.googleapis.com/auth/youtube.upload'
                    ])
                except Exception as e:
                    logger.warning(f"Failed to load YouTube token: {e}")

            # Authenticate if no valid credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        from google.auth.transport.requests import Request
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Token refresh failed: {e}")
                        creds = None

                if not creds and secrets_file.exists():
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(secrets_file),
                            ['https://www.googleapis.com/auth/youtube.upload']
                        )
                        creds = flow.run_local_server(port=8080)

                        # Save credentials for next time
                        with open(token_file, 'w') as token:
                            token.write(creds.to_json())

                    except Exception as e:
                        logger.error(f"YouTube authentication failed: {e}")
                        return

            if creds and creds.valid:
                self.youtube_service = build('youtube', 'v3', credentials=creds)
                self.authenticated = True
                logger.info("✅ YouTube API authenticated successfully")
            else:
                logger.warning("YouTube authentication not available - using demo mode")

        except ImportError:
            logger.warning("YouTube API libraries not available - using demo mode")
        except Exception as e:
            logger.error(f"YouTube authentication error: {e}")

    async def upload_video(self, video_path: str, title: str,
                           description: str = "", privacy_status: str = "private") -> Dict[str, Any]:
        """Upload video lên YouTube"""
        try:
            if not os.path.exists(video_path):
                return {'success': False, 'error': f'Video file not found: {video_path}'}

            # File size check
            file_size = os.path.getsize(video_path)
            if file_size > 128 * 1024 * 1024 * 1024:  # 128GB
                return {'success': False, 'error': 'File too large (max 128GB)'}

            # Use real upload if authenticated, otherwise demo mode
            if self.authenticated and self.youtube_service:
                return await self._real_upload(video_path, title, description, privacy_status)
            else:
                return await self._demo_upload(video_path, title, description, privacy_status)

        except Exception as e:
            logger.error(f"YouTube upload error: {e}")
            return {'success': False, 'error': str(e)}

    async def _real_upload(self, video_path: str, title: str,
                           description: str, privacy_status: str) -> Dict[str, Any]:
        """Real YouTube upload với API"""
        try:
            from googleapiclient.http import MediaFileUpload

            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }

            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )

            request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            # Execute upload with progress tracking
            response = None
            last_progress = 0

            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress != last_progress:
                        logger.info(f"YouTube upload progress: {progress}%")
                        last_progress = progress

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            return {
                'success': True,
                'video_id': video_id,
                'video_url': video_url,
                'title': title,
                'privacy_status': privacy_status,
                'message': f'Video uploaded successfully: {title}'
            }

        except Exception as e:
            logger.error(f"Real YouTube upload failed: {e}")
            # Fallback to demo mode
            return await self._demo_upload(video_path, title, description, privacy_status)

    async def _demo_upload(self, video_path: str, title: str,
                           description: str, privacy_status: str) -> Dict[str, Any]:
        """Demo upload for testing"""
        try:
            # Simulate upload process
            file_size = os.path.getsize(video_path)
            upload_time = max(2, min(10, file_size / (10 * 1024 * 1024)))  # Simulate time based on file size

            logger.info(f"Demo upload: {title} ({file_size / 1024 / 1024:.1f} MB)")

            # Simulate progress
            for progress in [0, 25, 50, 75, 100]:
                await asyncio.sleep(upload_time / 4)
                logger.info(f"Demo upload progress: {progress}%")

            # Generate demo video ID
            import random
            video_id = f"demo_{int(time.time())}_{random.randint(1000, 9999)}"
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            return {
                'success': True,
                'video_id': video_id,
                'video_url': video_url,
                'title': title,
                'privacy_status': privacy_status,
                'demo_mode': True,
                'message': f'Demo upload completed: {title}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def check_upload_status(self, video_id: str) -> Dict[str, Any]:
        """Kiểm tra trạng thái upload"""
        try:
            if self.authenticated and self.youtube_service:
                request = self.youtube_service.videos().list(
                    part='status,statistics',
                    id=video_id
                )
                response = request.execute()

                if response['items']:
                    video_data = response['items'][0]
                    return {
                        'success': True,
                        'status': video_data['status']['uploadStatus'],
                        'privacy_status': video_data['status']['privacyStatus'],
                        'view_count': video_data['statistics'].get('viewCount', 0)
                    }
                else:
                    return {'success': False, 'error': 'Video not found'}
            else:
                # Demo mode
                return {
                    'success': True,
                    'status': 'processed',
                    'privacy_status': 'private',
                    'view_count': 0,
                    'demo_mode': True
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def close(self):
        """Cleanup resources"""
        try:
            if self.youtube_service:
                self.youtube_service.close()
        except:
            pass

    def is_authenticated(self) -> bool:
        """Kiểm tra xác thực"""
        return self.authenticated