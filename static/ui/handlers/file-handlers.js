// ui/handlers/file-handlers.js
import { log, showStatus, showLoading } from '../utils/dom-utils.js';
import { fileUtils } from '../utils/file-utils.js';
import { dataFixer } from '../utils/dom-utils.js';

export function setupFileHandlers() {
    setupFileUploadHandlers();
    setupFileManagementHandlers();
    log('📁 File handlers initialized', 'success');
}

function setupFileUploadHandlers() {
    const logoUpload = document.getElementById('logoUpload');
    if (logoUpload) {
        logoUpload.addEventListener('change', function(e) {
            handleFileUpload(e.target.files[0], 'logo');
        });
    }
}

function setupFileManagementHandlers() {
    // Setup global file management functions
    window.cleanupFilesHandler = cleanupFilesHandler;
    window.refreshFilesHandler = refreshFilesHandler;
    window.populateFileDropdowns = populateFileDropdowns;
    window.updateStorageInfo = updateStorageInfo;
    window.selectFile = selectFile;
}

async function handleFileUpload(file, type) {
    if (!file) return;

    let isValid = false;
    if (type === 'logo') {
        isValid = fileUtils.isValidImageFile(file.name);
    } else if (type === 'music') {
        isValid = fileUtils.isValidAudioFile(file.name);
    }

    if (!isValid) {
        showStatus(`❌ Loại file không hợp lệ cho upload ${type}`, 'error');
        return;
    }

    const button = document.querySelector(`#${type}Upload`)?.closest('.file-upload');
    if (button) showLoading(button, true, `Đang upload ${file.name}...`);

    try {
        // Use global api instance
        const result = await window.api.fileManagement.uploadFile(file, type);
        if (result.success) {
            showStatus(`✅ ${type.charAt(0).toUpperCase() + type.slice(1)} đã upload: ${result.file_name}`, 'success');
            if (window.refreshFiles) window.refreshFiles();
        } else {
            showStatus(`❌ Upload thất bại: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Lỗi upload: ${error.message}`, 'error');
    } finally {
        if (button) showLoading(button, false);
    }
}

async function cleanupFilesHandler(type) {
    let confirmMessage = '';

    switch(type) {
        case 'downloads':
            confirmMessage = 'Bạn có chắc chắn muốn xóa tất cả file đã tải? Hành động này không thể hoàn tác.';
            break;
        case 'outputs':
            confirmMessage = 'Bạn có chắc chắn muốn xóa tất cả file xuất? Hành động này không thể hoàn tác.';
            break;
        case 'all':
            confirmMessage = 'Bạn có chắc chắn muốn xóa TẤT CẢ file? Điều này sẽ xóa tất cả file đã tải, file xuất và file nhạc. Hành động này không thể hoàn tác.';
            break;
        default:
            confirmMessage = 'Bạn có chắc chắn muốn dọn dẹp file? Hành động này không thể hoàn tác.';
    }

    if (!confirm(confirmMessage)) return;

    showStatus(`🗑️ Đang dọn dẹp file ${type}...`, 'info', 'filesStatus');

    try {
        const result = await window.api.fileManagement.cleanup(type);
        if (result.success) {
            showStatus(`✅ Đã dọn dẹp thành công ${result.deleted_files?.length || 0} file`, 'success', 'filesStatus');
            if (window.refreshFiles) window.refreshFiles();
            if (window.updateSystemStatus) window.updateSystemStatus();
        } else {
            showStatus(`❌ Dọn dẹp thất bại: ${result.error}`, 'error', 'filesStatus');
        }
    } catch (error) {
        showStatus(`❌ Lỗi dọn dẹp: ${error.message}`, 'error', 'filesStatus');
    }
}

async function refreshFilesHandler() {
    try {
        const result = await window.api.fileManagement.listFiles();
        if (result.success) {
            window.currentFiles = {
                downloads: dataFixer.fixFileData(result.downloads || []),
                outputs: dataFixer.fixFileData(result.outputs || []),
                music: dataFixer.fixFileData(result.music || []),
                logos: dataFixer.fixFileData(result.logos || [])
            };
            updateFileDisplays();
            if (window.populateFileDropdowns) populateFileDropdowns();
            const totalFiles = (result.downloads?.length || 0) + (result.outputs?.length || 0) + (result.music?.length || 0) + (result.logos?.length || 0);
            log(`📁 Đã tải ${totalFiles} file`, 'success');
        } else {
            log(`❌ Không thể tải file: ${result.error}`, 'error');
        }
    } catch (error) {
        log(`❌ Không thể tải file: ${error.message}`, 'error');
    }
}

function updateFileDisplays() {
    updateFilesList();
    if (window.updateStorageInfo) updateStorageInfo();
}

function updateFilesList() {
    const filesList = document.getElementById('filesList');
    if (!filesList) return;

    const allFiles = [
        ...(window.currentFiles?.downloads || []),
        ...(window.currentFiles?.outputs || []),
        ...(window.currentFiles?.music || []),
        ...(window.currentFiles?.logos || [])
    ];

    if (allFiles.length === 0) {
        filesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-folder-open"></i>
                </div>
                <p>Không có file media</p>
                <small>Tải video để bắt đầu</small>
            </div>
        `;
        return;
    }

    filesList.innerHTML = allFiles.map(file => {
        const fileIcon = fileUtils.getFileIcon(file.name);
        const fileSize = fileUtils.formatFileSize(file.size || 0);
        const fileDuration = file.type === 'video' ? fileUtils.formatDuration(file.duration) + ' • ' : '';
        const resolution = file.type === 'video' && file.width && file.height ? file.width + 'x' + file.height + ' • ' : '';

        return `
        <div class="file-item" data-path="${file.path}" data-type="${file.type}" draggable="true" onclick="selectFile('${file.path}')">
            <div class="file-icon">
                <i class="fas fa-${getFileIcon(file)}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-details">
                    ${fileDuration}${resolution}${fileSize}
                </div>
            </div>
            <div class="file-actions">
                <button class="file-action-btn" onclick="event.stopPropagation(); previewFile('${file.path}')" title="Xem trước">
                    <i class="fas fa-play"></i>
                </button>
                <button class="file-action-btn" onclick="event.stopPropagation(); deleteFile('${file.name}')" title="Xóa">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        `;
    }).join('');

    // Re-setup drag and drop after updating files
    if (window.timelineEngine) {
        window.timelineEngine.setupTimelineEvents();
    }
}

function getFileIcon(file) {
    if (file.type === 'video') return 'film';
    if (file.type === 'audio') return 'music';
    if (file.type === 'image') return 'image';
    return 'file';
}

function populateFileDropdowns() {
    const dropdowns = {
        'processVideo': { type: 'video', placeholder: 'Chọn video' },
        'processLogo': { type: 'image', placeholder: 'Chọn logo (tùy chọn)' },
        'audioSource': { type: 'video', placeholder: 'Chọn video' },
        'youtubeVideo': { type: 'video', placeholder: 'Chọn video' },
        'defaultLogo': { type: 'image', placeholder: 'Chọn logo mặc định' },
        'youtubeLogo': { type: 'image', placeholder: 'Chọn logo cho YouTube' },
        'youtubeAudio': { type: 'audio', placeholder: 'Chọn âm thanh nền' },
        'timelineLogo': { type: 'image', placeholder: 'Chọn logo cho timeline' }
    };

    const allFiles = [
        ...(window.currentFiles?.downloads || []),
        ...(window.currentFiles?.outputs || [])
    ];
    const logoFiles = window.currentFiles?.logos || [];
    const musicFiles = window.currentFiles?.music || [];

    Object.keys(dropdowns).forEach(dropdownId => {
        const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            const config = dropdowns[dropdownId];
            const currentValue = dropdown.value;
            let options = [];

            if (config.type === 'video') {
                options = allFiles.filter(file => file.type === 'video');
            } else if (config.type === 'image') {
                options = logoFiles;
            } else if (config.type === 'audio') {
                options = musicFiles;
            }

            dropdown.innerHTML = `<option value="">-- ${config.placeholder} --</option>` +
                options.map(file => `<option value="${file.path}" ${file.path === currentValue ? 'selected' : ''}>${file.name}</option>`).join('');
        }
    });
}

function updateStorageInfo() {
    const downloads = window.currentFiles?.downloads || [];
    const outputs = window.currentFiles?.outputs || [];
    const music = window.currentFiles?.music || [];
    const logos = window.currentFiles?.logos || [];

    const totalSize = [...downloads, ...outputs, ...music, ...logos].reduce((sum, file) => sum + (file.size || 0), 0);

    const totalSpace = document.getElementById('totalSpace');
    const usedSpace = document.getElementById('usedSpace');
    const availableSpace = document.getElementById('availableSpace');

    if (totalSpace) totalSpace.textContent = '500 GB';
    if (usedSpace) usedSpace.textContent = fileUtils.formatFileSize(totalSize);
    if (availableSpace) {
        const usedGB = totalSize / (1024 * 1024 * 1024);
        const availableGB = 500 - usedGB;
        availableSpace.textContent = `${availableGB.toFixed(1)} GB`;

        if (availableGB < 50) {
            availableSpace.style.color = 'var(--error-color)';
        } else if (availableGB < 100) {
            availableSpace.style.color = 'var(--warning-color)';
        } else {
            availableSpace.style.color = 'var(--success-color)';
        }
    }
}

function selectFile(filePath) {
    const fileItems = document.querySelectorAll('.file-item');
    fileItems.forEach(item => item.classList.remove('active'));
    const selectedItem = document.querySelector(`.file-item[data-path="${filePath}"]`);
    if (selectedItem) selectedItem.classList.add('active');
}

// Make functions available globally for HTML onclick events
window.cleanupFiles = cleanupFilesHandler;
window.refreshFiles = refreshFilesHandler;