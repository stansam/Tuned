from flask import render_template, redirect, url_for, request, flash
from urllib.parse import urlparse
from sqlalchemy import or_
from datetime import datetime, timedelta
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter, get_token_serializer
from app.models.user import User
from app.services.triggers.triggers import *
from app.utils.emails import send_verification_email, send_welcome_email
import logging
from app.auth import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("8 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        # Validate input
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return redirect(url_for('auth.login'))

        # Find user
        user = User.query.filter(
            or_(
                User.username.ilike(username),
                User.email.ilike(username)
            )
        ).first()

        # Check for too many failed attempts
        if user and user.failed_login_attempts >= 5 and user.last_failed_login:
            time_passed = datetime.now() - user.last_failed_login
            if time_passed < timedelta(minutes=15):
                logging.warning(f'Account locked due to too many failed attempts: {user.email}')
                flash('Account is temporarily locked. Please try again later.', 'danger')
                return redirect(url_for('auth.login'))
            else:
                # Reset counter after lockout period
                user.failed_login_attempts = 0
                db.session.commit()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_failed_login = None
            db.session.commit()

            if not user.email_verified:
                flash('Please verify your email first.', 'warning')
                send_verification_email(user)
                send_welcome_email(user)
                return redirect(url_for('auth.login'))
            # Login user with Flask-Login
            login_user(user, remember=remember)

            # Get the next page from request args, or default routes
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                if user.is_admin:
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('client.dashboard')

            flash(f'Welcome back, {user.get_name()}!', 'success')
            return redirect(next_page)
        else:
            if user:
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.now()
                db.session.commit()
                logging.warning(f'Failed login attempt for user: {user.email}')
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        # Get the token serializer from app config
        from flask import current_app
        token_serializer = get_token_serializer(current_app.config['SECRET_KEY'])
        
        email = token_serializer.loads(token, salt='email-verification-salt', max_age=86400)  # 24 hours
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid verification link.', 'danger')
            return redirect(url_for('auth.login'))
            
        if user.email_verified:
            flash('Email already verified. Please login.', 'info')
        elif user.email_verification_token == token:
            user.email_verified = True
            user.email_verification_token = None
            db.session.commit()
            logging.info(f'Email verified for user: {email}')
            flash('Your email has been verified! You can now log in.', 'success')
        else:
            logging.warning(f'Invalid verification attempt for email: {email}')
            flash('Invalid verification link.', 'danger')
    except Exception as e:
        logging.error(f'Email verification error: {str(e)}')
        flash('Invalid or expired verification link.', 'danger')

    return redirect(url_for('auth.login'))
    