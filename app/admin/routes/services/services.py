from app.admin.routes.samples.utils import validate_sample_data, process_image, extract_word_count
from flask import request, render_template, redirect, flash, url_for, jsonify, current_app
from app.models.service import Service, ServiceCategory
from app.models.price import PricingCategory
from sqlalchemy import func, and_
from app.admin.routes.decorator import admin_required
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.extensions import db

@admin_bp.route('/services')
@login_required
@admin_required
def services_management():
    """
    Display the services management page
    """
    categories = ServiceCategory.query.order_by(ServiceCategory.order).all()
    categories_data = [category.to_dict() for category in categories]
    services = Service.query.all()
    services_data = [service.to_dict() for service in services]
    featured_count = Service.query.filter_by(featured=True).count()
    pricing_categories = PricingCategory.query.order_by(PricingCategory.display_order).all()
    pricing_categories_data = [price_cat.to_dict() for price_cat in pricing_categories]
    # Add services to each category for template rendering
    for category in categories:
        category.services = Service.query.filter_by(category_id=category.id).all()
    
    return render_template(
        'admin/services/services.html',
        categories_data=categories_data,
        services_data=services_data,
        categories=categories,
        services=services,
        featured_count=featured_count,
        pricing_categories=pricing_categories,
        pricing_categories_data=pricing_categories_data,
        title='Services Management'
    )

@admin_bp.route('/services/category/save', methods=['POST'])
@login_required
@admin_required
def save_category():
    """
    Create or update a service category
    """
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    description = request.form.get('description')
    
    
    if not name:
        flash('Category name is required', 'danger')
        return redirect(url_for('admin.services_management'))
    
    # Update existing category
    if category_id:
        category = ServiceCategory.query.get(category_id)
        if not category:
            flash('Category not found', 'danger')
            return redirect(url_for('admin.services_management'))
        
        category.name = name
        category.description = description
        try:
            db.session.commit()
            # notify(current_user,
            #         title=f"Service category {category.name} updated",
            #         message="Category updated successfully",
            #         type='info',
            #         link=url_for('admin.services_management'))
            flash('Category updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Database error occurred', 'danger')
            return redirect(url_for('admin.services_management'))
    
    # Create new category
    else:
        # Get the highest order value
        max_order = db.session.query(db.func.max(ServiceCategory.order)).scalar() or 0
        category = ServiceCategory(
            name=name,
            description=description,
            order=max_order + 1
        )
        try:
            db.session.add(category)
            db.session.commit()
            # notify(current_user,
            #         title=f"New service category {category.name} created",
            #         message="Category created successfully",
            #         type='info',
            #         link=url_for('admin.services_management'))
            flash('Category created successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Database error occurred', 'danger')
            return redirect(url_for('admin.services_management'))
    
    # db.session.commit()
    return redirect(url_for('admin.services_management'))

@admin_bp.route('/services/category/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """
    Delete a service category and all its services
    """
    category = ServiceCategory.query.get_or_404(category_id)
    
    # Delete all services in this category first
    Service.query.filter_by(category_id=category_id).delete()
    
    # Delete the category
    try:
        db.session.delete(category)
        db.session.commit()
        # notify(current_user,
        #         title=f"Service category {category.name} deleted",
        #         message="Category and its services deleted successfully",
        #         type='info',
        #         link=url_for('admin.services_management'))
        flash(f'Category "{category.name}" and all its services have been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error occurred', 'danger')
        return redirect(url_for('admin.services_management'))
    return redirect(url_for('admin.services_management'))

@admin_bp.route('/services/category/order', methods=['POST'])
@login_required
@admin_required
def update_category_order():
    """
    Update the order of categories
    """
    data = request.json
    if not data or 'categories' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    
    categories = data['categories']
    
    try:
        for category_data in categories:
            category_id = category_data.get('id')
            order = category_data.get('order')
            
            category = ServiceCategory.query.get(category_id)
            if category:
                category.order = order
        
        db.session.commit()
        # notify(current_user,
        #         title="Service categories reordered",
        #         message="Categories reordered successfully",
        #         type='info',
        #         link=url_for('admin.services_management'))
        flash('Categories reordered successfully', 'success')
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        # notify(current_user,
        #         title="Error reordering service categories",
        #         message=str(e),
        #         type='error',
        #         link=url_for('admin.services_management'))
        flash('Error reordering categories', 'danger')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/services/service/save', methods=['POST'])
@login_required
@admin_required
def save_service():
    """
    Create or update a service
    """
    service_id = request.form.get('service_id')
    name = request.form.get('name')
    if len(name.strip()) > 100:  
        flash('Service name too long (max 100 characters)', 'danger')
        return redirect(url_for('admin.services_management'))
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    try:
        category_id = int(category_id) if category_id else None
    except ValueError:
        flash('Invalid category selection', 'danger')
        return redirect(url_for('admin.services_management'))
    featured = request.form.get('featured') == '1'
    tags = request.form.get('tags', '').strip()
    pricing_category_id = request.form.get('pricing_category_id')
    if not name:
        flash('Service name is required', 'danger')
        return redirect(url_for('admin.services_management'))
    
    if not category_id:
        flash('Category is required', 'danger')
        return redirect(url_for('admin.services_management'))
    
    if category_id:
        category_exists = ServiceCategory.query.get(category_id)
        if not category_exists:
            flash('Selected category does not exist', 'danger')
            return redirect(url_for('admin.services_management'))
   
    if service_id:
        service = Service.query.get(service_id)
        if not service:
            flash('Service not found', 'danger')
            return redirect(url_for('admin.services_management'))
        
        service.name = name
        service.description = description
        service.category_id = category_id
        service.featured = featured
        service.tags = tags
        service.pricing_category_id = pricing_category_id if pricing_category_id else None
        try:
            db.session.commit()
            # notify(current_user,
            #         title=f"Service {service.name} updated",
            #         message="Service updated successfully",
            #         type='info',
            #         link=url_for('admin.services_management'))
            flash('Service updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Database error occurred', 'danger')
            return redirect(url_for('admin.services_management'))

    
    # Create new service
    else:
        service = Service(
            name=name,
            description=description,
            category_id=category_id,
            featured=featured,
            tags=tags if tags else None,
            pricing_category_id=pricing_category_id if pricing_category_id else None
        )
        try:
            db.session.add(service)
            db.session.commit()
            # notify(current_user,
            #         title=f"New service {service.name} created",
            #         message="Service created successfully",
            #         type='info',
            #         link=url_for('admin.services_management'))
            flash('Service created successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Database error occurred', 'danger')
            return redirect(url_for('admin.services_management'))
    
    # db.session.commit()
    return redirect(url_for('admin.services_management'))

@admin_bp.route('/services/service/delete/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def delete_service(service_id):
    """
    Delete a service
    """
    service = Service.query.get_or_404(service_id)
    
    # Get service name before deletion for flash message
    service_name = service.name
    
    # Delete the service
    try:
        db.session.delete(service)
        db.session.commit()
        # notify(current_user,
        #         title=f"Service {service_name} deleted",
        #         message="Service deleted successfully",
        #         type='info',
        #         link=url_for('admin.services_management'))
        flash(f'Service "{service_name}" has been deleted', 'success')
        return redirect(url_for('admin.services_management'))
    except Exception as e:
        db.session.rollback()
        flash('Database error occurred', 'danger')
        return redirect(url_for('admin.services_management'))
