from app.admin.routes.samples.utils import validate_sample_data, process_image, extract_word_count
from flask import request, render_template, redirect, flash, url_for, jsonify, current_app
from app.models.order import Order
from app.models.user import User
from app.models.referral import Referral
from sqlalchemy import func, and_
from app.admin.routes.decorator import admin_required
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.extensions import db
from datetime import timedelta
import uuid
import os

@admin_bp.route('/users/')
@login_required
@admin_required
def list_users():
    """Display all users with filtering options."""
    admin_filter = request.args.get('admin', '')
    search_query = request.args.get('search', '')
    
    # Base query
    query = User.query
    
    # Apply filters
    if admin_filter == 'true':
        query = query.filter(User.is_admin == True)
    elif admin_filter == 'false':
        query = query.filter(User.is_admin == False)
        
    if search_query:
        query = query.filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%'))
        )
    
    # Get the sorted users
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(getattr(User, sort_by).desc())
    else:
        query = query.order_by(getattr(User, sort_by).asc())
    
    users = query.all()
    
    # Get stats for the sidebar
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    client_users = User.query.filter_by(is_admin=False).count()
    
    return render_template('admin/users/list.html', 
                           users=users,
                           admin_filter=admin_filter,
                           search_query=search_query,
                           sort_by=sort_by,
                           sort_order=sort_order,
                           total_users=total_users,
                           admin_users=admin_users,
                           client_users=client_users,
                           title='User Management')

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    """View detailed information about a specific user."""
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(client_id=user_id).all()
    referrals = Referral.query.filter_by(referrer_id=user_id).all()
    
    return render_template('admin/users/view.html',
                           user=user,
                           orders=orders,
                           timedelta=timedelta,
                           referrals=referrals,
                           title=f'User: {user.username}')

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        is_admin = True if request.form.get('is_admin') == 'true' else False
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('admin.create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('admin.create_user'))
        
        # Generate referral code
        referral_code = uuid.uuid4().hex[:8].upper()
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            referral_code=referral_code,
            email_verified=True  # Admin-created users are pre-verified
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        # notify(current_user,
        #         title=f"New user {user.username} created",
        #         message="User created successfully",
        #         type='info',
        #         link=url_for('admin.view_user', user_id=user.id))
        # notify(user,
        #         title="Welcome to TunedEssays!",
        #         message="Your account has been created successfully.",
        #         type='info',
        #         link=url_for('client.dashboard'))
        flash('User created successfully', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    return render_template('admin/users/create.html', title='Create New User')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user details
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.is_admin = True if request.form.get('is_admin') == 'true' else False
        user.email_verified = True if request.form.get('email_verified') == 'true' else False
        user.reward_points = request.form.get('reward_points', user.reward_points, type=int)
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password and new_password.strip():
            user.set_password(new_password)
        
        db.session.commit()
        # notify(current_user,
        #         title=f"User {user.username} updated",
        #         message="User details updated successfully",
        #         type='info',
        #         link=url_for('admin.view_user', user_id=user.id))
        # notify(user,
        #         title="Your account details have been updated",
        #         message="Your account information has been updated successfully.",
        #         type='info',
        #         link=url_for('client.dashboard'))
        
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    return render_template('admin/users/edit.html', user=user, title=f'Edit User: {user.username}')

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.list_users'))
    # notify(current_user,
    #         title=f"User {user.username} deleted",
    #         message="User account deleted successfully",
    #         type='info',
    #         link=url_for('admin.list_users'))
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/users/<int:user_id>/add-reward-points', methods=['POST'])
@login_required
@admin_required
def add_reward_points(user_id):
    """Add reward points to a user."""
    user = User.query.get_or_404(user_id)
    points = request.form.get('points', 0, type=int)
    
    if points <= 0:
        flash('Points must be a positive number', 'danger')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    user.reward_points += points
    db.session.commit()
    # notify(current_user,
    #         title=f"Reward points added to {user.username}",
    #         message=f"{points} reward points added successfully.",
    #         type='info',
    #         link=url_for('admin.view_user', user_id=user.id))
    # notify(user,
    #         title="Reward points added to your account",
    #         message=f"You have received {points} reward points.",
    #         type='info',
    #         link=url_for('client.dashboard'))
    flash(f'Added {points} reward points to {user.username}', 'success')
    return redirect(url_for('admin.view_user', user_id=user.id))

@admin_bp.route('/users/<int:user_id>/reset-failed-logins', methods=['POST'])
@login_required
@admin_required
def reset_failed_logins(user_id):
    """Reset failed login attempts for a user."""
    user = User.query.get_or_404(user_id)
    
    user.failed_login_attempts = 0
    user.last_failed_login = None
    db.session.commit()
    # notify(current_user,
    #         title=f"Failed login attempts reset for {user.username}",
    #         message="Failed login attempts reset successfully.",
    #         type='info',
    #         link=url_for('admin.view_user', user_id=user.id))
    # notify(user,
    #         title="Your failed login attempts have been reset",
    #         message="Your account is now secure.",
    #         type='info',
    #         link=url_for('client.dashboard'))
    flash('Failed login attempts reset successfully', 'success')
    return redirect(url_for('admin.view_user', user_id=user.id))
