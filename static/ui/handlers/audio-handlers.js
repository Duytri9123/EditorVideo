import { log, showLoading, showStatus } from '../utils/dom-utils.js';
import api from '../../api';

export function setupAudioHandlers() {
    if (window.populateFileDropdowns) populateFileDropdowns();
    log('🎵 Audio handlers initialized', 'success');
}

window.downloadAudioFromUrl = async function() {
    const audioUrl = document.getElementById('audioUrl').value.trim();
    const format = document.getElementById('audioFormat').value;
    const quality = document.getElementById('audioQuality').value;
    let filename = document.getElementById('audioFilename').value.trim();

    if (!audioUrl) {
        showStatus('❌ Vui lòng nhập URL video', 'error', 'audioStatus');
        return;
    }

    if (!api.isValidUrl(audioUrl)) {
        showStatus('❌ Vui lòng nhập URL hợp lệ', 'error', 'audioStatus');
        return;
    }

    if (filename) {
        if (!filename.toLowerCase().endsWith(`.${format}`)) {
            filename += `.${format}`;
        }

        const allFiles = [
            ...(window.currentFiles?.downloads || []),
            ...(window.currentFiles?.music || [])
        ];
        const existingFile = allFiles.find(file => file.name === filename);
        if (existingFile) {
            if (!confirm(`File "${filename}" đã tồn tại. Bạn có muốn ghi đè?`)) {
                return;
            }
        }
    }

    const button = document.querySelector('#audioTab .btn-primary');
    showLoading(button, true, 'Đang tải âm thanh...');

    try {
        const result = await api.download.downloadAudio(audioUrl, filename || undefined, format, quality);
        if (result.success) {
            showStatus(`✅ Âm thanh đã tải: ${result.file.name}`, 'success', 'audioStatus');
            if (window.refreshFiles) refreshFiles();
        } else {
            showStatus(`❌ Tải thất bại: ${result.error}`, 'error', 'audioStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi tải: ${error.message}`, 'error', 'audioStatus');
    } finally {
        showLoading(button, false);
    }
};

window.extractAudio = async function() {
    const videoFile = document.getElementById('audioSource').value;
    const outputFile = document.getElementById('audioOutput').value.trim() || 'am_thanh_trich_xuat.mp3';

    if (!videoFile) {
        showStatus('❌ Vui lòng chọn file video', 'error', 'audioStatus');
        return;
    }

    const allFiles = [
        ...(window.currentFiles?.downloads || []),
        ...(window.currentFiles?.outputs || []),
        ...(window.currentFiles?.music || [])
    ];
    const existingFile = allFiles.find(file => file.name === outputFile);
    if (existingFile) {
        if (!confirm(`File "${outputFile}" đã tồn tại. Bạn có muốn ghi đè?`)) {
            return;
        }
    }

    const button = document.querySelector('#audioTab .btn-primary');
    showLoading(button, true, 'Đang trích xuất âm thanh...');

    try {
        const result = await api.videoProcessing.extractAudioFromVideo(videoFile, outputFile);
        if (result.success) {
            showStatus(`✅ Âm thanh đã trích xuất: ${result.output_name}`, 'success', 'audioStatus');
            if (window.refreshFiles) refreshFiles();
        } else {
            showStatus(`❌ Trích xuất thất bại: ${result.error}`, 'error', 'audioStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi trích xuất: ${error.message}`, 'error', 'audioStatus');
    } finally {
        showLoading(button, false);
    }
};