from app.extensions import db, socketio
from app.models.communication import ChatMessage, Notification, Chat
from app.models.user import User
from datetime import datetime

online_users = {}

def send_unread_counts(user_id):
    """Send unread counts to user"""
    try:
        user_id_int = int(user_id)
        
        # Count unread messages
        unread_messages = db.session.query(ChatMessage).join(Chat).filter(
            ((Chat.user_id == user_id_int) | (Chat.admin_id == user_id_int)) &
            (ChatMessage.user_id != user_id_int) &
            (ChatMessage.is_read == False)
        ).count()
        
        # Count unread notifications
        unread_notifications = Notification.query.filter_by(
            user_id=user_id_int,
            is_read=False
        ).count()
        
        # Emit to user's personal room
        socketio.emit('unread_counts', {
            'messages': unread_messages,
            'notifications': unread_notifications,
            'total': unread_messages + unread_notifications
        }, room=f"user_{user_id}")
        
    except Exception as e:
        print(f"Error sending unread counts: {e}")

# def mark_chat_messages_as_read(chat_id, user_id):
#     """Mark all messages in a chat as read for a user"""
#     try:
#         # Mark messages from other users as read
#         ChatMessage.query.filter(
#             ChatMessage.chat_id == chat_id,
#             ChatMessage.user_id != user_id,
#             ChatMessage.is_read == False
#         ).update({'is_read': True})
        
#         db.session.commit()
#     except Exception as e:
#         print(f"Error marking messages as read: {e}")
#         db.session.rollback()
def mark_chat_messages_as_read(chat_id, user_id):
    """Mark all unread messages in a chat as read for a user and return their IDs"""
    try:
        # Fetch messages from other users that are unread
        unread_messages = ChatMessage.query.filter(
            ChatMessage.chat_id == chat_id,
            ChatMessage.user_id != user_id,
            ChatMessage.is_read == False
        ).all()

        message_ids = [msg.id for msg in unread_messages]

        # Mark as read
        for msg in unread_messages:
            msg.is_read = True

        db.session.commit()
        return message_ids

    except Exception as e:
        print(f"Error marking messages as read: {e}")
        db.session.rollback()
        return []


def send_message_notification(user_id, chat, message, sender):
    """Send notification for new message"""
    try:
        # Create notification
        notification = Notification(
            user_id=user_id,
            title=f"New message from {sender.username}",
            message=f"Subject: {chat.subject}\nMessage: {message.content[:50]}...",
            type='message',
            link=f"/chat/{chat.id}"
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Send real-time notification
        socketio.emit('new_notification', {
            'notification': notification.to_dict(),
            'sound_type': 'message',
            'priority': 'normal'
        }, room=f"user_{user_id}")
        
    except Exception as e:
        print(f"Error sending message notification: {e}")
        db.session.rollback()

def send_system_notification(user_id, title, message, notification_type='info', link=None, priority='normal'):
    """Send system notification to user"""
    try:
        # Create notification
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            link=link
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Determine sound type
        sound_type = 'notification'
        if notification_type in ['error', 'warning']:
            sound_type = 'alert'
        elif notification_type == 'success':
            sound_type = 'success'
        
        # Send real-time notification
        socketio.emit('new_notification', {
            'notification': notification.to_dict(),
            'sound_type': sound_type,
            'priority': priority
        }, room=f"user_{user_id}")
        
        return notification
        
    except Exception as e:
        print(f"Error sending system notification: {e}")
        db.session.rollback()
        return None

def broadcast_to_admins(event, data):
    """Broadcast message to all admin users"""
    socketio.emit(event, data, room="admin_room")

def is_user_online(user_id):
    """Check if user is online"""
    return str(user_id) in online_users

def get_online_users():
    """Get list of online user IDs"""
    return list(online_users.keys())