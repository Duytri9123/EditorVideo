// ui/handlers/tab-handlers.js
import { log } from '../utils/dom-utils.js';

export function setupTabHandlers() {
    initTabNavigation();
    initSidebarNavigation();
    log('🗂️ Tab handlers initialized', 'success');
}

function initTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const navLinks = document.querySelectorAll('.nav-link');

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

function initSidebarNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            if (tabName) {
                switchTab(tabName);
                
                // On mobile, close sidebar after selection
                if (window.innerWidth < 768) {
                    const sidebar = document.getElementById('sidebar');
                    if (sidebar) {
                        sidebar.classList.add('collapsed');
                    }
                }
            }
        });
    });
}

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

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeTabBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (activeTabBtn) {
        activeTabBtn.classList.add('active');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const activeNavLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
    if (activeNavLink) {
        activeNavLink.classList.add('active');
    }

    // Save state
    localStorage.setItem('activeTab', tabName);

    // Trigger tab-specific initialization
    onTabActivated(tabName);
    
    log(`📑 Switched to tab: ${tabName}`, 'info');
}

function onTabActivated(tabName) {
    // Call tab-specific handlers when a tab becomes active
    switch(tabName) {
        case 'download':
            // Nothing special needed
            break;
        case 'timeline':
            if (window.timelineEngine) {
                window.timelineEngine.updateLayout();
            }
            break;
        case 'files':
            if (window.refreshFiles) {
                window.refreshFiles();
            }
            break;
        case 'process':
        case 'audio':
        case 'youtube':
            if (window.populateFileDropdowns) {
                window.populateFileDropdowns();
            }
            break;
    }
}

// Make switchTab available globally
window.switchTab = switchTab;