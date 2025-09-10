from flask import redirect, render_template, url_for, flash
from flask_login import login_required, current_user
from app.models.order import Order 
from app.client import client_bp

@client_bp.route('/checkout/<int:order_id>')
@login_required
def checkout(order_id):
    """Display checkout page for an order with Fastlane integration"""
    order = Order.query.get_or_404(order_id)
    if order.client_id != current_user.id:
        flash('Access denied: This order does not belong to you.', 'error')
        return redirect(url_for('orders.list_orders'))
        
    if order.paid:
        flash('This order has already been paid for.', 'info')
        return redirect(url_for('orders.list_orders'))
    return render_template('client/payment/checkout.html', order=order)