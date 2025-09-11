from flask import request, render_template, redirect, flash, url_for, current_app
from app.models.payment import Payment, Transaction, Refund, Invoice
from app.services.triggers.triggers import handle_payment_completion, handle_assignment_status_change
from datetime import datetime, timedelta
from app.models.order import Order 
from app.models.user import User
from flask_login import login_required, current_user
from app.admin.routes.decorator import admin_required
from app.admin import admin_bp
from app.extensions import db

@admin_bp.route('/payments/')
@login_required
@admin_required
def list_payments():
    """Display all payments with filtering options."""
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Base query
    query = Payment.query
    
    # Apply filters
    if status_filter:
        query = query.filter(Payment.status == status_filter)
        
    if search_query:
        query = query.join(Order).join(User).filter(
            (Order.order_number.ilike(f'%{search_query}%')) |
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (Payment.transaction_id.ilike(f'%{search_query}%'))
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Payment.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj + timedelta(days=1)  # Include the entire day
            query = query.filter(Payment.created_at < date_to_obj)
        except ValueError:
            pass
    
    # Get the sorted payments
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(getattr(Payment, sort_by).desc())
    else:
        query = query.order_by(getattr(Payment, sort_by).asc())
    
    payments = query.all()
    
    # Get stats for the sidebar
    completed_count = Payment.query.filter_by(status='completed').count()
    pending_count = Payment.query.filter_by(status='pending').count()
    failed_count = Payment.query.filter_by(status='failed').count()
    refunded_count = Payment.query.filter_by(status='refunded').count()
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    
    return render_template('admin/payments/list.html', 
                           payments=payments,
                           status_filter=status_filter,
                           search_query=search_query,
                           date_from=date_from,
                           date_to=date_to,
                           sort_by=sort_by,
                           sort_order=sort_order,
                           completed_count=completed_count,
                           pending_count=pending_count,
                           failed_count=failed_count,
                           refunded_count=refunded_count,
                           total_revenue=total_revenue,
                           title='Payment Management')

@admin_bp.route('/payments/<int:payment_id>')
@login_required
@admin_required
def view_payment(payment_id):
    """View detailed information about a specific payment."""
    payment = Payment.query.get_or_404(payment_id)
    refunds = Refund.query.filter_by(payment_id=payment_id).all()
    
    return render_template('admin/payments/view.html',
                           payment=payment,
                           refunds=refunds,
                           title=f'Payment Details')

@admin_bp.route('/payments/<int:payment_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_payment_status(payment_id):
    """Update the status of a payment."""
    payment = Payment.query.get_or_404(payment_id)
    new_status = request.form.get('status')
    
    if new_status not in ['pending', 'completed', 'failed', 'refunded']:
        flash('Invalid status value', 'danger')
        return redirect(url_for('admin.view_payment', payment_id=payment_id))
    
    payment.status = new_status
    
    # If marking as completed, set payment date
    if new_status == 'completed' and not payment.payment_date:
        payment.payment_date = datetime.now()
    
    # Update the order's payment status
    if payment.order:
        if new_status == 'completed':
            payment.order.payment_status = 'Paid'
        elif new_status == 'refunded':
            payment.order.payment_status = 'Refunded'
        elif new_status == 'pending':
            payment.order.payment_status = 'Pending'
        elif new_status == 'failed':
            payment.order.payment_status = 'Unpaid'
    
    db.session.commit()
    
    flash(f'Payment status updated to {new_status}', 'success')
    return redirect(url_for('admin.view_payment', payment_id=payment_id))

@admin_bp.route('/payments/<int:order_id>/record-payment', methods=['POST'])
@login_required
@admin_required
def record_payment(order_id):
    """Record a payment for an order."""
    order = Order.query.get_or_404(order_id)
    amount = request.form.get('amount', 0, type=float)
    payment_method = request.form.get('payment_method', 'manual')
    payment_date_str = request.form.get('payment_date', datetime.now())
    
    if amount <= 0:
        flash('Invalid payment amount', 'danger')
        return redirect(url_for('admin.view_order', order_id=order_id))
    payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d %H:%M")
    # Create payment record
    payment = Payment(
        order_id=order.id,
        user_id=order.client_id,
        amount=amount,
        method=payment_method,
        # transaction_id=f"ORD-{order.order_number}-{uuid.uuid4().hex[:8].upper()}",
        status='completed',
        # created_at=payment_date,
        # updated_at=datetime.now()
    )
    db.session.add(payment)
    db.session.flush()  
    invoice = Invoice(
        order_id=order.id,
        user_id=current_user.id,
        payment_id=payment.id,
        subtotal=order.total_price,
        total=order.total_price,
        due_date=order.due_date,
        paid=True
    )
    
    db.session.add(invoice)
    db.session.flush()

    handle_payment_completion(order.id)

    order.paid = True
    order.status = 'active'

    db.session.commit()
    
    handle_assignment_status_change(order.id, status='in_progress')
    
    flash('Payment recorded successfully', 'success')
    return redirect(url_for('admin.view_order', order_id=order_id))

@admin_bp.route('/payments/<int:payment_id>/refund', methods=['GET', 'POST'])
@login_required
@admin_required
def create_refund(payment_id):
    """Process a refund for a payment."""
    payment = Payment.query.get_or_404(payment_id)
    
    # Check if payment can be refunded
    if payment.status != 'completed':
        flash('Only completed payments can be refunded', 'danger')
        return redirect(url_for('admin.view_payment', payment_id=payment_id))
    
    if request.method == 'POST':
        amount = request.form.get('amount', 0, type=float)
        reason = request.form.get('reason', '')
        
        if amount <= 0 or amount > payment.amount:
            flash('Invalid refund amount', 'danger')
            return redirect(url_for('admin.create_refund', payment_id=payment_id))
        
        # Create refund
        refund = Refund(
            payment_id=payment_id,
            amount=amount,
            reason=reason,
            processed_by=current_user.id,
            status='processed',
            refund_date=datetime.now()
        )
        
        db.session.add(refund)
        
        # Update payment status to refunded if full refund
        if amount == payment.amount:
            payment.status = 'refunded'
            if payment.order:
                payment.order.payment_status = 'Refunded'
        
        db.session.commit()
        
        flash('Refund processed successfully', 'success')
        return redirect(url_for('admin.view_payment', payment_id=payment_id))
    
    return render_template('admin/payments/refund.html',
                           payment=payment,
                           title='Process Refund')

