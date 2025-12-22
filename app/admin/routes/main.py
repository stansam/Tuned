from flask import render_template
from flask_login import login_required
from datetime import datetime
from app.extensions import db
from app.models.payment import Payment
from app.admin import admin_bp
from app.models.order import Order
from app.models.user import User
from app.models.communication import ChatMessage
from app.admin.routes.decorator import admin_required
from app.models.content import Testimonial

@admin_bp.route('/')
@login_required
@admin_required

def dashboard():
    users_count = User.query.filter_by(is_admin=False).count()
    orders_count = Order.query.count()
    unread_messages_count = ChatMessage.query.filter_by(is_read=False).count()
    pending_testimonials_count = Testimonial.query.filter_by(is_approved=False).count()
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Calculate client satisfaction rate (percentage of orders that weren't cancelled or refunded)
    total_completed_orders = Order.query.filter(Order.status == 'completed').count()
    total_orders_with_feedback = total_completed_orders or 1  # Avoid division by zero
    happy_clients_count = Order.query.filter(Order.status == 'completed').count()
    satisfaction_rate = int((happy_clients_count / total_orders_with_feedback) * 100)
    
    # Calculate order stats by status
    pending_count = Order.query.filter_by(status='pending').count()
    in_progress_count = Order.query.filter_by(status='active').count()
    completed_count = Order.query.filter_by(status='completed').count()
    cancelled_count = Order.query.filter_by(status='cancelled').count()
    revision_count = Order.query.filter_by(status='revision').count()
    overdue_count = Order.query.filter(Order.due_date < datetime.now()).count()
    
    # Calculate new vs returning clients
    total_clients = User.query.filter_by(is_admin=False).count()
    clients_with_multiple_orders = db.session.query(Order.client_id).group_by(Order.client_id).having(db.func.count(Order.id) > 1).count()
    new_clients = total_clients - clients_with_multiple_orders
    returning_rate = int((clients_with_multiple_orders / total_clients) * 100) if total_clients > 0 else 0
    
    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           orders_count=orders_count,
                           unread_messages_count=unread_messages_count,
                           pending_testimonials_count=pending_testimonials_count,
                           total_revenue=total_revenue,
                           recent_orders=recent_orders,
                           satisfaction_rate=satisfaction_rate,
                           pending_count=pending_count,
                           in_progress_count=in_progress_count,
                           completed_count=completed_count,
                           cancelled_count=cancelled_count,
                           revision_count=revision_count,
                           new_clients=new_clients,
                           returning_rate=returning_rate,
                           title="Admin Dashboard")