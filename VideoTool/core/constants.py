# video_tool/core/constants.py

# Supported video formats
SUPPORTED_VIDEO_FORMATS = {
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.3gp'
}

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma', '.opus'
}

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.tiff'
}

# All supported formats
SUPPORTED_FORMATS = SUPPORTED_VIDEO_FORMATS | SUPPORTED_AUDIO_FORMATS | SUPPORTED_IMAGE_FORMATS

# File size limits
MAX_FILE_SIZE = 128 * 1024 * 1024 * 1024  # 128GB

# Quality presets
DEFAULT_QUALITY = 'best[height<=1080]'

# Video quality presets
VIDEO_QUALITY_PRESETS = {
    'best': 'best[height<=1080]',
    '1080': 'best[height<=1080]',
    '720': 'best[height<=720]',
    '480': 'best[height<=480]',
    '360': 'best[height<=360]',
    'worst': 'worst'
}

# Audio quality presets
AUDIO_QUALITY_PRESETS = {
    'best': '320',
    'high': '256',
    'medium': '192',
    'low': '128',
    'worst': '64'
}

# Export quality settings
EXPORT_QUALITY = {
    'high': {'crf': 18, 'preset': 'slow'},
    'medium': {'crf': 23, 'preset': 'medium'},
    'low': {'crf': 28, 'preset': 'fast'}
}

# Effect types
EFFECT_TYPES = {
    'color_correction': 'Color Correction',
    'flip_rotate': 'Flip & Rotate',
    'blur_sharpen': 'Blur & Sharpen',
    'text_overlay': 'Text Overlay',
    'logo_watermark': 'Logo Watermark',
    'color_filter': 'Color Filter',
    'crop': 'Crop',
    'speed': 'Speed Change'
}

# Timeline constants
MAX_TIMELINE_TRACKS = 10
MAX_CLIP_DURATION = 36000  # 10 hours
MIN_CLIP_DURATION = 0.1    # 100 milliseconds

# Hardware acceleration backends
HARDWARE_ACCELERATION_BACKENDS = {
    'vaapi': 'Video Acceleration API (Intel)',
    'cuda': 'NVIDIA CUDA',
    'opencl': 'OpenCL',
    'quicksync': 'Intel Quick Sync',
    'videotoolbox': 'Apple Video Toolbox'
}

# AI enhancement types
AI_ENHANCEMENT_TYPES = {
    'super_resolution': 'Super Resolution',
    'denoising': 'Noise Reduction',
    'colorization': 'Color Enhancement',
    'frame_interpolation': 'Frame Interpolation',
    'slow_motion': 'Slow Motion'
}

# YouTube privacy settings
YOUTUBE_PRIVACY_SETTINGS = {
    'public': 'Public',
    'private': 'Private',
    'unlisted': 'Unlisted'
}

# YouTube categories
YOUTUBE_CATEGORIES = {
    '1': 'Film & Animation',
    '2': 'Autos & Vehicles',
    '10': 'Music',
    '15': 'Pets & Animals',
    '17': 'Sports',
    '18': 'Short Movies',
    '19': 'Travel & Events',
    '20': 'Gaming',
    '21': 'Videoblogging',
    '22': 'People & Blogs',
    '23': 'Comedy',
    '24': 'Entertainment',
    '25': 'News & Politics',
    '26': 'Howto & Style',
    '27': 'Education',
    '28': 'Science & Technology',
    '29': 'Nonprofits & Activism'
}

# Performance settings
DEFAULT_MAX_WORKERS = 4
DEFAULT_THREAD_POOL_SIZE = 8
DEFAULT_PROCESS_POOL_SIZE = 2

# Cache settings
CACHE_TTL = 30  # seconds
MAX_CACHE_SIZE = 1000  # items

# Logging levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Theme settings
THEMES = {
    'dark': 'Dark Theme',
    'light': 'Light Theme',
    'blue': 'Blue Theme',
    'green': 'Green Theme'
}

# Language settings
LANGUAGES = {
    'vi': 'Vietnamese',
    'en': 'English',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese'
}

# Social media platforms
SOCIAL_PLATFORMS = {
    'tiktok': 'TikTok',
    'instagram': 'Instagram',
    'facebook': 'Facebook',
    'twitter': 'Twitter',
    'linkedin': 'LinkedIn',
    'youtube': 'YouTube'
}