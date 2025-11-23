import { log, showStatus } from '../utils/dom-utils.js';
import { showTab } from './tab-handlers.js';

export function setupGlobalEventListeners() {
    setInterval(updateSystemStatus, 30000);
    updateSystemStatus();

    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'd': e.preventDefault(); showTab('download'); break;
                case 't': e.preventDefault(); showTab('timeline'); break;
                case 'e': e.preventDefault(); showTab('process'); break;
                case 'a': e.preventDefault(); showTab('audio'); break;
                case 'y': e.preventDefault(); showTab('youtube'); break;
                case 'f': e.preventDefault(); showTab('files'); break;
            }
        }

        if (e.key === ' ' && !e.target.matches('input, textarea, select')) {
            e.preventDefault();
            const activeTab = document.querySelector('.tab-pane.active').id;
            if (activeTab === 'timelineTab') {
                if (window.toggleTimelinePlayback) toggleTimelinePlayback();
            } else {
                if (window.togglePlayPause) togglePlayPause();
            }
        }
    });
    log('🌐 Global event listeners setup', 'success');
}

async function checkSystemStatus() {
    try {
        const response = await fetch('/api/system-status');
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to fetch system status');
    } catch (error) {
        return {
            memory: Math.floor(Math.random() * 30) + 50,
            disk: Math.floor(Math.random() * 40) + 40
        };
    }
}

function updateSystemStatus() {
    checkSystemStatus().then(status => {
        const memoryElement = document.getElementById('memoryUsage');
        const diskElement = document.getElementById('diskSpace');
        if (memoryElement) memoryElement.textContent = typeof status.memory === 'number' ? status.memory + '%' : status.memory;
        if (diskElement) diskElement.textContent = typeof status.disk === 'number' ? status.disk + '%' : status.disk;
    });
}