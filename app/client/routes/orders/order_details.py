from flask import render_template
from app.models.order import Order, OrderComment
from app.models.order_delivery import OrderDelivery
from app.models.content import Testimonial
from app.models.price import PriceRate
from app.models.service import Service
from flask_login import login_required, current_user
from datetime import datetime

from app.client import client_bp

@client_bp.route('/order-details/<int:order_id>')
@login_required
def order_details(order_id):
    """Display order details page"""
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    comments = OrderComment.query.filter_by(order_id=order_id).order_by(OrderComment.created_at.asc()).all()
    testimonials = Testimonial.query.filter_by(order_id=order_id).first()
    service = Service.query.filter_by(id=order.service_id).first_or_404()
    deliveries = OrderDelivery.query.filter_by(order_id=order_id).order_by(OrderDelivery.delivered_at.desc()).all()
    price_rate = PriceRate.query.filter_by(
        pricing_category_id=service.pricing_category_id,
        academic_level_id=order.academic_level_id,
        deadline_id=order.deadline_id
    ).first()
    
    # Attach comments and deliveries to order for template
    order.comments = comments
    order.deliveries = deliveries
    
    
    return render_template(
        'client/orders/order_details.html', 
        order=order, 
        now=datetime.now(),
        price_per_page=price_rate.price_per_page if price_rate else 0,)