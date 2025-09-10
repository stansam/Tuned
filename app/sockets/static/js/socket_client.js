class SocketClient {
    constructor() {
        this.socket = null;
        this.currentChat = null;
        this.sounds = this.initializeSounds();
        this.notificationQueue = [];
        this.isProcessingNotifications = false;
        this.unreadCounts = { messages: 0, notifications: 0, total: 0 };
        
        this.init();
    }
    
    init() {
        // Initialize socket connection
        this.socket = io();
        this.setupEventListeners();
        this.setupUIHandlers();
        
        // Connect on page load
        this.connect();
    }
    
    initializeSounds() {
        return {
            message: new Audio('/static/sounds/message.mp3'),
            notification: new Audio('/static/sounds/notification.mp3'),
            alert: new Audio('/static/sounds/alert.mp3'),
            success: new Audio('/static/sounds/success.mp3')
        };
    }
    
    connect() {
        this.socket.connect();
    }
    
    disconnect() {
        this.socket.disconnect();
    }
    
    setupEventListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('connection_status', (data) => {
            console.log('Connection status:', data);
        });
        
        // Chat events
        this.socket.on('new_message', (data) => {
            this.handleNewMessage(data);
        });
        
        this.socket.on('joined_chat', (data) => {
            console.log('Joined chat:', data.chat_id);
            this.currentChat = data.chat_id;
        });
        
        this.socket.on('left_chat', (data) => {
            console.log('Left chat:', data.chat_id);
            if (this.currentChat === data.chat_id) {
                this.currentChat = null;
            }
        });
        
        this.socket.on('messages_marked_read', (data) => {
            this.handleMessagesMarkedRead(data.chat_id);
        });
        
        // Notification events
        this.socket.on('new_notification', (data) => {
            this.handleNewNotification(data);
        });
        
        this.socket.on('notification_marked_read', (data) => {
            this.handleNotificationMarkedRead(data.notification_id);
        });
        
        this.socket.on('notifications_loaded', (data) => {
            this.handleNotificationsLoaded(data);
        });
        
        // Unread counts
        this.socket.on('unread_counts', (data) => {
            this.handleUnreadCounts(data);
        });
        
        // Admin specific events
        this.socket.on('new_order_alert', (data) => {
            this.handleNewOrderAlert(data);
        });
        
        // Error handling
        this.socket.on('error', (data) => {
            console.error('Socket error:', data);
            this.showToast('Error: ' + data.message, 'error');
        });
    }
    
    setupUIHandlers() {
        // Chat form submission
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }
        
        // Notification panel toggle
        const notificationBell = document.getElementById('notification-bell');
        if (notificationBell) {
            notificationBell.addEventListener('click', () => {
                this.toggleNotificationPanel();
            });
        }
        
        // Mark all notifications as read
        const markAllRead = document.getElementById('mark-all-notifications-read');
        if (markAllRead) {
            markAllRead.addEventListener('click', () => {
                this.markAllNotificationsRead();
            });
        }
    }
    
    // Chat methods
    joinChat(chatId) {
        this.socket.emit('join_chat', { chat_id: chatId });
    }
    
    leaveChat(chatId) {
        this.socket.emit('leave_chat', { chat_id: chatId });
    }
    
    sendMessage() {
        const messageInput = document.getElementById('message-input');
        const content = messageInput.value.trim();
        
        if (!content || !this.currentChat) {
            return;
        }
        
        this.socket.emit('send_message', {
            chat_id: this.currentChat,
            content: content
        });
        
        messageInput.value = '';
    }
    
    markMessagesRead(chatId) {
        this.socket.emit('mark_messages_read', { chat_id: chatId });
    }
    
    handleNewMessage(data) {
        // Add message to chat interface
        this.addMessageToChat(data);
        
        // If not in current chat, show notification
        if (data.chat_id !== this.currentChat) {
            this.showMessageNotification(data);
            this.playSound('message');
        }
        
        // Update unread counts (will be updated by server)
    }
    
    addMessageToChat(messageData) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageElement = this.createMessageElement(messageData);
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${messageData.user_id === currentUserId ? 'own-message' : 'other-message'}`;
        messageDiv.dataset.messageId = messageData.id;
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="username">${messageData.username}</span>
                <span class="timestamp">${this.formatTimestamp(messageData.created_at)}</span>
            </div>
            <div class="message-content">${this.escapeHtml(messageData.content)}</div>
        `;
        
        return messageDiv;
    }
    
    handleMessagesMarkedRead(chatId) {
        // Update UI to show messages as read
        const messages = document.querySelectorAll(`.message[data-chat-id="${chatId}"]`);
        messages.forEach(msg => msg.classList.add('read'));
    }
    
    // Notification methods
    handleNewNotification(data) {
        const notification = data.notification;
        const soundType = data.sound_type || 'notification';
        const priority = data.priority || 'normal';
        
        // Add to notification queue for processing
        this.notificationQueue.push({
            notification,
            soundType,
            priority,
            timestamp: Date.now()
        });
        
        // Process notification queue
        this.processNotificationQueue();
    }
    
    processNotificationQueue() {
        if (this.isProcessingNotifications || this.notificationQueue.length === 0) {
            return;
        }
        
        this.isProcessingNotifications = true;
        
        const notificationData = this.notificationQueue.shift();
        const { notification, soundType, priority } = notificationData;
        
        // Play sound
        this.playSound(soundType, priority);
        
        // Show toast notification
        this.showToast(notification.title, notification.type, notification.message);
        
        // Add to notification panel
        this.addNotificationToPanel(notification);
        
        // Process next notification after delay
        setTimeout(() => {
            this.isProcessingNotifications = false;
            this.processNotificationQueue();
        }, 1000); // 1 second delay between notifications
    }
    
    playSound(soundType, priority = 'normal') {
        try {
            // Check if sounds are enabled
            if (!this.areSoundsEnabled()) {
                return;
            }
            
            const sound = this.sounds[soundType];
            if (sound) {
                sound.currentTime = 0;
                
                // Adjust volume based on priority
                sound.volume = priority === 'high' ? 0.8 : 0.6;
                
                const playPromise = sound.play();
                if (playPromise !== undefined) {
                    playPromise.catch(error => {
                        console.warn('Audio play failed:', error);
                    });
                }
            }
        } catch (error) {
            console.warn('Sound playback error:', error);
        }
    }
    
    areSoundsEnabled() {
        return localStorage.getItem('notificationSounds') !== 'disabled';
    }
    
    toggleSounds() {
        const currentSetting = localStorage.getItem('notificationSounds');
        const newSetting = currentSetting === 'disabled' ? 'enabled' : 'disabled';
        localStorage.setItem('notificationSounds', newSetting);
        
        this.updateSoundToggleUI();
        return newSetting === 'enabled';
    }
    
    updateSoundToggleUI() {
        const soundToggle = document.getElementById('sound-toggle');
        if (soundToggle) {
            soundToggle.textContent = this.areSoundsEnabled() ? '🔊' : '🔇';
            soundToggle.title = this.areSoundsEnabled() ? 'Disable sounds' : 'Enable sounds';
        }
    }
    
    markNotificationRead(notificationId) {
        this.socket.emit('mark_notification_read', { notification_id: notificationId });
    }
    
    markAllNotificationsRead() {
        // Get all unread notification IDs
        const unreadNotifications = document.querySelectorAll('.notification-item:not(.read)');
        unreadNotifications.forEach(notif => {
            const notificationId = notif.dataset.notificationId;
            if (notificationId) {
                this.markNotificationRead(parseInt(notificationId));
            }
        });
    }
    
    handleNotificationMarkedRead(notificationId) {
        // Update UI
        const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationElement) {
            notificationElement.classList.add('read');
        }
    }
    
    loadNotifications(offset = 0, limit = 20) {
        this.socket.emit('get_notifications', { offset, limit });
    }
    
    handleNotificationsLoaded(data) {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        
        // Clear existing notifications if offset is 0
        if (data.offset === 0) {
            notificationsList.innerHTML = '';
        }
        
        // Add notifications to list
        data.notifications.forEach(notification => {
            this.addNotificationToPanel(notification);
        });
    }
    
    addNotificationToPanel(notification) {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        
        const notificationElement = this.createNotificationElement(notification);
        notificationsList.insertBefore(notificationElement, notificationsList.firstChild);
    }
    
    createNotificationElement(notification) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = `notification-item ${notification.type} ${notification.is_read ? 'read' : 'unread'}`;
        notificationDiv.dataset.notificationId = notification.id;
        
        notificationDiv.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${this.escapeHtml(notification.title)}</span>
                <span class="notification-time">${this.formatTimestamp(notification.created_at)}</span>
                ${!notification.is_read ? '<span class="unread-indicator"></span>' : ''}
            </div>
            <div class="notification-message">${this.escapeHtml(notification.message)}</div>
            ${notification.link ? `<div class="notification-actions">
                <a href="${notification.link}" class="notification-link">View Details</a>
            </div>` : ''}
        `;
        
        // Add click handler to mark as read
        if (!notification.is_read) {
            notificationDiv.addEventListener('click', () => {
                this.markNotificationRead(notification.id);
            });
        }
        
        return notificationDiv;
    }
    
    // Unread counts handling
    handleUnreadCounts(data) {
        this.unreadCounts = data;
        this.updateUnreadCountsUI();
    }
    
    updateUnreadCountsUI() {
        // Update notification bell badge
        const notificationBadge = document.getElementById('notification-badge');
        if (notificationBadge) {
            if (this.unreadCounts.total > 0) {
                notificationBadge.textContent = this.unreadCounts.total > 99 ? '99+' : this.unreadCounts.total;
                notificationBadge.style.display = 'block';
            } else {
                notificationBadge.style.display = 'none';
            }
        }
        
        // Update messages badge
        const messagesBadge = document.getElementById('messages-badge');
        if (messagesBadge) {
            if (this.unreadCounts.messages > 0) {
                messagesBadge.textContent = this.unreadCounts.messages;
                messagesBadge.style.display = 'block';
            } else {
                messagesBadge.style.display = 'none';
            }
        }
        
        // Update page title
        this.updatePageTitle();
    }
    
    updatePageTitle() {
        const originalTitle = document.title.replace(/^\(\d+\)\s*/, '');
        if (this.unreadCounts.total > 0) {
            document.title = `(${this.unreadCounts.total}) ${originalTitle}`;
        } else {
            document.title = originalTitle;
        }
    }
    
    // Admin specific methods
    handleNewOrderAlert(data) {
        if (!isAdmin) return;
        
        this.showToast(
            'New Order Received',
            'info',
            `Order #${data.order_id} from ${data.user}`,
            10000 // Show for 10 seconds
        );
        
        this.playSound('alert', 'high');
        
        // Update admin dashboard if visible
        this.updateAdminDashboard(data);
    }
    
    updateAdminDashboard(orderData) {
        const ordersList = document.getElementById('recent-orders-list');
        if (ordersList) {
            const orderElement = this.createOrderAlertElement(orderData);
            ordersList.insertBefore(orderElement, ordersList.firstChild);
        }
    }
    
    createOrderAlertElement(orderData) {
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-alert new-order';
        orderDiv.innerHTML = `
            <div class="order-info">
                <strong>Order #${orderData.order_id}</strong>
                <span class="user">from ${orderData.user}</span>
                <span class="subject">${orderData.subject}</span>
                <span class="time">${this.formatTimestamp(orderData.created_at)}</span>
            </div>
            <div class="order-actions">
                <a href="/admin/orders/${orderData.order_id}" class="btn btn-sm btn-primary">View</a>
            </div>
        `;
        
        return orderDiv;
    }
    
    // UI utility methods
    showToast(title, type = 'info', message = '', duration = 5000) {
        const toast = this.createToastElement(title, type, message);
        this.addToastToContainer(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
    }
    
    createToastElement(title, type, message) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        toast.innerHTML = `
            <div class="toast-header">
                <span class="toast-icon">${this.getToastIcon(type)}</span>
                <span class="toast-title">${this.escapeHtml(title)}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
            ${message ? `<div class="toast-message">${this.escapeHtml(message)}</div>` : ''}
        `;
        
        return toast;
    }
    
    addToastToContainer(toast) {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
    }
    
    removeToast(toast) {
        if (toast && toast.parentElement) {
            toast.classList.add('fade-out');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }
    }
    
    getToastIcon(type) {
        const icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'message': '💬'
        };
        return icons[type] || icons['info'];
    }
    
    toggleNotificationPanel() {
        const panel = document.getElementById('notification-panel');
        if (panel) {
            const isVisible = panel.style.display === 'block';
            panel.style.display = isVisible ? 'none' : 'block';
            
            if (!isVisible) {
                // Load notifications when panel is opened
                this.loadNotifications();
            }
        }
    }
    
    updateConnectionStatus(isConnected) {
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
            statusIndicator.title = isConnected ? 'Connected' : 'Disconnected';
        }
    }
    
    showMessageNotification(messageData) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`New message from ${messageData.username}`, {
                body: messageData.content,
                icon: '/static/images/message-icon.png',
                badge: '/static/images/badge-icon.png'
            });
        }
    }
    
    // Utility methods
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
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API methods
    enableSounds() {
        localStorage.setItem('notificationSounds', 'enabled');
        this.updateSoundToggleUI();
    }
    
    disableSounds() {
        localStorage.setItem('notificationSounds', 'disabled');
        this.updateSoundToggleUI();
    }
    
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                console.log('Notification permission:', permission);
            });
        }
    }
}

// Initialize socket client when DOM is loaded
let socketClient;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize socket client
    socketClient = new SocketClient();
    
    // Request notification permission
    socketClient.requestNotificationPermission();
    
    // Setup sound toggle
    const soundToggle = document.getElementById('sound-toggle');
    if (soundToggle) {
        soundToggle.addEventListener('click', () => {
            socketClient.toggleSounds();
        });
        socketClient.updateSoundToggleUI();
    }
    
    // Setup auto-join chat if on chat page
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        const chatId = chatContainer.dataset.chatId;
        if (chatId) {
            socketClient.joinChat(parseInt(chatId));
            
            // Mark messages as read when viewing chat
            socketClient.markMessagesRead(parseInt(chatId));
        }
    }
    
    // Setup page visibility change handler
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && socketClient.currentChat) {
            // Mark messages as read when page becomes visible
            socketClient.markMessagesRead(socketClient.currentChat);
        }
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (socketClient && socketClient.currentChat) {
        socketClient.leaveChat(socketClient.currentChat);
    }
});

// Global functions for external use
function joinChat(chatId) {
    if (socketClient) {
        socketClient.joinChat(chatId);
    }
}

function leaveChat(chatId) {
    if (socketClient) {
        socketClient.leaveChat(chatId);
    }
}

function markNotificationRead(notificationId) {
    if (socketClient) {
        socketClient.markNotificationRead(notificationId);
    }
}

function toggleNotificationPanel() {
    if (socketClient) {
        socketClient.toggleNotificationPanel();
    }
}