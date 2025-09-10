from app.models.order import Order
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.extensions import db
from flask import request
import os
from app.utils.file_upload import allowed_file
import mimetypes



def _update_overdue_orders():
    """Helper function to update orders that have passed their due date"""
    
    try:
        overdue_orders = Order.query.filter(
            and_(
                Order.due_date < datetime.now(),
                ~Order.status.in_(['completed', 'completed pending review', 'canceled', 'overdue'])
            )
        ).all()
        
        for order in overdue_orders:
            order.status = 'overdue'
            order.updated_at = datetime.now()
        
        if overdue_orders:
            db.session.commit()
            order_ids = [order.id for order in overdue_orders]
            current_app.logger.info(
                f"Marked {len(overdue_orders)} orders as overdue. IDs: {order_ids}"
            )
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating overdue orders: {e}")

def _auto_complete_orders():
    """Helper function to auto-complete orders stuck in 'completed pending review' for more than 3 days"""
    
    try:
        three_days_ago = datetime.now() - timedelta(days=3)

        pending_orders = Order.query.filter(
            and_(
                Order.status == 'completed pending review',
                Order.updated_at < three_days_ago
            )
        ).all()

        for order in pending_orders:
            order.status = 'completed'
            order.updated_at = datetime.now()

        if pending_orders:
            db.session.commit()
            order_ids = [order.id for order in pending_orders]
            current_app.logger.info(
                f"Auto-completed {len(pending_orders)} orders stuck in 'completed pending review'. IDs: {order_ids}"
            )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error auto-completing pending review orders: {e}")


def detect_file_type(file):
    """
    Detect if uploaded file is a picture or regular file
    Returns 'picture' or 'file'
    """
    mime_type, _ = mimetypes.guess_type(file.filename)
    
    if mime_type and mime_type.startswith('image/'):
        return 'picture'
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'}
    file_ext = os.path.splitext(file.filename.lower())[1]
    
    if file_ext in image_extensions:
        return 'picture'
    
    return 'file'

def validate_file_size(file, max_size_mb=50):
    """
    Validate file size
    Returns True if valid, False otherwise
    """
    file.seek(0, 2)  
    file_size = file.tell()
    file.seek(0)  
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_uploaded_files():
    """
    Validate all uploaded files
    Returns (is_valid, error_message, validated_files)
    """
    uploaded_files = request.files.getlist('files') if 'files' in request.files else []
    validated_files = []
    
    for file in uploaded_files:
        if file and file.filename:
            if not validate_file_size(file, max_size_mb=50):
                return False, f'File too large (max 50MB): {file.filename}', []
            
            file_type = detect_file_type(file)
            
            if not allowed_file(file.filename, type=file_type):
                return False, f'File type not allowed: {file.filename}', []
            
            validated_files.append((file, file_type))
    
    return True, None, validated_files