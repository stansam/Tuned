from flask import render_template, request, flash, redirect, url_for, current_app
from datetime import datetime, timedelta
import re
import secrets
from app.extensions import db
from app.models.user import User
from app.auth import auth_bp as forgot_password_bp
from app.auth.routes.pass_reset.utils import is_valid_email, send_password_reset_email


@forgot_password_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Validate email format
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            if user.is_admin:
                flash('Password Reset Denied! Log in or contact Customer Care for Help', 'error')
                return redirect(url_for('auth.login'))
            # Generate secure reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.now() + timedelta(hours=1)
            
            # Update user with reset token
            user.password_reset_token = reset_token
            user.password_reset_expires = reset_expires
            
            try:
                db.session.commit()
                
                # Send reset email
                if send_password_reset_email(user, reset_token):
                    current_app.logger.info(f"Password reset email sent to {email}")
                else:
                    current_app.logger.error(f"Failed to send password reset email to {email}")
                    flash('There was an error sending the reset email. Please try again later.', 'error')
                    return render_template('auth/forgot_password.html')
                    
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error during password reset: {str(e)}")
                flash('There was an error processing your request. Please try again later.', 'error')
                return render_template('auth/forgot_password.html')
        
        # Always show success message
        flash('If an account with that email exists, we have sent you a password reset link.', 'success')
        return redirect(url_for('auth.forgot_password'))
    return render_template('auth/forgot_password.html')

@forgot_password_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Validate token and find user
    user = User.query.filter_by(password_reset_token=token).first()

    if user:
        if user.is_admin:
            flash('Password Reset Denied! Log in or contact Customer Care for Help', 'error')
            return redirect(url_for('auth.login'))
    
    if not user or not user.password_reset_expires:
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # Check if token has expired
    if datetime.now() > user.password_reset_expires:
        # Clean up expired token
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        flash('This reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords
        if not new_password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Additional password strength validation
        if not re.search(r'[A-Z]', new_password):
            flash('Password must contain at least one uppercase letter.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if not re.search(r'[a-z]', new_password):
            flash('Password must contain at least one lowercase letter.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if not re.search(r'\d', new_password):
            flash('Password must contain at least one number.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password and clear reset token
        try:
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            # Reset failed login attempts on successful password reset
            user.failed_login_attempts = 0
            user.last_failed_login = None
            
            db.session.commit()
            
            current_app.logger.info(f"Password successfully reset for user {user.email}")
            flash('Your password has been successfully reset. You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))  
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during password reset: {str(e)}")
            flash('There was an error updating your password. Please try again.', 'error')
            return render_template('auth/reset_password.html', token=token)
    
    return render_template('auth/reset_password.html', token=token)


@forgot_password_bp.route('/check-reset-link/<token>')
def check_reset_link(token):
    """Check if a reset link is valid (useful for frontend validation)"""
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.password_reset_expires:
        return {'valid': False, 'message': 'Invalid reset link'}
    
    if datetime.now() > user.password_reset_expires:
        return {'valid': False, 'message': 'Reset link has expired'}
    
    return {'valid': True, 'message': 'Reset link is valid'}