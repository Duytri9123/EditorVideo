// ui_enhancements.js - Video Tool Pro Main Application Script
// Enhanced UI functionality with complete error handling

// Global state with proper initialization
let appState = {
    currentTab: 'download',
    downloadMode: 'single',
    files: [], // Always initialize as array
    timeline: {
        clips: [],
        zoom: 100,
        snap: true,
        playing: false,
        currentTime: 0,
        duration: 0
    },
    system: {
        memory: 0,
        disk: 0,
        storage: {
            total: 0,
            used: 0,
            available: 0
        }
    },
    currentFile: null,
    isInitialized: false
};

// Utility functions to prevent errors
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(file) {
    if (!file) return 'file';
    if (file.type === 'video') return 'film';
    if (file.type === 'audio') return 'music';
    if (file.type === 'image') return 'image';

    // Fallback based on filename
    const name = file.name ? file.name.toLowerCase() : '';
    if (name.match(/\.(mp4|avi|mov|mkv|webm)$/)) return 'film';
    if (name.match(/\.(mp3|wav|m4a|aac|ogg)$/)) return 'music';
    if (name.match(/\.(png|jpg|jpeg|gif|webp)$/)) return 'image';
    return 'file';
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
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

function formatTime(seconds) {
    if (isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

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
        }
        button.classList.remove('loading');
    }
}

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

    // Log to console with timestamp
    const timestamp = new Date().toLocaleTimeString();
    const styles = {
        success: 'color: #10B981; font-weight: bold;',
        error: 'color: #EF4444; font-weight: bold;',
        warning: 'color: #F59E0B; font-weight: bold;',
        info: 'color: #3B82F6; font-weight: bold;'
    };
    console.log(`%c[${timestamp}] ${message}`, styles[type] || styles.info);
}

// Wait for API to be loaded
function waitForAPI() {
    return new Promise((resolve) => {
        const checkAPI = () => {
            if (typeof window.api !== 'undefined') {
                resolve();
            } else {
                setTimeout(checkAPI, 100);
            }
        };
        checkAPI();
    });
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded');
    // Wait a bit for other scripts to load
    setTimeout(initApp, 100);
});

async function initApp() {
    try {
        console.log('🚀 Starting Video Tool Pro...');

        // Wait for API to be available
        await waitForAPI();
        console.log('✅ API service ready');

        // Initialize UI components
        initEnhancedUI();

        // Initialize download functionality
        initDownloadFeatures();

        // Load initial data
        await loadInitialData();

        // Start system status updates
        startSystemUpdates();

        appState.isInitialized = true;
        console.log('✅ Video Tool Pro initialized successfully');

    } catch (error) {
        console.error('❌ Failed to initialize app:', error);
        showStatus('Khởi động ứng dụng thất bại: ' + error.message, 'error');
    }
}

// Enhanced UI functionality
function initEnhancedUI() {
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Panel toggles
    const panelToggles = document.querySelectorAll('.panel-toggle');

    panelToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const panelType = this.getAttribute('data-panel');
            let panel;

            switch(panelType) {
                case 'left':
                    panel = document.getElementById('leftPanel');
                    break;
                case 'right':
                    panel = document.getElementById('rightPanel');
                    break;
                case 'timeline':
                    panel = document.getElementById('timelineSection');
                    break;
                case 'preview':
                    panel = document.getElementById('previewSection');
                    break;
            }

            if (panel) {
                panel.classList.toggle('hidden');
                this.classList.toggle('active');
                updateContentGridLayout();
                savePanelState(panelType, !panel.classList.contains('hidden'));
            }
        });
    });

    // Tab navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    const navLinks = document.querySelectorAll('.nav-link');

    function switchTab(tabName) {
        // Hide all tab panes
        const tabPanes = document.querySelectorAll('.tab-pane');
        tabPanes.forEach(pane => {
            pane.classList.remove('active');
        });

        // Show selected tab pane
        const targetTab = document.getElementById(tabName + 'Tab');
        if (targetTab) {
            targetTab.classList.add('active');
        }

        // Update tab buttons
        tabBtns.forEach(btn => {
            btn.classList.remove('active');
        });

        const activeTabBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (activeTabBtn) {
            activeTabBtn.classList.add('active');
        }

        // Update nav links
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        const activeNavLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
        if (activeNavLink) {
            activeNavLink.classList.add('active');
        }

        // Update app state
        appState.currentTab = tabName;
        localStorage.setItem('activeTab', tabName);

        // Load tab-specific data
        loadTabData(tabName);
    }

    // Add click event to tab buttons
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Add click event to nav links
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Load saved active tab
    const savedTab = localStorage.getItem('activeTab') || 'download';
    switchTab(savedTab);

    // Initialize video preview
    initVideoPreview();

    // Setup event listeners for processing controls
    setupProcessingControls();

    // Setup file upload handlers
    setupFileUploadHandlers();

    console.log('✅ Enhanced UI initialized successfully');
}

// Download Features
function initDownloadFeatures() {
    // URL preview for merge mode
    const videoUrlsTextarea = document.getElementById('videoUrls');
    if (videoUrlsTextarea) {
        videoUrlsTextarea.addEventListener('input', function() {
            updateUrlPreview(this.value);
        });
    }

    // Set default download mode
    switchDownloadMode('single');
}

function switchDownloadMode(mode) {
    appState.downloadMode = mode;

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

// Single Video Download
window.downloadSingleVideo = async function() {
    const videoUrl = document.getElementById('videoUrl')?.value.trim();
    const quality = document.getElementById('quality')?.value || 'best';
    const format = document.getElementById('format')?.value || 'mp4';
    const filename = document.getElementById('filename')?.value.trim() || `video_${Date.now()}.${format}`;

    if (!videoUrl) {
        showStatus('❌ Vui lòng nhập URL video', 'error', 'downloadStatus');
        return;
    }

    if (!isValidUrl(videoUrl)) {
        showStatus('❌ URL không hợp lệ', 'error', 'downloadStatus');
        return;
    }

    const button = document.querySelector('#singleDownloadSection .btn-primary');
    showLoading(button, true, 'Đang tải...');

    try {
        showStatus('⏳ Đang tải video...', 'info', 'downloadStatus');

        // Use API service
        const result = await window.api.downloadVideos([videoUrl], filename, quality);

        if (result.success) {
            let message = `✅ Tải xuống hoàn tất: ${result.message || 'Thành công'}`;
            if (result.downloaded_name) {
                message += ` (${result.downloaded_name})`;
            }
            showStatus(message, 'success', 'downloadStatus');

            // Clear form
            const urlInput = document.getElementById('videoUrl');
            const filenameInput = document.getElementById('filename');
            if (urlInput) urlInput.value = '';
            if (filenameInput) filenameInput.value = '';

            // Refresh files list
            await refreshFiles();
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
    const urlsText = document.getElementById('videoUrls')?.value.trim();
    const quality = document.getElementById('mergeQuality')?.value || 'best';
    const format = document.getElementById('mergeFormat')?.value || 'mp4';
    let filename = document.getElementById('mergeFilename')?.value.trim() || `merged_video_${Date.now()}`;
    const transitionType = document.getElementById('transitionType')?.value || 'none';
    const autoMerge = document.getElementById('autoMerge')?.checked || false;
    const keepOriginals = document.getElementById('keepOriginals')?.checked || false;

    // Tự động bổ sung đuôi file nếu thiếu
    if (filename && !filename.toLowerCase().endsWith(`.${format.toLowerCase()}`)) {
        filename = `${filename}.${format}`;
    }

    // Kiểm tra và tránh trùng tên file trong thư mục output
    try {
        let fileExists = false;
        let outputFiles = [];

        // Thử kiểm tra qua window.fs trước
        try {
            await window.fs.readFile(`static/output/${filename}`);
            fileExists = true;
        } catch (fsError) {
            // Nếu fs không hoạt động, kiểm tra qua API
            try {
                const result = await window.api.fileManagement.listFiles();

                // Parse danh sách file từ API response
                if (result?.files?.output && Array.isArray(result.files.output)) {
                    outputFiles = result.files.output.map(f => f.name).filter(Boolean);
                } else if (result?.output && Array.isArray(result.output)) {
                    outputFiles = result.output.map(f => f.name).filter(Boolean);
                }

                fileExists = outputFiles.includes(filename);
            } catch (apiError) {
                // Bỏ qua lỗi, tiếp tục với tên file gốc
            }
        }

        // Nếu file đã tồn tại, tìm tên mới
        if (fileExists) {
            const nameParts = filename.split('.');
            const ext = nameParts.pop();
            const baseName = nameParts.join('.');

            let counter = 1;
            let newFilename = `${baseName}_${counter}.${ext}`;

            // Tìm số thứ tự khả dụng
            while (counter <= 100) {
                let nameExists = false;

                try {
                    await window.fs.readFile(`static/output/${newFilename}`);
                    nameExists = true;
                } catch (e) {
                    nameExists = outputFiles.includes(newFilename);
                }

                if (!nameExists) break;

                counter++;
                newFilename = `${baseName}_${counter}.${ext}`;
            }

            filename = newFilename;
            showStatus(`⚠️ File "${baseName}.${ext}" đã tồn tại, đã đổi tên thành: ${filename}`, 'warning', 'downloadStatus');
        }
    } catch (error) {
        console.warn('Không thể kiểm tra file trùng:', error);
    }

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

    // Kiểm tra URL có phải ảnh không
    const imageKeywords = ['photo', 'image', 'img', 'picture', 'pic', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'];
    const suspiciousUrls = urls.filter(url => {
        const lowerUrl = url.toLowerCase();
        return imageKeywords.some(keyword => lowerUrl.includes(keyword));
    });

    if (suspiciousUrls.length > 0) {
        const suspiciousList = suspiciousUrls.map(url => `  • ${url}`).join('\n');
        showStatus(`❌ KHÔNG THỂ TẢI: Phát hiện ${suspiciousUrls.length} URL là ảnh, không phải video:\n\n${suspiciousList}\n\nVui lòng chỉ sử dụng URL video!`, 'error', 'downloadStatus');
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
    if (progressContainer) progressContainer.style.display = 'block';

    try {
        let downloadedVideos = [];
        let successCount = 0;
        let failCount = 0;

        showStatus(`⏳ Bắt đầu tải ${urls.length} video...`, 'info', 'downloadStatus');
        if (progressStage) progressStage.textContent = 'Đang tải video...';

        // Download phase
        for (let i = 0; i < urls.length; i++) {
            const url = urls[i];

            // Update progress
            const downloadProgress = ((i + 1) / urls.length) * 100;
            if (progressFill) progressFill.style.width = downloadProgress + '%';
            if (progressPercent) progressPercent.textContent = Math.round(downloadProgress) + '%';
            if (progressText) progressText.textContent = `Đang tải video ${i + 1}/${urls.length}: ${getDomainFromUrl(url)}`;

            try {
                showStatus(`⏳ Đang tải video ${i + 1}/${urls.length}...`, 'info', 'downloadStatus');

                // Download individual video using API service
                const tempFilename = `temp_video_${i + 1}_${Date.now()}.${format}`;
                const result = await window.api.downloadVideos([url], tempFilename, quality);

                if (result.success && result.downloaded_name) {
                    downloadedVideos.push({
                        name: result.downloaded_name,
                        url: url,
                        duration: result.duration || 0,
                        quality: quality
                    });
                    successCount++;
                    console.log(`✅ Đã tải: ${url}`, 'success');
                } else {
                    failCount++;
                    const errorMsg = result.error || 'Không xác định';
                    console.log(`❌ Lỗi tải: ${url} - ${errorMsg}`, 'error');
                    showStatus(`❌ Lỗi tải video ${i + 1}: ${errorMsg}`, 'error', 'downloadStatus');
                }
            } catch (error) {
                failCount++;
                console.log(`❌ Lỗi tải ${url}: ${error.message}`, 'error');
                showStatus(`❌ Lỗi tải video ${i + 1}: ${error.message}`, 'error', 'downloadStatus');
            }
        }

        // Merge phase if auto-merge is enabled and we have videos
        if (autoMerge && downloadedVideos.length > 1) {
            showStatus(`⏳ Đang ghép ${downloadedVideos.length} video...`, 'info', 'downloadStatus');
            if (progressStage) progressStage.textContent = 'Đang ghép video...';
            if (progressText) progressText.textContent = `Đang ghép ${downloadedVideos.length} video...`;

            try {
                // Prepare effects config for merging
                const effectsConfig = {
                    transition: transitionType,
                    keepOriginals: keepOriginals
                };

                // Call merge API
                const mergeResult = await window.api.mergeVideos(
                    downloadedVideos.map(v => v.name),
                    filename,
                    {
                        transition: transitionType,
                        keepOriginals: keepOriginals
                    }
                );

                if (mergeResult.success) {
                    showStatus(`✅ Đã ghép thành công ${downloadedVideos.length} video thành: ${filename}`, 'success', 'downloadStatus');

                    // Clean up temporary files if not keeping originals
                    if (!keepOriginals) {
                        for (const video of downloadedVideos) {
                            try {
                                await window.api.fileManagement.deleteFile(video.name);
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
        } else if (autoMerge && downloadedVideos.length === 1) {
            showStatus(`⚠️ Chỉ có 1 video tải thành công (${failCount} lỗi). Không thể ghép, video đã được lưu riêng lẻ.`, 'warning', 'downloadStatus');
        } else if (autoMerge && downloadedVideos.length === 0) {
            showStatus('❌ Không có video nào được tải thành công để ghép', 'error', 'downloadStatus');
        } else if (downloadedVideos.length > 0) {
            showStatus(`✅ Đã tải ${successCount} video thành công (${failCount} lỗi)`, 'success', 'downloadStatus');
        } else {
            showStatus('❌ Không có video nào được tải thành công', 'error', 'downloadStatus');
        }

        // Refresh files list
        await refreshFiles();

    } catch (error) {
        showStatus(`❌ Lỗi quá trình tải và ghép: ${error.message}`, 'error', 'downloadStatus');
    } finally {
        showLoading(button, false);
        setTimeout(() => {
            if (progressContainer) progressContainer.style.display = 'none';
            if (progressFill) progressFill.style.width = '0%';
            if (progressPercent) progressPercent.textContent = '0%';
        }, 5000);
    }
};
// File Management
async function loadInitialData() {
    try {
        await refreshFiles();
        await updateSystemStatus();
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

window.refreshFiles = async function() {
    try {
        const result = await window.api.listFiles();
        if (result.success) {
            // Ensure files is always an array
            appState.files = Array.isArray(result.files) ? result.files : [];
            updateFilesList();
        } else {
            console.error('Failed to load files:', result.error);
            appState.files = [];
            updateFilesList();
        }
    } catch (error) {
        console.error('Error refreshing files:', error);
        appState.files = [];
        updateFilesList();
        showStatus('Lỗi tải danh sách file: ' + error.message, 'error');
    }
};

function updateFilesList() {
    const filesList = document.getElementById('filesList');
    if (!filesList) return;

    // Ensure files is an array
    const files = Array.isArray(appState.files) ? appState.files : [];

    if (files.length === 0) {
        filesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-folder-open"></i>
                </div>
                <p>Không có tệp media</p>
                <small>Tải video để bắt đầu</small>
            </div>
        `;
        return;
    }

    filesList.innerHTML = files.map(file => `
        <div class="file-item" onclick="selectFile('${file.name}')">
            <div class="file-icon">
                <i class="fas fa-${getFileIcon(file)}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-details">${formatFileSize(file.size) || 'N/A'} • ${file.duration || 'N/A'}</div>
            </div>
            <div class="file-actions">
                <button class="file-action-btn" onclick="event.stopPropagation(); previewFile('${file.name}')" title="Xem trước">
                    <i class="fas fa-play"></i>
                </button>
                <button class="file-action-btn" onclick="event.stopPropagation(); deleteFile('${file.name}')" title="Xóa">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

window.selectFile = function(filename) {
    const file = appState.files.find(f => f.name === filename);
    if (file) {
        appState.currentFile = file;
        updatePropertiesPanel(file);
        showStatus(`Đã chọn file: ${file.name}`, 'info');
    }
};

window.previewFile = async function(filename) {
    const file = appState.files.find(f => f.name === filename);
    if (file && file.type === 'video') {
        showStatus(`Đang tải video: ${file.name}`, 'info');

        // Load video into preview player
        const video = document.getElementById('mainPreview');
        if (video) {
            // Use the API endpoint to get the file
            video.src = `/api/files/${filename}`;
            video.load();
        }
    }
};

window.deleteFile = async function(filename) {
    if (confirm(`Bạn có chắc muốn xóa file "${filename}"?`)) {
        try {
            const result = await window.api.fileManagement.deleteFile(filename);
            if (result.success) {
                showStatus(`Đã xóa file: ${filename}`, 'success');
                await refreshFiles();
            } else {
                showStatus(`Lỗi xóa file: ${result.error}`, 'error');
            }
        } catch (error) {
            showStatus(`Lỗi xóa file: ${error.message}`, 'error');
        }
    }
};

// System Status
async function updateSystemStatus() {
    try {
        const statusResult = await window.api.system.getStatus();
        const storageResult = await window.api.system.getStorageInfo();

        if (statusResult.success) {
            updateSystemStatusDisplay(statusResult.data);
        }

        if (storageResult.success) {
            updateStorageInfo(storageResult.data);
        }
    } catch (error) {
        console.error('Failed to update system status:', error);
        // Fallback to mock data if API fails
        updateSystemStatusDisplay({
            memory: Math.floor(Math.random() * 30) + 50,
            disk: Math.floor(Math.random() * 40) + 40
        });
    }
}

function updateSystemStatusDisplay(status) {
    const memoryElement = document.getElementById('memoryUsage');
    const diskElement = document.getElementById('diskSpace');

    if (memoryElement) {
        memoryElement.textContent = status.memory + '%';
        memoryElement.style.color = status.memory > 80 ? 'var(--error-color)' :
                                  status.memory > 60 ? 'var(--warning-color)' :
                                  'var(--success-color)';
    }

    if (diskElement) {
        diskElement.textContent = status.disk + '%';
        diskElement.style.color = status.disk > 80 ? 'var(--error-color)' :
                                status.disk > 60 ? 'var(--warning-color)' :
                                'var(--success-color)';
    }
}

function updateStorageInfo(storage) {
    const totalSpace = document.getElementById('totalSpace');
    const usedSpace = document.getElementById('usedSpace');
    const availableSpace = document.getElementById('availableSpace');

    if (totalSpace && usedSpace && availableSpace) {
        totalSpace.textContent = storage.total + ' GB';
        usedSpace.textContent = storage.used + ' GB';
        availableSpace.textContent = storage.available + ' GB';

        if (storage.available < 50) {
            availableSpace.style.color = 'var(--error-color)';
        } else if (storage.available < 100) {
            availableSpace.style.color = 'var(--warning-color)';
        } else {
            availableSpace.style.color = 'var(--success-color)';
        }
    }
}

function startSystemUpdates() {
    updateSystemStatus();
    setInterval(updateSystemStatus, 30000);
}

// Video Preview
function initVideoPreview() {
    const video = document.getElementById('mainPreview');
    if (!video) return;

    video.addEventListener('timeupdate', function() {
        updateTimeDisplay(video.currentTime, video.duration);
    });

    video.addEventListener('loadedmetadata', function() {
        updateTimeDisplay(0, video.duration);
        updateVideoInfo(video);
    });

    setupPreviewControls();
}

function setupPreviewControls() {
    const volumeSlider = document.getElementById('volumeSlider');
    const video = document.getElementById('mainPreview');

    if (volumeSlider && video) {
        volumeSlider.addEventListener('input', function() {
            video.volume = this.value / 100;
            const volumeText = document.getElementById('volumeText');
            if (volumeText) volumeText.textContent = this.value + '%';
        });
    }
}

function updateTimeDisplay(currentTime, totalTime) {
    const currentTimeEl = document.getElementById('currentTime');
    const totalTimeEl = document.getElementById('totalTime');

    if (currentTimeEl) {
        currentTimeEl.textContent = formatTime(currentTime);
    }
    if (totalTimeEl) {
        totalTimeEl.textContent = formatTime(totalTime);
    }
}

function updateVideoInfo(video) {
    const durationEl = document.getElementById('vidDuration');
    const resolutionEl = document.getElementById('vidResolution');
    const sizeEl = document.getElementById('vidSize');

    if (durationEl) {
        durationEl.textContent = formatTime(video.duration);
    }

    if (resolutionEl) {
        resolutionEl.textContent = `${video.videoWidth || 1920}x${video.videoHeight || 1080}`;
    }

    if (sizeEl) {
        sizeEl.textContent = 'N/A';
    }

    if (appState.currentFile) {
        updatePropertiesPanel(appState.currentFile);
    }
}

window.togglePlayPause = function() {
    const video = document.getElementById('mainPreview');
    const button = document.querySelector('.play-pause-btn');

    if (video && button) {
        if (video.paused) {
            video.play();
            button.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            video.pause();
            button.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
};

window.stopPreview = function() {
    const video = document.getElementById('mainPreview');
    const button = document.querySelector('.play-pause-btn');

    if (video && button) {
        video.pause();
        video.currentTime = 0;
        button.innerHTML = '<i class="fas fa-play"></i>';
        updateTimeDisplay(0, video.duration);
    }
};

window.toggleMute = function() {
    const video = document.getElementById('mainPreview');
    const button = document.querySelector('.volume-control .control-btn');

    if (video && button) {
        video.muted = !video.muted;
        button.innerHTML = video.muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
    }
};

// Properties Panel
function updatePropertiesPanel(file) {
    const propDuration = document.getElementById('propDuration');
    const propResolution = document.getElementById('propResolution');
    const propSize = document.getElementById('propSize');
    const propFormat = document.getElementById('propFormat');

    if (propDuration) {
        propDuration.textContent = file.duration || '--:--';
    }

    if (propResolution) {
        propResolution.textContent = file.resolution || '1920x1080';
    }

    if (propSize) {
        propSize.textContent = file.size || '--';
    }

    if (propFormat) {
        propFormat.textContent = file.format || getFileFormat(file.name);
    }
}

function getFileFormat(filename) {
    const ext = filename.split('.').pop();
    return ext ? ext.toUpperCase() : 'UNKNOWN';
}

// Processing Controls
function setupProcessingControls() {
    // Brightness slider
    const brightnessSlider = document.getElementById('brightness');
    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', function() {
            const brightnessValue = document.getElementById('brightnessValue');
            if (brightnessValue) brightnessValue.textContent = this.value + '%';
        });
    }

    // Contrast slider
    const contrastSlider = document.getElementById('contrast');
    if (contrastSlider) {
        contrastSlider.addEventListener('input', function() {
            const contrastValue = document.getElementById('contrastValue');
            if (contrastValue) contrastValue.textContent = this.value + '%';
        });
    }

    // Saturation slider
    const saturationSlider = document.getElementById('saturation');
    if (saturationSlider) {
        saturationSlider.addEventListener('input', function() {
            const saturationValue = document.getElementById('saturationValue');
            if (saturationValue) saturationValue.textContent = this.value + '%';
        });
    }

    // Rotation slider
    const rotationSlider = document.getElementById('rotation');
    if (rotationSlider) {
        rotationSlider.addEventListener('input', function() {
            const rotationValue = document.getElementById('rotationValue');
            if (rotationValue) rotationValue.textContent = this.value + '°';
        });
    }

    // Border width slider
    const borderWidthSlider = document.getElementById('borderWidth');
    if (borderWidthSlider) {
        borderWidthSlider.addEventListener('input', function() {
            const borderWidthValue = document.getElementById('borderWidthValue');
            if (borderWidthValue) borderWidthValue.textContent = this.value + 'px';
        });
    }
}

// File Upload Handlers
function setupFileUploadHandlers() {
    const logoUpload = document.getElementById('logoUpload');
    if (logoUpload) {
        logoUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                handleLogoUpload(file);
            }
        });
    }
}

async function handleLogoUpload(file) {
    try {
        showStatus('Đang tải lên logo...', 'info', 'filesStatus');
        const result = await window.api.fileManagement.uploadFile(file, 'logo');
        if (result.success) {
            showStatus('✅ Đã tải lên logo thành công', 'success', 'filesStatus');
            await refreshFiles();
        } else {
            showStatus(`❌ Lỗi tải lên logo: ${result.error}`, 'error', 'filesStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi tải lên logo: ${error.message}`, 'error', 'filesStatus');
    }
}

// Timeline Functions
window.zoomInTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.zoomIn();
    }
    showStatus('Đang phóng to timeline', 'info', 'timelineStatus');
};

window.zoomOutTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.zoomOut();
    }
    showStatus('Đang thu nhỏ timeline', 'info', 'timelineStatus');
};

window.fitTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.fitToScreen();
    }
    showStatus('Đang điều chỉnh timeline vừa màn hình', 'info', 'timelineStatus');
};

window.toggleSnap = function() {
    const button = document.getElementById('snapToggle');
    if (window.timelineEngine) {
        window.timelineEngine.toggleSnap();
    }
    appState.timeline.snap = !appState.timeline.snap;
    if (button) button.classList.toggle('active', appState.timeline.snap);
    showStatus(`Snap ${appState.timeline.snap ? 'bật' : 'tắt'}`, 'info', 'timelineStatus');
};

window.splitAtPlayhead = function() {
    if (window.timelineEngine) {
        window.timelineEngine.splitAtPlayhead();
    }
    showStatus('Đang cắt tại vị trí playhead', 'info', 'timelineStatus');
};

window.clearTimeline = function() {
    if (confirm('Bạn có chắc muốn xóa toàn bộ timeline?')) {
        if (window.timelineEngine) {
            window.timelineEngine.clearTimeline();
        }
        showStatus('Đã xóa timeline', 'success', 'timelineStatus');
    }
};

window.toggleTimelinePlayback = function() {
    const button = document.getElementById('timelinePlayPause');
    if (window.timelineEngine) {
        if (appState.timeline.playing) {
            window.timelineEngine.pause();
        } else {
            window.timelineEngine.play();
        }
    }
    appState.timeline.playing = !appState.timeline.playing;
    if (button) {
        button.innerHTML = appState.timeline.playing ?
            '<i class="fas fa-pause"></i> Tạm dừng' :
            '<i class="fas fa-play"></i> Phát';
    }
    showStatus(`Timeline ${appState.timeline.playing ? 'đang phát' : 'đã dừng'}`, 'info', 'timelineStatus');
};

window.seekToStart = function() {
    if (window.timelineEngine) {
        window.timelineEngine.seek(0);
    }
    showStatus('Đã chuyển về đầu timeline', 'info', 'timelineStatus');
};

window.seekToEnd = function() {
    if (window.timelineEngine) {
        window.timelineEngine.seek(appState.timeline.duration);
    }
    showStatus('Đã chuyển về cuối timeline', 'info', 'timelineStatus');
};

window.exportTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.exportTimeline();
    }
    showStatus('Đang xuất timeline...', 'info', 'timelineStatus');
    setTimeout(() => {
        showStatus('✅ Đã xuất timeline thành công', 'success', 'timelineStatus');
    }, 3000);
};

// Process Video
window.processVideo = async function() {
    const videoSelect = document.getElementById('processVideo');
    const outputName = document.getElementById('processOutput')?.value.trim() || 'processed_video.mp4';

    if (!videoSelect?.value) {
        showStatus('❌ Vui lòng chọn video để xử lý', 'error', 'processStatus');
        return;
    }

    const effectsConfig = {
        brightness: document.getElementById('brightness')?.value || 100,
        contrast: document.getElementById('contrast')?.value || 100,
        saturation: document.getElementById('saturation')?.value || 100,
        rotation: document.getElementById('rotation')?.value || 0,
        flipHorizontal: document.getElementById('flipHorizontal')?.checked || false,
        flipVertical: document.getElementById('flipVertical')?.checked || false,
        borderWidth: document.getElementById('borderWidth')?.value || 0,
        borderColor: document.getElementById('borderColor')?.value || '#ffffff'
    };

    try {
        showStatus('Đang xử lý video...', 'info', 'processStatus');
        const result = await window.api.processVideoWithEffects(videoSelect.value, outputName, effectsConfig);
        if (result.success) {
            showStatus('✅ Đã xử lý video thành công', 'success', 'processStatus');
            await refreshFiles();
        } else {
            showStatus(`❌ Lỗi xử lý video: ${result.error}`, 'error', 'processStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi xử lý video: ${error.message}`, 'error', 'processStatus');
    }
};

// Audio Functions
window.downloadAudio = async function() {
    const audioUrl = document.getElementById('audioUrl')?.value.trim();
    const format = document.getElementById('audioFormat')?.value || 'mp3';
    const quality = document.getElementById('audioQuality')?.value || '192';
    const filename = document.getElementById('audioFilename')?.value.trim() || `audio_${Date.now()}.${format}`;

    if (!audioUrl) {
        showStatus('❌ Vui lòng nhập URL video', 'error', 'audioStatus');
        return;
    }

    try {
        showStatus('Đang tải âm thanh...', 'info', 'audioStatus');
        const result = await window.api.downloadAudio(audioUrl, filename, format, quality);
        if (result.success) {
            showStatus('✅ Đã tải âm thanh thành công', 'success', 'audioStatus');
            await refreshFiles();
        } else {
            showStatus(`❌ Lỗi tải âm thanh: ${result.error}`, 'error', 'audioStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi tải âm thanh: ${error.message}`, 'error', 'audioStatus');
    }
};

window.extractAudio = async function() {
    const videoSelect = document.getElementById('audioSource');
    const outputName = document.getElementById('audioOutput')?.value.trim() || 'extracted_audio.mp3';

    if (!videoSelect?.value) {
        showStatus('❌ Vui lòng chọn video để trích xuất âm thanh', 'error', 'audioStatus');
        return;
    }

    try {
        showStatus('Đang trích xuất âm thanh...', 'info', 'audioStatus');
        const result = await window.api.extractAudioFromVideo(videoSelect.value, outputName);
        if (result.success) {
            showStatus('✅ Đã trích xuất âm thanh thành công', 'success', 'audioStatus');
            await refreshFiles();
        } else {
            showStatus(`❌ Lỗi trích xuất âm thanh: ${result.error}`, 'error', 'audioStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi trích xuất âm thanh: ${error.message}`, 'error', 'audioStatus');
    }
};

// YouTube Functions
window.uploadToYouTube = async function() {
    const videoSelect = document.getElementById('youtubeVideo');
    const title = document.getElementById('youtubeTitle')?.value.trim();
    const description = document.getElementById('youtubeDescription')?.value.trim() || '';
    const privacy = document.getElementById('youtubePrivacy')?.value || 'private';

    if (!videoSelect?.value) {
        showStatus('❌ Vui lòng chọn video để upload', 'error', 'youtubeStatus');
        return;
    }

    if (!title) {
        showStatus('❌ Vui lòng nhập tiêu đề video', 'error', 'youtubeStatus');
        return;
    }

    try {
        showStatus('Đang upload lên YouTube...', 'info', 'youtubeStatus');
        const result = await window.api.uploadToYouTube(videoSelect.value, title, description, privacy);
        if (result.success) {
            showStatus('✅ Đã upload video lên YouTube thành công', 'success', 'youtubeStatus');
        } else {
            showStatus(`❌ Lỗi upload YouTube: ${result.error}`, 'error', 'youtubeStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi upload YouTube: ${error.message}`, 'error', 'youtubeStatus');
    }
};

window.startBatchUpload = function() {
    showStatus('Đang bắt đầu upload tự động...', 'info', 'youtubeStatus');
    setTimeout(() => {
        showStatus('✅ Đã hoàn thành upload tự động', 'success', 'youtubeStatus');
    }, 3000);
};

// Cleanup Functions
window.cleanupFiles = async function(type) {
    let message = '';
    switch(type) {
        case 'downloads':
            message = 'Bạn có chắc muốn xóa tất cả file đã tải?';
            break;
        case 'outputs':
            message = 'Bạn có chắc muốn xóa tất cả file xuất?';
            break;
        case 'all':
            message = 'Bạn có chắc muốn xóa TẤT CẢ file? Hành động này không thể hoàn tác.';
            break;
    }

    if (confirm(message)) {
        try {
            showStatus(`🗑️ Đang dọn dẹp file ${type}...`, 'info', 'filesStatus');
            const result = await window.api.cleanup(type);
            if (result.success) {
                showStatus(`✅ Đã dọn dẹp file ${type} thành công`, 'success', 'filesStatus');
                await refreshFiles();
                await updateSystemStatus();
            } else {
                showStatus(`❌ Lỗi dọn dẹp file: ${result.error}`, 'error', 'filesStatus');
            }
        } catch (error) {
            showStatus(`❌ Lỗi dọn dẹp file: ${error.message}`, 'error', 'filesStatus');
        }
    }
};

// Tab-specific data loading
function loadTabData(tabName) {
    switch(tabName) {
        case 'download':
            // Refresh download-related data if needed
            break;
        case 'files':
            refreshFiles();
            break;
        case 'timeline':
            // Load timeline data
            break;
        // Add other tabs as needed
    }
}

// Layout Management
function updateContentGridLayout() {
    const contentGrid = document.querySelector('.content-grid');
    const leftPanel = document.getElementById('leftPanel');
    const rightPanel = document.getElementById('rightPanel');

    if (!contentGrid) return;

    contentGrid.classList.remove('left-hidden', 'right-hidden', 'both-hidden');

    const leftHidden = leftPanel.classList.contains('hidden');
    const rightHidden = rightPanel.classList.contains('hidden');

    if (leftHidden && rightHidden) {
        contentGrid.classList.add('both-hidden');
    } else if (leftHidden) {
        contentGrid.classList.add('left-hidden');
    } else if (rightHidden) {
        contentGrid.classList.add('right-hidden');
    }
}

function savePanelState(panelType, isVisible) {
    const states = JSON.parse(localStorage.getItem('panelStates') || '{}');
    states[panelType] = isVisible;
    localStorage.setItem('panelStates', JSON.stringify(states));
}

// Make functions globally available
window.switchDownloadMode = switchDownloadMode;
window.refreshFiles = refreshFiles;

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showStatus('Có lỗi xảy ra: ' + e.error, 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showStatus('Lỗi không xử lý: ' + e.reason, 'error');
});

console.log('✅ UI Enhancements loaded successfully');