from app.utils.file_upload import allowed_file
from werkzeug.utils import secure_filename
from flask import current_app
from app.config import Config
from app.models.service import Service
from PIL import Image 
import uuid
import os
import re

def process_image(file, upload_folder):
    """Process and save uploaded image with optimization"""
    if not file or not allowed_file(file.filename, "picture"):
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex}_{name}{ext}"
    
    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    
    try:
        # Open and process image
        image = Image.open(file.stream)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize image if too large (maintain aspect ratio)
        max_size = (1200, 800)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.LANCZOS)
        
        # Save optimized image
        image.save(file_path, optimize=True, quality=85)
        
        return unique_filename
    
    except Exception as e:
        current_app.logger.error(f"Error processing image: {str(e)}")
        return None

def extract_word_count(content):
    """Extract word count from HTML content"""
    if not content:
        return 0
    
    # Remove HTML tags and count words
    clean_text = re.sub(r'<[^>]+>', ' ', content)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    if not clean_text:
        return 0
    
    return len(clean_text.split())
pic_ext = Config.ALLOWED_PIC_EXT

def validate_sample_data(data, file=None):
    """Validate sample form data"""
    errors = []
    
    # Validate title
    title = data.get('title', '').strip()
    if not title:
        errors.append('Title is required.')
    elif len(title) < 10:
        errors.append('Title must be at least 10 characters long.')
    elif len(title) > 200:
        errors.append('Title must not exceed 200 characters.')
    
    # Validate service selection
    service_id = data.get('service_id')
    if not service_id:
        errors.append('Please select a service category.')
    else:
        try:
            service_id = int(service_id)
            service = Service.query.get(service_id)
            if not service:
                errors.append('Selected service category is invalid.')
        except (ValueError, TypeError):
            errors.append('Invalid service category selected.')
    
    # Validate content
    content = data.get('content', '').strip()
    if not content:
        errors.append('Content is required.')
    elif len(content) < 100:
        errors.append('Content must be at least 100 characters long.')
    
    # Validate excerpt (optional but with length limit)
    excerpt = data.get('excerpt', '').strip()
    if excerpt and len(excerpt) > 500:
        errors.append('Excerpt must not exceed 500 characters.')
    
    # Validate word count if provided
    word_count = data.get('word_count')
    if word_count:
        try:
            word_count = int(word_count)
            if word_count < 0:
                errors.append('Word count must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Word count must be a valid number.')
    
    # Validate featured flag
    featured = data.get('featured', '0')
    if featured not in ['0', '1']:
        errors.append('Invalid featured flag value.')
    
    # Validate image if provided
    if file and file.filename:
        if not allowed_file(file.filename, "picture"):
            errors.append(f'Invalid image format. Allowed formats: {", ".join(pic_ext).upper()}')
    
    return errors