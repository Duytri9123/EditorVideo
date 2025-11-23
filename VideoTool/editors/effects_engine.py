# video_tool/editors/effects_engine.py
import logging
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


class EffectsEngine:
    """Engine xử lý hiệu ứng video với real-time optimization"""

    def __init__(self):
        self.available_effects = self._get_available_effects()
        self.effect_presets = self._get_effect_presets()

        logger.info("Effects Engine initialized")

    def _get_available_effects(self) -> Dict[str, Dict]:
        """Danh sách hiệu ứng có sẵn"""
        return {
            'color_correction': {
                'name': 'Color Correction',
                'description': 'Adjust brightness, contrast, saturation',
                'parameters': {
                    'brightness': {'type': 'float', 'min': 0.1, 'max': 5.0, 'default': 1.0},
                    'contrast': {'type': 'float', 'min': 0.1, 'max': 5.0, 'default': 1.0},
                    'saturation': {'type': 'float', 'min': 0.0, 'max': 3.0, 'default': 1.0},
                    'hue': {'type': 'float', 'min': -180, 'max': 180, 'default': 0.0}
                }
            },
            'flip_rotate': {
                'name': 'Flip & Rotate',
                'description': 'Flip and rotate video',
                'parameters': {
                    'flip_horizontal': {'type': 'bool', 'default': False},
                    'flip_vertical': {'type': 'bool', 'default': False},
                    'rotate': {'type': 'float', 'min': -360, 'max': 360, 'default': 0.0}
                }
            },
            'blur_sharpen': {
                'name': 'Blur & Sharpen',
                'description': 'Apply blur or sharpen effects',
                'parameters': {
                    'blur_amount': {'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
                    'sharpen_amount': {'type': 'float', 'min': 0.0, 'max': 5.0, 'default': 0.0}
                }
            },
            'text_overlay': {
                'name': 'Text Overlay',
                'description': 'Add text to video',
                'parameters': {
                    'text': {'type': 'string', 'default': ''},
                    'font_size': {'type': 'int', 'min': 10, 'max': 100, 'default': 24},
                    'font_color': {'type': 'color', 'default': '#FFFFFF'},
                    'position': {'type': 'select',
                                 'options': ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'],
                                 'default': 'top-left'}
                }
            },
            'logo_watermark': {
                'name': 'Logo Watermark',
                'description': 'Add logo or watermark',
                'parameters': {
                    'logo_path': {'type': 'file', 'default': ''},
                    'logo_size': {'type': 'int', 'min': 10, 'max': 500, 'default': 80},
                    'logo_opacity': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.8},
                    'logo_position': {'type': 'select',
                                      'options': ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'],
                                      'default': 'top-left'}
                }
            },
            'color_filter': {
                'name': 'Color Filter',
                'description': 'Apply color filters',
                'parameters': {
                    'filter_type': {'type': 'select',
                                    'options': ['none', 'sepia', 'grayscale', 'vintage', 'cool', 'warm'],
                                    'default': 'none'},
                    'filter_intensity': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 1.0}
                }
            }
        }

    def _get_effect_presets(self) -> Dict[str, Dict]:
        """Presets hiệu ứng predefined"""
        return {
            'vintage_look': {
                'name': 'Vintage Look',
                'effects': {
                    'color_correction': {
                        'brightness': 0.9,
                        'contrast': 1.1,
                        'saturation': 0.8
                    },
                    'color_filter': {
                        'filter_type': 'sepia',
                        'filter_intensity': 0.3
                    }
                }
            },
            'cinematic': {
                'name': 'Cinematic',
                'effects': {
                    'color_correction': {
                        'brightness': 0.8,
                        'contrast': 1.3,
                        'saturation': 0.9
                    }
                }
            },
            'bright_and_vibrant': {
                'name': 'Bright & Vibrant',
                'effects': {
                    'color_correction': {
                        'brightness': 1.2,
                        'contrast': 1.1,
                        'saturation': 1.3
                    }
                }
            },
            'black_and_white': {
                'name': 'Black & White',
                'effects': {
                    'color_correction': {
                        'saturation': 0.0
                    }
                }
            }
        }

    def get_available_effects(self) -> Dict[str, Any]:
        """Lấy danh sách hiệu ứng có sẵn"""
        return {
            'effects': self.available_effects,
            'presets': self.effect_presets
        }

    def apply_effects_to_frame(self, frame: np.ndarray, effects_config: Dict) -> np.ndarray:
        """Áp dụng hiệu ứng lên frame với real-time optimization"""
        try:
            processed_frame = frame.copy()

            # Apply effects in optimized order
            if 'color_correction' in effects_config:
                processed_frame = self._apply_color_correction(processed_frame, effects_config['color_correction'])

            if 'flip_rotate' in effects_config:
                processed_frame = self._apply_flip_rotate(processed_frame, effects_config['flip_rotate'])

            if 'blur_sharpen' in effects_config:
                processed_frame = self._apply_blur_sharpen(processed_frame, effects_config['blur_sharpen'])

            if 'color_filter' in effects_config:
                processed_frame = self._apply_color_filter(processed_frame, effects_config['color_filter'])

            # Text and logo overlays applied last
            if 'text_overlay' in effects_config:
                processed_frame = self._apply_text_overlay(processed_frame, effects_config['text_overlay'])

            if 'logo_watermark' in effects_config:
                processed_frame = self._apply_logo_watermark(processed_frame, effects_config['logo_watermark'])

            return processed_frame

        except Exception as e:
            logger.error(f"Effect application failed: {e}")
            return frame

    def _apply_color_correction(self, frame: np.ndarray, config: Dict) -> np.ndarray:
        """Áp dụng color correction"""
        import cv2

        brightness = config.get('brightness', 1.0)
        contrast = config.get('contrast', 1.0)
        saturation = config.get('saturation', 1.0)
        hue = config.get('hue', 0.0)

        # Convert to HSV for saturation and hue adjustment
        if saturation != 1.0 or hue != 0.0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
            hsv[:, :, 0] = (hsv[:, :, 0] + hue) % 180
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Apply brightness and contrast
        if brightness != 1.0 or contrast != 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=(brightness - 1) * 128)

        return frame

    def _apply_flip_rotate(self, frame: np.ndarray, config: Dict) -> np.ndarray:
        """Áp dụng flip và rotate"""
        import cv2

        # Flip operations
        if config.get('flip_horizontal', False):
            frame = cv2.flip(frame, 1)
        if config.get('flip_vertical', False):
            frame = cv2.flip(frame, 0)

        # Rotation
        rotate_angle = config.get('rotate', 0.0)
        if rotate_angle != 0.0:
            center = (frame.shape[1] // 2, frame.shape[0] // 2)
            matrix = cv2.getRotationMatrix2D(center, rotate_angle, 1.0)
            frame = cv2.warpAffine(frame, matrix, (frame.shape[1], frame.shape[0]))

        return frame

    def _apply_blur_sharpen(self, frame: np.ndarray, config: Dict) -> np.ndarray:
        """Áp dụng blur và sharpen"""
        import cv2

        blur_amount = config.get('blur_amount', 0.0)
        sharpen_amount = config.get('sharpen_amount', 0.0)

        # Apply blur
        if blur_amount > 0.0:
            kernel_size = int(blur_amount * 2) + 1  # Ensure odd number
            frame = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

        # Apply sharpen
        if sharpen_amount > 0.0:
            kernel = np.array([[-1, -1, -1],
                               [-1, 9, -1],
                               [-1, -1, -1]]) * sharpen_amount
            frame = cv2.filter2D(frame, -1, kernel)

        return frame

    def _apply_color_filter(self, frame: np.ndarray, config: Dict) -> np.ndarray:
        """Áp dụng color filter"""
        import cv2

        filter_type = config.get('filter_type', 'none')
        intensity = config.get('filter_intensity', 1.0)

        if filter_type == 'none' or intensity == 0.0:
            return frame

        if filter_type == 'grayscale':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            return cv2.addWeighted(frame, 1 - intensity, gray_bgr, intensity, 0)

        elif filter_type == 'sepia':
            # Sepia filter matrix
            sepia_filter = np.array([[0.393, 0.769, 0.189],
                                     [0.349, 0.686, 0.168],
                                     [0.272, 0.534, 0.131]])
            sepia_frame = cv2.transform(frame, sepia_filter)
            sepia_frame = np.clip(sepia_frame, 0, 255)
            return cv2.addWeighted(frame, 1 - intensity, sepia_frame, intensity, 0)

        elif filter_type == 'cool':
            # Cool filter (blue tint)
            cool_filter = np.array([[1.0, 0.0, 0.0],
                                    [0.0, 1.0, 0.0],
                                    [0.2, 0.2, 1.2]])
            cool_frame = cv2.transform(frame, cool_filter)
            cool_frame = np.clip(cool_frame, 0, 255)
            return cv2.addWeighted(frame, 1 - intensity, cool_frame, intensity, 0)

        elif filter_type == 'warm':
            # Warm filter (orange/red tint)
            warm_filter = np.array([[1.2, 0.2, 0.2],
                                    [0.0, 1.0, 0.0],
                                    [0.0, 0.0, 1.0]])
            warm_frame = cv2.transform(frame, warm_filter)
            warm_frame = np.clip(warm_frame, 0, 255)
            return cv2.addWeighted(frame, 1 - intensity, warm_frame, intensity, 0)

        return frame

    def _apply_text_overlay(self, frame: np.ndarray, config: Dict) -> np.ndarray:
        """Áp dụng text overlay"""
        import cv2

        text = config.get('text', '')
        font_size = config.get('font_size', 24)
        font_color = config.get('font_color', '#FFFFFF')
        position = config.get('position', 'top-left')

        if not text:
            return frame

        # Convert hex color to BGR
        hex_color = font_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        color_bgr = (rgb[2], rgb[1], rgb[0])

        # Calculate position
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Get text size
        text_size = cv2.getTextSize(text, font, font_size / 30, 2)[0]

        # Calculate position based on configuration
        if position == 'top-left':
            x = 10
            y = text_size[1] + 10
        elif position == 'top-right':
            x = w - text_size[0] - 10
            y = text_size[1] + 10
        elif position == 'bottom-left':
            x = 10
            y = h - 10
        elif position == 'bottom-right':
            x = w - text_size[0] - 10
            y = h - 10
        else:  # center
            x = (w - text_size[0]) // 2
            y = (h + text_size[1]) // 2

        # Add text with shadow for better visibility
        shadow_color = (0, 0, 0)
        cv2.putText(frame, text, (x + 2, y + 2), font, font_size / 30, shadow_color, 2)
        cv2.putText(frame, text, (x, y), font, font_size / 30, color_bgr, 2)

        return frame

    def _apply_logo_watermark(self, frame: np.ndarray, config: Dict) -> np.ndarray:
        """Áp dụng logo watermark"""
        import cv2
        import os

        logo_path = config.get('logo_path', '')
        logo_size = config.get('logo_size', 80)
        logo_opacity = config.get('logo_opacity', 0.8)
        logo_position = config.get('logo_position', 'top-left')

        if not logo_path or not os.path.exists(logo_path):
            return frame

        try:
            # Read logo
            logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
            if logo is None:
                return frame

            # Resize logo
            h, w = logo.shape[:2]
            aspect_ratio = w / h
            new_height = logo_size
            new_width = int(new_height * aspect_ratio)

            logo_resized = cv2.resize(logo, (new_width, new_height))

            # Calculate position
            frame_h, frame_w = frame.shape[:2]
            margin = 10

            if logo_position == 'top-right':
                x = frame_w - new_width - margin
                y = margin
            elif logo_position == 'bottom-left':
                x = margin
                y = frame_h - new_height - margin
            elif logo_position == 'bottom-right':
                x = frame_w - new_width - margin
                y = frame_h - new_height - margin
            elif logo_position == 'center':
                x = (frame_w - new_width) // 2
                y = (frame_h - new_height) // 2
            else:  # top-left
                x = margin
                y = margin

            # Ensure coordinates are within frame bounds
            x = max(0, min(x, frame_w - new_width))
            y = max(0, min(y, frame_h - new_height))

            # Blend logo with frame
            if logo_resized.shape[2] == 4:  # PNG with alpha channel
                # Extract alpha channel
                logo_rgb = logo_resized[:, :, :3]
                alpha = logo_resized[:, :, 3] / 255.0 * logo_opacity

                # Get region of interest
                roi = frame[y:y + new_height, x:x + new_width]

                # Blend using alpha
                for c in range(3):
                    roi[:, :, c] = roi[:, :, c] * (1 - alpha) + logo_rgb[:, :, c] * alpha

                frame[y:y + new_height, x:x + new_width] = roi
            else:
                # Simple overlay for non-transparent images
                roi = frame[y:y + new_height, x:x + new_width]
                cv2.addWeighted(logo_resized, logo_opacity, roi, 1 - logo_opacity, 0, roi)

            return frame

        except Exception as e:
            logger.warning(f"Logo overlay failed: {e}")
            return frame

    def create_effect_preset(self, name: str, effects: Dict) -> Dict[str, Any]:
        """Tạo effect preset mới"""
        try:
            if name in self.effect_presets:
                return {'success': False, 'error': f'Preset "{name}" already exists'}

            self.effect_presets[name] = {
                'name': name,
                'effects': effects
            }

            logger.info(f"Created effect preset: {name}")

            return {
                'success': True,
                'preset_name': name,
                'message': f'Effect preset "{name}" created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_effect_preset(self, preset_name: str) -> Dict[str, Any]:
        """Lấy effect preset"""
        preset = self.effect_presets.get(preset_name)
        if preset:
            return {'success': True, 'preset': preset}
        else:
            return {'success': False, 'error': f'Preset "{preset_name}" not found'}