// ui/handlers/global-handlers.js
import { log } from '../utils/dom-utils.js';

export function setupGlobalHandlers() {
    // Global keyboard shortcuts
    document.addEventListener('keydown', handleGlobalKeyboard);
    
    // Global error handling
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    // Setup window resize handler
    window.addEventListener('resize', handleWindowResize);
    
    // Setup visibility change (tab switching)
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    log('🌐 Global handlers initialized', 'success');
}

function handleGlobalKeyboard(e) {
    // Ctrl/Cmd + S: Save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (window.exportTimeline) {
            window.exportTimeline();
        }
    }
    
    // Ctrl/Cmd + O: Open file dialog
    if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        // Trigger file open
    }
    
    // Space: Play/Pause (only if not typing)
    if (e.code === 'Space' && !isTyping()) {
        e.preventDefault();
        if (window.togglePlayPause) {
            window.togglePlayPause();
        }
    }
    
    // Esc: Close modals/cancel operations
    if (e.key === 'Escape') {
        handleEscapeKey();
    }
}

function isTyping() {
    const activeElement = document.activeElement;
    return activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
    );
}

function handleEscapeKey() {
    // Close any open modals or cancel operations
    const modals = document.querySelectorAll('.modal.active');
    modals.forEach(modal => modal.classList.remove('active'));
}

function handleGlobalError(event) {
    console.error('Global error:', event.error);
    // You can add custom error reporting here
}

function handleUnhandledRejection(event) {
    console.error('Unhandled promise rejection:', event.reason);
    // You can add custom error reporting here
}

function handleWindowResize() {
    // Debounce resize events
    clearTimeout(window.resizeTimeout);
    window.resizeTimeout = setTimeout(() => {
        // Update layouts that depend on window size
        if (window.timelineEngine) {
            window.timelineEngine.updateLayout();
        }
    }, 250);
}

function handleVisibilityChange() {
    if (document.hidden) {
        // Pause any ongoing operations when tab is hidden
        if (window.timelineEngine && window.timelineEngine.isPlaying) {
            window.timelineEngine.pause();
        }
    }
}