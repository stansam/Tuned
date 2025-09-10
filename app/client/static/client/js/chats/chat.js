// static/js/chat_modal.js
class ClientChatModal {
    constructor() {
        this.currentView = 'landing';
        this.currentChatId = null;
        this.selectedSubjectType = null;
        this.selectedOrderId = null;
        this.isOpen = false;
        this.chats = [];
        this.orders = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadChats();
        this.loadOrders();
        
        // Connect to socket client if available
        if (typeof socketClient !== 'undefined') {
            this.socketClient = socketClient;
            this.setupSocketIntegration();
        }
    }

    initializeElements() {
        this.chatFab = document.getElementById('chatFab');
        this.messageFab = document.getElementById('messageFab');
        this.chatModal = document.getElementById('chatModal');
        this.backBtn = document.getElementById('backBtn');
        this.chatTitle = document.getElementById('chatTitle');
        
        // Pages
        this.chatLanding = document.getElementById('chatLanding');
        this.newChatPage = document.getElementById('newChatPage');
        this.chatScreen = document.getElementById('chatScreen');
        
        // Controls
        this.newChatBtn = document.getElementById('newChatBtn');
        this.createChatBtn = document.getElementById('createChatBtn');
        this.sendBtn = document.getElementById('sendBtn');
        this.messageInput = document.getElementById('messageInput');
        
        // Lists
        this.chatList = document.getElementById('chatList');
        this.chatMessages = document.getElementById('chatMessages');
        this.orderSelect = document.getElementById('orderSelect');
        this.orderSelectDropdown = document.getElementById('orderSelectDropdown');
        this.typingIndicator = document.getElementById('typingIndicator');
    }

    bindEvents() {
        // Toggle modal
        this.chatFab.addEventListener('click', () => this.toggleModal());
        this.messageFab.addEventListener('click', () => this.toggleModal());
        
        // Navigation
        this.backBtn.addEventListener('click', () => this.goBack());
        this.newChatBtn.addEventListener('click', () => this.showNewChatPage());
        
        // Subject selection
        document.querySelectorAll('.subject-option').forEach(option => {
            option.addEventListener('click', (e) => this.selectSubjectType(e));
        });
        
        // Order selection
        this.orderSelectDropdown.addEventListener('change', (e) => {
            this.selectedOrderId = e.target.value;
            this.updateCreateChatButton();
        });
        
        // Create chat
        this.createChatBtn.addEventListener('click', () => this.createNewChat());
        
        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());
        
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.chatModal.contains(e.target) && !this.chatFab.contains(e.target) && !this.messageFab.contains(e.target)) {
                this.closeModal();
            }
        });
    }

    setupSocketIntegration() {
        // Extend socket client functionality
        const originalHandleNewMessage = this.socketClient.handleNewMessage.bind(this.socketClient);
        this.socketClient.handleNewMessage = (data) => {
            originalHandleNewMessage(data);
            this.handleNewMessage(data);
        };

        if (this.socketClient.socket) {
            this.socketClient.socket.on('messages_marked_read', (data) => {
                if(data.user_id === currentUserId){
                    this.markMessagesAsRead(data.message_ids);
                } else {
                    this.markMyMessagesAsSeen(data.message_ids);
                }
            });
            // TODO : Implement user typing and stopped typing handlers
            
            this.socketClient.socket.on('user_typing', (data) => {
                this.handleTypingIndicator(data);
            });
            
            this.socketClient.socket.on('user_stopped_typing', (data) => {
                this.hideTypingIndicator(data);
            });
        }
    }

    async loadChats() {
        try {
            const response = await fetch(`${API_BASE_URL}/client/chat/list`, {
                credentials: "include"
            });
            const data = await response.json();
            
            if (data.success) {
                this.chats = data.chats;
                this.renderChatList();
            } else {
                this.showError('Failed to load chats: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading chats:', error);
            this.showError('Failed to load chats');
        }
    }

    async loadOrders() {
        try {
            const response = await fetch(`${API_BASE_URL}/client/chat/orders`, {
                credentials: "include"
            });
            const data = await response.json();
            
            if (data.success) {
                this.orders = data.orders;
                this.renderOrderSelect();
            } else {
                console.error('Failed to load orders:', data.error);
            }
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    }

    renderChatList() {
        this.chatList.innerHTML = '';
        
        if (this.chats.length === 0) {
            this.chatList.innerHTML = `
                <div style="text-align: center; color: #666; padding: 40px 20px;">
                    <div style="font-size: 48px; margin-bottom: 15px;"><i class="fas fa-solid fa-comment-dots"></i></div>
                    <p>No chats yet</p>
                    <p style="font-size: 14px; margin-top: 8px;">Start a conversation with us!</p>
                </div>
            `;
            return;
        }
        
        this.chats.forEach(chat => {
            const chatItem = this.createChatItem(chat);
            this.chatList.appendChild(chatItem);
        });
    }

    createChatItem(chat) {
        const div = document.createElement('div');
        div.className = 'chat-item';
        div.onclick = () => this.showChatScreen(chat.id);
        
        const icon = chat.subject.includes('Order') ? '<i class="fas fa-solid fa-clipboard-list"></i>' : '<i class="fas fa-solid fa-question"></i>';
        
        div.innerHTML = `
            <div class="chat-avatar">${icon}</div>
            <div class="chat-info">
                <div class="chat-subject">${this.escapeHtml(chat.subject)}</div>
                <div class="chat-preview">${this.escapeHtml(chat.last_message)}</div>
            </div>
            ${chat.unread_count > 0 ? `<div class="unread-badge">${chat.unread_count}</div>` : ''}
        `;
        
        return div;
    }

    renderOrderSelect() {
        this.orderSelectDropdown.innerHTML = '<option value="">Select an order...</option>';
        
        this.orders.forEach(order => {
            const option = document.createElement('option');
            option.value = order.id;
            option.textContent = `#${order.id} - ${order.subject}`;
            this.orderSelectDropdown.appendChild(option);
        });
    }

    async createNewChat() {
        if (!this.selectedSubjectType) return;
        
        this.createChatBtn.innerHTML = '<div class="loading-spinner"></div> Creating...';
        this.createChatBtn.disabled = true;
        
        try {
            const requestData = {
                type: this.selectedSubjectType
            };
            
            if (this.selectedSubjectType === 'order' && this.selectedOrderId) {
                requestData.order_id = parseInt(this.selectedOrderId);
            }
            
            const response = await fetch(`${API_BASE_URL}/client/chat/create`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.getElementById('csrfToken').value
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Add to local chats list
                const newChat = {
                    id: data.chat.id,
                    subject: data.chat.subject,
                    last_message: 'Chat created',
                    unread_count: 0,
                    updated_at: data.chat.created_at
                };
                
                this.chats.unshift(newChat);
                
                // Show chat screen
                this.showChatScreen(data.chat.id);
                
                // Reload chats to get updated data
                this.loadChats();
            } else {
                this.showError('Failed to create chat: ' + data.error);
            }
        } catch (error) {
            console.error('Error creating chat:', error);
            this.showError('Failed to create chat');
        } finally {
            this.createChatBtn.innerHTML = 'Create Chat';
            this.createChatBtn.disabled = false;
        }
    }

    async loadChatMessages(chatId) {
        try {
            const response = await fetch(`${API_BASE_URL}/client/chat/${chatId}/messages`, {
                credentials: "include"
            });
            const data = await response.json();
            
            if (data.success) {
                this.chatTitle.textContent = data.chat.subject;
                this.chatMessages.innerHTML = '';
                
                data.messages.forEach(message => {
                    this.addMessage(message);
                });
                
                this.scrollToBottom();
            } else {
                this.showError('Failed to load messages: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Failed to load messages');
        }
    }

    toggleModal() {
        if (this.isOpen) {
            this.closeModal();
        } else {
            this.openModal();
        }
    }

    openModal() {
        this.isOpen = true;
        this.chatModal.classList.add('active');
        this.chatFab.classList.add('active');
        this.showLandingPage();
        
        // Reload chats when opening modal
        this.loadChats();
    }

    closeModal() {
        this.isOpen = false;
        this.chatModal.classList.remove('active');
        this.chatFab.classList.remove('active');
        
        // Leave current chat if any
        if (this.currentChatId && this.socketClient) {
            this.socketClient.leaveChat(this.currentChatId);
        }
    }

    showLandingPage() {
        this.currentView = 'landing';
        this.chatLanding.style.display = 'flex';
        this.newChatPage.classList.remove('active');
        this.chatScreen.classList.remove('active');
        this.backBtn.style.display = 'none';
        this.chatTitle.innerHTML = '<i class="fas fa-solid fa-comment-dots"></i> Chat';
    }

    showNewChatPage() {
        this.currentView = 'newChat';
        this.chatLanding.style.display = 'none';
        this.newChatPage.classList.add('active');
        this.chatScreen.classList.remove('active');
        this.backBtn.style.display = 'block';
        this.chatTitle.textContent = 'New Chat';
        this.resetNewChatForm();
    }

    showChatScreen(chatId) {
        this.currentView = 'chat';
        this.currentChatId = chatId;
        this.chatLanding.style.display = 'none';
        this.newChatPage.classList.remove('active');
        this.chatScreen.classList.add('active');
        this.backBtn.style.display = 'block';
        
        // Load chat messages
        this.loadChatMessages(chatId);
        
        // Join chat room via socket
        if (this.socketClient) {
            this.socketClient.joinChat(chatId);
            this.socketClient.markMessagesRead(chatId);
        }
    }

    goBack() {
        if (this.currentView === 'chat' && this.socketClient && this.currentChatId) {
            this.socketClient.leaveChat(this.currentChatId);
        }
        this.showLandingPage();
    }

    selectSubjectType(e) {
        // Remove previous selection
        document.querySelectorAll('.subject-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Add selection to clicked option
        e.currentTarget.classList.add('selected');
        this.selectedSubjectType = e.currentTarget.dataset.type;
        
        // Show/hide order selection
        if (this.selectedSubjectType === 'order') {
            this.orderSelect.classList.add('active');
        } else {
            this.orderSelect.classList.remove('active');
            this.selectedOrderId = null;
        }
        
        this.updateCreateChatButton();
    }

    updateCreateChatButton() {
        const canCreate = this.selectedSubjectType === 'general' || 
                         (this.selectedSubjectType === 'order' && this.selectedOrderId);
        
        this.createChatBtn.disabled = !canCreate;
    }

    resetNewChatForm() {
        document.querySelectorAll('.subject-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        this.orderSelect.classList.remove('active');
        this.selectedSubjectType = null;
        this.selectedOrderId = null;
        this.createChatBtn.disabled = true;
    }

    sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content || !this.currentChatId) return;
        
        const tempId = 'temp-' + Date.now();

        // Add message to UI immediately
        this.addMessage({
            id: tempId,
            content: content,
            is_own: true,
            created_at: new Date().toISOString()
        });

        // Send via socket
        if (this.socketClient) {
            this.socketClient.socket.emit('send_message', {
                chat_id: this.currentChatId,
                content: content,
                temp_id: tempId
            });
        }
        
        
        this.messageInput.value = '';
        this.autoResizeTextarea();
    }

    addMessage(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${messageData.is_own ? 'own' : 'other'}`;
        messageDiv.dataset.messageId = messageData.id;
        
        
        const time = new Date(messageData.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${this.escapeHtml(messageData.content)}
                <div class="message-time">${time}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom(); 
    }

    handleNewMessage(messageData) {
        if (messageData.chat_id === this.currentChatId) {
            if(messageData.temp_id){
                const existing = this.chatMessages.querySelector(
                    `.message[data-message-id="${messageData.temp_id}"]`
                );
                if (existing) {
                    existing.dataset.messageId = messageData.id;
                    existing.querySelector('.message-bubble').innerHTML = `
                        ${this.escapeHtml(messageData.content)}
                        <div class="message-time">${new Date(messageData.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                        })}</div>
                    `;
                    return;
                }
            }

            this.addMessage({
                id: messageData.id,
                content: messageData.content,
                is_own: messageData.user_id === currentUserId,
                created_at: messageData.created_at
            });
        }
        
        // Update chat list
        this.updateChatInList(messageData);
    }

    markMessagesAsRead(messageIds) {
        messageIds.forEach(id => {
            const msgEl = this.chatMessages.querySelector(`.message[data-message-id="${id}"]`);
            if (msgEl) {
                msgEl.classList.add('read');
            }
        });
    }

    markMyMessagesAsSeen(messageIds) {
        messageIds.forEach(id => {
            const msgEl = this.chatMessages.querySelector(`.message[data-message-id="${id}"]`);
            if (msgEl) msgEl.classList.add('seen');
        });
    }

    updateChatInList(messageData) {
        const chatIndex = this.chats.findIndex(c => c.id === messageData.chat_id);
        if (chatIndex !== -1) {
            this.chats[chatIndex].last_message = messageData.content;
            this.chats[chatIndex].updated_at = messageData.created_at;
            
            if (messageData.user_id !== currentUserId && messageData.chat_id !== this.currentChatId) {
                this.chats[chatIndex].unread_count = (this.chats[chatIndex].unread_count || 0) + 1;
            }
            
            // Move to top of list
            const chat = this.chats.splice(chatIndex, 1)[0];
            this.chats.unshift(chat);
            
            // Re-render if on landing page
            if (this.currentView === 'landing') {
                this.renderChatList();
            }
        }
    }

    handleTypingIndicator(data) {
        if (data.chat_id === this.currentChatId && data.user_id !== currentUserId) {
            this.typingIndicator.style.display = 'block';
        }
    }

    hideTypingIndicator(data) {
        if (data.chat_id === this.currentChatId) {
            this.typingIndicator.style.display = 'none';
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        // You can integrate this with your existing toast system
        if (typeof socketClient !== 'undefined' && socketClient.showToast) {
            socketClient.showToast(message, 'error');
        } else {
            alert(message);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof currentUserId !== 'undefined' && currentUserId) {
        window.clientChatModal = new ClientChatModal();
    }
});