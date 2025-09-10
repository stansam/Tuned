from flask import jsonify, request
from flask_login import login_required
from datetime import datetime, timedelta
import calendar
from app.extensions import db
# from app.admin import admin_bp
from app.models.order import Order
from app.models.user import User
from app.models.communication import ChatMessage
from app.models.payment import Payment
from app.models.service import Service
from app.admin.routes.decorator import admin_required
from app.api import api_bp


@api_bp.route('/admin/revenue-chart-data')
@login_required
@admin_required
def revenue_chart_data():
    """Get data for the revenue chart."""
    period = request.args.get('period', 'monthly')
    
    current_date = datetime.now()
    
    if period == 'weekly':
        # Get data for the last 7 days
        labels = []
        current_data = []
        previous_data = []
        
        for i in range(6, -1, -1):
            day = current_date - timedelta(days=i)
            previous_day = day - timedelta(days=7)
            
            labels.append(day.strftime('%a'))
            
            # Current week data
            day_revenue = db.session.query(db.func.sum(Payment.amount)) \
                .filter(Payment.status == 'completed') \
                .filter(db.func.date(Payment.created_at) == day.date()) \
                .scalar() or 0
            current_data.append(float(day_revenue))
            
            # Previous week data
            prev_day_revenue = db.session.query(db.func.sum(Payment.amount)) \
                .filter(Payment.status == 'completed') \
                .filter(db.func.date(Payment.created_at) == previous_day.date()) \
                .scalar() or 0
            previous_data.append(float(prev_day_revenue))
    
    elif period == 'monthly':
        # Get data for the last 6 months
        labels = []
        current_data = []
        previous_data = []
        
        for i in range(5, -1, -1):
            # Calculate current and previous month dates
            month_offset = i
            current_month = current_date.month - month_offset
            current_year = current_date.year
            
            # Adjust year if needed
            while current_month <= 0:
                current_month += 12
                current_year -= 1
            
            # Calculate previous year's equivalent month
            prev_year = current_year - 1
            
            # Get month name
            month_name = calendar.month_abbr[current_month]
            labels.append(month_name)
            
            # Get start and end dates for current month
            current_start = datetime(current_year, current_month, 1)
            if current_month == 12:
                current_end = datetime(current_year + 1, 1, 1) - timedelta(days=1)
            else:
                current_end = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
            
            # Get start and end dates for previous year's month
            prev_start = datetime(prev_year, current_month, 1)
            if current_month == 12:
                prev_end = datetime(prev_year + 1, 1, 1) - timedelta(days=1)
            else:
                prev_end = datetime(prev_year, current_month + 1, 1) - timedelta(days=1)
            
            # Current month revenue
            month_revenue = db.session.query(db.func.sum(Payment.amount)) \
                .filter(Payment.status == 'completed') \
                .filter(Payment.created_at.between(current_start, current_end)) \
                .scalar() or 0
            current_data.append(float(month_revenue))
            
            # Previous year's month revenue
            prev_month_revenue = db.session.query(db.func.sum(Payment.amount)) \
                .filter(Payment.status == 'completed') \
                .filter(Payment.created_at.between(prev_start, prev_end)) \
                .scalar() or 0
            previous_data.append(float(prev_month_revenue))
    
    else:  # yearly
        # Get data for the last 5 years
        labels = []
        current_data = []
        
        current_year = current_date.year
        
        for i in range(4, -1, -1):
            year = current_year - i
            labels.append(str(year))
            
            # Year revenue
            year_revenue = db.session.query(db.func.sum(Payment.amount)) \
                .filter(Payment.status == 'completed') \
                .filter(db.extract('year', Payment.created_at) == year) \
                .scalar() or 0
            current_data.append(float(year_revenue))
    
    return jsonify({
        'labels': labels,
        'current': current_data,
        'previous': previous_data if period != 'yearly' else []
    })

@api_bp.route('/admin/orders-by-status')
@login_required
@admin_required
def orders_by_status():
    """Get data for the orders by status chart."""
    # Count orders by status
    pending_count = Order.query.filter_by(status='pending').count()
    in_progress_count = Order.query.filter_by(status='active').count()
    completed_count = Order.query.filter_by(status='completed').count()
    cancelled_count = Order.query.filter_by(status='cancelled').count()
    revision_count = Order.query.filter_by(status='revision').count()
    
    return jsonify({
        'labels': ['pending', 'active', 'completed', 'cancelled', 'revision'],
        'data': [pending_count, in_progress_count, completed_count, cancelled_count, revision_count],
        'colors': ['#FFC107', '#2196F3', '#4CAF50', '#F44336', '#9C27B0']
    })

@api_bp.route('/admin/orders-by-service')
@login_required
@admin_required
def orders_by_service():
    """Get data for the orders by service chart."""
    # Get top services by order count
    services_data = db.session.query(
        Order.service_id,
        db.func.count(Order.id).label('order_count')
    ) \
    .join(Order.service) \
    .group_by(Order.service_id) \
    .order_by(db.desc('order_count')) \
    .limit(5) \
    .all()
    
    labels = []
    data = []
    
    for service_id, count in services_data:
        service = db.session.query(Service).get(service_id)
        if service:
            labels.append(service.name)
            data.append(count)
    
    return jsonify({
        'labels': labels,
        'data': data
    })
