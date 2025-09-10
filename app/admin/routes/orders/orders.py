from app.admin.routes.samples.utils import validate_sample_data, process_image, extract_word_count
from flask import request, render_template, redirect, flash, url_for, jsonify, current_app
from app.models.order import Order, OrderComment, OrderFile, SupportTicket
from app.models.order_delivery import OrderDelivery, OrderDeliveryFile
from app.models.payment import Payment
from app.models.communication import Chat
from sqlalchemy import func, and_
from app.admin.routes.decorator import admin_required
from flask_login import login_required, current_user
# from werkzeug.exceptions import RequestEntityTooLarge
# from app.models.service import Service
# from app.models.user import User
from app.admin import admin_bp
from app.extensions import db
from datetime import datetime
import os

@admin_bp.route('/orders')
@login_required
@admin_required
def list_orders():
    """Display all orders with filtering options."""
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Base query
    query = Order.query
    
    # Apply filters
    if status_filter:
        query = query.filter(Order.status == status_filter)
        
    if search_query:
        query = query.filter(
            (Order.order_number.ilike(f'%{search_query}%')) |
            (Order.subject.ilike(f'%{search_query}%')) |
            (Order.topic.ilike(f'%{search_query}%'))
        )
    
    # Get the sorted orders
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(getattr(Order, sort_by).desc())
    else:
        query = query.order_by(getattr(Order, sort_by).asc())
    
    orders = query.all()
    
    # Get stats for the sidebar
    pending_count = Order.query.filter_by(status='pending').count()
    in_progress_count = Order.query.filter_by(status='active').count()
    under_review_count = Order.query.filter_by(status='completed pending review').count()
    completed_count = Order.query.filter_by(status='completed').count()
    revision_count = Order.query.filter_by(status='revision').count()
    now = datetime.now()
    return render_template('admin/orders/list.html', 
                           orders=orders,
                           status_filter=status_filter,
                           search_query=search_query,
                           sort_by=sort_by,
                           sort_order=sort_order,
                           pending_count=pending_count,
                           in_progress_count=in_progress_count,
                           under_review_count=under_review_count,
                           completed_count=completed_count,
                           revision_count=revision_count,
                           now=now,
                           title='Order Management')

@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def view_order(order_id):
    """View detailed information about a specific order."""
    order = Order.query.get_or_404(order_id)
    comments = OrderComment.query.filter_by(order_id=order_id).order_by(OrderComment.created_at.desc()).all()
    files = OrderFile.query.filter_by(order_id=order_id).all()
    delivery = OrderDelivery.query.filter_by(order_id=order_id).first()
    chat = Chat.query.filter_by(order_id=order_id).first()
    if not chat:
        chat = []
    support_ticket = SupportTicket.query.filter_by(order_id=order_id).first()
    print(support_ticket)
    if not support_ticket:
        support_ticket = []
    # print(delivery)
    if delivery:           
        admin_files = OrderDeliveryFile.query.filter_by(delivery_id=delivery.id).all()
    else:
        admin_files = []
    payments = Payment.query.filter_by(order_id=order_id).all()
    
    client_stats = {
        'total_orders': Order.query.filter_by(client_id=order.client_id).count(),
        'total_spent': db.session.query(
            func.coalesce(func.sum(Order.total_price), 0.0)
        ).filter(
            and_(
                Order.client_id == order.client_id,
                Order.paid == True
            )
        ).scalar(),
        'joined_days': (datetime.now() - order.client.created_at).days
    }

    return render_template('admin/orders/view.html',
                           order=order,
                           chat=chat,
                           comments=comments,
                           files=files,
                           admin_files=admin_files,
                           payments=payments,
                           
                           client_stats=client_stats,
                           datetime=datetime.now(),
                           support_ticket=support_ticket,
                           title=f'Order #{order.order_number}')



@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_status(order_id):
    """Update the status of an order."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status not in ['pending', 'active', 'completed', 'cancelled', 'revision', 'overdue']:
        flash('Invalid status value', 'danger')
        return redirect(url_for('admin.view_order', order_id=order_id))
    
    # If marking as completed, set completion date
    if new_status == 'completed' and order.status != 'completed':
        order.completion_date = datetime.now()
    
    order.status = new_status
    db.session.commit()
    # notify(current_user,
    #         title=f"Order #{order.order_number} status updated to {new_status}",
    #         message="Order status updated successfully",
    #         type='info',
    #         link=url_for('admin.view_order', order_id=order.id))
    # notify(order.client,
    #         title=f"Your order #{order.order_number} status updated to {new_status}",
    #         message="Order status updated successfully",
    #         type='info',
    #         link=url_for('orders.order_detail', order_number=order.id))
    flash(f'Order status updated to {new_status}', 'success')
    return redirect(url_for('admin.view_order', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/add-comment', methods=['POST'])
@login_required
@admin_required
def add_comment(order_id):
    """Add a comment to an order."""
    order = Order.query.get_or_404(order_id)
    message = request.form.get('message')
    
    if not message:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('admin.view_order', order_id=order_id))
    
    comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        message=message,
        is_admin=True
    )
    # notify(current_user,
    #         title=f"Comment added to Order #{order.order_number}",
    #         message=message,
    #         type='info',
    #         link=url_for('admin.view_order', order_id=order.id))
    # notify(order.client,
    #         title=f"New comment on your Order #{order.order_number}",
    #         message=message,
    #         type='info',
    #         link=url_for('client.view_order', order_id=order.id))
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully', 'success')
    return redirect(url_for('admin.view_order', order_id=order_id))
