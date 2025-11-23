import { setupDownloadHandlers } from './download-handlers.js';
import { setupFileHandlers } from './file-handlers.js';
import { setupTabHandlers } from './tab-handlers.js';
import { setupPreviewHandlers } from './preview-handlers.js';
import { setupProcessHandlers } from './process-handlers.js';
import { setupAudioHandlers } from './audio-handlers.js';
import { setupYouTubeHandlers } from './youtube-handlers.js';
import { setupTimelineHandlers } from './timeline-handlers.js';
import { setupGlobalHandlers } from './global-handlers.js';

export function initializeAllHandlers() {
    console.log('🚀 Initializing all handlers...');

    setupGlobalHandlers();
    setupTabHandlers();
    setupDownloadHandlers();
    setupFileHandlers();
    setupPreviewHandlers();
    setupProcessHandlers();
    setupAudioHandlers();
    setupYouTubeHandlers();
    setupTimelineHandlers();

    console.log('✅ All handlers initialized successfully');
}

// Export individual handlers for selective initialization
export {
    setupDownloadHandlers,
    setupFileHandlers,
    setupTabHandlers,
    setupPreviewHandlers,
    setupProcessHandlers,
    setupAudioHandlers,
    setupYouTubeHandlers,
    setupTimelineHandlers,
    setupGlobalHandlers
};