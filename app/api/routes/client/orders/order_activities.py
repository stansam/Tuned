from flask import request, jsonify, current_app
from app.models.order import Order, OrderComment, OrderFile, SupportTicket
from app.services.triggers.triggers import *
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.api import api_bp

@api_bp.route('/client/order/<int:order_id>/comments')
@login_required
def get_order_comments(order_id):
    """Get comments for an order"""
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    # comment_owner = 
    
    comments = []
    for comment in OrderComment.query.filter_by(user_id=current_user.id).order_by(OrderComment.created_at.desc()):
        comments.append({
            'message': comment.message,
            'username': current_user.username,
            'created_at': comment.created_at.isoformat()
        })
    
    return jsonify({'comments': comments})

@api_bp.route('/client/order/comment', methods=['POST'])
@login_required
def add_order_comment():
    """Add a comment to an order"""
    data = request.get_json()
    order_id = data.get('order_id')
    message = data.get('message')
    
    if not order_id or not message:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    
    comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        message=message,
        is_admin=False
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/client/order/upload', methods=['POST'])
@login_required
def upload_additional_files():
    """Upload additional files for an order"""
    order_id = request.form.get('order_id')
    files = request.files.getlist('files')
    
    if not order_id or not files:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 404
    
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    
    uploaded_files = []
    
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, f"{order_id}_{filename}")
            file.save(file_path)

            if not OrderFile.query.filter_by(order_id=order_id).first():
                from app.sockets.utils import send_system_notification
                from flask import url_for
                admin_user = User.query.filter_by(is_admin=True).first()
                send_system_notification(
                    user_id=admin_user.id,
                    title=f"New Files Added in Order number: #{order.order_number}",
                    message="Review Files Added By Client",
                    notification_type="info",
                    link=url_for('admin.view_order', order_id=order.id),
                    priority="high"
                )

            # Create database record
            order_file = OrderFile(
                order_id=order_id,
                filename=filename,
                file_path=file_path
            )
            
            db.session.add(order_file)
            uploaded_files.append(filename)
    
    db.session.commit()
    
    return jsonify({'success': True, 'uploaded_files': uploaded_files})

@api_bp.route('/client/order/<int:order_id>/deadline', methods=['PUT'])
@login_required
def update_order_deadline(order_id):
    """Update order deadline"""
    data = request.get_json()
    new_deadline = data.get('deadline')
    
    if not new_deadline:
        return jsonify({'success': False, 'error': 'Missing deadline'})
    
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    
    try:
        order.due_date = datetime.fromisoformat(new_deadline.replace('Z', '+00:00'))
        order.updated_at = datetime.now()
        db.session.commit()

        from app.sockets.utils import send_system_notification
        from flask import url_for
        admin_user = User.query.filter_by(is_admin=True).first()
        send_system_notification(
            user_id=admin_user.id,
            title=f"Deadline updated for Order number: #{order.order_number}",
            message="Review updated deadline By Client",
            notification_type="info",
            link=url_for('admin.view_order', order_id=order.id),
            priority="normal"
        )
        
        return jsonify({'success': True})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid deadline format'})

@api_bp.route('/client/order/<int:order_id>/complete', methods=['POST'])
@login_required
def mark_order_complete(order_id):
    """Mark order as completed"""
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    
    if not order.is_delivered:
        return jsonify({'success': False, 'error': 'Order has not been delivered yet'})
    
    order.status = 'completed'
    order.updated_at = datetime.now()
    db.session.commit()
    
    handle_assignment_status_change(order.id, status='completed')
    handle_order_completion_by_client(order.id)

    # send_anything_else_email(current_user)
    return jsonify({'success': True})

@api_bp.route('/client/order/<int:order_id>/revision', methods=['POST'])
@login_required
def request_revision(order_id):
    """Request revision for an order"""
    data = request.get_json()
    reason = data.get('revision_details')
    if not reason:
        reason = data.get('reason', '')
    
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    
    # Create a comment with the revision request
    comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        message=f"REVISION REQUEST: {reason}",
        is_admin=False
    )
    subject="Revision Request"
    support = SupportTicket(
        order_id=order_id,
        user_id=current_user.id,
        subject=subject,
        message=reason,
        status="open"
    )
    # Update order status
    order.status = 'revision'
    order.updated_at = datetime.now()
    
    db.session.add(comment)
    db.session.commit()

    db.session.add(support)
    db.session.commit()

    handle_revision_request(order.id, reason)
    handle_assignment_status_change(order.id, status='revision')

    # send_revision_request_email(order, current_user)
    return jsonify({'success': True})
