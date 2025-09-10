from app.admin.routes.samples.utils import validate_sample_data, process_image, extract_word_count
from app.admin.routes.blogs.utils import generate_unique_slug
from app.admin.routes.decorator import admin_required
from flask import jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from app.models.content import Sample
from flask_login import login_required
from app.extensions import db
from app.api import api_bp
import os

@api_bp.route('/admin/samples/edit/<int:sample_id>', methods=['GET'])
@login_required
@admin_required
def get_sample_for_edit(sample_id):
    """Get sample details for editing"""
    try:
        sample = Sample.query.get_or_404(sample_id)
        
        sample_data = {
            'id': sample.id,
            'title': sample.title,
            'content': sample.content,
            'excerpt': sample.excerpt,
            'service_id': sample.service_id,
            'word_count': sample.word_count,
            'featured': sample.featured,
            'tags': sample.tags,
            'image': sample.image,
            'created_at': sample.created_at.isoformat() if sample.created_at else None
        }
        
        return jsonify({
            'success': True,
            'sample': sample_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching sample {sample_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching sample'
        }), 500

@api_bp.route('/admin/samples/edit/<int:sample_id>', methods=['PUT', 'POST'])
@login_required
@admin_required
def update_sample(sample_id):
    """Update existing sample"""
    try:
        sample = Sample.query.get_or_404(sample_id)
        
        # Get form data
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        service_id = request.form.get('service_id')
        featured = request.form.get('featured', 'false').lower() == 'true'
        tags = request.form.get('tags', '').strip()
        
        # Validation
        if not title:
            return jsonify({
                'success': False,
                'message': 'Title is required'
            }), 400
            
        if not content:
            return jsonify({
                'success': False,
                'message': 'Content is required'
            }), 400
        
        # Handle image upload if provided
        image_filename = sample.image  # Keep existing image by default
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                try:
                    # Delete old image if it exists
                    if sample.image:
                        old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], sample.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # Process new image using existing helper function
                    image_filename = process_image(file, current_app.config['UPLOAD_FOLDER'])
                    
                except Exception as e:
                    current_app.logger.error(f"Error processing image: {str(e)}")
                    return jsonify({
                        'success': False,
                        'message': 'Error processing image'
                    }), 500
        
        # Extract word count using existing helper function
        word_count = extract_word_count(content)
        
        # Update sample fields
        sample.title = title
        sample.content = content
        sample.excerpt = excerpt
        sample.service_id = int(service_id) if service_id else None
        sample.word_count = word_count
        sample.featured = featured
        sample.tags = tags 
        sample.image = image_filename
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sample updated successfully',
            'sample': {
                'id': sample.id,
                'title': sample.title,
                'content': sample.content,
                'excerpt': sample.excerpt,
                'service_id': sample.service_id,
                'word_count': sample.word_count,
                'featured': sample.featured,
                'tags' : sample.tags,
                'image': sample.image,
                'created_at': sample.created_at.isoformat() if sample.created_at else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating sample {sample_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error updating sample'
        }), 500
