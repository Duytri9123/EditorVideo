# video_tool/utils/config.py
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AppConfig:
    """Quản lý cấu hình ứng dụng với persistence"""

    DEFAULT_CONFIG = {
        'download_dir': 'downloads',
        'output_dir': 'output',
        'music_dir': 'music',
        'logos_dir': 'logos',
        'temp_dir': 'temp',
        'max_workers': 4,
        'enable_hardware_acceleration': True,
        'enable_ai_enhancement': True,
        'default_quality': 'best',
        'log_level': 'INFO',
        'max_file_size': 128 * 1024 * 1024 * 1024,  # 128GB
        'auto_cleanup_temp': True,
        'temp_cleanup_interval': 3600,  # 1 hour
        'preview_quality': 'medium',
        'export_quality': 'high',
        'timeline_auto_save': True,
        'timeline_auto_save_interval': 300,  # 5 minutes
        'youtube_privacy': 'private',
        'youtube_category': '22',
        'ffmpeg_path': 'ffmpeg',
        'enable_notifications': True,
        'theme': 'dark',
        'language': 'vi'
    }

    def __init__(self, user_config: Dict[str, Any] = None, config_file: str = 'video_tool_config.json'):
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()

        # Load from file if exists
        self._load_from_file()

        # Apply user config
        if user_config:
            self.config.update(user_config)

        # Apply environment variables
        self._apply_env_vars()

        # Ensure directories exist
        self._ensure_directories()

        logger.info("App Config initialized")

    def _load_from_file(self):
        """Load cấu hình từ file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                logger.info(f"Loaded config from {self.config_file}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")

    def _save_to_file(self):
        """Lưu cấu hình vào file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved config to {self.config_file}")
        except Exception as e:
            logger.warning(f"Could not save config file: {e}")

    def _apply_env_vars(self):
        """Áp dụng biến môi trường"""
        env_mapping = {
            'VIDEO_TOOL_DOWNLOAD_DIR': 'download_dir',
            'VIDEO_TOOL_OUTPUT_DIR': 'output_dir',
            'VIDEO_TOOL_LOG_LEVEL': 'log_level',
            'VIDEO_TOOL_MAX_WORKERS': 'max_workers',
            'VIDEO_TOOL_FFMPEG_PATH': 'ffmpeg_path',
            'VIDEO_TOOL_THEME': 'theme',
            'VIDEO_TOOL_LANGUAGE': 'language'
        }

        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                # Convert string to appropriate type
                if config_key in ['max_workers']:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif config_key in ['enable_hardware_acceleration', 'enable_ai_enhancement', 'auto_cleanup_temp']:
                    value = value.lower() in ['true', '1', 'yes', 'on']

                self.config[config_key] = value
                logger.debug(f"Applied environment variable {env_var}={value}")

    def _ensure_directories(self):
        """Đảm bảo các thư mục tồn tại"""
        directories = [
            self.config['download_dir'],
            self.config['output_dir'],
            self.config['music_dir'],
            self.config['logos_dir'],
            self.config['temp_dir']
        ]

        for directory in directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị config"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True):
        """Đặt giá trị config"""
        old_value = self.config.get(key)
        self.config[key] = value

        if save:
            self._save_to_file()

        logger.debug(f"Config updated: {key} = {value} (was {old_value})")

    def update(self, updates: Dict[str, Any], save: bool = True):
        """Cập nhật nhiều giá trị"""
        for key, value in updates.items():
            self.config[key] = value

        if save:
            self._save_to_file()

        logger.debug(f"Config updated with {len(updates)} values")

    def reset(self, key: str = None, save: bool = True):
        """Reset config về giá trị mặc định"""
        if key is None:
            # Reset all
            self.config = self.DEFAULT_CONFIG.copy()
            logger.info("Config reset to defaults")
        else:
            # Reset specific key
            if key in self.DEFAULT_CONFIG:
                self.config[key] = self.DEFAULT_CONFIG[key]
                logger.debug(f"Config reset: {key} = {self.DEFAULT_CONFIG[key]}")

        if save:
            self._save_to_file()

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành dictionary"""
        return self.config.copy()

    def validate(self) -> Dict[str, Any]:
        """Validate cấu hình"""
        errors = []
        warnings = []

        # Validate directories
        for dir_key in ['download_dir', 'output_dir', 'music_dir', 'logos_dir', 'temp_dir']:
            dir_path = Path(self.config[dir_key])
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {dir_key}: {dir_path} - {e}")

            # Check write permission
            if dir_path.exists():
                test_file = dir_path / '.write_test'
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    errors.append(f"No write permission in {dir_key}: {dir_path} - {e}")

        # Validate numeric values
        if self.config['max_workers'] < 1:
            errors.append("max_workers must be at least 1")

        if self.config['max_file_size'] < 1024 * 1024:  # 1MB
            warnings.append("max_file_size seems too small")

        # Validate quality settings
        valid_qualities = ['best', '1080', '720', '480', '360']
        if self.config['default_quality'] not in valid_qualities:
            warnings.append(f"default_quality should be one of {valid_qualities}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'config_summary': {
                'directories': {
                    k: str(Path(self.config[k]))
                    for k in ['download_dir', 'output_dir', 'music_dir', 'logos_dir', 'temp_dir']
                },
                'performance': {
                    'max_workers': self.config['max_workers'],
                    'hardware_acceleration': self.config['enable_hardware_acceleration'],
                    'ai_enhancement': self.config['enable_ai_enhancement']
                },
                'features': {
                    'auto_cleanup': self.config['auto_cleanup_temp'],
                    'timeline_auto_save': self.config['timeline_auto_save'],
                    'notifications': self.config['enable_notifications']
                }
            }
        }

    def get_directory_path(self, directory_key: str) -> Path:
        """Lấy đường dẫn thư mục"""
        return Path(self.config[directory_key])

    def get_export_settings(self) -> Dict[str, Any]:
        """Lấy cài đặt export"""
        return {
            'quality': self.config['export_quality'],
            'format': 'mp4',
            'codec': 'libx264',
            'audio_codec': 'aac',
            'crf': 23 if self.config['export_quality'] == 'high' else 28,
            'preset': 'medium'
        }

    def get_preview_settings(self) -> Dict[str, Any]:
        """Lấy cài đặt preview"""
        return {
            'quality': self.config['preview_quality'],
            'max_width': 1280 if self.config['preview_quality'] == 'high' else 854,
            'max_height': 720 if self.config['preview_quality'] == 'high' else 480
        }