import os
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.api import api_bp as profile_bp
from app.utils.image_upload import validate_image, generate_unique_filename, resize_and_save_image, delete_profile_picture


@profile_bp.route('/profile/upload-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """
    API endpoint to upload and save user profile picture.
    """
    try:
        if 'profile_pic' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['profile_pic']
        
        is_valid, error_message = validate_image(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': error_message
            }), 400
        
        unique_filename = generate_unique_filename(file.filename)
        
        # Define file paths
        if current_user.is_admin:
            from app.admin import admin_bp
            admin_upload_dir = os.path.join(admin_bp.static_folder, 'assets', 'profile_pics')
            os.makedirs(admin_upload_dir, exist_ok=True)
            filepath = os.path.join(admin_upload_dir, unique_filename)
        else:
            from app.client import client_bp
            client_upload_dir = os.path.join(client_bp.static_folder, 'client', 'assets', 'profile_pics')
            os.makedirs(client_upload_dir, exist_ok=True)
            filepath = os.path.join(client_upload_dir, unique_filename)
        
        
        file.seek(0)  
        if not resize_and_save_image(file, filepath):
            return jsonify({
                'success': False,
                'message': 'Failed to process and save image'
            }), 500
        
        
        
        old_filename = current_user.profile_pic
        if old_filename and old_filename != 'default.png':
            delete_profile_picture(old_filename)
        
        current_user.profile_pic = unique_filename
        db.session.commit()
        
        profile_pic_url = current_user.get_profile_pic_url()
        
        return jsonify({
            'success': True,
            'message': 'Profile picture updated successfully',
            'data': {
                'filename': unique_filename,
                'profile_pic_url': profile_pic_url
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading profile picture: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while uploading the profile picture'
        }), 500

@profile_bp.route('/profile/remove-picture', methods=['DELETE'])
@login_required
def remove_profile_picture():
    """
    API endpoint to remove user profile picture and set it back to default.
    """
    try:
        current_filename = current_user.profile_pic
        
        if not current_filename or current_filename == 'default.png':
            return jsonify({
                'success': False,
                'message': 'User already has default profile picture'
            }), 400
        
        if not delete_profile_picture(current_filename):
            current_app.logger.warning(f"Failed to delete profile picture file: {current_filename}")
        
        current_user.profile_pic = 'default.png'
        db.session.commit()
        
        profile_pic_url = current_user.get_profile_pic_url()
        
        return jsonify({
            'success': True,
            'message': 'Profile picture removed successfully',
            'data': {
                'filename': 'default.png',
                'profile_pic_url': profile_pic_url
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing profile picture: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while removing the profile picture'
        }), 500

@profile_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'message': f'File too large. Maximum size: {current_app.config('MAX_CONTENT_LENGTH') / (1024*1024):.1f}MB'
    }), 413

@profile_bp.errorhandler(415)
def unsupported_media_type(e):
    return jsonify({
        'success': False,
        'message': f'Unsupported file type. Allowed types: {", ".join(current_app.config('ALLOWED_PIC_EXTENSIONS'))}'
    }), 415