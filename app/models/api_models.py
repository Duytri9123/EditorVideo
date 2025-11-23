# app/models/api_models.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class DownloadRequest:
    url: str
    filename: Optional[str] = None
    quality: str = 'best'

@dataclass
class TimelineClip:
    file_path: str
    start_time: float = 0
    end_time: Optional[float] = None
    track: int = 0

@dataclass
class VideoProcessingRequest:
    input_file: str
    output_name: str
    effects_config: Dict[str, Any] = None

@dataclass
class YouTubeUploadRequest:
    video_file: str
    title: str
    description: str = ''
    privacy_status: str = 'private'