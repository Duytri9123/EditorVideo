# app/utils/file_utils.py
import os
from typing import List


def get_file_icon(filename: str) -> str:
    """Get emoji icon for file type"""
    if not filename:
        return '📄'

    if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv')):
        return '🎬'
    if filename.lower().endswith(('.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac')):
        return '🎵'
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
        return '🖼️'
    return '📄'


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if not size_bytes or size_bytes == 0:
        return '0 B'

    size_names = ['B', 'KB', 'MB', 'GB']
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.2f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """Format duration in HH:MM:SS or MM:SS"""
    if not seconds or seconds == 0:
        return '00:00'

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    if not filename:
        return 'file'

    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename


def get_unique_filename(desired_name: str, existing_files: List[str]) -> str:
    """Generate unique filename if desired name already exists"""
    if desired_name not in existing_files:
        return desired_name

    base_name, extension = os.path.splitext(desired_name)
    counter = 1

    while True:
        new_name = f"{base_name} ({counter}){extension}"
        if new_name not in existing_files:
            return new_name
        counter += 1