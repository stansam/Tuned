from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from sqlalchemy import or_, and_, desc, asc
import mimetypes
import logging
import uuid
from app.extensions import db
from app.models.order import Order, OrderFile, SupportTicket
from app.models.user import User
from app.models.service import Service, AcademicLevel, Deadline
import logging
import requests

from app.client import client_bp
from app.client.routes.orders.utils import _update_overdue_orders

# from app.routes.main import notify
# from app.routes.api import calculate_price
# from app.utils.file_upload import allowed_file
# from app.utils.emails import send_payment_completion_email, send_order_created, send_order_confirmation


@client_bp.route('/orders')
@login_required
def list_orders():
    """Display client orders with filtering, sorting, and search functionality"""

    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort_by', 'date')
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  
    
    query = Order.query.filter_by(client_id=current_user.id)
    
    if status_filter and status_filter != 'all':
        if status_filter == 'completed':
            query = query.filter(Order.status.in_(['completed', 'completed pending review']))
        elif status_filter == 'overdue':
            query = query.filter(
                and_(
                    Order.due_date < datetime.now(),
                    ~Order.status.in_(['completed', 'completed pending review', 'canceled'])
                )
            )
        else:
            query = query.filter_by(status=status_filter)
    
    if search_query:
        search_term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Order.title.ilike(search_term),
                Order.order_number.ilike(search_term),
                Order.description.ilike(search_term)
            )
        )
    
    if sort_by == 'date':
        query = query.order_by(desc(Order.created_at))
    elif sort_by == 'title':
        query = query.order_by(asc(Order.title))
    elif sort_by == 'deadline':
        query = query.order_by(asc(Order.due_date))
    elif sort_by == 'price':
        query = query.order_by(desc(Order.total_price))
    else:
        query = query.order_by(desc(Order.created_at))
    
    orders = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    _update_overdue_orders()
    
    return render_template(
        'client/orders.html',
        orders=orders,
        current_status=status_filter,
        sort_by=sort_by,
        search_query=search_query
    )

@client_bp.route('/orders/refresh')
@login_required
def refresh_orders_data():
    """
    AJAX endpoint to refresh dashboard data without full page reload
    """
    try:
        # This could be used for real-time updates if needed
        return redirect(url_for('client.list_orders'))
    except Exception as e:
        logging.error(f"Error refreshing orders: {str(e)}")
        flash('Unable to refresh orders data', 'error')
        return redirect(url_for('client.list_orders'))


@client_bp.route('/orders/status-counts')
@login_required
def get_order_status_counts():
    """API endpoint to get order counts by status for current user"""
    
    user_orders = Order.query.filter_by(client_id=current_user.id)
    
    # Count orders by status
    counts = {
        'all': user_orders.count(),
        'active': user_orders.filter_by(status='active').count(),
        'pending': user_orders.filter_by(status='pending').count(),
        'completed': user_orders.filter(
            Order.status.in_(['completed', 'completed pending review'])
        ).count(),
        'overdue': user_orders.filter(
            and_(
                Order.due_date < datetime.now(),
                ~Order.status.in_(['completed', 'completed pending review', 'canceled'])
            )
        ).count()
    }
    
    return jsonify(counts)