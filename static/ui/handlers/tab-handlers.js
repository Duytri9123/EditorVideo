import { log } from '../utils/dom-utils.js';

export function setupTabHandlers() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            showTab(tabName);
        });
    });
    showTab('download');
}

export function showTab(tabName) {
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => pane.classList.remove('active'));
    const targetTab = document.getElementById(`${tabName}Tab`);
    if (targetTab) {
        targetTab.classList.add('active');
        log(`📑 Switched to ${tabName} tab`, 'info');
        if (tabName === 'timeline' && window.refreshTimeline) refreshTimeline();
        else if (tabName === 'files' && window.refreshFiles) refreshFiles();
    }
}