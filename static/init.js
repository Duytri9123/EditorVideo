// init.js - Enhanced Initialization for 15-minute videos
import TimelineEngine from './timeline/TimelineEngine';

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Video Tool Pro for 15-minute videos...');

    // Khởi tạo timeline engine
    window.timelineEngine = new TimelineEngine();

    setupGlobalTimelineEvents();
    setupTimelineIntegration();
    initializePanelStates();

    window.addEventListener('beforeunload', () => {
        if (window.timelineEngine) {
            window.timelineEngine.cleanup();
        }
    });

    console.log('✅ Timeline Engine fully initialized for 15-minute videos');
});

function setupGlobalTimelineEvents() {
    document.addEventListener('dblclick', (e) => {
        if (e.target.closest('.timeline-clip')) {
            const clipId = e.target.closest('.timeline-clip').dataset.clipId;
            if (clipId && window.timelineEngine) {
                window.timelineEngine.previewClip(clipId);
            }
        }

        if (e.target.closest('.timeline-track') && !e.target.closest('.timeline-clip')) {
            if (window.timelineEngine && window.timelineEngine.timelineTrack) {
                const rect = window.timelineEngine.timelineTrack.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const time = (x / rect.width) * window.timelineEngine.totalDuration;
                window.timelineEngine.playheadPosition = time;
                window.timelineEngine.ui.updatePlayhead();
                window.timelineEngine.showInfo(`Jumped to ${window.timelineEngine.utils.formatTime(time)}`);
            }
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === ' ' && !e.target.matches('input, textarea, select')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.toggleTimelinePlayback();
            }
        }

        if (e.key === 'Escape') {
            if (window.timelineEngine) {
                window.timelineEngine.stopPreview();
                window.timelineEngine.selectedClipId = null;
                if (window.timelineEngine.ui) {
                    window.timelineEngine.ui.hideClipProperties();
                }
            }
        }

        if (e.key === 'Delete' && window.timelineEngine && window.timelineEngine.selectedClipId) {
            window.timelineEngine.removeFromTimeline(window.timelineEngine.selectedClipId);
        }

        if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && window.timelineEngine && window.timelineEngine.selectedClipId) {
            e.preventDefault();
            const direction = e.key === 'ArrowLeft' ? 'left' : 'right';
            if (window.timelineEngine.controls) {
                window.timelineEngine.controls.moveClipTime(window.timelineEngine.selectedClipId, direction);
            }
        }

        if ((e.key === '+' || e.key === '-') && window.timelineEngine && window.timelineEngine.selectedClipId) {
            e.preventDefault();
            const speedChange = e.key === '+' ? 0.1 : -0.1;
            if (window.timelineEngine.controls) {
                window.timelineEngine.controls.adjustClipSpeed(window.timelineEngine.selectedClipId, speedChange);
            }
        }

        if (e.ctrlKey && (e.key === '=' || e.key === '-')) {
            e.preventDefault();
            if (e.key === '=') {
                window.timelineEngine?.zoomIn();
            } else {
                window.timelineEngine?.zoomOut();
            }
        }

        if (e.key === 'i' && window.timelineEngine) {
            e.preventDefault();
            // Mark in point
        }

        if (e.key === 'o' && window.timelineEngine) {
            e.preventDefault();
            // Mark out point
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target.closest('.play-timeline-btn') || e.target.closest('#timelinePlayPause')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.toggleTimelinePlayback();
                updateTimelinePlayButton();
            }
        }

        if (e.target.closest('.seek-start-btn')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.seekToStart();
            }
        }

        if (e.target.closest('.seek-end-btn')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.seekToEnd();
            }
        }

        if (e.target.closest('[onclick*="zoomIn"]')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.zoomIn();
            }
        }

        if (e.target.closest('[onclick*="zoomOut"]')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.zoomOut();
            }
        }

        if (e.target.closest('[onclick*="fitTimeline"]')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.fitTimeline();
            }
        }

        if (e.target.closest('[onclick*="toggleSnap"]')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.toggleSnap();
                updateSnapButton();
            }
        }

        if (e.target.closest('[onclick*="splitAtPlayhead"]')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.splitAtPlayhead();
            }
        }

        if (e.target.closest('[onclick*="exportTimeline"]')) {
            e.preventDefault();
            if (window.timelineEngine) {
                window.timelineEngine.exportTimeline();
            }
        }

        if (e.target.closest('.add-image-btn')) {
            e.preventDefault();
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.onchange = (event) => {
                const file = event.target.files[0];
                if (file) {
                    const url = URL.createObjectURL(file);
                    window.timelineEngine.addImageToTimeline(url, 10, 0, file.name);
                }
            };
            fileInput.click();
        }
    });

    window.addEventListener('resize', debounce(() => {
        if (window.timelineEngine) {
            window.timelineEngine.calculateTotalDuration();
            if (window.timelineEngine.ui) {
                window.timelineEngine.ui.generateTimelineRuler();
                window.timelineEngine.ui.updatePlayhead();
            }
        }
    }, 250));

    document.addEventListener('click', (e) => {
        if (e.target.closest('.panel-toggle')) {
            setTimeout(updateContentGridLayout, 100);
        }
    });
}

function setupTimelineIntegration() {
    // Override loadFiles để cập nhật source files trong timeline
    const originalLoadFiles = window.loadFiles;
    if (originalLoadFiles) {
        window.loadFiles = async function() {
            await originalLoadFiles();
            if (window.timelineEngine && window.timelineEngine.ui) {
                setTimeout(() => {
                    window.timelineEngine.ui.updateSourceFiles();
                }, 100);
            }
        };
    }

    window.addFileToTimeline = function(filePath, fileType = 'auto') {
        const allFiles = [
            ...(window.currentFiles?.downloads || []),
            ...(window.currentFiles?.outputs || []),
            ...(window.currentFiles?.music || []),
            ...(window.currentFiles?.logos || [])
        ];
        const fileData = allFiles.find(file => file.path === filePath);

        if (fileData) {
            if (window.timelineEngine) {
                let actualType = fileType;
                if (fileType === 'auto') {
                    if (fileData.name.match(/\.(mp3|wav|aac|m4a|ogg)$/i)) {
                        actualType = 'audio';
                    } else if (fileData.name.match(/\.(png|jpg|jpeg|gif|bmp|webp|svg)$/i)) {
                        actualType = 'image';
                    } else {
                        actualType = 'video';
                    }
                }

                switch (actualType) {
                    case 'audio':
                        if (window.timelineEngine.addAudioToTimeline) {
                            window.timelineEngine.addAudioToTimeline(filePath, fileData.name);
                        }
                        break;
                    case 'image':
                        if (window.timelineEngine.addImageToTimeline) {
                            window.timelineEngine.addImageToTimeline(filePath, 10, 0, fileData.name);
                        }
                        break;
                    default:
                        if (window.timelineEngine.addToTimeline) {
                            window.timelineEngine.addToTimeline(filePath, 0, null, fileData.name);
                        }
                }
                console.log(`✅ Added "${fileData.name}" to timeline as ${actualType}`);
            } else {
                console.error('❌ Timeline engine not initialized');
            }
        } else {
            console.error('❌ File not found');
        }
    };

    window.clearTimeline = function() {
        if (window.timelineEngine && window.timelineEngine.clearTimeline) {
            window.timelineEngine.clearTimeline();
        }
    };

    window.exportTimelineProject = function() {
        if (window.timelineEngine && window.timelineEngine.exportTimeline) {
            window.timelineEngine.exportTimeline();
        }
    };

    window.addImageToTimeline = function(filePath, duration = 10, startTime = 0) {
        if (window.timelineEngine && window.timelineEngine.addImageToTimeline) {
            window.timelineEngine.addImageToTimeline(filePath, duration, startTime);
        }
    };
}

function initializePanelStates() {
    const rightPanelToggle = document.querySelector('[data-panel="right"]');
    if (rightPanelToggle) {
        rightPanelToggle.classList.remove('active');
    }

    const rightPanel = document.getElementById('rightPanel');
    if (rightPanel) {
        rightPanel.classList.add('hidden');
    }

    updateContentGridLayout();
}

function updateContentGridLayout() {
    const contentGrid = document.querySelector('.content-grid');
    const leftPanel = document.getElementById('leftPanel');
    const rightPanel = document.getElementById('rightPanel');

    if (!contentGrid) return;

    contentGrid.classList.remove('left-hidden', 'right-hidden', 'both-hidden');

    const leftHidden = leftPanel && leftPanel.classList.contains('hidden');
    const rightHidden = rightPanel && rightPanel.classList.contains('hidden');

    if (leftHidden && rightHidden) {
        contentGrid.classList.add('both-hidden');
    } else if (leftHidden) {
        contentGrid.classList.add('left-hidden');
    } else if (rightHidden) {
        contentGrid.classList.add('right-hidden');
    }
}

function updateTimelinePlayButton() {
    const playButton = document.getElementById('timelinePlayPause');
    if (!playButton || !window.timelineEngine) return;

    if (window.timelineEngine.isPlaying) {
        playButton.innerHTML = '<i class="fas fa-pause"></i> Tạm dừng';
        playButton.classList.add('playing');
    } else {
        playButton.innerHTML = '<i class="fas fa-play"></i> Phát';
        playButton.classList.remove('playing');
    }
}

function updateSnapButton() {
    const snapButton = document.getElementById('snapToggle');
    const timelineSnapButton = document.getElementById('timelineSnapToggle');

    if (!window.timelineEngine) return;

    const isActive = window.timelineEngine.snapToGrid;

    if (snapButton) {
        if (isActive) {
            snapButton.classList.add('active');
            snapButton.title = 'Snap: ON';
        } else {
            snapButton.classList.remove('active');
            snapButton.title = 'Snap: OFF';
        }
    }

    if (timelineSnapButton) {
        if (isActive) {
            timelineSnapButton.classList.add('active');
            timelineSnapButton.title = 'Snap: ON';
        } else {
            timelineSnapButton.classList.remove('active');
            timelineSnapButton.title = 'Snap: OFF';
        }
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Global functions
window.toggleTimelinePlayback = () => {
    if (window.timelineEngine && window.timelineEngine.toggleTimelinePlayback) {
        window.timelineEngine.toggleTimelinePlayback();
        updateTimelinePlayButton();
    }
};

window.seekToStart = () => {
    if (window.timelineEngine && window.timelineEngine.seekToStart) {
        window.timelineEngine.seekToStart();
    }
};

window.seekToEnd = () => {
    if (window.timelineEngine && window.timelineEngine.seekToEnd) {
        window.timelineEngine.seekToEnd();
    }
};

window.clearTimeline = () => {
    if (window.timelineEngine && window.timelineEngine.clearTimeline) {
        window.timelineEngine.clearTimeline();
    }
};

window.exportTimeline = () => {
    if (window.timelineEngine && window.timelineEngine.exportTimeline) {
        window.timelineEngine.exportTimeline();
    }
};

window.zoomInTimeline = () => {
    if (window.timelineEngine && window.timelineEngine.zoomIn) {
        window.timelineEngine.zoomIn();
    }
};

window.zoomOutTimeline = () => {
    if (window.timelineEngine && window.timelineEngine.zoomOut) {
        window.timelineEngine.zoomOut();
    }
};

window.toggleSnap = () => {
    if (window.timelineEngine && window.timelineEngine.toggleSnap) {
        window.timelineEngine.toggleSnap();
        updateSnapButton();
    }
};

window.splitAtPlayhead = () => {
    if (window.timelineEngine && window.timelineEngine.splitAtPlayhead) {
        window.timelineEngine.splitAtPlayhead();
    }
};

// FIXED: startBatchUpload function với kiểm tra element tồn tại
window.startBatchUpload = async function() {
    console.log('🔄 Starting batch upload...');

    // Helper functions để lấy giá trị element an toàn
    const getElementValue = (id, defaultValue = '') => {
        const element = document.getElementById(id);
        return element ? element.value.trim() : defaultValue;
    };

    const getElementChecked = (id, defaultValue = false) => {
        const element = document.getElementById(id);
        return element ? element.checked : defaultValue;
    };

    const getElementSelectValue = (id, defaultValue = '') => {
        const element = document.getElementById(id);
        return element ? element.value : defaultValue;
    };

    // Lấy giá trị với fallback an toàn
    const urlsText = getElementValue('autoUrls');
    const titleTemplate = getElementValue('autoTitle', 'Video {number}');
    const descriptionTemplate = getElementValue('autoDescription', '');
    const privacy = getElementSelectValue('autoPrivacy', 'private');
    const logoPath = getElementSelectValue('youtubeLogo', '');
    const audioPath = getElementSelectValue('youtubeAudio', '');
    const autoProcess = getElementChecked('autoProcess', true);

    console.log('📝 Batch upload parameters:', {
        urlsText,
        titleTemplate,
        descriptionTemplate,
        privacy,
        logoPath,
        audioPath,
        autoProcess
    });

    if (!urlsText) {
        showStatus('❌ Vui lòng nhập ít nhất một URL video', 'error', 'youtubeStatus');
        return;
    }

    // Parse URLs
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0 && (url.startsWith('http://') || url.startsWith('https://')));

    if (urls.length === 0) {
        showStatus('❌ Vui lòng nhập ít nhất một URL video hợp lệ', 'error', 'youtubeStatus');
        return;
    }

    // Tìm button an toàn hơn
    const button = document.querySelector('#youtubeTab .btn-secondary') ||
                   document.querySelector('#youtubeTab button') ||
                   document.querySelector('.btn-secondary');

    const progressContainer = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (button) showLoading(button, true, 'Bắt đầu upload tự động...');
    if (progressContainer) progressContainer.style.display = 'block';

    try {
        console.log(`📤 Starting batch upload for ${urls.length} videos...`);

        // Sử dụng API thực
        if (!window.api) {
            throw new Error('API service not available');
        }

        const result = await window.api.batchUploadToYouTube(
            urls,
            titleTemplate,
            descriptionTemplate,
            privacy,
            logoPath || null,
            {
                audio: audioPath || null,
                autoProcess: autoProcess
            }
        );

        console.log('📦 Batch upload result:', result);

        if (result.success) {
            const successCount = result.summary?.success || 0;
            const total = result.summary?.total || urls.length;
            const message = `✅ Upload tự động hoàn tất! Thành công: ${successCount}/${total}`;
            showStatus(message, 'success', 'youtubeStatus');

            // Show detailed results
            if (result.results && result.results.length > 0) {
                showBatchUploadResults(result.results);
            }

            // Refresh files
            if (window.refreshFiles) {
                setTimeout(() => window.refreshFiles(), 2000);
            }
        } else {
            const errorMsg = result.error || 'Unknown error occurred';
            showStatus(`❌ Upload tự động thất bại: ${errorMsg}`, 'error', 'youtubeStatus');
        }

    } catch (error) {
        console.error('❌ Batch upload error:', error);
        showStatus(`❌ Lỗi upload tự động: ${error.message}`, 'error', 'youtubeStatus');
    } finally {
        if (button) showLoading(button, false);
        setTimeout(() => {
            if (progressContainer) progressContainer.style.display = 'none';
            if (progressFill) progressFill.style.width = '0%';
            if (progressText) progressText.textContent = '';
        }, 5000);
    }
};

// FIXED: Thêm hàm showBatchUploadResults còn thiếu
function showBatchUploadResults(results) {
    const statusElement = document.getElementById('youtubeStatus');
    if (!statusElement || !results.length) return;

    let detailsHtml = '<div style="margin-top: 10px; font-size: 12px; max-height: 200px; overflow-y: auto; border: 1px solid #334155; padding: 10px; border-radius: 4px;">';
    detailsHtml += '<strong>Kết quả chi tiết:</strong><br><br>';

    results.forEach((result, index) => {
        const statusIcon = result.status === 'success' ? '✅' : '❌';
        const shortUrl = result.url && result.url.length > 40 ? result.url.substring(0, 40) + '...' : (result.url || `Video ${index + 1}`);

        detailsHtml += `<div style="margin-bottom: 8px; padding: 5px; background: ${result.status === 'success' ? '#10b98120' : '#ef444420'}; border-radius: 3px;">`;
        detailsHtml += `<strong>${statusIcon} URL ${index + 1}:</strong> ${shortUrl}<br>`;
        detailsHtml += `<small>Trạng thái: ${result.step || result.status || 'unknown'}`;

        if (result.status === 'success') {
            detailsHtml += ` → ${result.title || 'Upload thành công'}`;
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

// FIXED: Thêm hàm showLoading còn thiếu
function showLoading(button, isLoading, loadingText = 'Loading...') {
    if (!button) return;

    if (isLoading) {
        button.disabled = true;
        button.setAttribute('data-original-text', button.innerHTML);
        button.innerHTML = `<span class="loading-spinner"></span> ${loadingText}`;
        button.classList.add('loading');
    } else {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        } else {
            // Fallback text
            button.innerHTML = '<i class="fas fa-bolt"></i> Start Batch Upload';
        }
        button.classList.remove('loading');
    }
}

// FIXED: Thêm hàm showStatus còn thiếu
function showStatus(message, type = 'info', elementId = 'status') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = message;
        element.className = `status-message status-${type}`;

        // Auto-hide success messages after 8 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (element.innerHTML === message) {
                    element.innerHTML = '';
                    element.className = 'status-message';
                }
            }, 8000);
        }

        // Auto-hide info messages after 5 seconds
        if (type === 'info') {
            setTimeout(() => {
                if (element.innerHTML === message) {
                    element.innerHTML = '';
                    element.className = 'status-message';
                }
            }, 5000);
        }
    }

    // Sử dụng log function nếu có
    if (window.log) {
        window.log(message, type);
    } else {
        console.log(`[${type}] ${message}`);
    }
}

// FIXED: downloadAudio function sử dụng API thực
window.downloadAudio = async function() {
    const audioUrl = document.getElementById('audioUrl')?.value.trim();
    const format = document.getElementById('audioFormat')?.value || 'mp3';
    const quality = document.getElementById('audioQuality')?.value || '192';
    const filename = document.getElementById('audioFilename')?.value.trim();

    if (!audioUrl) {
        showStatus('❌ Vui lòng nhập URL video', 'error', 'audioStatus');
        return;
    }

    const button = document.querySelector('#audioTab .btn-primary');
    showLoading(button, true, 'Đang tải âm thanh...');

    try {
        // Sử dụng API thực thay vì demo
        if (!window.api) {
            throw new Error('API service not available');
        }

        const result = await window.api.downloadAudio(audioUrl, filename || undefined, format, quality);

        if (result.success) {
            showStatus(`✅ Âm thanh đã tải: ${result.file?.name || 'thành công'}`, 'success', 'audioStatus');
            if (window.refreshFiles) {
                window.refreshFiles();
            }
        } else {
            showStatus(`❌ Tải thất bại: ${result.error}`, 'error', 'audioStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi tải: ${error.message}`, 'error', 'audioStatus');
    } finally {
        showLoading(button, false);
    }
};

// Preview control functions
window.togglePlayPause = () => {
    const video = document.getElementById('mainPreview');
    const button = document.querySelector('.play-pause-btn');

    if (!video) return;

    if (video.paused || video.ended) {
        video.play().catch(e => {
            console.error('Cannot play video:', e);
            showStatus('❌ Không thể phát video', 'error');
        });
        if (button) {
            button.innerHTML = '<i class="fas fa-pause"></i>';
        }
    } else {
        video.pause();
        if (button) {
            button.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
};

window.stopPreview = () => {
    const video = document.getElementById('mainPreview');
    const button = document.querySelector('.play-pause-btn');

    if (!video) return;

    video.pause();
    video.currentTime = 0;

    if (button) {
        button.innerHTML = '<i class="fas fa-play"></i>';
    }
};

window.toggleMute = () => {
    const video = document.getElementById('mainPreview');
    const volumeSlider = document.getElementById('volumeSlider');
    const volumeText = document.getElementById('volumeText');

    if (!video) return;

    video.muted = !video.muted;

    if (volumeSlider && volumeText) {
        if (video.muted) {
            volumeSlider.value = 0;
            volumeText.textContent = '0%';
        } else {
            volumeSlider.value = video.volume * 100;
            volumeText.textContent = Math.round(video.volume * 100) + '%';
        }
    }
};

window.changeVolume = (value) => {
    const video = document.getElementById('mainPreview');
    const volumeText = document.getElementById('volumeText');

    if (!video) return;

    const volume = parseInt(value) / 100;
    video.volume = volume;
    video.muted = (volume === 0);

    if (volumeText) {
        volumeText.textContent = value + '%';
    }
};

// Khởi tạo khi DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (window.initUIHandlers) {
                window.initUIHandlers();
            }
            if (window.refreshFiles) {
                window.refreshFiles();
            }
        }, 100);
    });
} else {
    setTimeout(() => {
        if (window.initUIHandlers) {
            window.initUIHandlers();
        }
        if (window.refreshFiles) {
            window.refreshFiles();
        }
    }, 100);
}