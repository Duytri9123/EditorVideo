# app/main.py
import os
import asyncio
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

from app.config import Config
from app.services.video_service import VideoService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global progress tracking
download_progress = {}

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__,
                static_folder='../static',
                static_url_path='')

    app.config.from_object(config_class)
    CORS(app)

    # Initialize services
    video_service = VideoService(config_class)
    app.video_service = video_service

    # Register routes
    register_routes(app, video_service)

    # Serve static files
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:filename>')
    def serve_static_files(filename):
        if filename.endswith('.js'):
            return send_from_directory(app.static_folder, filename, mimetype='application/javascript')
        elif filename.endswith('.css'):
            return send_from_directory(app.static_folder, filename, mimetype='text/css')
        elif filename.endswith('.html'):
            return send_from_directory(app.static_folder, filename, mimetype='text/html')
        else:
            return send_from_directory(app.static_folder, filename)

    return app


def register_routes(app, video_service):
    """Register all API routes"""

    @app.route('/api')
    def api_root():
        return jsonify({
            'message': 'Video Tool Pro API',
            'version': '2.0',
            'status': 'running',
            'mode': 'direct-download',
            'features': ['progress_tracking', 'real_time_updates']
        })

    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Server is running'})

    # === PROGRESS TRACKING ===
    @app.route('/api/progress/<download_id>')
    def get_progress_api(download_id):
        """Get download progress for a specific download"""
        try:
            progress = download_progress.get(download_id, {})
            return jsonify({
                'success': True,
                'download_id': download_id,
                'progress': progress
            })
        except Exception as e:
            logger.error(f"❌ Progress check error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # === DOWNLOAD ROUTES WITH PROGRESS TRACKING ===
    @app.route('/api/download-video', methods=['POST'])
    def download_video_api():
        """Download video endpoint with progress tracking"""
        try:
            data = request.get_json() or {}
            url = data.get('url')
            filename = data.get('filename')
            quality = data.get('quality', 'best')
            format = data.get('format', 'mp4')

            logger.info(f"📥 Download video request: {url[:100]}...")

            if not url:
                return jsonify({'success': False, 'error': 'No URL provided'}), 400

            # Generate unique download ID
            download_id = f"download_{int(time.time())}_{hash(url) % 10000}"
            
            # Initialize progress tracking
            download_progress[download_id] = {
                'status': 'starting',
                'percent': 0,
                'stage': 'Initializing',
                'speed': 0,
                'eta': 0,
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'start_time': time.time(),
                'url': url,
                'filename': filename
            }

            # Start download in background thread
            def download_with_progress():
                try:
                    # Define progress callback
                    def my_progress_callback(p_data):
                        if download_id in download_progress:
                            # Map progress data to our structure
                            download_progress[download_id].update({
                                'status': p_data.get('status', 'downloading'),
                                'stage': p_data.get('stage', 'Downloading video data'),
                                'percent': p_data.get('percent', 0),
                                'downloaded_bytes': p_data.get('downloaded_bytes', 0),
                                'total_bytes': p_data.get('total_bytes', 0),
                                'speed': p_data.get('speed', 0),
                                'eta': p_data.get('eta', 0)
                            })

                    # Run download with real progress tracking
                    result = asyncio.run(video_service.download_video_with_progress(
                        url, filename, quality, format, 
                        progress_callback=my_progress_callback
                    ))
                    
                    if result.get('success') and result.get('file_path'):
                        file_path = Path(result['file_path'])
                        if file_path.exists():
                            # Download completed successfully
                            download_progress[download_id].update({
                                'status': 'completed',
                                'percent': 100,
                                'stage': 'Download completed',
                                'completion_time': time.time(),
                                'file_path': str(file_path),
                                'filename': result['filename'],
                                'size': result.get('size', 0),
                                'duration': result.get('duration', 0)
                            })
                        else:
                            download_progress[download_id].update({
                                'status': 'error',
                                'stage': 'File not found after download',
                                'error': 'Downloaded file not found'
                            })
                    else:
                        download_progress[download_id].update({
                            'status': 'error',
                            'stage': 'Download failed',
                            'error': result.get('error', 'Unknown error')
                        })

                except Exception as e:
                    logger.error(f"❌ Background download error: {e}")
                    download_progress[download_id].update({
                        'status': 'error',
                        'stage': 'Download error',
                        'error': str(e)
                    })

            # Start download in thread
            import threading
            thread = threading.Thread(target=download_with_progress)
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'download_id': download_id,
                'message': 'Download started',
                'progress_url': f'/api/progress/{download_id}'
            })

        except Exception as e:
            logger.error(f"❌ Download video error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/download-audio', methods=['POST'])
    def download_audio_api():
        """Download audio endpoint with progress tracking"""
        try:
            data = request.get_json() or {}
            url = data.get('url')
            filename = data.get('filename')
            format = data.get('format', 'mp3')
            quality = data.get('quality', '192')

            if not url:
                return jsonify({'success': False, 'error': 'No URL provided'}), 400

            # Generate unique download ID
            download_id = f"audio_{int(time.time())}_{hash(url) % 10000}"
            
            # Initialize progress tracking
            download_progress[download_id] = {
                'status': 'starting',
                'percent': 0,
                'stage': 'Initializing audio download',
                'speed': 0,
                'eta': 0,
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'start_time': time.time(),
                'url': url,
                'filename': filename
            }

            # Start download in background
            def download_audio_with_progress():
                try:
                    # Update progress
                    download_progress[download_id].update({
                        'status': 'preparing',
                        'percent': 10,
                        'stage': 'Preparing audio download',
                        'eta': 20
                    })

                    target_dir = data.get('target_dir')

                    # Run download
                    result = asyncio.run(video_service.download_video_with_progress(
                        url, filename, quality, format, 
                        target_dir=target_dir
                    ))
                    
                    if result.get('success') and result.get('file_path'):
                        file_path = Path(result['file_path'])
                        if file_path.exists():
                            download_progress[download_id].update({
                                'status': 'completed',
                                'percent': 100,
                                'stage': 'Audio download completed',
                                'speed': 0,
                                'eta': 0,
                                'downloaded_bytes': result.get('size', 0),
                                'total_bytes': result.get('size', 0),
                                'completion_time': time.time(),
                                'file_path': str(file_path),
                                'filename': result['filename'],
                                'size': result.get('size', 0),
                                'duration': result.get('duration', 0)
                            })
                        else:
                            download_progress[download_id].update({
                                'status': 'error',
                                'stage': 'Audio file not found',
                                'error': 'Downloaded audio file not found'
                            })
                    else:
                        download_progress[download_id].update({
                            'status': 'error',
                            'stage': 'Audio download failed',
                            'error': result.get('error', 'Unknown error')
                        })

                except Exception as e:
                    logger.error(f"❌ Background audio download error: {e}")
                    download_progress[download_id].update({
                        'status': 'error',
                        'stage': 'Audio download error',
                        'error': str(e)
                    })

            # Start download in thread
            import threading
            thread = threading.Thread(target=download_audio_with_progress)
            thread.daemon = True
            thread.start()

            # Simulate audio download progress
            def simulate_audio_progress():
                stages = [
                    ('Analyzing audio source', 20),
                    ('Extracting audio stream', 40),
                    ('Downloading audio', 65),
                    ('Converting format', 85),
                    ('Finalizing audio', 95)
                ]
                
                for stage, percent in stages:
                    time.sleep(2)  # Shorter stages for audio
                    if download_id in download_progress and download_progress[download_id]['status'] not in ['completed', 'error']:
                        download_progress[download_id].update({
                            'stage': stage,
                            'percent': percent,
                            'speed': 512 * 1024,  # 512 KB/s simulated
                            'eta': 15 - (percent / 100 * 15),
                            'downloaded_bytes': percent * 512 * 1024,
                            'total_bytes': 2 * 1024 * 1024
                        })

            progress_thread = threading.Thread(target=simulate_audio_progress)
            progress_thread.daemon = True
            progress_thread.start()

            return jsonify({
                'success': True,
                'download_id': download_id,
                'message': 'Audio download started',
                'progress_url': f'/api/progress/{download_id}'
            })

        except Exception as e:
            logger.error(f"❌ Download audio error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # === REAL PROGRESS TRACKING (requires yt-dlp with progress hooks) ===
    @app.route('/api/download-video-advanced', methods=['POST'])
    def download_video_advanced_api():
        """Advanced download with real progress tracking"""
        try:
            data = request.get_json() or {}
            url = data.get('url')
            filename = data.get('filename')
            quality = data.get('quality', 'best')
            format = data.get('format', 'mp4')

            if not url:
                return jsonify({'success': False, 'error': 'No URL provided'}), 400

            download_id = f"adv_{int(time.time())}_{hash(url) % 10000}"
            
            # Initialize progress
            download_progress[download_id] = {
                'status': 'starting',
                'percent': 0,
                'stage': 'Initializing advanced download',
                'speed': 0,
                'eta': 0,
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'start_time': time.time(),
                'url': url
            }

            # Start advanced download with real progress
            def advanced_download():
                try:
                    target_dir = data.get('target_dir')
                    
                    result = asyncio.run(video_service.download_video_with_progress(
                        url, filename, quality, format, 
                        progress_callback=lambda p: update_download_progress(download_id, p),
                        target_dir=target_dir
                    ))
                    
                    if result.get('success'):
                        download_progress[download_id].update({
                            'status': 'completed',
                            'percent': 100,
                            'stage': 'Download completed',
                            'file_path': result.get('file_path'),
                            'filename': result.get('filename'),
                            'size': result.get('size', 0)
                        })
                    else:
                        download_progress[download_id].update({
                            'status': 'error',
                            'stage': 'Download failed',
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    download_progress[download_id].update({
                        'status': 'error',
                        'stage': 'Download error',
                        'error': str(e)
                    })

            # Start in thread
            import threading
            thread = threading.Thread(target=advanced_download)
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'download_id': download_id,
                'message': 'Advanced download started with real progress tracking',
                'progress_url': f'/api/progress/{download_id}'
            })

        except Exception as e:
            logger.error(f"❌ Advanced download error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # === FILE SERVING ===
    @app.route('/api/files/<path:filename>')
    def serve_downloaded_file(filename):
        """Serve downloaded files for browser download"""
        try:
            file_path = video_service.temp_dir / filename
            if file_path.exists():
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename
                )
            else:
                return jsonify({'success': False, 'error': 'File not found'}), 404
                
        except Exception as e:
            logger.error(f"❌ Error serving file: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/list-files')
    def list_files_api():
        """List temporary files"""
        try:
            files = []
            if video_service.temp_dir.exists():
                for file_path in video_service.temp_dir.iterdir():
                    if file_path.is_file():
                        stat = file_path.stat()
                        files.append({
                            'name': file_path.name,
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'type': _get_file_type(file_path.name)
                        })
            
            return jsonify({
                'success': True,
                'files': sorted(files, key=lambda x: x['modified'], reverse=True)
            })
            
        except Exception as e:
            logger.error(f"❌ Error listing files: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/merge-videos', methods=['POST'])
    def merge_videos_api():
        """Merge videos endpoint"""
        try:
            data = request.get_json() or {}
            video_urls = data.get('video_urls', [])
            output_filename = data.get('filename', f"merged_{int(time.time())}.mp4")
            target_dir = data.get('target_dir')
            
            if not video_urls:
                logger.warning("⚠️ Merge requested with empty video_urls")
                return jsonify({'success': False, 'error': 'No video URLs provided'}), 400

            logger.info(f"💾 Merging {len(video_urls)} videos: {video_urls}")
            
            # Implementation assuming they are filenames in temp or full paths
            video_paths = []
            for item in video_urls:
                path = Path(item)
                if not path.is_absolute():
                    path = video_service.temp_dir / path.name
                
                if path.exists():
                    video_paths.append(str(path))
                else:
                    logger.error(f"❌ File not found for merge: {path}")
                    return jsonify({'success': False, 'error': f'File not found: {item}'}), 404

            # Run merge and cleanup sources
            result = asyncio.run(video_service.merge_videos(video_paths, output_filename, cleanup_sources=True))
            
            if result.get('success') and target_dir:
                # Use the new _move_to_target_dir method
                result = asyncio.run(video_service._move_to_target_dir(result, target_dir))

            return jsonify(result)

        except Exception as e:
            logger.error(f"❌ Merge API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # === CLEANUP ===
    @app.route('/api/cleanup-progress', methods=['POST'])
    def cleanup_progress_api():
        """Clean up old progress entries"""
        try:
            current_time = time.time()
            expired_ids = []
            
            for download_id, progress in download_progress.items():
                start_time = progress.get('start_time', 0)
                # Remove entries older than 1 hour
                if current_time - start_time > 3600:
                    expired_ids.append(download_id)
            
            for download_id in expired_ids:
                del download_progress[download_id]
            
            return jsonify({
                'success': True,
                'cleaned_count': len(expired_ids),
                'remaining_count': len(download_progress)
            })
            
        except Exception as e:
            logger.error(f"❌ Progress cleanup error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/cleanup-temp', methods=['POST'])
    def cleanup_temp_api():
        """Clean up temporary files"""
        try:
            data = request.get_json() or {}
            older_than_hours = data.get('older_than_hours', 1)
            
            deleted_count = asyncio.run(video_service.cleanup_temp_files(older_than_hours))
            
            return jsonify({
                'success': True,
                'message': f'Cleaned up {deleted_count} temporary files',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


def update_download_progress(download_id, progress_data):
    """Update progress for a download (callback function)"""
    if download_id in download_progress:
        download_progress[download_id].update(progress_data)


def _get_file_type(filename: str) -> str:
    """Get file type from extension"""
    ext = filename.lower().split('.')[-1]
    if ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        return 'video'
    elif ext in ['mp3', 'wav', 'm4a', 'aac', 'ogg']:
        return 'audio'
    else:
        return 'other'


def run_app():
    """Run the application"""
    app = create_app()

    print("=" * 60)
    print("🚀 Video Tool Pro Server - Version 2.0")
    print("📊 Real-time Progress Tracking Enabled")
    print("=" * 60)
    print("📡 Server URL: http://localhost:5000")
    print("📡 Network URL: http://0.0.0.0:5000")
    print("=" * 60)
    print("🔄 Progress endpoints available:")
    print("   GET /api/progress/<download_id>")
    print("   POST /api/cleanup-progress")
    print("=" * 60)

    static_path = app.static_folder
    print(f"📁 Static folder: {static_path}")
    print(f"📄 Index.html exists: {os.path.exists(os.path.join(static_path, 'index.html'))}")
    print("=" * 60)
    print("✅ Server ready with progress tracking...")
    print("=" * 60)

    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        threaded=True
    )


if __name__ == '__main__':
    run_app()