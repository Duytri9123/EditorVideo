# app/config.py
import os
from typing import Dict, Any


class Config:
    """Application configuration"""

    # Flask settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # File directories - UPDATED: static cùng cấp với app
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

    DIRECTORIES = {
        'downloads': os.path.join(STATIC_DIR, 'downloads'),
        'output': os.path.join(STATIC_DIR, 'output'),
        'music': os.path.join(STATIC_DIR, 'music'),
        'logos': os.path.join(STATIC_DIR, 'logos'),
        'temp': os.path.join(STATIC_DIR, 'temp')
    }

    # Upload configurations
    UPLOAD_CONFIGS = {
        'logo': {
            'directory': os.path.join(STATIC_DIR, 'logos'),
            'allowed_extensions': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
            'max_size': 10 * 1024 * 1024  # 10MB
        },
        'music': {
            'directory': os.path.join(STATIC_DIR, 'music'),
            'allowed_extensions': ['.mp3', '.wav', '.m4a', '.aac', '.ogg'],
            'max_size': 50 * 1024 * 1024  # 50MB
        },
        'video': {
            'directory': os.path.join(STATIC_DIR, 'downloads'),
            'allowed_extensions': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'max_size': 2 * 1024 * 1024 * 1024  # 2GB
        }
    }

    # API settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max upload