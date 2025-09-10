from flask import jsonify, current_app, request
from flask_login import current_user, login_required
from app.api import api_bp
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from app.api.routes.client.profile.utils import validate_profile_data


@api_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get current user's profile data
    """
    try:
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'gender': current_user.gender.value if current_user.gender else None,
            'email_verified': current_user.email_verified,
            'is_admin': current_user.is_admin,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'referral_code': current_user.referral_code,
            'reward_points': current_user.reward_points,
            'full_name': current_user.get_name()
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching profile for user {current_user.id}: {str(e)}")
        return jsonify({'message': 'An error occurred while fetching your profile.'}), 500
    
@api_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """
    Update current user's profile data
    """
    from app.models import GenderEnum
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided.'}), 400
        
        # Validate the data
        is_valid, errors = validate_profile_data(data, current_user.id)
        
        if not is_valid:
            return jsonify({'errors': errors}), 400
        
        # Get database instance
        
        # Track if email changed for verification purposes
        email_changed = False
        old_email = current_user.email
        new_email = data.get('email', '').strip().lower()
        gender = (data.get('gender') or '').strip().lower()

        
        if old_email != new_email:
            email_changed = True
        
        # Update user fields
        current_user.first_name = data.get('first_name', '').strip()
        current_user.last_name = data.get('last_name', '').strip()
        current_user.username = data.get('username', '').strip()
        current_user.email = new_email
        # current_user.gender = GenderEnum(gender)
        try:
            current_user.gender = GenderEnum(gender)
        except ValueError:
            raise ValueError("Invalid gender value: must be 'male' or 'female'")
        
        # If email changed, reset email verification
        if email_changed:
            current_user.email_verified = False
            current_user.email_verification_token = None
            # You might want to generate a new verification token here
            # and send a verification email
        
        # Commit changes to database
        db.session.commit()
        
        # Log the update
        current_app.logger.info(f"Profile updated for user {current_user.id} ({current_user.username})")
        
        # Prepare response data
        response_data = {
            'message': 'Profile updated successfully.',
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'gender': current_user.gender.value if current_user.gender else None,
                'email_verified': current_user.email_verified,
                'full_name': current_user.get_name()
            }
        }
        
        # Add email verification notice if email changed
        if email_changed:
            response_data['email_verification_required'] = True
            response_data['message'] = 'Profile updated successfully. Please verify your new email address.'
        
        return jsonify(response_data), 200
            
    except IntegrityError as e:
        # Handle database integrity errors (unique constraints)
        db.session.rollback()
        current_app.logger.error(f"Integrity error updating profile for user {current_user.id}: {str(e)}")
        
        # Check which field caused the integrity error
        error_message = str(e.orig).lower()
        if 'username' in error_message:
            return jsonify({'errors': {'username': 'This username is already taken.'}}), 400
        elif 'email' in error_message:
            return jsonify({'errors': {'email': 'This email is already registered.'}}), 400
        else:
            return jsonify({'message': 'A database error occurred. Please try again.'}), 500
            
    except Exception as e:
        # Handle any other unexpected errors
        db.session.rollback()
        current_app.logger.error(f"Unexpected error updating profile for user {current_user.id}: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred. Please try again.'}), 500

