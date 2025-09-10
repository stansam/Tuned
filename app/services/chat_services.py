from app.models import Chat, ChatMessage, User
from app.extensions import db
# from app.sockets.utils import send_message_notification
from datetime import datetime

class ChatService:
    """Service class for managing chat operations"""
    
    @staticmethod
    def create_chat(user_id, admin_id, subject, order_id=None):
        """Create a new chat"""
        chat = Chat(
            user_id=user_id,
            admin_id=admin_id,
            subject=subject,
            order_id=order_id,
            status='active'
        )
        
        db.session.add(chat)
        db.session.commit()
        
        return chat
    
    @staticmethod
    def send_automated_message(chat_id, content, from_admin=True):
        """Send an automated message (from system/admin)"""
        chat = Chat.query.get(chat_id)
        if not chat:
            return None
        
        # Use admin_id if from_admin, otherwise use a system user
        sender_id = chat.admin_id if from_admin else 1  # Assuming user ID 1 is system
        
        message = ChatMessage(
            user_id=sender_id,
            chat_id=chat_id,
            content=content,
            is_read=False
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Send notification to other participant
        recipient_id = chat.user_id if from_admin else chat.admin_id
        sender = User.query.get(sender_id)
        
        # send_message_notification(recipient_id, chat, message, sender)
        
        return message
    
    @staticmethod
    def get_user_chats(user_id, is_admin=False):
        """Get all chats for a user"""
        if is_admin:
            chats = Chat.query.filter_by(admin_id=user_id).all()
        else:
            chats = Chat.query.filter_by(user_id=user_id).all()
        
        return chats
    
    @staticmethod
    def get_chat_with_messages(chat_id, user_id):
        """Get chat with messages if user has access"""
        chat = Chat.query.get(chat_id)
        if not chat or (chat.user_id != user_id and chat.admin_id != user_id):
            return None
        
        messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(
            ChatMessage.created_at.asc()
        ).all()
        
        return chat, messages
    
    @staticmethod
    def close_chat(chat_id):
        """Close a chat"""
        chat = Chat.query.get(chat_id)
        if chat:
            chat.status = 'closed'
            db.session.commit()
        
        return chat
