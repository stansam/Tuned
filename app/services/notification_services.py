from app.sockets.utils import send_system_notification, broadcast_to_admins
from app.models import User, Order
from app.extensions import db
from app.utils.emails import send_order_confirmation, send_order_created, send_order_completed_email, send_payment_completion_email, send_payment_confirmation_email, send_revision_request_email, send_extension_request_email

class NotificationService:
    """Service class for managing notifications"""
    
    @staticmethod
    def notify_assignment_status_change(order_id, status, user_id=None):
        """Notify user about assignment status change"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        target_user_id = user_id or order.client_id
        
        status_messages = {
            'confirmed': 'Your assignment has been confirmed and is being processed.',
            'in_progress': 'Work has started on your assignment.',
            'completed': 'Your assignment has been completed! Please check your dashboard.',
            'delivered': 'Your completed assignment has been delivered.',
            'revision': 'Your revision request has been recieved and is being processed',
            'cancelled': 'Your assignment has been cancelled.',
        }
        
        message = status_messages.get(status, f'Assignment status updated to: {status}')
        notification_type = 'success' if status in ['completed', 'delivered'] else 'info'
        priority = 'high' if status in ['completed', 'delivered', 'cancelled'] else 'normal'
        
        send_system_notification(
            user_id=target_user_id,
            title=f"Assignment #{order.id} - {status.title()}",
            message=message,
            notification_type=notification_type,
            link=f"/client/orders/{order.id}",
            priority=priority
        )
    
    @staticmethod
    def notify_new_order(order_id):
        """Notify admins about new order"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        # Send to all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        for admin in admin_users:
            send_system_notification(
                user_id=admin.id,
                title="New Order Received",
                message=f"New assignment order #{order.id} from {order.client.username}",
                notification_type='info',
                link=f"/admin/orders/{order.id}",
                priority='high'
            )
            send_order_created(admin, order)
        
        # Also broadcast to admin room
        broadcast_to_admins('new_order_alert', {
            'order_id': order.id,
            'user': order.client.username,
            'subject': getattr(order, 'subject', 'N/A'),
            'created_at': order.created_at.isoformat()
        })
    
    @staticmethod
    def notify_payment_received(order_id):
        """Notify about payment confirmation"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        send_system_notification(
            user_id=order.client_id,
            title="Payment Confirmed",
            message=f"Payment for assignment #{order.id} has been confirmed. Work will begin shortly.",
            notification_type='success',
            link=f"/client/orders/{order.id}",
            priority='high'
        )
    
    @staticmethod
    def notify_deadline_reminder(order_id, hours_remaining):
        """Send deadline reminder"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        message = f"Deadline reminder: Assignment #{order.id} is due in {hours_remaining} hours."
        
        send_system_notification(
            user_id=order.client_id,
            title="Deadline Reminder",
            message=message,
            notification_type='warning',
            link=f"/client/orders/{order.id}",
            priority='high'
        )
    
    # =============================================================================
    # ADMIN INCOMING NOTIFICATIONS (From Client to Admin)
    # =============================================================================

    @staticmethod
    def notify_new_user_registration(user_id):
        """Notify admins about new user registration"""
        user = User.query.get(user_id)
        if not user:
            return
        
        # Send to all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        for admin in admin_users:
            send_system_notification(
                user_id=admin.id,
                title="New User Registration",
                message=f"New user {user.username} ({user.email}) has registered on the platform.",
                notification_type='info',
                link=f"/admin/users/{user.id}",
                priority='normal'
            )
        
        # Broadcast to admin room
        broadcast_to_admins('new_user_registration', {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'registered_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
        })

    @staticmethod
    def notify_client_payment_complete(order_id):
        """Notify admins when client completes payment"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        admin_users = User.query.filter_by(is_admin=True).all()
        
        for admin in admin_users:
            send_system_notification(
                user_id=admin.id,
                title="Payment Completed",
                message=f"Client {order.client.username} has completed payment for order #{order.id}.",
                notification_type='success',
                link=f"/admin/orders/{order.id}",
                priority='high'
            )
            
        user = User.query.get(order.client_id)
        invoice = invoice.query.filter_by(order_id=order.id).first()
        send_payment_confirmation_email(invoice, user)

        broadcast_to_admins('payment_completed', {
            'order_id': order.id,
            'client_username': order.client.username,
            'amount': getattr(order, 'amount', 0),
            'paid_at': order.updated_at.isoformat() if hasattr(order, 'updated_at') else None
        })

    @staticmethod
    def notify_order_deadline_approaching_admin(order_id, hours_remaining):
        """Notify admins about approaching order deadline"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        admin_users = User.query.filter_by(is_admin=True).all()
        
        for admin in admin_users:
            send_system_notification(
                user_id=admin.id,
                title="Order Deadline Approaching",
                message=f"Order #{order.id} from {order.client.username} is due in {hours_remaining} hours.",
                notification_type='warning',
                link=f"/admin/orders/{order.id}",
                priority='high'
            )
        
        broadcast_to_admins('deadline_approaching', {
            'order_id': order.id,
            'client_username': order.client.username,
            'hours_remaining': hours_remaining,
            'deadline': order.deadline.isoformat() if hasattr(order, 'deadline') else None
        })

    @staticmethod
    def notify_order_marked_complete_by_client(order_id):
        """Notify admins when client accepts and marks order as complete"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        admin_users = User.query.filter_by(is_admin=True).all()
        
        for admin in admin_users:
            send_system_notification(
                user_id=admin.id,
                title="Order Completed by Client",
                message=f"Client {order.client.username} has accepted and marked order #{order.id} as complete.",
                notification_type='success',
                link=f"/admin/orders/{order.id}",
                priority='normal'
            )

        broadcast_to_admins('order_completed_by_client', {
            'order_id': order.id,
            'client_username': order.client.username,
            'completed_at': order.updated_at.isoformat() if hasattr(order, 'updated_at') else None
        })

    @staticmethod
    def notify_revision_requested(order_id, revision_message=None):
        """Notify admins when client requests order revision"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        admin_users = User.query.filter_by(is_admin=True).all()
        
        message = f"Client {order.client.username} has requested a revision for order #{order.id}."
        if revision_message:
            message += f" Message: {revision_message[:100]}..."

        user = User.query.get(order.client_id)
        send_revision_request_email(order, user)

        for admin in admin_users:
            send_system_notification(
                user_id=admin.id,
                title="Revision Requested",
                message=message,
                notification_type='warning',
                link=f"/admin/orders/{order.id}",
                priority='high'
            )
        
        broadcast_to_admins('revision_requested', {
            'order_id': order.id,
            'client_username': order.client.username,
            'revision_message': revision_message,
            'requested_at': order.updated_at.isoformat() if hasattr(order, 'updated_at') else None
        })

    # =============================================================================
    # ADMIN OUTGOING NOTIFICATIONS (From Admin to Client)
    # =============================================================================

    @staticmethod
    def notify_welcome_new_user(user_id):
        """Send welcome notification to new user"""
        user = User.query.get(user_id)
        if not user:
            return
        
        send_system_notification(
            user_id=user_id,
            title="Welcome to Tuned Essays!",
            message="Welcome! Your account has been successfully created. You can now place orders and manage your assignments through your dashboard.",
            notification_type='success',
            link="/client/dashboard",
            priority='normal'
        )

    @staticmethod
    def notify_order_received(order_id):
        """Notify client that order has been received"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        user = User.query.get(order.client_id)
        send_order_confirmation(order, user)

        send_system_notification(
            user_id=order.client_id,
            title="Order Received",
            message=f"We have received your order #{order.id}. Please complete the payment to begin processing.",
            notification_type='info',
            link=f"/client/orders/{order.id}",
            priority='normal'
        )

    @staticmethod
    def notify_complete_payment(order_id):
        """Notify client to complete payment"""
        order = Order.query.get(order_id)
        if not order:
            return
        user = User.query.get(order.client_id)

        send_payment_completion_email(user=user, order=order)
        send_system_notification(
            user_id=order.client_id,
            title="Complete Payment Required",
            message=f"Please complete payment for order #{order.id} to start processing your assignment.",
            notification_type='warning',
            link=f"/client/orders/{order.id}/payment",
            priority='high'
        )

    @staticmethod
    def notify_order_deadline_extension_request(order_id, reason=None):
        """Notify client about deadline extension request from admin"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        message = f"We are requesting an extension for order #{order.id}."
        if reason:
            message += f" Reason: {reason}"

        user = User.query.get(order.client_id)
        send_extension_request_email(order, user)

        send_system_notification(
            user_id=order.client_id,
            title="Deadline Extension Request",
            message=message,
            notification_type='info',
            link=f"/client/orders/{order.id}",
            priority='high'
        )

    @staticmethod
    def notify_order_delivered_awaiting_review(order_id):
        """Notify client that order is delivered and awaiting review"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        user = User.query.get(order.client_id)
        send_order_completed_email(order, user)

        send_system_notification(
            user_id=order.client_id,
            title="Order Delivered - Review Required",
            message=f"Your order #{order.id} has been delivered! Please review the work and confirm completion.",
            notification_type='success',
            link=f"/client/orders/{order.id}",
            priority='high'
        )

    @staticmethod
    def notify_order_revised_delivered(order_id):
        """Notify client that revised order has been delivered"""
        order = Order.query.get(order_id)
        if not order:
            return
        
        send_system_notification(
            user_id=order.client_id,
            title="Revised Order Delivered",
            message=f"Your revised order #{order.id} has been delivered! Please review the updated work.",
            notification_type='success',
            link=f"/client/orders/{order.id}",
            priority='high'
        )

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    @staticmethod
    def notify_multiple_users(user_ids, title, message, notification_type='info', link=None, priority='normal'):
        """Send notification to multiple users"""
        for user_id in user_ids:
            send_system_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link,
                priority=priority
            )

    @staticmethod
    def notify_all_admins(title, message, notification_type='info', link=None, priority='normal'):
        """Send notification to all admin users"""
        admin_users = User.query.filter_by(is_admin=True).all()
        admin_ids = [admin.id for admin in admin_users]
        
        NotificationService.notify_multiple_users(
            user_ids=admin_ids,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            priority=priority
        )