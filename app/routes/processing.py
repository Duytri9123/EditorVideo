# app/routes/processing.py
from flask import Blueprint, request, jsonify
import logging
import asyncio

logger = logging.getLogger(__name__)

processing_bp = Blueprint('processing', __name__)

@processing_bp.route('/process-video', methods=['POST'])
async def process_video():
    """Process video with effects"""
    try:
        data = request.get_json() or {}
        video_file = data.get('videoFile')
        output_name = data.get('outputName')
        effects_config = data.get('effects', {})

        if not video_file or not output_name:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        result = await processing_bp.video_service.process_video_with_effects(
            video_file, output_name, effects_config
        )
        return jsonify(result)

    except Exception as e:
        logger.error(f"Process video error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@processing_bp.route('/extract-audio', methods=['POST'])
async def extract_audio():
    """Extract audio from video"""
    try:
        data = request.get_json() or {}
        video_file = data.get('videoFile')
        output_name = data.get('outputName')

        if not video_file or not output_name:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        result = await processing_bp.video_service.extract_audio_from_video(video_file, output_name)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Extract audio error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@processing_bp.route('/merge-videos', methods=['POST'])
async def merge_videos():
    """Merge multiple videos"""
    try:
        data = request.get_json() or {}
        video_files = data.get('videoFiles', [])
        output_name = data.get('outputName', 'merged_video.mp4')
        transition_type = data.get('transitionType', 'none')

        if not video_files:
            return jsonify({'success': False, 'error': 'No video files provided'}), 400

        # This would use the actual merge functionality
        # For now, simulate with download_and_merge_videos using dummy URLs
        dummy_urls = [f'file://{file}' for file in video_files]
        result = await processing_bp.video_service.download_and_merge_videos(
            urls=dummy_urls,
            output_filename=output_name,
            transition_type=transition_type
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Merge videos error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500