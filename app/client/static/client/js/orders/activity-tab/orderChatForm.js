class OrderChatHandler {
    constructor(orderId, chatId = null) {
        this.orderId = orderId;
        this.chatId = chatId;
        this.isTyping = false;
        this.typingTimeout = null;
        
        this.initializeElements();
        this.bindEvents();
        this.setupSocketIntegration();
        
        if (this.chatId) {
            this.loadMessages();
        } else {
            this.createChatForOrder();
        }
    }

    initializeElements() {
        this.chatCard = document.getElementById('orderChatCard');
        this.messagesContainer = document.getElementById('orderChatMessagesContainer');
        this.textarea = document.getElementById('orderChatTextarea');
        this.sendBtn = document.getElementById('orderChatSendBtn');
        this.attachBtn = document.getElementById('orderChatAttachBtn');
        this.emojiBtn = document.getElementById('orderChatEmojiBtn');
        this.charCounter = document.getElementById('orderChatCharCounter');
        this.typingIndicator = document.getElementById('orderChatTypingIndicator');
        this.loading = document.getElementById('orderChatLoading');
        this.empty = document.getElementById('orderChatEmpty');
        this.chatTitle = document.getElementById('orderChatTitle');
        this.chatSubtitle = document.getElementById('orderChatSubtitle');
    }

    bindEvents() {
        // Send message on button click
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter (without Shift)
        this.textarea.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.textarea.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateCharCounter();
            this.handleTyping();
        });

        // Typing indicator
        this.textarea.addEventListener('focus', () => this.handleTyping());
        this.textarea.addEventListener('blur', () => this.handleStoppedTyping());

        // Optional: Attachment handling
        this.attachBtn.addEventListener('click', () => this.handleAttachment());
        
        // Optional: Emoji handling
        this.emojiBtn.addEventListener('click', () => this.handleEmoji());
    }

    setupSocketIntegration() {
        if (typeof socketClient !== 'undefined' && socketClient.socket) {
            // Extend existing socket functionality
            const originalHandleNewMessage = socketClient.handleNewMessage.bind(socketClient);
            socketClient.handleNewMessage = (data) => {
                originalHandleNewMessage(data);
                this.handleNewMessage(data);
            };

            // Listen for typing indicators
            socketClient.socket.on('user_typing', (data) => {
                if (data.chat_id === this.chatId) {
                    this.showTypingIndicator(data);
                }
            });

            socketClient.socket.on('user_stopped_typing', (data) => {
                if (data.chat_id === this.chatId) {
                    this.hideTypingIndicator(data);
                }
            });

            // Join chat room
            if (this.chatId) {
                socketClient.joinChat(this.chatId);
            }
        }
    }

    async createChatForOrder() {
        try {
            this.showLoading();
            
            const response = await fetch(`${API_BASE_URL}/client/chat/create`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.getElementById('csrfToken')?.value || ''
                },
                body: JSON.stringify({
                    type: 'order',
                    order_id: this.orderId
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.chatId = data.chat.id;
                this.updateChatInfo(data.chat);
                
                // Join socket room
                if (typeof socketClient !== 'undefined') {
                    socketClient.joinChat(this.chatId);
                }
                
                this.hideLoading();
                this.showEmpty();
            } else {
                throw new Error(data.error || 'Failed to create chat');
            }
        } catch (error) {
            console.error('Error creating chat:', error);
            this.hideLoading();
            this.showError('Failed to create chat: ' + error.message);
        }
    }

    async loadMessages() {
        try {
            this.showLoading();
            
            const response = await fetch(`${API_BASE_URL}/client/chat/${this.chatId}/messages`, {
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateChatInfo(data.chat);
                this.renderMessages(data.messages);
                
                // Mark messages as read
                if (typeof socketClient !== 'undefined') {
                    socketClient.markMessagesRead(this.chatId);
                }
            } else {
                throw new Error(data.error || 'Failed to load messages');
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Failed to load messages: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    sendMessage() {
        const content = this.textarea.value.trim();
        if (!content || !this.chatId) return;

        const tempId = 'temp-' + Date.now();

        // Add message to UI immediately
        this.addMessage({
            id: tempId,
            content: content,
            is_own: true,
            created_at: new Date().toISOString()
        });

        // Send via socket
        if (typeof socketClient !== 'undefined' && socketClient.socket) {
            socketClient.socket.emit('send_message', {
                chat_id: this.chatId,
                content: content,
                temp_id: tempId
            });
        }

        // Clear input
        this.textarea.value = '';
        this.autoResizeTextarea();
        this.updateCharCounter();
        this.handleStoppedTyping();
    }

    addMessage(messageData) {
        // Hide empty state
        this.hideEmpty();

        const messageDiv = document.createElement('div');
        messageDiv.className = `order-chat-message ${messageData.is_own ? 'order-chat-own' : 'order-chat-other'}`;
        messageDiv.dataset.messageId = messageData.id;

        const time = new Date(messageData.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });

        const formattedContent = this.formatMessageContent(messageData.content);

        messageDiv.innerHTML = `
            <div class="order-chat-message-bubble">
                ${formattedContent}
                <div class="order-chat-message-time">${time}</div>
            </div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    handleNewMessage(messageData) {
        if (messageData.chat_id === this.chatId) {
            // Handle temp message replacement
            if (messageData.temp_id) {
                const existingMessage = this.messagesContainer.querySelector(
                    `.order-chat-message[data-message-id="${messageData.temp_id}"]`
                );
                if (existingMessage) {
                    existingMessage.dataset.messageId = messageData.id;
                    const bubble = existingMessage.querySelector('.order-chat-message-bubble');
                    const time = new Date(messageData.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    bubble.innerHTML = `
                        ${this.formatMessageContent(messageData.content)}
                        <div class="order-chat-message-time">${time}</div>
                    `;
                    return;
                }
            }

            // Add new message
            this.addMessage({
                id: messageData.id,
                content: messageData.content,
                is_own: messageData.user_id === (window.currentUserId || currentUserId),
                created_at: messageData.created_at
            });
        }
    }

    renderMessages(messages) {
        this.messagesContainer.innerHTML = '';
        
        if (messages.length === 0) {
            this.showEmpty();
            return;
        }

        messages.forEach(message => {
            this.addMessage({
                id: message.id,
                content: message.content,
                is_own: message.user_id === (window.currentUserId || currentUserId),
                created_at: message.created_at
            });
        });

        this.scrollToBottom();
    }

    formatMessageContent(content) {
        // Convert line breaks to <br> tags
        return this.escapeHtml(content).replace(/\n/g, '<br>');
    }

    handleTyping() {
        if (!this.chatId || typeof socketClient === 'undefined') return;

        if (!this.isTyping) {
            this.isTyping = true;
            socketClient.socket.emit('user_typing', { chat_id: this.chatId });
        }

        // Reset timeout
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.handleStoppedTyping();
        }, 3000);
    }

    handleStoppedTyping() {
        if (this.isTyping && typeof socketClient !== 'undefined') {
            this.isTyping = false;
            socketClient.socket.emit('user_stopped_typing', { chat_id: this.chatId });
        }
        clearTimeout(this.typingTimeout);
    }

    showTypingIndicator(data) {
        if (data.user_id !== (window.currentUserId || currentUserId)) {
            this.typingIndicator.style.display = 'block';
            this.scrollToBottom();
        }
    }

    hideTypingIndicator(data) {
        this.typingIndicator.style.display = 'none';
    }

    autoResizeTextarea() {
        this.textarea.style.height = 'auto';
        this.textarea.style.height = Math.min(this.textarea.scrollHeight, 120) + 'px';
    }

    updateCharCounter() {
        const remaining = 2500 - this.textarea.value.length;
        this.charCounter.textContent = `${remaining} characters remaining`;
        
        if (remaining < 100) {
            this.charCounter.style.color = '#dc3545';
        } else {
            this.charCounter.style.color = '#6c757d';
        }
    }

    updateChatInfo(chatData) {
        this.chatTitle.textContent = chatData.subject || 'Order Discussion';
        this.chatSubtitle.textContent = `Order #${this.orderId}`;
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    showLoading() {
        this.loading.style.display = 'flex';
        this.empty.style.display = 'none';
    }

    hideLoading() {
        this.loading.style.display = 'none';
    }

    showEmpty() {
        this.empty.style.display = 'flex';
        this.loading.style.display = 'none';
    }

    hideEmpty() {
        this.empty.style.display = 'none';
    }

    showError(message) {
        if (typeof socketClient !== 'undefined' && socketClient.showToast) {
            socketClient.showToast(message, 'error');
        } else {
            console.error(message);
            // Fallback: show in chat
            this.messagesContainer.innerHTML = `
                <div style="text-align: center; color: #dc3545; padding: 20px;">
                    <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    handleAttachment() {
        // Implement file attachment logic
        console.log('Attachment button clicked');
        // You can integrate with your existing file upload system
    }

    handleEmoji() {
        // Implement emoji picker logic
        console.log('Emoji button clicked');
        // You can integrate with an emoji picker library
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    destroy() {
        // Cleanup
        if (this.chatId && typeof socketClient !== 'undefined') {
            socketClient.leaveChat(this.chatId);
        }
        clearTimeout(this.typingTimeout);
    }
}

// Global function to initialize order chat
window.initializeOrderChat = function(orderId, chatId = null) {
    return new OrderChatHandler(orderId, chatId);
};

