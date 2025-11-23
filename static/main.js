// Trong main.js - thêm các hàm sau vào cuối file

// Timeline integration
function setupTimelineIntegration() {
    // Auto-refresh source files khi files thay đổi
    const originalLoadFiles = window.loadFiles;
    window.loadFiles = async function() {
        await originalLoadFiles?.();

        // Update timeline source files
        if (window.timelineEngine && window.timelineEngine.ui) {
            setTimeout(() =>    {
                window.timelineEngine.ui.updateSourceFiles();
            }, 100);
        }
    };

    // Thêm hàm để thêm file vào timeline từ bất kỳ đâu
    window.addFileToTimeline = function(filePath) {
        const allFiles = [...window.currentFiles.downloads, ...window.currentFiles.outputs];
        const fileData = allFiles.find(file => file.path === filePath);

        if (fileData) {
            if (window.timelineEngine) {
                // Kiểm tra loại file
                if (fileData.name.match(/\.(mp3|wav|aac|m4a|ogg)$/i)) {
                    window.timelineEngine.addAudioToTimeline(filePath, fileData.name);
                } else {
                    window.timelineEngine.addToTimeline(filePath, 0, null, fileData.name);
                }
                log(`✅ Added "${fileData.name}" to timeline`, 'success');
            } else {
                log('❌ Timeline engine not initialized', 'error');
            }
        } else {
            log('❌ File not found', 'error');
        }
    };
}

// Cập nhật hàm initializeApp để gọi setupTimelineIntegration
async function initializeApp() {
    try {
        log('🚀 Starting Video Editor Pro...', 'info');

        // Initialize core services
        await initCoreServices();

        // Initialize UI components
        initUIComponents();

        // Load initial data
        await loadInitialData();

        // Setup timeline integration
        setupTimelineIntegration();

        window.appInitialized = true;
        log('✅ Video Editor Pro initialized successfully!', 'success');

    } catch (error) {
        log(`❌ Failed to initialize application: ${error.message}`, 'error');
        showCriticalError('Application initialization failed. Please refresh the page.');
    }
}