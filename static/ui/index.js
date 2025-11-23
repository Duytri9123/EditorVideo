// static/ui/index.js - Main UI entry point

// Import các module
import { initializeAllHandlers } from './handlers/index.js';

// Import components
import { ProgressTracker } from './components/progress-tracker.js';
import { TimelineManager } from './components/timeline-manager.js';

// Import utilities
import * as utils from './utils/index.js';

// Khởi tạo global objects với fallback để tránh lỗi
function initializeGlobals() {
    try {
        window.globalProgress = new ProgressTracker();
        console.log('✅ ProgressTracker initialized');
    } catch (error) {
        console.warn('❌ ProgressTracker initialization failed, using fallback');
        window.globalProgress = {
            update: (progress) => console.log('Progress:', progress),
            reset: () => console.log('Progress reset')
        };
    }

    // Khởi tạo utilities với fallback
    window.fileUtils = utils.fileUtils || {
        formatFileSize: (bytes) => {
            if (!bytes || bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        getFileIcon: (file) => {
            const name = file.name ? file.name.toLowerCase() : '';
            if (name.match(/\.(mp4|avi|mov|mkv|webm)$/)) return 'film';
            if (name.match(/\.(mp3|wav|m4a|aac|ogg)$/)) return 'music';
            if (name.match(/\.(png|jpg|jpeg|gif|webp)$/)) return 'image';
            return 'file';
        }
    };

    window.dataFixer = utils.dataFixer || {
        ensureArray: (data) => Array.isArray(data) ? data : [],
        ensureObject: (data) => typeof data === 'object' ? data : {}
    };

    window.timelineUtils = utils.timelineUtils || {
        initialize: () => console.log('Timeline utils initialized'),
        formatTime: (seconds) => {
            if (isNaN(seconds)) return '00:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    };

    console.log('✅ Global utilities initialized');
}

// Khởi tạo UI khi DOM sẵn sàng
function initializeUI() {
    console.log('🎨 Starting UI initialization...');

    try {
        // Khởi tạo global objects trước
        initializeGlobals();

        // Khởi tạo handlers
        initializeAllHandlers();
        console.log('✅ UI handlers initialized');

        // Khởi tạo Timeline Manager nếu có
        if (typeof TimelineManager !== 'undefined') {
            try {
                window.timelineManager = new TimelineManager();
                console.log('✅ Timeline Manager initialized');
            } catch (error) {
                console.warn('❌ Timeline Manager initialization failed:', error);
            }
        }

        // Refresh files nếu hàm tồn tại
        if (typeof window.refreshFiles === 'function') {
            setTimeout(() => {
                window.refreshFiles();
            }, 500);
        }

        console.log('✅ UI initialization completed successfully');
        return true;

    } catch (error) {
        console.error('❌ UI initialization failed:', error);
        return false;
    }
}

// Đợi DOM ready và khởi tạo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Đợi thêm một chút để đảm bảo các script khác đã load
        setTimeout(initializeUI, 100);
    });
} else {
    // DOM đã sẵn sàng
    setTimeout(initializeUI, 100);
}

// Export cho module system
export {
    initializeUI as initializeAllHandlers,
    ProgressTracker,
    TimelineManager,
    utils
};

// Export cho global usage
if (typeof window !== 'undefined') {
    window.initializeUI = initializeUI;
    window.UI = {
        initialize: initializeUI,
        ProgressTracker,
        TimelineManager,
        utils
    };
}