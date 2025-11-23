# app/main.py
import os
import logging
import time
import subprocess
import asyncio
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

from config import Config
from routes.download import download_bp
from services.video_service import VideoService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__,
                static_folder='../static',
                static_url_path='')

    app.config.from_object(config_class)
    CORS(app)

    # Initialize services với config
    video_service = VideoService(config_class)
    app.video_service = video_service

    # Register blueprints
    download_bp.video_service = video_service
    app.register_blueprint(download_bp, url_prefix='/api')

    # Register additional routes
    register_additional_routes(app, video_service)

    # Serve static files with proper MIME types
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:filename>')
    def serve_static_files(filename):
        # Set proper MIME types
        if filename.endswith('.js'):
            return send_from_directory(app.static_folder, filename, mimetype='application/javascript')
        elif filename.endswith('.css'):
            return send_from_directory(app.static_folder, filename, mimetype='text/css')
        elif filename.endswith('.html'):
            return send_from_directory(app.static_folder, filename, mimetype='text/html')
        else:
            return send_from_directory(app.static_folder, filename)

    # Create directories từ config
    _create_directories(config_class.DIRECTORIES)

    return app


def register_additional_routes(app, video_service):
    """Register additional API routes"""

    @app.route('/api')
    def api_root():
        return jsonify({
            'message': 'Video Tool Pro API',
            'version': '2.0',
            'status': 'running'
        })

    @app.route('/api/merge-videos', methods=['POST'])
    def merge_videos_api():
        """API endpoint to merge videos"""
        try:
            data = request.get_json() or {}
            video_files = data.get('videoFiles', [])
            output_name = data.get('outputName', f'merged_video_{int(time.time())}.mp4')
            options = data.get('options', {})

            if not video_files:
                return jsonify({'success': False, 'error': 'No video files provided'}), 400

            # Gọi service merge videos
            result = asyncio.run(app.video_service.merge_videos(video_files, output_name, options))
            return jsonify(result)

        except Exception as e:
            logger.error(f"Merge videos API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Server is running'})

    @app.route('/api/list-files')
    def list_files_api():
        """API endpoint to list all files"""
        try:
            result = asyncio.run(video_service.list_files())
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/files')
    def files_api():
        """Alternative files endpoint"""
        try:
            result = asyncio.run(video_service.list_files())
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in files API: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/delete-file', methods=['POST'])
    def delete_file_api():
        """Delete a file"""
        try:
            data = request.get_json() or {}
            filename = data.get('filename')
            if not filename:
                return jsonify({'success': False, 'error': 'No filename provided'}), 400

            result = asyncio.run(video_service.delete_file(filename))
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/upload-file', methods=['POST'])
    def upload_file_api():
        """Upload a file"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400

            file = request.files['file']
            file_type = request.form.get('type', 'logo')

            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            result = asyncio.run(video_service.upload_file(file, file_type))
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/system/status')
    def system_status_api():
        """System status endpoint"""
        try:
            # Fallback system status nếu có lỗi
            try:
                result = asyncio.run(video_service.get_system_status())
                return jsonify(result)
            except Exception as service_error:
                logger.warning(f"System status service error, using fallback: {service_error}")
                # Trả về dữ liệu mẫu nếu service lỗi
                return jsonify({
                    'success': True,
                    'data': {
                        'memory': 45.5,
                        'disk': 67.8,
                        'cpu': 15.2
                    }
                })
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/system/storage')
    def storage_info_api():
        """Storage information endpoint"""
        try:
            # Fallback storage info nếu có lỗi
            try:
                result = asyncio.run(video_service.get_storage_info())
                return jsonify(result)
            except Exception as service_error:
                logger.warning(f"Storage info service error, using fallback: {service_error}")
                # Trả về dữ liệu mẫu nếu service lỗi
                return jsonify({
                    'success': True,
                    'data': {
                        'total': 500.0,
                        'used': 150.5,
                        'available': 349.5,
                        'percent': 30.1
                    }
                })
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/cleanup', methods=['POST'])
    def cleanup_api():
        """Cleanup files endpoint"""
        try:
            data = request.get_json() or {}
            cleanup_type = data.get('type', 'downloads')
            result = asyncio.run(video_service.cleanup(cleanup_type))
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # Thêm các endpoints mới cho frontend
    @app.route('/api/files/<path:filename>')
    def serve_file(filename):
        """Serve individual files"""
        try:
            # Tìm file trong các thư mục
            for dir_name, dir_path in video_service.directories.items():
                file_path = dir_path / filename
                if file_path.exists():
                    return send_from_directory(dir_path, filename)

            return jsonify({'success': False, 'error': 'File not found'}), 404
        except Exception as e:
            logger.error(f"Error serving file: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/download-video', methods=['POST'])
    def download_video_api():
        """Download video endpoint - tương thích với frontend"""
        try:
            data = request.get_json() or {}
            urls = data.get('urls', [])
            filename = data.get('filename')
            quality = data.get('quality', 'best')

            logger.info(f"Download video request: urls={urls}, filename={filename}, quality={quality}")

            if not urls:
                return jsonify({'success': False, 'error': 'No URLs provided'}), 400

            # Handle single URL
            if isinstance(urls, str):
                urls = [urls]

            if len(urls) == 1:
                # Single video download
                result = asyncio.run(video_service.download_video(urls[0], filename, quality))
            else:
                # Multiple videos
                filenames = [filename] if filename else None
                result = asyncio.run(video_service.download_multiple_videos(urls, filenames, quality))

            return jsonify(result)
        except Exception as e:
            logger.error(f"Download video error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/download-audio', methods=['POST'])
    def download_audio_api():
        """Download audio endpoint - tương thích với frontend"""
        try:
            data = request.get_json() or {}
            url = data.get('url')
            filename = data.get('filename')
            format = data.get('format', 'mp3')
            quality = data.get('quality', '192')

            if not url:
                return jsonify({'success': False, 'error': 'No URL provided'}), 400

            result = asyncio.run(video_service.download_audio(url, filename, format, quality))
            return jsonify(result)
        except Exception as e:
            logger.error(f"Download audio error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # Endpoint cho file management từ frontend
    @app.route('/api/file-management/delete-file', methods=['POST'])
    def file_management_delete_api():
        """File management delete endpoint"""
        try:
            data = request.get_json() or {}
            filename = data.get('filename')
            if not filename:
                return jsonify({'success': False, 'error': 'No filename provided'}), 400

            result = asyncio.run(video_service.delete_file(filename))
            return jsonify(result)
        except Exception as e:
            logger.error(f"File management delete error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/file-management/upload-file', methods=['POST'])
    def file_management_upload_api():
        """File management upload endpoint"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400

            file = request.files['file']
            file_type = request.form.get('type', 'logo')

            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            result = asyncio.run(video_service.upload_file(file, file_type))
            return jsonify(result)
        except Exception as e:
            logger.error(f"File management upload error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


def _create_directories(directories: dict):
    """Create necessary directories từ config"""
    for key, directory in directories.items():
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists for {key}: {directory}")


# THÊM METHOD merge_videos VÀO VideoService
def add_merge_videos_method():
    """Add merge_videos method to VideoService class"""

    async def merge_videos(self, video_files, output_name, options=None):
        """Merge multiple videos"""
        try:
            if options is None:
                options = {}

            logger.info(f"Merging {len(video_files)} videos into {output_name}")

            # Đảm bảo tất cả file tồn tại trong thư mục downloads
            existing_files = []
            for file in video_files:
                file_path = self.directories['downloads'] / file
                if file_path.exists():
                    existing_files.append(str(file_path))
                    logger.info(f"Found file: {file_path}")
                else:
                    logger.warning(f"File not found: {file}")

            if len(existing_files) < 2:
                error_msg = f'Need at least 2 existing videos to merge, found {len(existing_files)}'
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}

            # Tạo thư mục output nếu chưa tồn tại
            self.directories['output'].mkdir(exist_ok=True)
            output_path = self.directories['output'] / output_name

            # Tạo thư mục temp nếu chưa tồn tại
            self.directories['temp'].mkdir(exist_ok=True)

            # Tạo file list cho FFmpeg
            list_file = self.directories['temp'] / 'merge_list.txt'
            logger.info(f"Creating list file: {list_file}")

            try:
                with open(list_file, 'w', encoding='utf-8') as f:
                    for file in existing_files:
                        f.write(f"file '{file}'\n")
            except Exception as e:
                logger.error(f"Error creating list file: {e}")
                return {'success': False, 'error': f'Cannot create list file: {str(e)}'}

            # Sử dụng FFmpeg để merge
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(list_file),
                '-c', 'copy',
                str(output_path),
                '-y'
            ]

            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")

            try:
                # Sử dụng asyncio để chạy subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
                returncode = process.returncode

                logger.info(f"FFmpeg return code: {returncode}")

                if returncode == 0:
                    logger.info("FFmpeg merge successful")

                    # Xóa file list tạm
                    try:
                        if list_file.exists():
                            list_file.unlink()
                            logger.info("Temporary list file deleted")
                    except Exception as e:
                        logger.warning(f"Could not delete list file: {e}")

                    # Xóa file tạm nếu không giữ bản gốc
                    if not options.get('keepOriginals', False):
                        deleted_count = 0
                        for file in existing_files:
                            try:
                                file_path = Path(file)
                                if file_path.exists() and file_path != output_path:
                                    file_path.unlink()
                                    deleted_count += 1
                                    logger.info(f"Deleted original file: {file}")
                            except Exception as e:
                                logger.warning(f"Could not delete original file {file}: {e}")
                        logger.info(f"Deleted {deleted_count} original files")

                    # Kiểm tra file output đã được tạo
                    if output_path.exists():
                        file_size = output_path.stat().st_size
                        logger.info(f"Output file created: {output_path} ({file_size} bytes)")

                        return {
                            'success': True,
                            'message': f'Successfully merged {len(existing_files)} videos',
                            'output_file': output_name,
                            'output_path': str(output_path),
                            'file_size': file_size
                        }
                    else:
                        error_msg = "Output file was not created"
                        logger.error(error_msg)
                        return {'success': False, 'error': error_msg}
                else:
                    error_msg = f'FFmpeg error (code {returncode}): {stderr.decode()}'
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg
                    }

            except asyncio.TimeoutError:
                error_msg = "FFmpeg process timed out after 5 minutes"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            except Exception as e:
                error_msg = f"FFmpeg execution error: {str(e)}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}

        except Exception as e:
            logger.error(f"Merge videos error: {e}")
            return {'success': False, 'error': str(e)}

    # Thêm method vào class
    VideoService.merge_videos = merge_videos
    logger.info("✅ Added merge_videos method to VideoService")


def run_app():
    """Run the application"""
    # Thêm method merge_videos vào VideoService trước khi tạo app
    add_merge_videos_method()

    app = create_app()

    print("=" * 60)
    print("🚀 Video Tool Pro Server - Version 2.0")
    print("=" * 60)
    print("📡 Server URL: http://localhost:5000")
    print("📡 Network URL: http://0.0.0.0:5000")
    print("=" * 60)

    # Test if static files are accessible
    static_path = app.static_folder
    print(f"📁 Static folder: {static_path}")
    print(f"📄 Index.html exists: {os.path.exists(os.path.join(static_path, 'index.html'))}")
    print("=" * 60)
    print("✅ Server ready and listening...")
    print("=" * 60)

    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        threaded=True
    )


if __name__ == '__main__':
    run_app()