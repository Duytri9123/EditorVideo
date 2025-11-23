import { log, showLoading, showStatus } from '../utils/dom-utils.js';
import api from '../../api';

export function setupProcessHandlers() {
    const brightnessSlider = document.getElementById('brightness');
    const brightnessValue = document.getElementById('brightnessValue');
    if (brightnessSlider && brightnessValue) {
        brightnessSlider.addEventListener('input', function() {
            brightnessValue.textContent = `${this.value}%`;
        });
    }

    const contrastSlider = document.getElementById('contrast');
    const contrastValue = document.getElementById('contrastValue');
    if (contrastSlider && contrastValue) {
        contrastSlider.addEventListener('input', function() {
            contrastValue.textContent = `${this.value}%`;
        });
    }

    const saturationSlider = document.getElementById('saturation');
    const saturationValue = document.getElementById('saturationValue');
    if (saturationSlider && saturationValue) {
        saturationSlider.addEventListener('input', function() {
            saturationValue.textContent = `${this.value}%`;
        });
    }

    const rotationSlider = document.getElementById('rotation');
    const rotationValue = document.getElementById('rotationValue');
    if (rotationSlider && rotationValue) {
        rotationSlider.addEventListener('input', function() {
            rotationValue.textContent = `${this.value}°`;
        });
    }

    const borderWidthSlider = document.getElementById('borderWidth');
    const borderWidthValue = document.getElementById('borderWidthValue');
    if (borderWidthSlider && borderWidthValue) {
        borderWidthSlider.addEventListener('input', function() {
            borderWidthValue.textContent = `${this.value}px`;
        });
    }

    if (window.populateFileDropdowns) populateFileDropdowns();
    log('⚙️ Process handlers initialized', 'success');
}

window.processVideo = async function() {
    const inputFile = document.getElementById('processVideo').value;
    const outputFile = document.getElementById('processOutput').value.trim() || 'video_da_xu_ly.mp4';
    const brightness = document.getElementById('brightness').value / 100;
    const contrast = document.getElementById('contrast').value / 100;
    const saturation = document.getElementById('saturation').value / 100;
    const rotation = document.getElementById('rotation').value;

    const flipHorizontal = document.getElementById('flipHorizontal') ? document.getElementById('flipHorizontal').checked : false;
    const flipVertical = document.getElementById('flipVertical') ? document.getElementById('flipVertical').checked : false;
    const logoFile = document.getElementById('processLogo') ? document.getElementById('processLogo').value : '';
    const logoPosition = document.getElementById('processLogoPosition') ? document.getElementById('processLogoPosition').value : 'top-left';
    const borderWidth = document.getElementById('borderWidth') ? document.getElementById('borderWidth').value : 0;
    const borderColor = document.getElementById('borderColor') ? document.getElementById('borderColor').value : '#ffffff';

    if (!inputFile) {
        showStatus('❌ Vui lòng chọn video để xử lý', 'error', 'processStatus');
        return;
    }

    const allFiles = [
        ...(window.currentFiles?.downloads || []),
        ...(window.currentFiles?.outputs || [])
    ];
    const existingFile = allFiles.find(file => file.name === outputFile);
    if (existingFile) {
        if (!confirm(`File "${outputFile}" đã tồn tại. Bạn có muốn ghi đè?`)) {
            return;
        }
    }

    const button = document.querySelector('#processTab .btn-primary');
    showLoading(button, true, 'Đang xử lý video...');

    const effectsConfig = {
        brightness: brightness,
        contrast: contrast,
        saturation: saturation,
        rotate: parseInt(rotation),
        flip_horizontal: flipHorizontal,
        flip_vertical: flipVertical,
        border_width: parseInt(borderWidth),
        border_color: borderColor
    };

    if (logoFile) {
        effectsConfig.logo_path = logoFile;
        effectsConfig.logo_position = logoPosition;
        effectsConfig.logo_size = 80;
        effectsConfig.logo_opacity = 0.8;
    }

    try {
        const result = await api.videoProcessing.processVideoWithEffects(inputFile, outputFile, effectsConfig);
        if (result.success) {
            showStatus(`✅ Video đã xử lý: ${result.output_name}`, 'success', 'processStatus');
            if (window.refreshFiles) refreshFiles();
        } else {
            showStatus(`❌ Xử lý thất bại: ${result.error}`, 'error', 'processStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi xử lý: ${error.message}`, 'error', 'processStatus');
    } finally {
        showLoading(button, false);
    }
};