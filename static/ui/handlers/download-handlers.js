import { log, showLoading, showStatus } from '../utils/dom-utils.js';
import api from '../../api/index.js';

export function setupDownloadHandlers() {
    const urlInput = document.getElementById('videoUrl');
    if (urlInput) {
        urlInput.addEventListener('paste', function() {
            setTimeout(() => {
                const url = this.value;
                if (url.includes('youtube.com') || url.includes('youtu.be')) {
                    const videoId = extractYouTubeId(url);
                    if (videoId) {
                        const filenameInput = document.getElementById('filename');
                        if (filenameInput && !filenameInput.value) {
                            filenameInput.value = `youtube_${videoId}.mp4`;
                        }
                    }
                }
            }, 100);
        });
        urlInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); downloadVideo(); }
        });
    }

    // Setup merge download handlers
    const videoUrlsTextarea = document.getElementById('videoUrls');
    if (videoUrlsTextarea) {
        videoUrlsTextarea.addEventListener('input', function() {
            updateUrlPreview(this.value);
        });
    }

    // Set default download mode
    switchDownloadMode('single');

    log('📥 Download handlers initialized', 'success');
}

function extractYouTubeId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
}

// Download Mode Management
export function switchDownloadMode(mode) {
    window.currentDownloadMode = mode;

    // Update mode buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-mode') === mode) {
            btn.classList.add('active');
        }
    });

    // Show/hide sections
    document.getElementById('singleDownloadSection').classList.toggle('active', mode === 'single');
    document.getElementById('mergeDownloadSection').classList.toggle('active', mode === 'merge');

    // Clear status
    document.getElementById('downloadStatus').innerHTML = '';
}

function updateUrlPreview(urlsText) {
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);

    const previewContainer = document.getElementById('urlPreviewContainer');
    const previewList = document.getElementById('urlPreview');

    if (urls.length === 0) {
        previewContainer.style.display = 'none';
        return;
    }

    previewContainer.style.display = 'block';
    previewList.innerHTML = urls.map((url, index) => `
        <div class="preview-item">
            <span class="preview-index">${index + 1}</span>
            <span class="preview-url">${getDomainFromUrl(url)}</span>
        </div>
    `).join('');
}

function getDomainFromUrl(url) {
    try {
        const domain = new URL(url).hostname;
        return domain.replace('www.', '');
    } catch {
        return url.substring(0, 30) + '...';
    }
}

// Single Video Download
window.downloadVideo = async function() {
    const url = document.getElementById('videoUrl').value.trim();
    const quality = document.getElementById('quality').value;
    let filename = document.getElementById('filename').value.trim();

    if (!url) {
        showStatus('❌ Vui lòng nhập URL video', 'error', 'downloadStatus');
        return;
    }

    if (!isValidUrl(url)) {
        showStatus('❌ Vui lòng nhập URL hợp lệ', 'error', 'downloadStatus');
        return;
    }

    if (filename) {
        if (!filename.toLowerCase().endsWith('.mp4')) {
            filename += '.mp4';
        }

        // Check if file already exists
        try {
            const files = await api.file.getFiles();
            const existingFile = files.downloads.find(file => file.name === filename);
            if (existingFile) {
                if (!confirm(`File "${filename}" đã tồn tại. Bạn có muốn ghi đè?`)) {
                    return;
                }
            }
        } catch (error) {
            console.warn('Could not check existing files:', error);
        }
    }

    const button = document.querySelector('#singleDownloadSection .btn-primary');
    showLoading(button, true, 'Đang tải...');

    try {
        showStatus('⏳ Đang tải video...', 'info', 'downloadStatus');

        const result = await api.download.downloadVideo(url, filename || undefined, quality);

        if (result.success) {
            let message = `✅ Tải xuống hoàn tất: ${result.message || 'Thành công'}`;
            if (result.downloaded_name) {
                message += ` (${result.downloaded_name})`;
            }
            showStatus(message, 'success', 'downloadStatus');

            // Clear form
            document.getElementById('videoUrl').value = '';
            document.getElementById('filename').value = '';

            // Refresh files list
            if (window.refreshFiles) {
                setTimeout(window.refreshFiles, 1000);
            }
        } else {
            let errorMsg = `❌ Tải xuống thất bại: ${result.error || 'Lỗi không xác định'}`;
            if (result.errors && result.errors.length > 0) {
                errorMsg += ` - ${result.errors.join(', ')}`;
            }
            showStatus(errorMsg, 'error', 'downloadStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi tải xuống: ${error.message}`, 'error', 'downloadStatus');
    } finally {
        showLoading(button, false);
    }
};

// Download and Merge Videos
window.downloadAndMergeVideos = async function() {
    const urlsText = document.getElementById('videoUrls').value.trim();
    const quality = document.getElementById('mergeQuality').value;
    const format = document.getElementById('mergeFormat').value;
    const filename = document.getElementById('mergeFilename').value.trim() || `merged_video_${Date.now()}.${format}`;
    const transitionType = document.getElementById('transitionType').value;
    const autoMerge = document.getElementById('autoMerge').checked;
    const keepOriginals = document.getElementById('keepOriginals').checked;

    if (!urlsText) {
        showStatus('❌ Vui lòng nhập ít nhất một URL video', 'error', 'downloadStatus');
        return;
    }

    // Parse URLs
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0 && isValidUrl(url));

    if (urls.length === 0) {
        showStatus('❌ Không có URL hợp lệ', 'error', 'downloadStatus');
        return;
    }

    if (urls.length === 1) {
        showStatus('⚠️ Chỉ có một URL. Sử dụng chế độ tải video đơn để hiệu quả hơn.', 'warning', 'downloadStatus');
        return;
    }

    const button = document.querySelector('#mergeDownloadSection .btn-primary');
    const progressContainer = document.getElementById('mergeProgress');
    const progressFill = document.getElementById('mergeProgressFill');
    const progressText = document.getElementById('mergeProgressText');
    const progressStage = document.getElementById('mergeStage');
    const progressPercent = document.getElementById('mergePercent');

    showLoading(button, true, 'Đang xử lý...');
    progressContainer.style.display = 'block';

    try {
        let downloadedVideos = [];
        let successCount = 0;
        let failCount = 0;

        showStatus(`⏳ Bắt đầu tải ${urls.length} video...`, 'info', 'downloadStatus');
        progressStage.textContent = 'Đang tải video...';

        // Download phase
        for (let i = 0; i < urls.length; i++) {
            const url = urls[i];

            // Update progress
            const downloadProgress = ((i + 1) / urls.length) * 100;
            progressFill.style.width = downloadProgress + '%';
            progressPercent.textContent = Math.round(downloadProgress) + '%';
            progressText.textContent = `Đang tải video ${i + 1}/${urls.length}: ${getDomainFromUrl(url)}`;

            try {
                showStatus(`⏳ Đang tải video ${i + 1}/${urls.length}...`, 'info', 'downloadStatus');

                // Download individual video
                const tempFilename = `temp_video_${i + 1}_${Date.now()}.${format}`;
                const result = await api.download.downloadVideo(url, tempFilename, quality);

                if (result.success) {
                    downloadedVideos.push({
                        name: result.downloaded_name || tempFilename,
                        url: url,
                        duration: result.duration || 0,
                        quality: quality
                    });
                    successCount++;
                    log(`✅ Đã tải: ${url}`, 'success');
                } else {
                    failCount++;
                    log(`❌ Lỗi tải: ${url} - ${result.error}`, 'error');
                }
            } catch (error) {
                failCount++;
                log(`❌ Lỗi tải ${url}: ${error.message}`, 'error');
            }
        }

        // Merge phase if auto-merge is enabled and we have videos
        if (autoMerge && downloadedVideos.length > 0) {
            showStatus(`⏳ Đang ghép ${downloadedVideos.length} video...`, 'info', 'downloadStatus');
            progressStage.textContent = 'Đang ghép video...';
            progressText.textContent = `Đang ghép ${downloadedVideos.length} video...`;

            try {
                // Call merge API
                const videoPaths = downloadedVideos.map(video => video.name);
                const mergeResult = await api.process.mergeVideos(videoPaths, filename, {
                    transition: transitionType,
                    keepOriginals: keepOriginals
                });

                if (mergeResult.success) {
                    const totalDuration = downloadedVideos.reduce((sum, video) => sum + (video.duration || 0), 0);

                    showStatus(`✅ Đã ghép thành công ${downloadedVideos.length} video thành: ${filename}`, 'success', 'downloadStatus');

                    // Clean up temporary files if not keeping originals
                    if (!keepOriginals) {
                        for (const video of downloadedVideos) {
                            try {
                                await api.file.deleteFile(video.name);
                            } catch (error) {
                                console.warn(`Could not delete temporary file: ${video.name}`, error);
                            }
                        }
                        setTimeout(() => {
                            showStatus('🗑️ Đã dọn dẹp file tạm', 'info', 'downloadStatus');
                        }, 1000);
                    }
                } else {
                    showStatus(`❌ Lỗi ghép video: ${mergeResult.error}`, 'error', 'downloadStatus');
                }
            } catch (error) {
                showStatus(`❌ Lỗi ghép video: ${error.message}`, 'error', 'downloadStatus');
            }
        } else if (downloadedVideos.length > 0) {
            showStatus(`✅ Đã tải ${successCount} video thành công (${failCount} lỗi)`, 'success', 'downloadStatus');
        } else {
            showStatus('❌ Không có video nào được tải thành công', 'error', 'downloadStatus');
        }

        // Refresh files list
        if (window.refreshFiles) {
            setTimeout(window.refreshFiles, 1000);
        }

    } catch (error) {
        showStatus(`❌ Lỗi quá trình tải và ghép: ${error.message}`, 'error', 'downloadStatus');
    } finally {
        showLoading(button, false);
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressFill.style.width = '0%';
            progressPercent.textContent = '0%';
        }, 5000);
    }
};

// Helper function to validate URL
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}