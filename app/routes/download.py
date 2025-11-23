# app/routes/download.py
from flask import Blueprint, request, jsonify
import logging
import asyncio
from typing import List, Optional

logger = logging.getLogger(__name__)

download_bp = Blueprint('download', __name__)

@download_bp.route('/download', methods=['POST'])
async def download_video():
    """Universal video download endpoint"""
    try:
        data = request.get_json() or {}
        urls = data.get('urls', [])
        filename = data.get('filename')
        quality = data.get('quality', 'best')

        if not urls:
            return jsonify({'success': False, 'error': 'Không có URL nào được cung cấp'}), 400

        # Handle single URL
        if isinstance(urls, str):
            urls = [urls]

        if len(urls) == 1:
            # Single video download
            result = await download_bp.video_service.download_video(urls[0], filename, quality)
        else:
            # Multiple videos - download individually
            filenames = [filename] if filename else None
            result = await download_bp.video_service.download_multiple_videos(urls, filenames, quality)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@download_bp.route('/download-multiple', methods=['POST'])
async def download_multiple_videos():
    """Download multiple videos from various platforms"""
    try:
        data = request.get_json() or {}
        urls = data.get('urls', [])
        filenames = data.get('filenames', [])
        quality = data.get('quality', 'best')

        if not urls:
            return jsonify({'success': False, 'error': 'Không có URL nào được cung cấp'}), 400

        result = await download_bp.video_service.download_multiple_videos(urls, filenames, quality)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Multiple download error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@download_bp.route('/download-and-merge', methods=['POST'])
async def download_and_merge_videos():
    """Download and merge multiple videos"""
    try:
        data = request.get_json() or {}
        urls = data.get('urls', [])
        output_filename = data.get('output_filename', f'merged_video_{int(asyncio.get_event_loop().time())}.mp4')
        quality = data.get('quality', 'best[height<=1080]')
        transition_type = data.get('transition_type', 'none')
        keep_originals = data.get('keep_originals', False)

        if not urls:
            return jsonify({'success': False, 'error': 'Không có URL nào được cung cấp'}), 400

        if len(urls) < 2:
            return jsonify({'success': False, 'error': 'Cần ít nhất 2 URL để ghép video'}), 400

        result = await download_bp.video_service.download_and_merge_videos(
            urls, output_filename, quality, transition_type, keep_originals
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Download and merge error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@download_bp.route('/download-audio', methods=['POST'])
async def download_audio():
    """Download audio from video URL"""
    try:
        data = request.get_json() or {}
        url = data.get('url')
        filename = data.get('filename')
        format = data.get('format', 'mp3')
        quality = data.get('quality', '192')

        if not url:
            return jsonify({'success': False, 'error': 'Không có URL nào được cung cấp'}), 400

        result = await download_bp.video_service.download_audio(url, filename, format, quality)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Audio download error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@download_bp.route('/supported-platforms', methods=['GET'])
async def get_supported_platforms():
    """Get list of supported platforms"""
    platforms = [
        'YouTube (youtube.com, youtu.be)',
        'TikTok (tiktok.com, vm.tiktok.com, vt.tiktok.com)',
        'Instagram (instagram.com)',
        'Facebook (facebook.com, fb.watch)',
        'Twitter/X (twitter.com, x.com)',
        'Vimeo (vimeo.com)',
        'Dailymotion (dailymotion.com)',
        'Twitch (twitch.tv)',
        'Reddit (reddit.com)',
        'LinkedIn (linkedin.com)',
        'Pinterest (pinterest.com)',
        'Likee (likee.com)',
        'Kwai (kwai.com)',
        'Bilibili (bilibili.com)',
        'Douyin (douyin.com)',
        'Weibo (weibo.com)',
        'Streamable (streamable.com)',
        'Gfycat (gfycat.com)',
        'Imgur (imgur.com)',
        'Flickr (flickr.com)',
        '9GAG (9gag.com)',
        'Tumblr (tumblr.com)',
        'VK (vk.com)',
        'OK.ru (ok.ru)',
        'Rutube (rutube.ru)',
        'Coub (coub.com)',
        'Rumble (rumble.com)',
        'Odysee (odysee.com)',
        'DTube (dtube.com)',
        'LBRY (lbry.com)',
        'Brighteon (brighteon.com)',
        'Bitchute (bitchute.com)',
        'PeerTube (various instances)',
        'Direct video links (.mp4, .webm, .mov, .avi, .mkv)'
    ]

    return jsonify({
        'success': True,
        'platforms': platforms,
        'count': len(platforms)
    })

@download_bp.route('/platform-info', methods=['POST'])
async def get_platform_info():
    """Get information about a specific URL's platform"""
    try:
        data = request.get_json() or {}
        url = data.get('url')

        if not url:
            return jsonify({'success': False, 'error': 'Không có URL nào được cung cấp'}), 400

        platform = download_bp.video_service._identify_platform(url)
        is_supported = download_bp.video_service._is_supported_url(url)

        return jsonify({
            'success': True,
            'url': url,
            'platform': platform,
            'supported': is_supported,
            'suggested_filename': download_bp.video_service._generate_filename_from_url(url, platform)
        })

    except Exception as e:
        logger.error(f"Platform info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500