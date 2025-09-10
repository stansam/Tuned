from app.admin.routes.blogs.utils import generate_unique_slug
from app.admin.routes.decorator import admin_required
from flask import jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from app.models.blog import BlogCategory
from flask_login import login_required
from app.extensions import db
from app.api import api_bp

@api_bp.route('/admin/blog/categories/create', methods=['POST'])
@login_required
@admin_required
def create_blog_category():
    """Create a new blog category."""
    try:
        data =request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        name = data.get('name')
        description = data.get('description', '')
        
        
        # Generate slug from name
        slug = generate_unique_slug(name, BlogCategory)

        existing_name = BlogCategory.query.filter_by(name=name).first()
        if existing_name:
            return jsonify({
                'success': False,
                'message': f'A category with the name "{name}" already exists'
            }), 400
        existing_slug = BlogCategory.query.filter_by(slug=slug).first()
        if existing_slug:
            return jsonify({
                'success': False,
                'message': f'A category with the slug "{slug}" already exists'
            }), 400
        
        # Create category
        category = BlogCategory(
            name=name,
            slug=slug,
            description=description if description else None,
            
        )
        # other = current_user
        # notify(other, 
        #     title=f"Blog category #{category.name} has been created by {current_user.get_name()}", 
        #     message="Category created successfully", 
        #     type='info', 
        #     link=None)
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category created successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description
            }
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'A category with this name or slug already exists'
        }), 400
        
    except Exception as e:
        db.session.rollback()
        # Log the error for debugging
        current_app.logger.error(f'Error creating blog category: {str(e)}')
        
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the category'
        }), 500   