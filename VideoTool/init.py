# video_tool/init.py (updated)
"""
Video Tool Pro - Professional Video Editing and Processing Tool
Optimized for Intel ThinkPad T14 Gen3 with hardware acceleration
"""

from .main import OptimizedVideoTool
from .editors.clip_manager import ClipManager, Clip, ClipProperties
from .uploaders.social_uploader import SocialUploader
from .core.exceptions import (
    VideoToolError, ProcessingError, UploadError, DownloadError,
    FileError, ConfigurationError, TimelineError, EffectError,
    HardwareAccelerationError, AIEnhancementError, ValidationError
)

__version__ = "2.0.0"
__author__ = "Video Tool Pro Team"
__description__ = "Professional video editing and processing tool with hardware acceleration"

__all__ = [
    'OptimizedVideoTool',
    'ClipManager',
    'Clip',
    'ClipProperties',
    'SocialUploader',
    'VideoToolError',
    'ProcessingError',
    'UploadError',
    'DownloadError',
    'FileError',
    'ConfigurationError',
    'TimelineError',
    'EffectError',
    'HardwareAccelerationError',
    'AIEnhancementError',
    'ValidationError'
]