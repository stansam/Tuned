import os
import uuid
from PIL import Image
from flask import current_app
from app.utils.file_upload import allowed_file
from app.config import Config

def validate_image(file):
    """
    Validate uploaded image file.
    Returns (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename, type="picture"):
        return False, f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_PIC_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > Config.MAX_CONTENT_LENGTH:
        return False, f"File size too large. Maximum size: {Config.MAX_CONTENT_LENGTH / (1024*1024):.1f}MB"
    
    # Validate image format using PIL
    try:
        img = Image.open(file)
        img.verify()  # Verify it's a valid image
        file.seek(0)  # Reset file pointer after verification
        
        # Check image dimensions (optional)
        img = Image.open(file)
        width, height = img.size
        if width > 5000 or height > 5000:
            return False, "Image dimensions too large. Maximum: 5000x5000 pixels"
            
        file.seek(0)  # Reset file pointer
        return True, "Valid image"
        
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def generate_unique_filename(original_filename):
    """
    Generate a unique filename for the uploaded image.
    Returns the new filename with extension.
    """
    # Get file extension
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    
    # Generate unique filename using UUID
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    return unique_filename

def resize_and_save_image(file, filepath, max_size=Config.MAX_IMAGE_SIZE):
    """
    Resize image if needed and save to filepath.
    Returns True if successful, False otherwise.
    """
    try:
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if image is larger than max_size
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save with optimization
        img.save(filepath, optimize=True, quality=85)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error processing image: {str(e)}")
        return False

def delete_profile_picture(filename):
    """
    Delete profile picture file from filesystem.
    Returns True if successful or file doesn't exist, False on error.
    """
    if not filename or filename == 'default.png':
        return True
        
    try:
        # Construct file paths for both admin and client directories
        from flask_login import current_user

        if current_user.is_admin:
            from app.admin import admin_bp

            file_path = os.path.join(admin_bp.static_folder, 'assets', 'profile_pics', filename)
        else:
            from app.client import client_bp

            file_path = os.path.join(client_bp.static_folder, 'client', 'assets', 'profile_pics', filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.info(f"Deleted profile picture: {file_path}")
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error deleting profile picture {filename}: {str(e)}")
        return False