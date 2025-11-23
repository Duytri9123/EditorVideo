// NotificationManager.js - Enhanced Notification System
export class NotificationManager {
    constructor() {
        this.notificationContainer = null;
        this.notificationQueue = [];
        this.isProcessingQueue = false;
        this.maxNotifications = 5;
        this.createNotificationContainer();
    }

    createNotificationContainer() {
        const existingContainer = document.querySelector('.notification-container');
        if (existingContainer) {
            existingContainer.remove();
        }

        this.notificationContainer = document.createElement('div');
        this.notificationContainer.className = 'notification-container';
        this.notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(this.notificationContainer);
    }

    showSuccess(message, duration = 5000) {
        this.showNotification(message, 'success', duration);
    }

    showError(message, duration = 7000) {
        this.showNotification(message, 'error', duration);
    }

    showWarning(message, duration = 6000) {
        this.showNotification(message, 'warning', duration);
    }

    showInfo(message, duration = 4000) {
        this.showNotification(message, 'info', duration);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: this.generateNotificationId(),
            message,
            type,
            duration,
            timestamp: Date.now()
        };

        this.notificationQueue.push(notification);
        this.processQueue();

        return notification.id;
    }

    processQueue() {
        if (this.isProcessingQueue || this.notificationQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;

        if (this.notificationQueue.length > this.maxNotifications * 2) {
            this.notificationQueue = this.notificationQueue.slice(-this.maxNotifications);
        }

        const currentNotifications = this.notificationContainer.querySelectorAll('.notification');
        if (currentNotifications.length >= this.maxNotifications) {
            const oldestNotification = currentNotifications[0];
            this.removeNotification(oldestNotification);
        }

        const notification = this.notificationQueue.shift();
        this.displayNotification(notification);

        setTimeout(() => {
            this.isProcessingQueue = false;
            this.processQueue();
        }, 300);
    }

    displayNotification(notification) {
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification notification-${notification.type}`;
        notificationElement.setAttribute('data-notification-id', notification.id);

        notificationElement.style.cssText = `
            background: ${this.getBackgroundColor(notification.type)};
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            pointer-events: auto;
            cursor: pointer;
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease;
            max-width: 400px;
            word-wrap: break-word;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        `;

        notificationElement.innerHTML = `
            <div style="font-size: 16px; flex-shrink: 0;">${this.getIcon(notification.type)}</div>
            <div style="flex: 1; min-width: 0;">
                <div style="font-size: 14px; line-height: 1.4;">${this.escapeHtml(notification.message)}</div>
                <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">
                    ${this.formatTime(notification.timestamp)}
                </div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="background: none; border: none; color: white; cursor: pointer; font-size: 18px; padding: 0; margin-left: 8px; flex-shrink: 0;">
                ×
            </button>
        `;

        this.notificationContainer.appendChild(notificationElement);

        requestAnimationFrame(() => {
            notificationElement.style.transform = 'translateX(0)';
            notificationElement.style.opacity = '1';
        });

        const autoRemove = setTimeout(() => {
            this.removeNotification(notificationElement);
        }, notification.duration);

        notificationElement.addEventListener('click', (e) => {
            if (!e.target.matches('button')) {
                clearTimeout(autoRemove);
                this.removeNotification(notificationElement);
            }
        });

        notificationElement.addEventListener('mouseenter', () => {
            clearTimeout(autoRemove);
        });

        notificationElement.addEventListener('mouseleave', () => {
            setTimeout(() => {
                this.removeNotification(notificationElement);
            }, notification.duration);
        });
    }

    removeNotification(notificationElement) {
        if (!notificationElement || !notificationElement.parentNode) return;

        notificationElement.style.transform = 'translateX(100%)';
        notificationElement.style.opacity = '0';

        setTimeout(() => {
            if (notificationElement.parentNode) {
                notificationElement.parentNode.removeChild(notificationElement);
            }
        }, 300);
    }

    removeNotificationById(notificationId) {
        const notificationElement = this.notificationContainer.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationElement) {
            this.removeNotification(notificationElement);
        }
    }

    clearAll() {
        const notifications = this.notificationContainer.querySelectorAll('.notification');
        notifications.forEach(notification => {
            this.removeNotification(notification);
        });

        this.notificationQueue = [];
    }

    getBackgroundColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        return colors[type] || colors.info;
    }

    getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    generateNotificationId() {
        return 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    formatTime(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;

        if (diff < 60000) {
            return 'Just now';
        } else if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        } else if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        } else {
            const date = new Date(timestamp);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }

    showProgress(message, progress = 0) {
        const notificationId = this.showInfo(`
            <div>${message}</div>
            <div style="margin-top: 8px;">
                <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.3); border-radius: 2px; overflow: hidden;">
                    <div style="width: ${Math.max(0, Math.min(100, progress))}%; height: 100%; background: white; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 12px; text-align: center; margin-top: 4px;">${Math.round(progress)}%</div>
            </div>
        `, 0);

        return notificationId;
    }

    updateProgress(notificationId, progress, message = null) {
        const notificationElement = this.notificationContainer.querySelector(`[data-notification-id="${notificationId}"]`);
        if (!notificationElement) return false;

        if (message) {
            const messageElement = notificationElement.querySelector('div > div:first-child');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }

        const progressBar = notificationElement.querySelector('div > div > div:last-child');
        if (progressBar) {
            progressBar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        }

        const progressText = notificationElement.querySelector('div > div > div:last-child + div');
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }

        return true;
    }

    showConfirmation(message, confirmText = 'Confirm', cancelText = 'Cancel') {
        return new Promise((resolve) => {
            const notificationId = this.generateNotificationId();

            const notificationElement = document.createElement('div');
            notificationElement.className = 'notification notification-info';
            notificationElement.setAttribute('data-notification-id', notificationId);

            notificationElement.style.cssText = `
                background: #3b82f6;
                color: white;
                padding: 16px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                pointer-events: auto;
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.3s ease;
                max-width: 400px;
            `;

            notificationElement.innerHTML = `
                <div style="margin-bottom: 12px; font-size: 14px; line-height: 1.4;">${this.escapeHtml(message)}</div>
                <div style="display: flex; gap: 8px; justify-content: flex-end;">
                    <button onclick="this.closest('.notification').remove(); window.notificationManager.resolveConfirmation('${notificationId}', false)" 
                            style="padding: 6px 12px; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 4px; cursor: pointer;">
                        ${cancelText}
                    </button>
                    <button onclick="this.closest('.notification').remove(); window.notificationManager.resolveConfirmation('${notificationId}', true)" 
                            style="padding: 6px 12px; background: white; border: none; color: #3b82f6; border-radius: 4px; cursor: pointer; font-weight: 500;">
                        ${confirmText}
                    </button>
                </div>
            `;

            this.notificationContainer.appendChild(notificationElement);

            requestAnimationFrame(() => {
                notificationElement.style.transform = 'translateX(0)';
                notificationElement.style.opacity = '1';
            });

            this.confirmationResolvers = this.confirmationResolvers || {};
            this.confirmationResolvers[notificationId] = resolve;

            setTimeout(() => {
                if (this.confirmationResolvers[notificationId]) {
                    this.resolveConfirmation(notificationId, false);
                }
            }, 30000);
        });
    }

    resolveConfirmation(notificationId, result) {
        if (this.confirmationResolvers && this.confirmationResolvers[notificationId]) {
            this.confirmationResolvers[notificationId](result);
            delete this.confirmationResolvers[notificationId];
        }

        const notificationElement = this.notificationContainer.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationElement) {
            this.removeNotification(notificationElement);
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification notification-${type} notification-toast`;

        notificationElement.style.cssText = `
            background: ${this.getBackgroundColor(type)};
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            pointer-events: auto;
            cursor: pointer;
            transform: translateY(-100%);
            opacity: 0;
            transition: all 0.3s ease;
            font-size: 13px;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
        `;

        notificationElement.innerHTML = `
            <span>${this.getIcon(type)}</span>
            <span>${this.escapeHtml(message)}</span>
        `;

        this.notificationContainer.appendChild(notificationElement);

        requestAnimationFrame(() => {
            notificationElement.style.transform = 'translateY(0)';
            notificationElement.style.opacity = '1';
        });

        setTimeout(() => {
            this.removeNotification(notificationElement);
        }, duration);

        notificationElement.addEventListener('click', () => {
            this.removeNotification(notificationElement);
        });
    }
}

window.NotificationManager = NotificationManager;
export default NotificationManager;