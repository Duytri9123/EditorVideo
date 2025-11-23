import { log, showLoading, showStatus } from '../utils/dom-utils.js';
import api from '../../api';

export function setupYouTubeHandlers() {
    const titleInput = document.getElementById('youtubeTitle');
    if (titleInput) {
        titleInput.addEventListener('focus', function() {
            if (!this.value) {
                const uploadSelect = document.getElementById('youtubeVideo');
                if (uploadSelect && uploadSelect.value) {
                    const filename = uploadSelect.options[uploadSelect.selectedIndex].text;
                    this.value = filename.replace(/\.[^/.]+$/, "").replace(/[_-]/g, ' ');
                }
            }
        });
    }
    if (window.populateFileDropdowns) populateFileDropdowns();
    log('☁️ YouTube handlers initialized', 'success');
}

window.uploadToYouTube = async function() {
    const videoFile = document.getElementById('youtubeVideo').value;
    const title = document.getElementById('youtubeTitle').value.trim();
    const description = document.getElementById('youtubeDescription').value.trim();
    const privacy = document.getElementById('youtubePrivacy').value;

    if (!videoFile) {
        showStatus('❌ Vui lòng chọn video để upload', 'error', 'youtubeStatus');
        return;
    }
    if (!title) {
        showStatus('❌ Vui lòng nhập tiêu đề video', 'error', 'youtubeStatus');
        return;
    }

    const button = document.querySelector('#youtubeTab .btn-primary');
    showLoading(button, true, 'Đang upload lên YouTube...');

    try {
        const result = await api.youtube.uploadToYouTube(videoFile, title, description, privacy);
        if (result.success) {
            showStatus(`✅ Video đã upload thành công! Video ID: ${result.video_id}`, 'success', 'youtubeStatus');
        } else {
            showStatus(`❌ Upload thất bại: ${result.error}`, 'error', 'youtubeStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi upload: ${error.message}`, 'error', 'youtubeStatus');
    } finally {
        showLoading(button, false);
    }
};

window.startBatchUpload = async function() {
    const urlsText = document.getElementById('autoUrls').value.trim();
    const titleTemplate = document.getElementById('autoTitle').value.trim() || 'Video {number}';
    const descriptionTemplate = document.getElementById('autoDescription').value.trim();
    const privacy = document.getElementById('autoPrivacy').value;
    const logoPath = document.getElementById('youtubeLogo').value || null;
    const audioPath = document.getElementById('youtubeAudio').value || null;
    const autoProcess = document.getElementById('autoProcess').checked;

    if (!urlsText) {
        showStatus('❌ Vui lòng nhập ít nhất một URL video', 'error', 'youtubeStatus');
        return;
    }

    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0 && api.isValidUrl(url));

    if (urls.length === 0) {
        showStatus('❌ Vui lòng nhập ít nhất một URL video hợp lệ', 'error', 'youtubeStatus');
        return;
    }

    const invalidUrls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0 && !api.isValidUrl(url));

    if (invalidUrls.length > 0) {
        showStatus(`❌ URL không hợp lệ: ${invalidUrls.join(', ')}`, 'error', 'youtubeStatus');
        return;
    }

    const button = document.querySelector('#youtubeTab .btn-secondary');
    const progressContainer = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    showLoading(button, true, 'Bắt đầu upload tự động...');
    if (progressContainer) progressContainer.style.display = 'block';

    try {
        window.globalProgress.reset();
        window.globalProgress.total = urls.length;

        const result = await api.download.batchUploadToYouTube(urls, titleTemplate, descriptionTemplate, privacy, logoPath, { audio: audioPath, autoProcess });

        if (result.success) {
            const successCount = result.summary?.success || 0;
            const total = result.summary?.total || urls.length;
            const message = `✅ Upload tự động hoàn tất! Thành công: ${successCount}/${total}`;
            showStatus(message, 'success', 'youtubeStatus');

            showBatchUploadResults(result.results || []);
            if (window.refreshFiles) refreshFiles();
        } else {
            showStatus(`❌ Upload tự động thất bại: ${result.error}`, 'error', 'youtubeStatus');
        }

    } catch (error) {
        showStatus(`❌ Lỗi upload tự động: ${error.message}`, 'error', 'youtubeStatus');
    } finally {
        showLoading(button, false);
        setTimeout(() => {
            if (progressContainer) progressContainer.style.display = 'none';
            if (progressFill) progressFill.style.width = '0%';
        }, 5000);
    }
};

function showBatchUploadResults(results) {
    const statusElement = document.getElementById('youtubeStatus');
    if (!statusElement || !results.length) return;

    let detailsHtml = '<div style="margin-top: 10px; font-size: 12px; max-height: 200px; overflow-y: auto; border: 1px solid #334155; padding: 10px; border-radius: 4px;">';
    detailsHtml += '<strong>Kết quả chi tiết:</strong><br><br>';

    results.forEach((result, index) => {
        const statusIcon = result.status === 'success' ? '✅' : '❌';
        const shortUrl = result.url.length > 40 ? result.url.substring(0, 40) + '...' : result.url;

        detailsHtml += `<div style="margin-bottom: 8px; padding: 5px; background: ${result.status === 'success' ? '#10b98120' : '#ef444420'}; border-radius: 3px;">`;
        detailsHtml += `<strong>${statusIcon} URL ${index + 1}:</strong> ${shortUrl}<br>`;
        detailsHtml += `<small>Trạng thái: ${result.step || result.status}`;

        if (result.status === 'success') {
            detailsHtml += ` → ${result.title}`;
            if (result.youtube_url) {
                detailsHtml += ` (<a href="${result.youtube_url}" target="_blank">Xem</a>)`;
            }
        } else if (result.error) {
            detailsHtml += ` → ${result.error}`;
        }

        detailsHtml += '</small></div>';
    });

    detailsHtml += '</div>';
    statusElement.innerHTML += detailsHtml;
}