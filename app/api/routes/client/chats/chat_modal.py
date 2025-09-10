# app/routes/chat_modal.py
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Chat, ChatMessage
from app.models.user import User
from app.models.order import Order
from app.extensions import db
from app.services.chat_services import ChatService
from datetime import datetime

from app.api import api_bp


@api_bp.route('/client/chat/list')
@login_required
def get_user_chats():
    """Get all chats for the current user"""
    try:
        # Get user chats
        if current_user.is_admin:
            chats = Chat.query.filter_by(admin_id=current_user.id).order_by(
                Chat.created_at.desc()
            ).all()
        else:
            chats = Chat.query.filter_by(user_id=current_user.id).order_by(
                Chat.created_at.desc()
            ).all()
        
        chat_list = []
        for chat in chats:
            # Get last message
            last_message = ChatMessage.query.filter_by(
                chat_id=chat.id
            ).order_by(ChatMessage.created_at.desc()).first()
            
            # Count unread messages
            unread_count = ChatMessage.query.filter(
                ChatMessage.chat_id == chat.id,
                ChatMessage.user_id != current_user.id,
                ChatMessage.is_read == False
            ).count()
            
            chat_data = {
                'id': chat.id,
                'subject': chat.subject,
                'status': chat.status,
                'last_message': last_message.content if last_message else 'No messages yet',
                'unread_count': unread_count,
                # 'updated_at': chat.updated_at.isoformat(),
                'created_at': chat.created_at.isoformat()
            }
            chat_list.append(chat_data)
        
        return jsonify({
            'success': True,
            'chats': chat_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/client/chat/orders')
@login_required
def get_user_orders():
    """Get user's orders for chat creation"""
    try:
        # Get user's orders that can have chats
        orders = Order.query.filter_by(client_id=current_user.id).order_by(
            Order.created_at.desc()
        ).limit(20).all()
        
        order_list = []
        for order in orders:
            order_data = {
                'id': order.id,
                'subject': getattr(order, 'subject', f'Order #{order.id}'),
                'status': getattr(order, 'status', 'pending'),
                'created_at': order.created_at.isoformat()
            }
            order_list.append(order_data)
        
        return jsonify({
            'success': True,
            'orders': order_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/client/chat/create', methods=['POST'])
@login_required
def create_new_chat():
    """Create a new chat"""
    try:
        data = request.get_json()
        subject_type = data.get('type')  # 'general' or 'order'
        order_id = data.get('order_id')
        
        if not subject_type:
            return jsonify({
                'success': False,
                'error': 'Subject type is required'
            }), 400
        
        # Determine subject and admin
        if subject_type == 'general':
            subject = 'General Inquiry'
            order_id = None
        elif subject_type == 'order':
            if not order_id:
                return jsonify({
                    'success': False,
                    'error': 'Order ID is required for order chats'
                }), 400
            
            order = Order.query.get(order_id)
            if not order or order.client_id != current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Order not found or access denied'
                }), 403
            
            subject = f'Order #{order.id}'
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid subject type'
            }), 400
        
        
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            return jsonify({
                'success': False,
                'error': 'No admin available'
            }), 500
        
        
        if order_id:
            existing_chat = Chat.query.filter_by(
                user_id=current_user.id,
                order_id=order_id
            ).first()
            
            if existing_chat:
                return jsonify({
                    'success': True,
                    'chat': {
                        'id': existing_chat.id,
                        'subject': existing_chat.subject,
                        'status': existing_chat.status,
                        'created_at': existing_chat.created_at.isoformat()
                    }
                })
        
        # Create new chat
        chat = ChatService.create_chat(
            user_id=current_user.id,
            admin_id=admin_user.id,
            subject=subject,
            order_id=order_id
        )
        
        # Send initial welcome message from admin
        welcome_message = ChatService.send_automated_message(
            chat_id=chat.id,
            content="Hello! Thank you for reaching out. How can I assist you today?",
            from_admin=True
        )
        
        return jsonify({
            'success': True,
            'chat': {
                'id': chat.id,
                'subject': chat.subject,
                'status': chat.status,
                'admin_id': chat.admin_id,
                'created_at': chat.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/client/chat/<int:chat_id>/messages')
@login_required
def get_chat_messages(chat_id):
    """Get messages for a specific chat"""
    try:
        # Verify chat access
        chat = Chat.query.get(chat_id)
        if not chat or (chat.user_id != current_user.id and chat.admin_id != current_user.id):
            return jsonify({
                'success': False,
                'error': 'Chat not found or access denied'
            }), 403
        
        # Get messages
        messages = ChatMessage.query.filter_by(
            chat_id=chat_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        message_list = []
        for message in messages:
            message_data = {
                'id': message.id,
                'content': message.content,
                'user_id': message.user_id,
                'username': message.user.username,
                'is_own': message.user_id == current_user.id,
                'is_read': message.is_read,
                'created_at': message.created_at.isoformat()
            }
            message_list.append(message_data)
        
        # Mark messages as read for current user
        ChatMessage.query.filter(
            ChatMessage.chat_id == chat_id,
            ChatMessage.user_id != current_user.id,
            ChatMessage.is_read == False
        ).update({'is_read': True})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'chat': {
                'id': chat.id,
                'subject': chat.subject,
                'status': chat.status
            },
            'messages': message_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/client/chat/<int:chat_id>/close', methods=['POST'])
@login_required
def close_chat(chat_id):
    """Close a chat (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        chat = ChatService.close_chat(chat_id)
        
        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Chat closed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500