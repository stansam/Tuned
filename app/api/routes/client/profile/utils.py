import re
from email_validator import validate_email, EmailNotValidError
from app.models.user import User


def validate_profile_data(data, user_id=None):
    """
    Validate profile data with comprehensive checks
    Returns (is_valid, errors_dict)
    """
    errors = {}
    
    # First Name validation
    first_name = data.get('first_name', '').strip()
    if not first_name:
        errors['firstName'] = 'First name is required.'
    elif len(first_name) < 2:
        errors['firstName'] = 'First name must be at least 2 characters long.'
    elif len(first_name) > 100:
        errors['firstName'] = 'First name cannot exceed 100 characters.'
    elif not re.match(r'^[a-zA-Z\s\-\'\.]+$', first_name):
        errors['firstName'] = 'First name can only contain letters, spaces, hyphens, and apostrophes.'
    
    # Last Name validation
    last_name = data.get('last_name', '').strip()
    if not last_name:
        errors['lastName'] = 'Last name is required.'
    elif len(last_name) < 2:
        errors['lastName'] = 'Last name must be at least 2 characters long.'
    elif len(last_name) > 100:
        errors['lastName'] = 'Last name cannot exceed 100 characters.'
    elif not re.match(r'^[a-zA-Z\s\-\'\.]+$', last_name):
        errors['lastName'] = 'Last name can only contain letters, spaces, hyphens, and apostrophes.'
    
    # Username validation
    username = data.get('username', '').strip()
    if not username:
        errors['username'] = 'Username is required.'
    elif len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters long.'
    elif len(username) > 64:
        errors['username'] = 'Username cannot exceed 64 characters.'
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = 'Username can only contain letters, numbers, and underscores.'
    else:
        # Check if username is already taken (excluding current user)        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and (user_id is None or existing_user.id != user_id):
            errors['username'] = 'This username is already taken.'
    
    # Email validation
    email = data.get('email', '').strip().lower()
    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            # Validate email format
            validate_email(email)
            
            # Check email length
            if len(email) > 120:
                errors['email'] = 'Email cannot exceed 120 characters.'
            else:
                # Check if email is already taken (excluding current user)               
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and (user_id is None or existing_user.id != user_id):
                    errors['email'] = 'This email is already registered.'
                    
        except EmailNotValidError:
            errors['email'] = 'Please enter a valid email address.'
    
    # Gender validation
    gender = data.get('gender', '').strip()
    if not gender:
        errors['gender'] = 'Gender is required.'
    elif gender not in ['male', 'female']:
        errors['gender'] = 'Please select a valid gender.'
    
    return len(errors) == 0, errors