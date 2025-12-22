from flask import render_template, redirect, url_for, flash
from app.client import client_bp
from flask_login import login_required, current_user
from app.models.user import User
from app.models.order import Order
from app.models.communication import Notification
from app.models.referral import Referral
# from app.models.content import Order
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.extensions import db
import logging
from app.client.routes.orders.utils import _auto_complete_orders


@client_bp.route('/')
@login_required
def dashboard():
    try:
        current_time = datetime.now()
        
        dashboard_data = {
            'current_time': current_time,
            'recent_orders': [],
            'active_orders': [],
            'pending_orders': [],
            'completed_orders': [],
            'overdue_orders': [],
            'referrals': [],
            'referral_count': 0,
            'unread_notifications': [],
            'unread_count': 0,
            'total_orders': 0,
            'total_spent': 0.0,
            'avg_order_value': 0.0,
            'completion_rate': 0.0,
            'orders_this_month': 0,
            'spent_this_month': 0.0,
            'reward_points': 0,
            'referral_earnings': 0.0,
            'upcoming_deadlines': [],
            'order_status_counts': {},
            'monthly_order_trend': [],
            'error_message': None
        }
        
        try:
            recent_orders = Order.query.filter_by(client_id=current_user.id)\
                                     .order_by(Order.created_at.desc())\
                                     .limit(10)\
                                     .all()
            dashboard_data['recent_orders'] = recent_orders
            
            pending_orders = Order.query.filter_by(client_id=current_user.id, status='pending')\
                                      .order_by(Order.due_date.asc())\
                                      .all()
            dashboard_data['pending_orders'] = pending_orders
            
            active_orders = Order.query.filter_by(client_id=current_user.id, status='active')\
                                     .order_by(Order.due_date.asc())\
                                     .all()
            dashboard_data['active_orders'] = active_orders
            
            completed_orders = Order.query.filter_by(client_id=current_user.id, status='completed')\
                                         .order_by(Order.created_at.desc())\
                                         .limit(10)\
                                         .all()
            dashboard_data['completed_orders'] = completed_orders
            
            overdue_orders = Order.query.filter(
                and_(
                    Order.client_id == current_user.id,
                    Order.status.in_(['active', 'pending']),
                    Order.due_date < current_time
                )
            ).order_by(Order.due_date.asc()).all()
            dashboard_data['overdue_orders'] = overdue_orders
            
            next_week = current_time + timedelta(days=7)
            upcoming_deadlines = Order.query.filter(
                and_(
                    Order.client_id == current_user.id,
                    Order.status.in_(['active', 'pending']),
                    Order.due_date.between(current_time, next_week)
                )
            ).order_by(Order.due_date.asc()).limit(5).all()
            dashboard_data['upcoming_deadlines'] = upcoming_deadlines
            
        except Exception as e:
            logging.error(f"Error fetching orders for user {current_user.id}: {str(e)}")
            dashboard_data['error_message'] = "Unable to load order information"
        
        try:
            referrals = Referral.query.filter_by(referrer_id=current_user.id)\
                                    .order_by(Referral.created_at.desc())\
                                    .all()
            dashboard_data['referrals'] = referrals
            dashboard_data['referral_count'] = len(referrals)
            
            referral_earnings = sum(r.commission for r in referrals if r.status == 'completed')
            dashboard_data['referral_earnings'] = referral_earnings
            
        except Exception as e:
            logging.error(f"Error fetching referrals for user {current_user.id}: {str(e)}")
        
        try:
            unread_notifications = Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False
            ).order_by(Notification.created_at.desc()).limit(10).all()
            dashboard_data['unread_notifications'] = unread_notifications
            dashboard_data['unread_count'] = len(unread_notifications)
            
        except Exception as e:
            logging.error(f"Error fetching notifications for user {current_user.id}: {str(e)}")
        
        try:
            total_orders = Order.query.filter_by(client_id=current_user.id).count()
            dashboard_data['total_orders'] = total_orders
            
            total_spent_result = db.session.query(func.sum(Order.total_price))\
                                         .filter_by(client_id=current_user.id, paid=True)\
                                         .scalar()
            total_spent = float(total_spent_result) if total_spent_result else 0.0
            dashboard_data['total_spent'] = total_spent
            
            if total_orders > 0:
                avg_order_value = total_spent / max(1, Order.query.filter_by(client_id=current_user.id, paid=True).count())
                dashboard_data['avg_order_value'] = avg_order_value
            
            completed_count = Order.query.filter_by(client_id=current_user.id, status='completed').count()
            if total_orders > 0:
                completion_rate = (completed_count / total_orders) * 100
                dashboard_data['completion_rate'] = completion_rate
            
            start_of_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            orders_this_month = Order.query.filter(
                and_(
                    Order.client_id == current_user.id,
                    Order.created_at >= start_of_month
                )
            ).count()
            dashboard_data['orders_this_month'] = orders_this_month
            
            spent_this_month_result = db.session.query(func.sum(Order.total_price))\
                                               .filter(
                                                   and_(
                                                       Order.client_id == current_user.id,
                                                       Order.paid == True,
                                                       Order.created_at >= start_of_month
                                                   )
                                               ).scalar()
            spent_this_month = float(spent_this_month_result) if spent_this_month_result else 0.0
            dashboard_data['spent_this_month'] = spent_this_month
            
            status_counts = db.session.query(
                Order.status, 
                func.count(Order.id).label('count')
            ).filter_by(client_id=current_user.id).group_by(Order.status).all()
            
            dashboard_data['order_status_counts'] = {status: count for status, count in status_counts}
            
        except Exception as e:
            logging.error(f"Error calculating statistics for user {current_user.id}: {str(e)}")
        
        try:
            dashboard_data['reward_points'] = getattr(current_user, 'reward_points', 0) or 0
        except Exception as e:
            logging.error(f"Error fetching reward points for user {current_user.id}: {str(e)}")
        
        try:
            monthly_trend = []
            for i in range(6):
                month_start = (current_time.replace(day=1) - timedelta(days=32*i)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_orders = Order.query.filter(
                    and_(
                        Order.client_id == current_user.id,
                        Order.created_at.between(month_start, month_end)
                    )
                ).count()
                
                monthly_trend.append({
                    'month': month_start.strftime('%b %Y'),
                    'orders': month_orders
                })
            
            dashboard_data['monthly_order_trend'] = list(reversed(monthly_trend))
            
        except Exception as e:
            logging.error(f"Error calculating monthly trend for user {current_user.id}: {str(e)}")
            
        _auto_complete_orders()
        return render_template('client/dashboard.html', **dashboard_data)
        
    except Exception as e:
        logging.error(f"Critical error in dashboard for user {getattr(current_user, 'id', 'unknown')}: {str(e)}")
        flash('An error occurred while loading your dashboard. Please try again.', 'error')
        return render_template('client/dashboard.html', 
                             error_message="Unable to load dashboard data",
                             **{k: v for k, v in dashboard_data.items() if k != 'error_message'})

@client_bp.route('/dashboard/refresh')
@login_required
def refresh_dashboard_data():
    """
    AJAX endpoint to refresh dashboard data without full page reload
    """
    try:
        # This could be used for real-time updates if needed
        return redirect(url_for('client.dashboard'))
    except Exception as e:
        logging.error(f"Error refreshing dashboard: {str(e)}")
        flash('Unable to refresh dashboard data', 'error')
        return redirect(url_for('client.dashboard'))