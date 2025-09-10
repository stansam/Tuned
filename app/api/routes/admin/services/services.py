from flask import request, jsonify, current_app
from app.api.routes.admin.services.utils import handle_request_type
from app.api import api_bp as admin_bp
from app.admin.routes.decorator import admin_required
from flask_login import login_required, current_user
from app.models import ServiceCategory, Service
from app.extensions import db

@admin_bp.route('/admin/services/category/save', methods=['POST'])
@login_required
@admin_required
@handle_request_type
def save_category():
    """
    Create or update a service category
    Handles both AJAX and regular form submissions
    """
    try:
        # Validate CSRF token for non-AJAX requests
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Add CSRF validation here if needed
            pass
        
        category_id = request.form.get('category_id')
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validation
        errors = {}
        if not name:
            errors['name'] = ['Category name is required']
        elif len(name) > 100:
            errors['name'] = ['Category name must be less than 100 characters']
        
        if errors:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Update existing category
        if category_id:
            category = ServiceCategory.query.get(category_id)
            if not category:
                return jsonify({
                    'success': False,
                    'message': 'Category not found'
                }), 404
            
            # Check for duplicate names (excluding current category)
            existing = ServiceCategory.query.filter(
                ServiceCategory.name.ilike(name),
                ServiceCategory.id != category_id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'A category with this name already exists',
                    'errors': {'name': ['Category name must be unique']}
                }), 400
            
            category.name = name
            category.description = description
            
            db.session.commit()
            
            current_app.logger.info(f"Category {category.name} (ID: {category.id}) updated by user {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Category updated successfully',
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'order': category.order
                }
            })
        
        # Create new category
        else:
            # Check for duplicate names
            existing = ServiceCategory.query.filter(
                ServiceCategory.name.ilike(name)
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'A category with this name already exists',
                    'errors': {'name': ['Category name must be unique']}
                }), 400
            
            # Get the highest order value
            max_order = db.session.query(db.func.max(ServiceCategory.order)).scalar() or 0
            
            category = ServiceCategory(
                name=name,
                description=description,
                order=max_order + 1
            )
            
            db.session.add(category)
            db.session.commit()
            
            current_app.logger.info(f"New category {category.name} (ID: {category.id}) created by user {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Category created successfully',
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'order': category.order
                }
            })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Database error in save_category: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Database error occurred',
            'error': str(e) if current_app.debug else 'Internal server error'
        }), 500

@admin_bp.route('/admin/services/category/order', methods=['POST'])
@login_required
@admin_required
def update_category_order():
    """
    Update the order of categories
    AJAX only endpoint
    """
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data or 'categories' not in data:
            return jsonify({
                'success': False,
                'message': 'Invalid data format. Expected {"categories": [...]}'
            }), 400
        
        categories = data['categories']
        
        if not isinstance(categories, list):
            return jsonify({
                'success': False,
                'message': 'Categories must be an array'
            }), 400
        
        # Validate each category entry
        valid_ids = []
        for i, category_data in enumerate(categories):
            if not isinstance(category_data, dict):
                return jsonify({
                    'success': False,
                    'message': f'Category at index {i} must be an object'
                }), 400
            
            category_id = category_data.get('id')
            order = category_data.get('order')
            
            if not category_id or not isinstance(order, int):
                return jsonify({
                    'success': False,
                    'message': f'Category at index {i} missing valid id or order'
                }), 400
            
            valid_ids.append((category_id, order))
        
        # Update categories in database
        updated_count = 0
        for category_id, order in valid_ids:
            category = ServiceCategory.query.get(category_id)
            if category:
                category.order = order
                updated_count += 1
            else:
                current_app.logger.warning(f"Category ID {category_id} not found during order update")
        
        db.session.commit()
        
        current_app.logger.info(f"Updated order for {updated_count} categories by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated order for {updated_count} categories',
            'updated_count': updated_count
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating category order: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error reordering categories',
            'error': str(e) if current_app.debug else 'Internal server error'
        }), 500

@admin_bp.route('/admin/services/service/save', methods=['POST'])
@admin_bp.route('/admin/services/service/save/<int:service_id>', methods=['POST'])
@login_required
@admin_required
@handle_request_type
def save_service(service_id=None):
    """
    Create or update a service
    Handles both AJAX and regular form submissions
    """
    try:
        # Get form data
        if not service_id:
            service_id = request.form.get('service_id')
        
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id')
        featured = request.form.get('featured') == '1'
        tags = request.form.get('tags', '').strip()
        pricing_category_id = request.form.get('pricing_category_id')
        
        # Validation
        errors = {}
        
        if not name:
            errors['name'] = ['Service name is required']
        elif len(name) > 100:
            errors['name'] = ['Service name must be less than 100 characters']
        
        if not category_id:
            errors['category_id'] = ['Category is required']
        else:
            try:
                category_id = int(category_id)
                category_exists = ServiceCategory.query.get(category_id)
                if not category_exists:
                    errors['category_id'] = ['Selected category does not exist']
            except (ValueError, TypeError):
                errors['category_id'] = ['Invalid category selection']
        
        # Validate pricing category if provided
        if pricing_category_id:
            try:
                pricing_category_id = int(pricing_category_id)
                # Add validation for pricing category existence if needed
            except (ValueError, TypeError):
                errors['pricing_category_id'] = ['Invalid pricing category selection']
        else:
            pricing_category_id = None
        
        if errors:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Update existing service
        if service_id:
            service = Service.query.get(service_id)
            if not service:
                return jsonify({
                    'success': False,
                    'message': 'Service not found'
                }), 404
            
            # Check for duplicate names (excluding current service)
            existing = Service.query.filter(
                Service.name.ilike(name),
                Service.id != service_id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'A service with this name already exists',
                    'errors': {'name': ['Service name must be unique']}
                }), 400
            
            service.name = name
            service.description = description
            service.category_id = category_id
            service.featured = featured
            service.tags = tags if tags else None
            service.pricing_category_id = pricing_category_id
            
            db.session.commit()
            
            current_app.logger.info(f"Service {service.name} (ID: {service.id}) updated by user {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Service updated successfully',
                'data': {
                    'id': service.id,
                    'name': service.name,
                    'description': service.description,
                    'category_id': service.category_id,
                    'featured': service.featured,
                    'tags': service.tags,
                    'pricing_category_id': service.pricing_category_id
                }
            })
        
        # Create new service
        else:
            # Check for duplicate names
            existing = Service.query.filter(
                Service.name.ilike(name)
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'A service with this name already exists',
                    'errors': {'name': ['Service name must be unique']}
                }), 400
            
            service = Service(
                name=name,
                description=description,
                category_id=category_id,
                featured=featured,
                tags=tags if tags else None,
                pricing_category_id=pricing_category_id
            )
            
            db.session.add(service)
            db.session.commit()
            
            current_app.logger.info(f"New service {service.name} (ID: {service.id}) created by user {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Service created successfully',
                'data': {
                    'id': service.id,
                    'name': service.name,
                    'description': service.description,
                    'category_id': service.category_id,
                    'featured': service.featured,
                    'tags': service.tags,
                    'pricing_category_id': service.pricing_category_id
                }
            })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Database error in save_service: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Database error occurred',
            'error': str(e) if current_app.debug else 'Internal server error'
        }), 500