from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models.order import SupportTicket
from app.models.user import User
from app.models.order import Order
from app.sockets.utils import send_system_notification
from app.utils.emails import send_ticket_status_update_email
from datetime import datetime
from app.api import api_bp as admin_api 


# Admin required decorator
def admin_required(f):
    """Decorator to ensure only admins can access certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin privileges required'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


@admin_api.route('/admin/support-tickets/<int:ticket_id>/status', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_ticket_status(ticket_id):
    """
    Update the status of a support ticket.
    
    Expected JSON payload:
    {
        "status": "open|in_progress|closed",
        "admin_note": "Optional note about the status change"
    }
    
    Returns:
        JSON response with success status and updated ticket data
    """
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Status field is required'
            }), 400
        
        new_status = data.get('status', '').strip().lower()
        admin_note = data.get('admin_note', '').strip()
        
        # Validate status value
        valid_statuses = ['open', 'in_progress', 'closed']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Fetch the ticket
        ticket = SupportTicket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({
                'success': False,
                'message': f'Support ticket with ID {ticket_id} not found'
            }), 404
        
        # Store old status for comparison
        old_status = ticket.status
        
        # Check if status is actually changing
        if old_status == new_status:
            return jsonify({
                'success': True,
                'message': 'Ticket status is already set to this value',
                'data': {
                    'ticket_id': ticket.id,
                    'status': ticket.status,
                    'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None
                }
            }), 200
        
        # Update the ticket
        ticket.status = new_status
        ticket.updated_at = datetime.now()
        
        # If admin note is provided, you might want to store it
        # (You'd need to add an admin_notes field or create a TicketNote model)
        if admin_note:
            # Option 1: Add to existing message field (not recommended for production)
            # ticket.admin_notes = admin_note
            
            # Option 2: Log it (recommended for now)
            current_app.logger.info(f"Admin note for ticket {ticket_id}: {admin_note}")
        
        # Commit the changes
        db.session.commit()
        
        # Send notification to the user
        try:
            user = ticket.user
            if user:
                # Create notification message based on status
                status_messages = {
                    'open': 'Your support ticket has been reopened',
                    'in_progress': 'Your support ticket is being processed',
                    'closed': 'Your support ticket has been resolved and closed'
                }
                
                notification_message = status_messages.get(
                    new_status,
                    f'Your support ticket status has been updated to {new_status}'
                )
                
                # Send in-app notification
                send_system_notification(
                    user.id,
                    f"Ticket #{ticket.id} - Status Update",
                    notification_message,
                    type='info',
                    link=f"/orders/{ticket.order_id}"
                )
                
                # Send email notification
                send_ticket_status_update_email(
                    user=user,
                    ticket=ticket,
                    old_status=old_status,
                    new_status=new_status,
                    admin_note=admin_note
                )
        except Exception as e:
            # Log the error but don't fail the request
            current_app.logger.error(f"Failed to send notification for ticket {ticket_id}: {str(e)}")
        
        # Log the action
        current_app.logger.info(
            f"Admin {current_user.username} (ID: {current_user.id}) "
            f"updated ticket {ticket_id} status from '{old_status}' to '{new_status}'"
        )
        
        return jsonify({
            'success': True,
            'message': f'Ticket status successfully updated to {new_status}',
            'data': {
                'ticket_id': ticket.id,
                'order_id': ticket.order_id,
                'subject': ticket.subject,
                'status': ticket.status,
                'old_status': old_status,
                'updated_at': ticket.updated_at.isoformat(),
                'updated_by': current_user.username
            }
        }), 200
        
    except Exception as e:
        # Rollback the transaction
        db.session.rollback()
        
        # Log the error
        current_app.logger.error(f"Error updating ticket {ticket_id} status: {str(e)}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the ticket status',
            'error': str(e) if current_app.debug else 'Internal server error'
        }), 500


@admin_api.route('/admin/support-tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_ticket(ticket_id):
    """
    Delete a support ticket (soft delete recommended, hard delete implemented).
    
    Query parameters:
        - force: Set to 'true' for hard delete (optional)
    
    Returns:
        JSON response with success status
    """
    try:
        # Check if force delete is requested
        force_delete = request.args.get('force', 'false').lower() == 'true'
        
        # Fetch the ticket
        ticket = SupportTicket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({
                'success': False,
                'message': f'Support ticket with ID {ticket_id} not found'
            }), 404
        
        # Store ticket information for logging and response
        ticket_info = {
            'ticket_id': ticket.id,
            'order_id': ticket.order_id,
            'user_id': ticket.user_id,
            'subject': ticket.subject,
            'status': ticket.status,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None
        }
        
        # Get user for notification (before deletion)
        user = ticket.user
        order_id = ticket.order_id
        
        # Soft delete option (recommended for production)
        # If you want to implement soft delete, add a 'deleted_at' column to your model
        # and uncomment the following:
        
        # if not force_delete:
        #     ticket.deleted_at = datetime.now()
        #     ticket.status = 'deleted'
        #     db.session.commit()
        #     delete_type = 'soft'
        # else:
        #     # Hard delete
        #     db.session.delete(ticket)
        #     db.session.commit()
        #     delete_type = 'hard'
        
        # Hard delete (current implementation)
        db.session.delete(ticket)
        db.session.commit()
        delete_type = 'hard'
        
        # Send notification to user (optional - might not want to notify on deletion)
        try:
            if user:
                send_system_notification(
                    user.id,
                    "Support Ticket Closed",
                    f"Your support ticket regarding '{ticket_info['subject']}' has been resolved and removed from the system.",
                    type='info',
                    link=f"/orders/{order_id}"
                )
        except Exception as e:
            current_app.logger.error(f"Failed to send deletion notification for ticket {ticket_id}: {str(e)}")
        
        # Log the deletion
        current_app.logger.warning(
            f"Admin {current_user.username} (ID: {current_user.id}) "
            f"performed {delete_type} delete on ticket {ticket_id} "
            f"(Order: {ticket_info['order_id']}, User: {ticket_info['user_id']})"
        )
        
        return jsonify({
            'success': True,
            'message': f'Support ticket successfully deleted',
            'data': {
                'deleted_ticket': ticket_info,
                'delete_type': delete_type,
                'deleted_by': current_user.username,
                'deleted_at': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        # Rollback the transaction
        db.session.rollback()
        
        # Log the error
        current_app.logger.error(f"Error deleting ticket {ticket_id}: {str(e)}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the ticket',
            'error': str(e) if current_app.debug else 'Internal server error'
        }), 500


@admin_api.route('/admin/support-tickets/<int:ticket_id>/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_ticket_action(ticket_id):
    """
    Perform bulk actions on multiple tickets.
    
    Expected JSON payload:
    {
        "action": "update_status|delete",
        "ticket_ids": [1, 2, 3, 4],
        "status": "closed"  # Required only for update_status action
    }
    
    Returns:
        JSON response with results for each ticket
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'action' not in data or 'ticket_ids' not in data:
            return jsonify({
                'success': False,
                'message': 'action and ticket_ids fields are required'
            }), 400
        
        action = data.get('action', '').strip().lower()
        ticket_ids = data.get('ticket_ids', [])
        
        # Validate action
        valid_actions = ['update_status', 'delete']
        if action not in valid_actions:
            return jsonify({
                'success': False,
                'message': f'Invalid action. Must be one of: {", ".join(valid_actions)}'
            }), 400
        
        # Validate ticket_ids
        if not isinstance(ticket_ids, list) or len(ticket_ids) == 0:
            return jsonify({
                'success': False,
                'message': 'ticket_ids must be a non-empty array'
            }), 400
        
        # Limit bulk operations to prevent abuse
        if len(ticket_ids) > 100:
            return jsonify({
                'success': False,
                'message': 'Maximum 100 tickets can be processed at once'
            }), 400
        
        results = {
            'success': [],
            'failed': []
        }
        
        if action == 'update_status':
            new_status = data.get('status', '').strip().lower()
            valid_statuses = ['open', 'in_progress', 'closed']
            
            if new_status not in valid_statuses:
                return jsonify({
                    'success': False,
                    'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                }), 400
            
            for ticket_id in ticket_ids:
                try:
                    ticket = SupportTicket.query.get(ticket_id)
                    if ticket:
                        old_status = ticket.status
                        ticket.status = new_status
                        ticket.updated_at = datetime.now()
                        db.session.commit()
                        
                        results['success'].append({
                            'ticket_id': ticket_id,
                            'old_status': old_status,
                            'new_status': new_status
                        })
                        
                        # Send notification
                        try:
                            if ticket.user:
                                send_system_notification(
                                    ticket.user.id,
                                    f"Ticket #{ticket.id} - Status Update",
                                    f"Your support ticket status has been updated to {new_status}",
                                    type='info',
                                    link=f"/orders/{ticket.order_id}"
                                )
                        except Exception:
                            pass
                    else:
                        results['failed'].append({
                            'ticket_id': ticket_id,
                            'reason': 'Ticket not found'
                        })
                except Exception as e:
                    db.session.rollback()
                    results['failed'].append({
                        'ticket_id': ticket_id,
                        'reason': str(e)
                    })
        
        elif action == 'delete':
            for ticket_id in ticket_ids:
                try:
                    ticket = SupportTicket.query.get(ticket_id)
                    if ticket:
                        db.session.delete(ticket)
                        db.session.commit()
                        results['success'].append({
                            'ticket_id': ticket_id,
                            'action': 'deleted'
                        })
                    else:
                        results['failed'].append({
                            'ticket_id': ticket_id,
                            'reason': 'Ticket not found'
                        })
                except Exception as e:
                    db.session.rollback()
                    results['failed'].append({
                        'ticket_id': ticket_id,
                        'reason': str(e)
                    })
        
        # Log bulk action
        current_app.logger.info(
            f"Admin {current_user.username} performed bulk {action} on "
            f"{len(results['success'])} tickets (Failed: {len(results['failed'])})"
        )
        
        return jsonify({
            'success': True,
            'message': f'Bulk {action} completed',
            'data': {
                'total_processed': len(ticket_ids),
                'successful': len(results['success']),
                'failed': len(results['failed']),
                'results': results
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk ticket action: {str(e)}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': 'An error occurred during bulk operation',
            'error': str(e) if current_app.debug else 'Internal server error'
        }), 500


