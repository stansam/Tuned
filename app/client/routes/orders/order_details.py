from flask import render_template, current_app, send_file, abort
from app.models.order import Order, OrderComment, OrderFile
from app.models.order_delivery import OrderDelivery, OrderDeliveryFile
from app.models.content import Testimonial
from app.models.price import PriceRate
from app.models.service import Service
from flask_login import login_required, current_user
from datetime import datetime
import os
import zipfile
import io

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

@client_bp.route('/download_file/<int:file_id>')
@login_required
def download_file(file_id):
    """Download an order attachment file"""
    file = OrderFile.query.join(Order).filter(
        OrderFile.id == file_id,
        Order.client_id == current_user.id
    ).first_or_404()
    
    # file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file_path = os.path.abspath(file.file_path)
    print("DOWNLOADING FILE...")
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.filename
    )

@client_bp.route('/download_delivery_file/<int:file_id>')
@login_required
def download_delivery_file(file_id):
    """Download a delivery file"""
    delivery_file = OrderDeliveryFile.query.join(OrderDelivery).join(Order).filter(
        OrderDeliveryFile.id == file_id,
        Order.client_id == current_user.id
    ).first_or_404()
    
    # file_path = os.path.join(current_app.config['DELIVERY_UPLOAD_FOLDER'], delivery_file.filename)
    file_path = os.path.abspath(delivery_file.file_path)

    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=delivery_file.original_filename
    )

@client_bp.route('/download-order-files/<int:order_id>')
@login_required
def download_order_files(order_id):
    """Download all files for an order as a ZIP"""
    order = Order.query.filter_by(id=order_id, client_id=current_user.id).first_or_404()
    
    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add order attachment files
        for file in order.files:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            if os.path.exists(file_path):
                zip_file.write(file_path, f"attachments/{file.filename}")
        
        # Add delivery files
        for delivery in order.deliveries:
            for delivery_file in delivery.delivery_files:
                file_path = os.path.join(current_app.config['DELIVERY_UPLOAD_FOLDER'], delivery_file.filename)
                if os.path.exists(file_path):
                    zip_file.write(file_path, f"deliveries/{delivery_file.original_filename}")
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"order_{order.order_number}_files.zip",
        mimetype='application/zip'
    )