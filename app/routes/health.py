# app/routes/health.py
from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'message': 'Video Tool Pro API is running',
            'timestamp': '2024-01-01T00:00:00Z'  # You can use datetime here
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500