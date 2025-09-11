import re
import secrets
from datetime import datetime, timedelta
from flask import request, render_template, redirect, url_for, flash, current_app, jsonify
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import User, GenderEnum
from app.utils.emails import send_verification_email  
from app.services.triggers.triggers import handle_user_registration
from app.utils.referrals import generate_referral_code
from app.auth import auth_bp as reg_bp  

@reg_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Robust registration view function with comprehensive validation and security measures.
    """
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    if request.method == 'POST':
        # Extract form data
        form_data = {
            'username': request.form.get('username', '').strip().lower(),
            'fullname': request.form.get('fullname', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
            'gender': request.form.get('gender', ''),
            'phone': request.form.get('phone', '').strip()
        }
        
        errors = {}
        
        # Comprehensive validation
        errors.update(_validate_username(form_data['username']))
        errors.update(_validate_fullname(form_data['fullname']))
        errors.update(_validate_email(form_data['email']))
        errors.update(_validate_passwords(form_data['password'], form_data['confirm_password']))
        errors.update(_validate_gender(form_data['gender']))
        errors.update(_validate_phone(form_data['phone']))
        
        # Check for existing users
        errors.update(_check_existing_user(form_data['username'], form_data['email']))
        
        # If validation fails, return errors
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            
            for field, error in errors.items():
                flash(f"{field.replace('_', ' ').title()}: {error}", 'error')
            return render_template('auth/register.html', **form_data)
        
        try:
            # Create new user
            user = _create_user(form_data)
            
            # Send verification email
            if not _send_verification_email(user):
                flash('Account created but verification email failed to send. Please contact support.', 'warning')


            handle_user_registration(user)

            flash('Registration successful! Please check your email to verify your account.', 'success')
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Registration successful!',
                    'redirect_url': url_for('auth.login')  
                }), 200
            
            return redirect(url_for('auth.login'))  
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error during registration: {str(e)}")
            
            error_msg = "Registration failed. Username or email might already exist."
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            
            flash(error_msg, 'error')
            return render_template('auth/register.html', **form_data)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error during registration: {str(e)}")
            
            error_msg = "An unexpected error occurred. Please try again."
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 500
            
            flash(error_msg, 'error')
            return render_template('auth/register.html', **form_data)


def _validate_username(username):
    """Validate username field."""
    errors = {}
    
    if not username:
        errors['username'] = 'Username is required'
    elif len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters long'
    elif len(username) > 64:
        errors['username'] = 'Username cannot exceed 64 characters'
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = 'Username can only contain letters, numbers, and underscores'
    elif username.startswith('_') or username.endswith('_'):
        errors['username'] = 'Username cannot start or end with an underscore'
    elif '__' in username:
        errors['username'] = 'Username cannot contain consecutive underscores'
    
    return errors


def _validate_fullname(fullname):
    """Validate full name field."""
    errors = {}
    
    if not fullname:
        errors['fullname'] = 'Full name is required'
    elif len(fullname) < 2:
        errors['fullname'] = 'Full name must be at least 2 characters long'
    elif len(fullname) > 200:
        errors['fullname'] = 'Full name cannot exceed 200 characters'
    elif not re.match(r'^[a-zA-Z\s\'-]+$', fullname):
        errors['fullname'] = 'Full name can only contain letters, spaces, hyphens, and apostrophes'
    elif not any(char.isalpha() for char in fullname):
        errors['fullname'] = 'Full name must contain at least one letter'
    
    return errors


def _validate_email(email):
    """Validate email field."""
    errors = {}
    
    if not email:
        errors['email'] = 'Email is required'
    elif len(email) > 120:
        errors['email'] = 'Email cannot exceed 120 characters'
    else:
        # RFC 5322 compliant email regex (simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors['email'] = 'Please enter a valid email address'
        
        # Additional checks
        if '..' in email or email.startswith('.') or email.endswith('.'):
            errors['email'] = 'Email format is invalid'
        
        # Check for suspicious patterns
        suspicious_domains = ['temp-mail.org', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1].lower() if '@' in email else ''
        if domain in suspicious_domains:
            errors['email'] = 'Temporary email addresses are not allowed'
    
    return errors


def _validate_passwords(password, confirm_password):
    """Validate password fields."""
    errors = {}
    
    if not password:
        errors['password'] = 'Password is required'
        return errors
    
    if not confirm_password:
        errors['confirm_password'] = 'Password confirmation is required'
        return errors
    
    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match'
    
    # Password strength validation
    if len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters long'
    elif len(password) > 128:
        errors['password'] = 'Password cannot exceed 128 characters'
    else:
        strength_checks = {
            'lowercase': bool(re.search(r'[a-z]', password)),
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'digit': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
        }
        
        passed_checks = sum(strength_checks.values())
        if passed_checks < 3:
            missing = []
            if not strength_checks['lowercase']:
                missing.append('lowercase letter')
            if not strength_checks['uppercase']:
                missing.append('uppercase letter')
            if not strength_checks['digit']:
                missing.append('number')
            if not strength_checks['special']:
                missing.append('special character')
            
            errors['password'] = f'Password must contain at least 3 of: {", ".join(missing)}'
    
    # Check for common weak passwords
    common_passwords = ['password', '12345678', 'qwerty123', 'password123']
    if password.lower() in common_passwords:
        errors['password'] = 'Password is too common. Please choose a stronger password'
    
    return errors


def _validate_gender(gender):
    """Validate gender field."""
    errors = {}
    
    if not gender:
        errors['gender'] = 'Gender selection is required'
    elif gender not in ['male', 'female']:
        errors['gender'] = 'Invalid gender selection'
    
    return errors


def _validate_phone(phone):
    """Validate phone number field."""
    errors = {}
    
    if not phone:
        errors['phone'] = 'Phone number is required'
    else:
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'[^\d]', '', phone)
        
        if len(digits_only) < 7:
            errors['phone'] = 'Phone number is too short'
        elif len(digits_only) > 15:
            errors['phone'] = 'Phone number is too long'
        elif not re.match(r'^\+\d{7,15}$', phone):
            errors['phone'] = 'Phone number format is invalid'
    
    return errors


def _check_existing_user(username, email):
    """Check if username or email already exists."""
    errors = {}
    
    try:
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            errors['username'] = 'Username is already taken'
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            errors['email'] = 'Email is already registered'
            
    except Exception as e:
        current_app.logger.error(f"Error checking existing users: {str(e)}")
        errors['general'] = 'Unable to verify user information. Please try again.'
    
    return errors


def _create_user(form_data):
    """Create and save new user to database."""
    # Parse full name
    name_parts = form_data['fullname'].split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Generate verification token and referral code
    verification_token = secrets.token_urlsafe(32)
    referral_code = generate_referral_code()  
    
    # Create user instance
    user = User(
        username=form_data['username'],
        email=form_data['email'],
        first_name=first_name,
        last_name=last_name,
        gender=GenderEnum(form_data['gender']),
        phone_number=form_data['phone'],
        email_verification_token=verification_token,
        referral_code=referral_code,
        created_at=datetime.now()
    )
    
    # Set password hash
    user.set_password(form_data['password'])
    
    # Save to database
    db.session.add(user)
    db.session.commit()
    
    current_app.logger.info(f"New user registered: {user.username} ({user.email})")
    
    return user


def _send_verification_email(user):
    """Send email verification link to user."""
    try:
        return send_verification_email(user)
        
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


