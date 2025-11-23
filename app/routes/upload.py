# app/routes/upload.py
from flask import Blueprint, request, jsonify
import logging
import asyncio

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload-youtube', methods=['POST'])
async def upload_youtube():
    """Upload video to YouTube"""
    try:
        data = request.get_json() or {}
        video_file = data.get('videoFile')
        title = data.get('title')
        description = data.get('description', '')
        privacy_status = data.get('privacyStatus', 'private')

        if not video_file or not title:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        result = await upload_bp.video_service.upload_to_youtube(
            video_file, title, description, privacy_status
        )
        return jsonify(result)

    except Exception as e:
        logger.error(f"YouTube upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upload_bp.route('/batch-upload-youtube', methods=['POST'])
async def batch_upload_youtube():
    """Batch upload to YouTube"""
    try:
        data = request.get_json() or {}
        urls = data.get('urls', [])
        title_template = data.get('titleTemplate', 'Video {number}')
        description_template = data.get('descriptionTemplate', '')
        privacy_status = data.get('privacyStatus', 'private')
        effects_config = data.get('effects', {})

        if not urls:
            return jsonify({'success': False, 'error': 'No URLs provided'}), 400

        # Mock implementation - process each URL
        results = []
        for i, url in enumerate(urls):
            # Download video
            download_result = await upload_bp.video_service.download_video(url)
            if download_result['success']:
                video_file = download_result['downloaded_name']

                # Process with effects if configured
                if effects_config:
                    processed_name = f'processed_{video_file}'
                    await upload_bp.video_service.process_video_with_effects(
                        video_file, processed_name, effects_config
                    )
                    video_file = processed_name

                # Upload to YouTube
                title = title_template.replace('{number}', str(i + 1))
                description = description_template.replace('{number}', str(i + 1))

                upload_result = await upload_bp.video_service.upload_to_youtube(
                    video_file, title, description, privacy_status
                )

                results.append({
                    'url': url,
                    'success': upload_result['success'],
                    'video_id': upload_result.get('video_id'),
                    'title': title,
                    'error': upload_result.get('error')
                })
            else:
                results.append({
                    'url': url,
                    'success': False,
                    'error': download_result.get('error')
                })

        successful = len([r for r in results if r['success']])
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(urls),
                'successful': successful,
                'failed': len(urls) - successful
            }
        })

    except Exception as e:
        logger.error(f"Batch YouTube upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500