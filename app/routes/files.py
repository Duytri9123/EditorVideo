# app/routes/files.py
from flask import Blueprint, request, jsonify
import logging
import asyncio

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)

@files_bp.route('/files', methods=['GET'])
async def list_files():
    """List all files"""
    try:
        result = await files_bp.video_service.list_files()
        return jsonify(result)
    except Exception as e:
        logger.error(f"List files error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/file-info', methods=['POST'])
def get_file_info():
    """Get file information"""
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path')

        if not file_path:
            return jsonify({'success': False, 'error': 'No file path provided'}), 400

        # Mock implementation
        return jsonify({
            'success': True,
            'file_info': {
                'name': file_path.split('/')[-1],
                'path': file_path,
                'size': 10485760,  # 10MB
                'type': 'video',
                'duration': 120.5,
                'resolution': '1920x1080',
                'format': 'mp4'
            }
        })

    except Exception as e:
        logger.error(f"Get file info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/cleanup', methods=['POST'])
async def cleanup_files():
    """Clean up files"""
    try:
        data = request.get_json() or {}
        cleanup_type = data.get('type', 'downloads')

        result = await files_bp.video_service.cleanup(cleanup_type)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/upload-file', methods=['POST'])
async def upload_file():
    """Upload file (logo, audio, etc.)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        file_type = request.form.get('type', 'logo')

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        result = await files_bp.video_service.upload_file(file, file_type)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Upload file error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500