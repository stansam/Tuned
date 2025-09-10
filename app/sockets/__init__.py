from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request
from app.extensions import db, socketio
from app.models import Chat, ChatMessage, Notification, User
from datetime import datetime
from app.sockets.utils import send_unread_counts, mark_chat_messages_as_read, send_message_notification
import json

from .utils import online_users

def init_socketio_events(socketio):
    """Initialize all socket event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle user connection"""
        if not current_user.is_authenticated:
            disconnect()
            return False
        
        user_id = str(current_user.id)
        session_id = request.sid
        
        # Track online user
        if user_id not in online_users:
            online_users[user_id] = []
        online_users[user_id].append(session_id)
        
        # Join user to their personal room for notifications
        join_room(f"user_{user_id}")
        
        # Join admin users to admin room
        if current_user.is_admin:
            join_room("admin_room")
        
        # Emit connection status
        emit('connection_status', {
            'status': 'connected',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send unread counts
        send_unread_counts(user_id)
        
        print(f"User {current_user.username} connected with session {session_id}")
    
    @socketio.on('disconnect')
    def handle_disconnect(sid):
        """Handle user disconnection"""
        if not current_user.is_authenticated:
            return
        
        user_id = str(current_user.id)
        session_id = sid
        
        # Remove user from tracking
        if user_id in online_users:
            if session_id in online_users[user_id]:
                online_users[user_id].remove(session_id)
            if not online_users[user_id]:
                del online_users[user_id]
        
        print(f"User {current_user.username} disconnected")
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """Handle user joining a chat room"""
        if not current_user.is_authenticated:
            return
        
        chat_id = data.get('chat_id')
        if not chat_id:
            return
        
        # Verify user has access to this chat
        chat = Chat.query.get(chat_id)
        if not chat or (chat.user_id != current_user.id and chat.admin_id != current_user.id):
            emit('error', {'message': 'Access denied to this chat'})
            return
        
        # Join chat room
        join_room(f"chat_{chat_id}")
        
        # Mark messages as read
        message_ids = mark_chat_messages_as_read(chat_id, current_user.id)
        
        emit('messages_marked_read', {
            'chat_id': chat_id,
            'message_ids': message_ids,
            'user_id': current_user.id
        }, room=f"chat_{chat_id}")
        
        emit('joined_chat', {
            'chat_id': chat_id,
            'status': 'joined'
        })
    
    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """Handle user leaving a chat room"""
        chat_id = data.get('chat_id')
        if chat_id:
            leave_room(f"chat_{chat_id}")
            emit('left_chat', {'chat_id': chat_id})
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle sending chat messages"""
        if not current_user.is_authenticated:
            return
        
        chat_id = data.get('chat_id')
        content = data.get('content', '').strip()
        temp_id = data.get('temp_id')
        
        if not chat_id or not content:
            emit('error', {'message': 'Chat ID and content are required'})
            return
        
        # Verify chat access
        chat = Chat.query.get(chat_id)
        if not chat or (chat.user_id != current_user.id and chat.admin_id != current_user.id):
            emit('error', {'message': 'Access denied'})
            return
        
        # Create message
        message = ChatMessage(
            user_id=current_user.id,
            chat_id=chat_id,
            content=content,
            is_read=False
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Prepare message data
        message_data = {
            'id': message.id,
            'chat_id': chat_id,
            'user_id': current_user.id,
            'username': current_user.username,
            'content': content,
            'created_at': message.created_at.isoformat(),
            'is_read': False,
            'temp_id': temp_id
        }
        
        # Emit to chat room
        socketio.emit('new_message', message_data, room=f"chat_{chat_id}")
        
        # Send notification to other participant
        other_user_id = chat.admin_id if chat.user_id == current_user.id else chat.user_id
        # send_message_notification(other_user_id, chat, message, current_user)
        
        # Update unread counts
        send_unread_counts(str(other_user_id))
    
    @socketio.on('mark_messages_read')
    def handle_mark_messages_read(data):
        """Mark messages as read"""
        if not current_user.is_authenticated:
            return
        
        chat_id = data.get('chat_id')
        if not chat_id:
            return
        
        message_ids = mark_chat_messages_as_read(chat_id, current_user.id)
        
        # Update unread counts
        send_unread_counts(str(current_user.id))
        
        emit('messages_marked_read', {'chat_id': chat_id, 'message_ids': message_ids, 'user_id': current_user.id}, room=f"chat_{chat_id}")
    
    @socketio.on('mark_notification_read')
    def handle_mark_notification_read(data):
        """Mark notification as read"""
        if not current_user.is_authenticated:
            return
        
        notification_id = data.get('notification_id')
        if not notification_id:
            return
        
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if notification:
            notification.mark_as_read()
            send_unread_counts(str(current_user.id))
            emit('notification_marked_read', {'notification_id': notification_id})
    
    @socketio.on('get_notifications')
    def handle_get_notifications(data):
        """Get user notifications"""
        if not current_user.is_authenticated:
            return
        
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        
        notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Notification.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        notifications_data = [notif.to_dict() for notif in notifications]
        
        emit('notifications_loaded', {
            'notifications': notifications_data,
            'offset': offset,   
            'limit': limit,
            'total_count': Notification.query.filter_by(user_id=current_user.id).count()
        })
    
    @socketio.on('get_all_notifications')
    def handle_get_all_notifications(data):
        """Get all notifications for the modal with enhanced filtering support"""
        if not current_user.is_authenticated:
            return
        
        limit = data.get('limit', 100)  # Higher limit for modal
        offset = data.get('offset', 0)
        
        try:
            # Build query with optional filters
            query = Notification.query.filter_by(user_id=current_user.id)
            
            # Apply filters if provided
            notification_type = data.get('type')
            if notification_type:
                query = query.filter_by(type=notification_type)
            
            status = data.get('status')
            if status == 'read':
                query = query.filter_by(is_read=True)
            elif status == 'unread':
                query = query.filter_by(is_read=False)
            
            # Search functionality
            search_term = data.get('search')
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    db.or_(
                        Notification.title.ilike(search_pattern),
                        Notification.message.ilike(search_pattern)
                    )
                )
            
            # Order by created_at descending and apply pagination
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            # Get total count for pagination info
            total_count = query.count()
            
            notifications_data = [notif.to_dict() for notif in notifications]
            
            emit('all_notifications_loaded', {
                'notifications': notifications_data,
                'offset': offset,   
                'limit': limit,
                'total_count': total_count,
                'has_more': (offset + limit) < total_count
            })
            
        except Exception as e:
            print(f"Error getting all notifications: {e}")
            emit('error', {'message': 'Failed to load notifications'})

    @socketio.on_error_default
    def default_error_handler(e):
        print(f"Socket error: {e}")
        emit('error', {'message': 'An error occurred'})
    
    return socketio