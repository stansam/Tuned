# notification_triggers.py
"""
Example usage of notification triggers in your Flask routes and background tasks.
These are example implementations showing how to integrate the notifications 
into your existing application workflow.
"""

from app.services.notification_services import NotificationService
from app.models.user import User
from app.models.order import Order
from app.extensions import db
from datetime import datetime, timedelta
from app.utils.emails import send_welcome_email
# from celery import Celery  # If you're using Celery for background tasks

# =============================================================================
# USER REGISTRATION FLOW
# =============================================================================

def handle_user_registration(user):
    """Called after successful user registration"""
    try:
        # Send welcome notification to new user
        NotificationService.notify_welcome_new_user(user.id)
        send_welcome_email(user) 
        # Notify admins about new registration
        NotificationService.notify_new_user_registration(user.id)
        
    except Exception as e:
        print(f"Error in user registration notifications: {e}")

# =============================================================================
# ORDER WORKFLOW NOTIFICATIONS
# =============================================================================

def handle_new_order_creation(order_id):
    """Called when a new order is created"""
    try:
        # Notify client that order was received
        NotificationService.notify_order_received(order_id)
        
        
        # Notify admins about new order
        NotificationService.notify_new_order(order_id)
        
        # Notify client to complete payment 
        order = Order.query.get(order_id)
        if order and not getattr(order, 'is_paid', False):
            NotificationService.notify_complete_payment(order_id)
            
    except Exception as e:
        print(f"Error in new order notifications: {e}")

def handle_payment_completion(order_id):
    """Called when client completes payment"""
    try:
        # Notify client that payment was received
        NotificationService.notify_payment_received(order_id)
        
        # Notify admins that payment is complete
        NotificationService.notify_client_payment_complete(order_id)
        
    except Exception as e:
        print(f"Error in payment completion notifications: {e}")

def handle_assignment_status_change(order_id, status):
    try:
        NotificationService.notify_assignment_status_change(order_id, status)
    except Exception as e:
        print(f"Error in order status change notification: {e}")

def handle_order_delivery(order_id):
    """Called when order is delivered to client"""
    try:
        # Notify client that order is delivered and awaiting review
        NotificationService.notify_order_delivered_awaiting_review(order_id)
        
    except Exception as e:
        print(f"Error in order delivery notifications: {e}")

def handle_revision_request(order_id, revision_message=None):
    """Called when client requests a revision"""
    try:
        # Notify admins about revision request
        NotificationService.notify_revision_requested(order_id, revision_message)
        
    except Exception as e:
        print(f"Error in revision request notifications: {e}")

def handle_revised_order_delivery(order_id):
    """Called when revised order is delivered"""
    try:
        # Notify client that revised order has been delivered
        NotificationService.notify_order_revised_delivered(order_id)
        
    except Exception as e:
        print(f"Error in revised order delivery notifications: {e}")

def handle_order_completion_by_client(order_id):
    """Called when client marks order as complete"""
    try:
        # Notify admins that client has accepted the order
        NotificationService.notify_order_marked_complete_by_client(order_id)
        
    except Exception as e:
        print(f"Error in order completion notifications: {e}")

def handle_deadline_extension_request(order_id, reason=None):
    """Called when admin requests deadline extension"""
    try:
        # Notify client about deadline extension request
        NotificationService.notify_order_deadline_extension_request(
            order_id, reason
        )
        
    except Exception as e:
        print(f"Error in deadline extension notifications: {e}")

# =============================================================================
# BACKGROUND TASKS (for deadline monitoring)
# =============================================================================

def check_approaching_deadlines():
    """Background task to check for approaching deadlines"""
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Check for deadlines in next 24 hours
        deadline_24h = now + timedelta(hours=24)
        orders_24h = Order.query.filter(
            Order.deadline <= deadline_24h,
            Order.deadline > now,
            Order.status.in_(['confirmed', 'in_progress']),  # Only active orders
            Order.deadline_24h_notified != True  # Only if not already notified
        ).all()
        
        for order in orders_24h:
            hours_remaining = int((order.deadline - now).total_seconds() / 3600)
            
            # Notify client
            NotificationService.notify_deadline_reminder(order.id, hours_remaining)
            
            # Notify admins
            NotificationService.notify_order_deadline_approaching_admin(order.id, hours_remaining)
            
            # Mark as notified to avoid duplicate notifications
            order.deadline_24h_notified = True
            
        # Check for deadlines in next 6 hours
        deadline_6h = now + timedelta(hours=6)
        orders_6h = Order.query.filter(
            Order.deadline <= deadline_6h,
            Order.deadline > now,
            Order.status.in_(['confirmed', 'in_progress']),
            Order.deadline_6h_notified != True
        ).all()
        
        for order in orders_6h:
            hours_remaining = int((order.deadline - now).total_seconds() / 3600)
            
            # Notify client
            NotificationService.notify_deadline_reminder(order.id, hours_remaining)
            
            # Notify admins
            NotificationService.notify_order_deadline_approaching_admin(order.id, hours_remaining)
            
            # Mark as notified
            order.deadline_6h_notified = True
        
        # Commit changes
        db.session.commit()
        
    except Exception as e:
        print(f"Error checking approaching deadlines: {e}")
        db.session.rollback()

# =============================================================================
# FLASK ROUTE EXAMPLES
# =============================================================================

# Example Flask route implementations
"""
@app.route('/register', methods=['POST'])
def register():
    # Your existing registration logic here
    user = User(...)
    db.session.add(user)
    db.session.commit()
    
    # Trigger notifications
    handle_user_registration(user.id)
    
    return jsonify({'success': True})

@app.route('/orders', methods=['POST'])
def create_order():
    # Your existing order creation logic
    order = Order(...)
    db.session.add(order)
    db.session.commit()
    
    # Trigger notifications
    handle_new_order_creation(order.id)
    
    return jsonify({'order_id': order.id})

@app.route('/orders/<int:order_id>/pay', methods=['POST'])
def complete_payment(order_id):
    # Your existing payment logic
    order = Order.query.get_or_404(order_id)
    order.is_paid = True
    order.payment_completed_at = datetime.utcnow()
    db.session.commit()
    
    # Trigger notifications
    handle_payment_completion(order_id)
    
    return jsonify({'success': True})

@app.route('/orders/<int:order_id>/deliver', methods=['POST'])
def deliver_order(order_id):
    # Your existing delivery logic
    order = Order.query.get_or_404(order_id)
    order.status = 'delivered'
    order.delivered_at = datetime.utcnow()
    db.session.commit()
    
    # Trigger notifications
    handle_order_delivery(order_id)
    
    return jsonify({'success': True})

@app.route('/orders/<int:order_id>/request-revision', methods=['POST'])
def request_revision(order_id):
    # Your existing revision request logic
    data = request.get_json()
    revision_message = data.get('message')
    
    order = Order.query.get_or_404(order_id)
    order.status = 'revision_requested'
    order.revision_message = revision_message
    db.session.commit()
    
    # Trigger notifications
    handle_revision_request(order_id, revision_message)
    
    return jsonify({'success': True})

@app.route('/orders/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    # Your existing order completion logic
    order = Order.query.get_or_404(order_id)
    order.status = 'completed'
    order.completed_at = datetime.utcnow()
    db.session.commit()
    
    # Trigger notifications
    handle_order_completion_by_client(order_id)
    
    return jsonify({'success': True})
"""

# =============================================================================
# CELERY TASK EXAMPLES (if using Celery)
# =============================================================================

# Example Celery tasks for background notification processing
"""
@celery.task
def send_deadline_reminders():
    check_approaching_deadlines()

@celery.task
def send_welcome_notifications(user_id):
    handle_user_registration(user_id)

@celery.task
def process_order_notifications(order_id, action):
    if action == 'created':
        handle_new_order_creation(order_id)
    elif action == 'paid':
        handle_payment_completion(order_id)
    elif action == 'delivered':
        handle_order_delivery(order_id)
    # ... etc
"""