class NotificationManager {
    constructor() {
        this.allNotifications = [];
        this.filteredNotifications = [];
        this.currentPage = 0;
        this.pageSize = 50;
        this.isLoading = false;
        this.searchTerm = '';
        this.typeFilter = '';
        this.statusFilter = '';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupModalEventListeners();
    }
    
    setupEventListeners() {
        // View all notifications button
        const viewAllBtn = document.getElementById('view-all-notifications');
        const sideNotifBtn = document.getElementById('notification-side-item');

        if (viewAllBtn) {
            viewAllBtn.addEventListener('click', () => {
                this.openModal();
            });
        }

        if (sideNotifBtn) {
            sideNotifBtn.addEventListener('click', () => {
                this.openModal();
            });
        }

        // Click outside to close notification panel
        document.addEventListener('click', (e) => {
            this.handleOutsideClick(e);
        });
    }
    
    setupModalEventListeners() {
        // Modal close
        const closeBtn = document.getElementById('notif-modal-close');
        const overlay = document.getElementById('notif-modal-overlay');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }
        
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closeModal();
                }
            });
        }
        
        // Search functionality
        const searchInput = document.getElementById('notif-search-input');
        const searchClear = document.getElementById('notif-search-clear');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchTerm = e.target.value;
                this.updateSearchClearButton();
                this.filterNotifications();
                this.renderModalNotifications();
            });
        }
        
        if (searchClear) {
            searchClear.addEventListener('click', () => {
                searchInput.value = '';
                this.searchTerm = '';
                this.updateSearchClearButton();
                this.filterNotifications();
                this.renderModalNotifications();
            });
        }
        
        // Filter functionality
        const typeFilter = document.getElementById('notif-type-filter');
        const statusFilter = document.getElementById('notif-status-filter');
        
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.typeFilter = e.target.value;
                this.filterNotifications();
                this.renderModalNotifications();
            });
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.statusFilter = e.target.value;
                this.filterNotifications();
                this.renderModalNotifications();
            });
        }
        
        // Modal actions
        const markAllReadBtn = document.getElementById('notif-modal-mark-all-read');
        const refreshBtn = document.getElementById('notif-modal-refresh');
        
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshNotifications();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    handleOutsideClick(e) {
        const notificationPanel = document.getElementById('notification-panel');
        const notificationBell = document.getElementById('notification-bell');
        
        if (notificationPanel && notificationBell) {
            if (!notificationPanel.contains(e.target) && !notificationBell.contains(e.target)) {
                notificationPanel.style.display = 'none';
            }
        }
    }
    
    updateSearchClearButton() {
        const searchClear = document.getElementById('notif-search-clear');
        if (searchClear) {
            searchClear.style.display = this.searchTerm ? 'flex' : 'none';
        }
    }
    
    openModal() {
        const modal = document.getElementById('notif-modal-overlay');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            this.loadAllNotifications();
        }
    }
    
    closeModal() {
        const modal = document.getElementById('notif-modal-overlay');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
    
    async loadAllNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(); 
        
        try {
            // Use existing socket method to get notifications
            if (socketClient) {
                console.log('Emitting get_all_notifications')
                socketClient.socket.emit('get_all_notifications', {
                    offset: 0,
                    limit: 1000 // Load a large number for modal
                });
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.hideLoading();
            this.showEmptyState();
        }
    }
    
    handleNotificationsLoaded(data) {
        this.allNotifications = data.notifications || [];
        this.filterNotifications();
        this.renderModalNotifications();
        this.hideLoading();
        this.isLoading = false;
    }
    
    filterNotifications() {
        this.filteredNotifications = this.allNotifications.filter(notification => {
            // Search filter
            if (this.searchTerm) {
                const searchLower = this.searchTerm.toLowerCase();
                const titleMatch = notification.title.toLowerCase().includes(searchLower);
                const messageMatch = notification.message.toLowerCase().includes(searchLower);
                if (!titleMatch && !messageMatch) return false;
            }
            
            // Type filter
            if (this.typeFilter && notification.type !== this.typeFilter) {
                return false;
            }
            
            // Status filter
            if (this.statusFilter) {
                if (this.statusFilter === 'read' && !notification.is_read) return false;
                if (this.statusFilter === 'unread' && notification.is_read) return false;
            }
            
            return true;
        });
    }
    
    renderModalNotifications() {
        const modalList = document.getElementById('notif-modal-list');
        const emptyState = document.getElementById('notif-empty-state');
        
        if (!modalList) return;
        
        if (this.filteredNotifications.length === 0) {
            modalList.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }
        
        if (emptyState) emptyState.style.display = 'none';
        
        modalList.innerHTML = this.filteredNotifications.map(notification => 
            this.createModalNotificationHTML(notification)
        ).join('');
        
        // Add event listeners to notification items
        this.addModalNotificationListeners();
    }
    
    createModalNotificationHTML(notification) {
        return `
            <div class="notif-modal-item ${notification.is_read ? 'read' : 'unread'}" 
                 data-notification-id="${notification.id}">
                <div class="notif-modal-item-header">
                    <div class="notif-modal-item-title">${this.escapeHtml(notification.title)}</div>
                    <div class="notif-modal-item-time">
                        <span class="notif-type-badge notif-type-${notification.type}">${notification.type}</span>
                        ${this.formatTimestamp(notification.created_at)}
                        ${!notification.is_read ? '<span class="unread-indicator"></span>' : ''}
                    </div>
                </div>
                <div class="notif-modal-item-message">${this.escapeHtml(notification.message)}</div>
                <div class="notif-modal-item-actions">
                    ${notification.link ? `<a href="${notification.link}" class="notif-modal-item-link">View Details</a>` : ''}
                    ${!notification.is_read ? `<button class="notif-btn" onclick="notificationManager.markAsRead(${notification.id})">Mark as Read</button>` : ''}
                </div>
            </div>
        `;
    }
    
    addModalNotificationListeners() {
        const notificationItems = document.querySelectorAll('#notif-modal-list .notif-modal-item');
        notificationItems.forEach(item => {
            if (!item.classList.contains('read')) {
                item.addEventListener('click', (e) => {
                    if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                        const notificationId = parseInt(item.dataset.notificationId);
                        this.markAsRead(notificationId);
                    }
                });
            }
        });
    }
    
    markAsRead(notificationId) {
        if (socketClient) {
            socketClient.markNotificationRead(notificationId);
            
            // Update local data
            const notification = this.allNotifications.find(n => n.id === notificationId);
            if (notification) {
                notification.is_read = true;
            }
            
            this.filterNotifications();
            this.renderModalNotifications();
        }
    }
    
    markAllAsRead() {
        const unreadNotifications = this.filteredNotifications.filter(n => !n.is_read);
        
        if (unreadNotifications.length === 0) {
            this.showToast('No unread notifications to mark', 'info');
            return;
        }
        
        unreadNotifications.forEach(notification => {
            this.markAsRead(notification.id);
        });
        
        this.showToast(`Marked ${unreadNotifications.length} notifications as read`, 'success');
    }
    
    refreshNotifications() {
        this.loadAllNotifications();
        this.showToast('Notifications refreshed', 'success');
    }
    
    showLoading() {
        const loading = document.getElementById('notif-modal-loading');
        const modalList = document.getElementById('notif-modal-list');
        const emptyState = document.getElementById('notif-empty-state');
        
        if (loading) loading.style.display = 'block';
        if (modalList) modalList.innerHTML = '';
        if (emptyState) emptyState.style.display = 'none';
    }
    
    hideLoading() {
        const loading = document.getElementById('notif-modal-loading');
        if (loading) loading.style.display = 'none';
    }
    
    showEmptyState() {
        const emptyState = document.getElementById('notif-empty-state');
        if (emptyState) emptyState.style.display = 'block';
    }
    
    clearReadNotificationsFromPanel() {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        
        const readNotifications = notificationsList.querySelectorAll('.notification-item.read');
        readNotifications.forEach(notification => {
            notification.remove();
        });
    }
    
    showToast(message, type = 'info') {
        if (socketClient) {
            socketClient.showToast(message, type);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffInMinutes = Math.floor((now - date) / (1000 * 60));
        
        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
        if (diffInMinutes < 10080) return `${Math.floor(diffInMinutes / 1440)}d ago`;
        
        return date.toLocaleDateString();
    }
}

// Initialize notification manager
let notificationManager;

document.addEventListener('DOMContentLoaded', function() {
    notificationManager = new NotificationManager();
    
    window.notificationManager = notificationManager;

    // Clear read notifications from panel every 30 seconds
    setInterval(() => {
        if (notificationManager) {
            notificationManager.clearReadNotificationsFromPanel();
        }
    }, 30000);
});

