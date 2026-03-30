// ui_enhancements.js - Optimized UI Manager (Only handles UI interactions, no logic)

// Global state
let appState = {
    currentTab: 'download',
    currentFile: null,
    isInitialized: false,
    minimalMode: false,
    focusMode: false,
    panelStates: {
        left: true,
        right: false,
        timeline: false,
        preview: false,
    }
};

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
    setTimeout(initApp, 100);
});

async function initApp() {
    try {
        console.log('🚀 Starting Video Tool Pro...');

        // Wait for API
        await waitForAPI();
        console.log('✅ API service ready');

        // Initialize UI components only
        initEnhancedUI();
        initDownloadModeUI();
        initQuickSettings();
        initPanelCollapse();
        
        appState.isInitialized = true;
        console.log('✅ Video Tool Pro UI initialized successfully');

    } catch (error) {
        console.error('❌ Failed to initialize app:', error);
    }
}

// UI Initialization (No Logic)
function initEnhancedUI() {
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Panel toggles
    initPanelToggles();

    // Tab navigation
    initTabNavigation();

    // Initialize video preview controls (UI only)
    initVideoPreviewControls();

    // Setup processing slider displays
    setupProcessingSliderDisplays();

    // Focus mode
    const focusModeBtn = document.getElementById('focusModeBtn');
    if (focusModeBtn) {
        focusModeBtn.addEventListener('click', toggleFocusMode);
    }

    // Minimal mode
    const minimalModeBtn = document.getElementById('minimalModeBtn');
    if (minimalModeBtn) {
        minimalModeBtn.addEventListener('click', toggleMinimalMode);
    }

    console.log('✅ Enhanced UI initialized');
}

// Quick Settings Panel
function initQuickSettings() {
    const settingsToggle = document.getElementById('quickSettingsToggle');
    const settingsPanel = document.getElementById('quickSettingsPanel');
    const closeSettings = document.getElementById('closeSettings');

    if (settingsToggle && settingsPanel) {
        settingsToggle.addEventListener('click', () => {
            settingsPanel.classList.toggle('active');
        });
    }

    if (closeSettings && settingsPanel) {
        closeSettings.addEventListener('click', () => {
            settingsPanel.classList.remove('active');
        });
    }

    // Initialize toggle switches
    initToggleSwitches();
}

// Initialize toggle switches
function initToggleSwitches() {
    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            document.body.classList.toggle('dark-mode', this.checked);
            localStorage.setItem('darkMode', this.checked);
        });

        // Load saved preference
        const savedDarkMode = localStorage.getItem('darkMode') === 'true';
        darkModeToggle.checked = savedDarkMode;
        document.body.classList.toggle('dark-mode', savedDarkMode);
    }

    // Animations toggle
    const animationsToggle = document.getElementById('animationsToggle');
    if (animationsToggle) {
        animationsToggle.addEventListener('change', function() {
            document.body.classList.toggle('no-animations', !this.checked);
            localStorage.setItem('animations', this.checked);
        });

        // Load saved preference
        const savedAnimations = localStorage.getItem('animations') !== 'false';
        animationsToggle.checked = savedAnimations;
        document.body.classList.toggle('no-animations', !savedAnimations);
    }

    // Panel visibility toggles
    initPanelVisibilityToggles();
}

// Panel visibility toggles
function initPanelVisibilityToggles() {
    const toggles = {
        'hideLeftPanelToggle': 'left',
        'hideRightPanelToggle': 'right',
        'hideTimelineToggle': 'timeline',
        'hidePreviewToggle': 'preview'
    };

    Object.keys(toggles).forEach(toggleId => {
        const toggle = document.getElementById(toggleId);
        const panelType = toggles[toggleId];

        if (toggle) {
            toggle.addEventListener('change', function() {
                togglePanel(panelType, !this.checked);
                appState.panelStates[panelType] = !this.checked;
                savePanelStates();
            });

            // Load saved state
            const savedStates = JSON.parse(localStorage.getItem('panelStates') || '{}');
            if (savedStates[panelType] !== undefined) {
                toggle.checked = !savedStates[panelType];
                appState.panelStates[panelType] = savedStates[panelType];
                togglePanel(panelType, savedStates[panelType]);
            }
        }
    });

    // Focus mode toggle
    const focusModeToggle = document.getElementById('focusModeToggle');
    if (focusModeToggle) {
        focusModeToggle.addEventListener('change', function() {
            if (this.checked) {
                enableFocusMode();
            } else {
                disableFocusMode();
            }
        });
    }
}

// Panel Toggles
function initPanelToggles() {
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
}

// Panel Collapse Functionality
function initPanelCollapse() {
    const collapseButtons = document.querySelectorAll('.panel-collapse-btn, .preview-collapse-btn, .timeline-collapse-btn');

    collapseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const panelType = this.getAttribute('data-panel');
            collapsePanel(panelType);
        });
    });
}

function collapsePanel(panelType) {
    let panel;
    let isCollapsed = false;

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
        isCollapsed = panel.classList.contains('collapsed');
        
        if (isCollapsed) {
            panel.classList.remove('collapsed');
        } else {
            panel.classList.add('collapsed');
        }

        updateContentGridLayout();
        savePanelState(panelType, !isCollapsed);
    }
}

function togglePanel(panelType, show) {
    let panel;
    let toggleButton;

    switch(panelType) {
        case 'left':
            panel = document.getElementById('leftPanel');
            toggleButton = document.querySelector('.panel-toggle[data-panel="left"]');
            break;
        case 'right':
            panel = document.getElementById('rightPanel');
            toggleButton = document.querySelector('.panel-toggle[data-panel="right"]');
            break;
        case 'timeline':
            panel = document.getElementById('timelineSection');
            toggleButton = document.querySelector('.panel-toggle[data-panel="timeline"]');
            break;
        case 'preview':
            panel = document.getElementById('previewSection');
            toggleButton = document.querySelector('.panel-toggle[data-panel="preview"]');
            break;
    }

    if (panel && toggleButton) {
        if (show) {
            panel.classList.remove('hidden');
            toggleButton.classList.add('active');
        } else {
            panel.classList.add('hidden');
            toggleButton.classList.remove('active');
        }
        updateContentGridLayout();
    }
}

// Tab Navigation
function initTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const navLinks = document.querySelectorAll('.nav-link');

    function switchTab(tabName) {
        // Hide all tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });

        // Show selected tab
        const targetTab = document.getElementById(tabName + 'Tab');
        if (targetTab) {
            targetTab.classList.add('active');
        }

        // Update buttons
        tabBtns.forEach(btn => btn.classList.remove('active'));
        const activeTabBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (activeTabBtn) activeTabBtn.classList.add('active');

        // Update nav links
        navLinks.forEach(link => link.classList.remove('active'));
        const activeNavLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
        if (activeNavLink) activeNavLink.classList.add('active');

        // Update state
        appState.currentTab = tabName;
        localStorage.setItem('activeTab', tabName);
    }

    // Add click events
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.getAttribute('data-tab'));
        });
    });

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab(this.getAttribute('data-tab'));
        });
    });

    // Load saved tab
    const savedTab = localStorage.getItem('activeTab') || 'download';
    switchTab(savedTab);
}

// Download Mode UI (No Logic)
function initDownloadModeUI() {
    // URL preview for merge mode
    const videoUrlsTextarea = document.getElementById('videoUrls');
    if (videoUrlsTextarea) {
        videoUrlsTextarea.addEventListener('input', function() {
            if (window.updateUrlPreview) {
                window.updateUrlPreview(this.value);
            }
        });
    }
}

// Video Preview Controls (UI Only)
function initVideoPreviewControls() {
    const video = document.getElementById('mainPreview');
    if (!video) return;

    // Time update display
    video.addEventListener('timeupdate', function() {
        updateTimeDisplay(video.currentTime, video.duration);
    });

    video.addEventListener('loadedmetadata', function() {
        updateTimeDisplay(0, video.duration);
    });

    // Volume slider
    const volumeSlider = document.getElementById('volumeSlider');
    if (volumeSlider) {
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

    if (currentTimeEl) currentTimeEl.textContent = formatTime(currentTime);
    if (totalTimeEl) totalTimeEl.textContent = formatTime(totalTime);
}

function formatTime(seconds) {
    if (isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Play/Pause Control
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
        button.innerHTML = video.muted ? 
            '<i class="fas fa-volume-mute"></i>' : 
            '<i class="fas fa-volume-up"></i>';
    }
};

// Processing Slider Displays (UI Only)
function setupProcessingSliderDisplays() {
    const sliders = [
        { id: 'brightness', valueId: 'brightnessValue', suffix: '%' },
        { id: 'contrast', valueId: 'contrastValue', suffix: '%' },
        { id: 'saturation', valueId: 'saturationValue', suffix: '%' },
        { id: 'rotation', valueId: 'rotationValue', suffix: '°' },
        { id: 'borderWidth', valueId: 'borderWidthValue', suffix: 'px' }
    ];

    sliders.forEach(slider => {
        const element = document.getElementById(slider.id);
        const valueElement = document.getElementById(slider.valueId);
        
        if (element && valueElement) {
            element.addEventListener('input', function() {
                valueElement.textContent = this.value + slider.suffix;
            });
        }
    });
}

// Switch Download Mode (UI Only)
window.switchDownloadMode = function(mode) {
    // Update mode buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-mode') === mode) {
            btn.classList.add('active');
        }
    });

    // Show/hide sections
    const singleSection = document.getElementById('singleDownloadSection');
    const mergeSection = document.getElementById('mergeDownloadSection');
    
    if (singleSection) singleSection.classList.toggle('active', mode === 'single');
    if (mergeSection) mergeSection.classList.toggle('active', mode === 'merge');

    // Clear status
    const statusElement = document.getElementById('downloadStatus');
    if (statusElement) statusElement.innerHTML = '';
};

// Layout Management
function updateContentGridLayout() {
    const contentGrid = document.querySelector('.content-grid');
    const leftPanel = document.getElementById('leftPanel');
    const rightPanel = document.getElementById('rightPanel');

    if (!contentGrid) return;

    contentGrid.classList.remove('left-hidden', 'right-hidden', 'both-hidden', 'left-collapsed', 'right-collapsed');

    const leftHidden = leftPanel?.classList.contains('hidden');
    const rightHidden = rightPanel?.classList.contains('hidden');
    const leftCollapsed = leftPanel?.classList.contains('collapsed');
    const rightCollapsed = rightPanel?.classList.contains('collapsed');

    if (leftHidden && rightHidden) {
        contentGrid.classList.add('both-hidden');
    } else if (leftHidden) {
        contentGrid.classList.add('left-hidden');
    } else if (rightHidden) {
        contentGrid.classList.add('right-hidden');
    } else if (leftCollapsed && rightCollapsed) {
        contentGrid.classList.add('left-collapsed', 'right-collapsed');
    } else if (leftCollapsed) {
        contentGrid.classList.add('left-collapsed');
    } else if (rightCollapsed) {
        contentGrid.classList.add('right-collapsed');
    }
}

function savePanelState(panelType, isVisible) {
    const states = JSON.parse(localStorage.getItem('panelStates') || '{}');
    states[panelType] = isVisible;
    localStorage.setItem('panelStates', JSON.stringify(states));
}

function savePanelStates() {
    localStorage.setItem('panelStates', JSON.stringify(appState.panelStates));
}

// Focus Mode
function toggleFocusMode() {
    if (appState.focusMode) {
        disableFocusMode();
    } else {
        enableFocusMode();
    }
}

function enableFocusMode() {
    appState.focusMode = true;
    document.body.classList.add('focus-mode');
    
    // Hide all panels except the center content
    togglePanel('left', false);
    togglePanel('right', false);
    togglePanel('timeline', false);
    
    // Update toggle states
    const focusModeToggle = document.getElementById('focusModeToggle');
    if (focusModeToggle) focusModeToggle.checked = true;
    
    // Update button state
    const focusModeBtn = document.getElementById('focusModeBtn');
    if (focusModeBtn) focusModeBtn.classList.add('active');
}

function disableFocusMode() {
    appState.focusMode = false;
    document.body.classList.remove('focus-mode');
    
    // Restore panel states
    Object.keys(appState.panelStates).forEach(panelType => {
        togglePanel(panelType, appState.panelStates[panelType]);
    });
    
    // Update toggle states
    const focusModeToggle = document.getElementById('focusModeToggle');
    if (focusModeToggle) focusModeToggle.checked = false;
    
    // Update button state
    const focusModeBtn = document.getElementById('focusModeBtn');
    if (focusModeBtn) focusModeBtn.classList.remove('active');
}

// Minimal Mode
function toggleMinimalMode() {
    appState.minimalMode = !appState.minimalMode;
    
    if (appState.minimalMode) {
        document.body.classList.add('minimal-mode');
        // Hide sidebar and some controls
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.add('collapsed');
        
        // Update button state
        const minimalModeBtn = document.getElementById('minimalModeBtn');
        if (minimalModeBtn) minimalModeBtn.classList.add('active');
    } else {
        document.body.classList.remove('minimal-mode');
        // Show sidebar
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('collapsed');
        
        // Update button state
        const minimalModeBtn = document.getElementById('minimalModeBtn');
        if (minimalModeBtn) minimalModeBtn.classList.remove('active');
    }
}

// Timeline UI Controls (No Logic)
window.zoomInTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.zoomIn();
    }
};

window.zoomOutTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.zoomOut();
    }
};

window.fitTimeline = function() {
    if (window.timelineEngine) {
        window.timelineEngine.fitToScreen();
    }
};

window.toggleSnap = function() {
    const button = document.getElementById('snapToggle');
    if (button) button.classList.toggle('active');
    if (window.timelineEngine) {
        window.timelineEngine.toggleSnap();
    }
};

window.splitAtPlayhead = function() {
    if (window.timelineEngine) {
        window.timelineEngine.splitAtPlayhead();
    }
};

window.clearTimeline = function() {
    if (confirm('Bạn có chắc muốn xóa toàn bộ timeline?')) {
        if (window.timelineEngine) {
            window.timelineEngine.clearTimeline();
        }
    }
};

window.toggleTimelinePlayback = function() {
    const button = document.getElementById('timelinePlayPause');
    if (window.timelineEngine) {
        if (window.timelineEngine.isPlaying) {
            window.timelineEngine.pause();
            if (button) button.innerHTML = '<i class="fas fa-play"></i> Phát';
        } else {
            window.timelineEngine.play();
            if (button) button.innerHTML = '<i class="fas fa-pause"></i> Tạm dừng';
        }
    }
};

window.seekToStart = function() {
    if (window.timelineEngine) {
        window.timelineEngine.seek(0);
    }
};

window.seekToEnd = function() {
    if (window.timelineEngine) {
        if (window.timelineEngine.duration) {
            window.timelineEngine.seek(window.timelineEngine.duration);
        }
    }
};

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});

console.log('✅ UI Enhancements loaded successfully');