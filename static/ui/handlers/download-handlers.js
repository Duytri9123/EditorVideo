import { log, showLoading, showStatus } from '../utils/dom-utils.js';

// Biến toàn cục để theo dõi tiến trình
const downloadProgress = new Map();

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
            if (e.key === 'Enter') { 
                e.preventDefault(); 
                downloadSingleVideo(); 
            }
        });
    }

    // Setup merge download handlers
    const videoUrlsTextarea = document.getElementById('videoUrls');
    if (videoUrlsTextarea) {
        videoUrlsTextarea.addEventListener('input', function() {
            updateUrlPreview(this.value);
        });
    }

    log('📥 Download handlers initialized', 'success');
}

function extractYouTubeId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
}

function updateUrlPreview(urlsText) {
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);

    const previewContainer = document.getElementById('urlPreviewContainer');
    const previewList = document.getElementById('urlPreview');

    if (urls.length === 0) {
        if (previewContainer) previewContainer.style.display = 'none';
        return;
    }

    if (previewContainer && previewList) {
        previewContainer.style.display = 'block';
        previewList.innerHTML = urls.map((url, index) => `
            <div class="preview-item">
                <span class="preview-index">${index + 1}</span>
                <span class="preview-url">${getDomainFromUrl(url)}</span>
            </div>
        `).join('');
    }
}

function getDomainFromUrl(url) {
    try {
        const domain = new URL(url).hostname;
        return domain.replace('www.', '');
    } catch {
        return url.substring(0, 30) + '...';
    }
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    if (!seconds || seconds < 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Function to trigger browser download
function triggerBrowserDownload(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Update progress display với dữ liệu thực từ server
function updateProgress(progressData, elementPrefix = 'download') {
    const progressContainer = document.getElementById(`${elementPrefix}Progress`);
    const progressFill = document.getElementById(`${elementPrefix}ProgressFill`);
    const progressText = document.getElementById(`${elementPrefix}ProgressText`);
    const progressStage = document.getElementById(`${elementPrefix}Stage`);
    const progressPercent = document.getElementById(`${elementPrefix}Percent`);
    const progressSize = document.getElementById(`${elementPrefix}Size`);
    const progressSpeed = document.getElementById(`${elementPrefix}Speed`);
    const progressETA = document.getElementById(`${elementPrefix}ETA`);
    const progressTime = document.getElementById(`${elementPrefix}Time`);

    if (progressContainer) progressContainer.style.display = 'block';
    
    const percent = progressData.percent || 0;
    if (progressFill) progressFill.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = Math.round(percent) + '%';
    
    if (progressText) progressText.textContent = progressData.text || progressData.stage || '';
    if (progressStage) progressStage.textContent = progressData.stage || '';
    
    if (progressSize && progressData.downloaded_bytes !== undefined && progressData.total_bytes) {
        progressSize.textContent = `${formatFileSize(progressData.downloaded_bytes)} / ${formatFileSize(progressData.total_bytes)}`;
    } else if (progressSize && progressData.size) {
        progressSize.textContent = formatFileSize(progressData.size);
    }
    
    if (progressSpeed && progressData.speed) {
        progressSpeed.textContent = `${formatFileSize(progressData.speed)}/s`;
    }
    
    if (progressETA && progressData.eta) {
        progressETA.textContent = formatTime(progressData.eta);
    }

    // Hiển thị thời gian đã trôi qua
    if (progressTime && progressData.start_time) {
        const elapsed = Math.floor((Date.now() / 1000) - progressData.start_time);
        progressTime.textContent = formatTime(elapsed);
    }
}

// Hàm polling để kiểm tra tiến trình từ server
async function pollDownloadProgress(downloadId, elementPrefix, onComplete, onError) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${downloadId}`);
            const result = await response.json();
            
            if (result.success && result.progress) {
                const progress = result.progress;
                updateProgress(progress, elementPrefix);
                
                if (progress.status === 'completed') {
                    clearInterval(pollInterval);
                    onComplete(progress);
                } else if (progress.status === 'error') {
                    clearInterval(pollInterval);
                    onError(progress.error || 'Lỗi không xác định từ server');
                }
            }
        } catch (error) {
            log(`❌ Error polling progress: ${error.message}`, 'error');
            // Tiếp tục poll trừ khi lỗi quá nặng
        }
    }, 1500);
    
    return pollInterval;
}

// Single Video Download với Progress Tracking thực tế
export async function downloadSingleVideo() {
    const url = document.getElementById('videoUrl')?.value.trim();
    const quality = document.getElementById('quality')?.value || 'best';
    const format = document.getElementById('format')?.value || 'mp4';
    let filename = document.getElementById('filename')?.value.trim();

    if (!url) {
        showStatus('❌ Vui lòng nhập URL video', 'error', 'downloadStatus');
        return;
    }

    if (!isValidUrl(url)) {
        showStatus('❌ URL không hợp lệ', 'error', 'downloadStatus');
        return;
    }

    // Auto add extension if needed
    if (filename && !filename.toLowerCase().endsWith(`.${format}`)) {
        filename += `.${format}`;
    }

    const button = document.querySelector('#singleDownloadSection .btn-primary');
    showLoading(button, true, 'Đang khởi tạo...');

    try {
        showStatus('⏳ Đang yêu cầu máy chủ tải video...', 'info', 'downloadStatus');

        // Gọi API download (API này sẽ trả về ngay lập tức với download_id)
        const response = await fetch('/api/download-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                filename: filename,
                quality: quality,
                format: format,
                target_dir: document.getElementById('targetDir')?.value.trim()
            })
        });

        const result = await response.json();

        if (result.success && result.download_id) {
            const downloadId = result.download_id;
            
            // Bắt đầu polling tiến trình thực tế
            pollDownloadProgress(
                downloadId, 
                'download',
                async (finalProgress) => {
                    // Khi hoàn thành
                    const finalFilename = finalProgress.filename;
                    
                    try {
                        // Tải file về máy nếu không có target_dir
                        const targetDir = document.getElementById('targetDir')?.value.trim();
                        if (!targetDir) {
                            const fileResponse = await fetch(`/api/files/${finalFilename}`);
                            const blob = await fileResponse.blob();
                            triggerBrowserDownload(blob, finalFilename);
                            
                            let message = `✅ Đã tải xuống thành công: ${finalFilename}`;
                            if (finalProgress.size) {
                                message += ` (${formatFileSize(finalProgress.size)})`;
                            }
                            showStatus(message, 'success', 'downloadStatus');
                        } else {
                            let message = `✅ Video đã được lưu vào: ${targetDir}\\${finalFilename}`;
                            showStatus(message, 'success', 'downloadStatus');
                            log(`📂 File saved localy to ${targetDir}`, 'success');
                        }
                    } catch (err) {
                        showStatus(`❌ Lỗi khi lưu file: ${err.message}`, 'error', 'downloadStatus');
                    }

                    showLoading(button, false);
                    
                    // Clear form
                    const urlInput = document.getElementById('videoUrl');
                    if (urlInput) urlInput.value = '';

                    // Ẩn progress sau 5 giây
                    setTimeout(() => {
                        const progressContainer = document.getElementById('downloadProgress');
                        if (progressContainer) progressContainer.style.display = 'none';
                    }, 5000);
                },
                (errorMessage) => {
                    // Khi có lỗi
                    showStatus(`❌ Tải xuống thất bại: ${errorMessage}`, 'error', 'downloadStatus');
                    showLoading(button, false);
                }
            );

        } else {
            showStatus(`❌ Không thể bắt đầu tải: ${result.error || 'Lỗi không xác định'}`, 'error', 'downloadStatus');
            showLoading(button, false);
        }

    } catch (error) {
        showStatus(`❌ Lỗi hệ thống: ${error.message}`, 'error', 'downloadStatus');
        showLoading(button, false);
    }
}

// Download and Merge Videos với Progress Tracking
export async function downloadAndMergeVideos() {
    const urlsText = document.getElementById('videoUrls')?.value.trim();
    const quality = document.getElementById('mergeQuality')?.value || 'best';
    const format = document.getElementById('mergeFormat')?.value || 'mp4';
    let filename = document.getElementById('mergeFilename')?.value.trim();
    const transitionType = document.getElementById('transitionType')?.value || 'none';
    const autoMerge = document.getElementById('autoMerge')?.checked || false;
    const keepOriginals = document.getElementById('keepOriginals')?.checked || false;

    if (!urlsText) {
        showStatus('❌ Vui lòng nhập ít nhất một URL video', 'error', 'downloadStatus');
        return;
    }

    const urls = urlsText.split('\n').map(u => u.trim()).filter(u => u.length > 0);
    if (urls.length === 0) return;

    if (!filename) {
        filename = `merged_video_${Date.now()}.${format}`;
    } else if (!filename.toLowerCase().endsWith(`.${format}`)) {
        filename += `.${format}`;
    }

    const button = document.querySelector('#mergeDownloadSection .btn-primary');
    showLoading(button, true, 'Đang xử lý...');

    const startTime = Date.now();
    let downloadedVideos = [];
    let successCount = 0;
    let failCount = 0;

    try {
        showStatus(`⏳ Bắt đầu tải ${urls.length} video...`, 'info', 'downloadStatus');

        for (let i = 0; i < urls.length; i++) {
                const response = await fetch('/api/download-video', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        url: urls[i], 
                        quality, 
                        format,
                        target_dir: '' // Luôn tải vào temp trước khi gộp
                    })
                });

            const startResult = await response.json();
            if (startResult.success && startResult.download_id) {
                const finalProgress = await new Promise((resolve, reject) => {
                    pollDownloadProgress(startResult.download_id, 'merge', resolve, reject);
                });
                
                if (finalProgress && finalProgress.filename) {
                    console.log(`✅ Video ${i+1} downloaded: ${finalProgress.filename}`);
                    downloadedVideos.push({ name: finalProgress.filename });
                    successCount++;
                } else {
                    console.warn(`⚠️ Video ${i+1} completed but filename is missing`, finalProgress);
                    failCount++;
                }
            } else {
                failCount++;
            }

            updateProgress({
                percent: ((i + 1) / urls.length) * 50,
                text: `Đã tải xong ${i + 1}/${urls.length} video`,
                stage: 'Đang tải danh sách video',
                start_time: startTime / 1000
            }, 'merge');
        }

        console.log(`📊 Total downloaded for merge: ${downloadedVideos.length}`, downloadedVideos);

        if (autoMerge && downloadedVideos.length > 1) {
            updateProgress({ percent: 75, text: 'Đang ghép video...', stage: 'Đang ghép video', start_time: startTime / 1000 }, 'merge');
            
            const mergeTargetDir = document.getElementById('mergeTargetDir')?.value.trim();
            const mergeResponse = await fetch('/api/merge-videos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    video_urls: downloadedVideos.map(v => v.name), 
                    filename: filename,
                    target_dir: mergeTargetDir
                })
            });
            const mergeResult = await mergeResponse.json();
            if (mergeResult.success) {
                if (!mergeTargetDir) {
                    const fileResponse = await fetch(`/api/files/${mergeResult.filename}`);
                    triggerBrowserDownload(await fileResponse.blob(), mergeResult.filename);
                    showStatus(`✅ Đã ghép thành công: ${filename}`, 'success', 'downloadStatus');
                } else {
                    showStatus(`✅ Đã ghép và lưu vào: ${mergeTargetDir}\\${mergeResult.filename}`, 'success', 'downloadStatus');
                }
            } else {
                showStatus(`❌ Lỗi ghép video: ${mergeResult.error}`, 'error', 'downloadStatus');
            }
        } else {
            for (const video of downloadedVideos) {
                const fileResponse = await fetch(`/api/files/${video.name}`);
                triggerBrowserDownload(await fileResponse.blob(), video.name);
            }
            showStatus(`✅ Đã tải ${successCount} video thành công`, 'success', 'downloadStatus');
        }

        setTimeout(() => {
            const container = document.getElementById('mergeProgress');
            if (container) container.style.display = 'none';
        }, 5000);

    } catch (error) {
        showStatus(`❌ Lỗi: ${error.message}`, 'error', 'downloadStatus');
    } finally {
        showLoading(button, false);
    }
}

// Export functions for global access
window.downloadSingleVideo = downloadSingleVideo;
window.downloadAndMergeVideos = downloadAndMergeVideos;