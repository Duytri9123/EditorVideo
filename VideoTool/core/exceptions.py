# video_tool/core/exceptions.py

class VideoToolError(Exception):
    """Base exception cho Video Tool"""
    pass

class ProcessingError(VideoToolError):
    """Lỗi xử lý video"""
    pass

class UploadError(VideoToolError):
    """Lỗi upload"""
    pass

class DownloadError(VideoToolError):
    """Lỗi download"""
    pass

class FileError(VideoToolError):
    """Lỗi file operations"""
    pass

class ConfigurationError(VideoToolError):
    """Lỗi cấu hình"""
    pass

class TimelineError(VideoToolError):
    """Lỗi timeline operations"""
    pass

class EffectError(VideoToolError):
    """Lỗi effect operations"""
    pass

class HardwareAccelerationError(VideoToolError):
    """Lỗi hardware acceleration"""
    pass

class AIEnhancementError(VideoToolError):
    """Lỗi AI enhancement"""
    pass

class ValidationError(VideoToolError):
    """Lỗi validation"""
    pass

class SocialUploadError(VideoToolError):
    """Lỗi social media upload"""
    pass

class ClipManagerError(VideoToolError):
    """Lỗi clip management"""
    pass