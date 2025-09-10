from flask import request, render_template, redirect, flash, url_for
from app.models.content import Testimonial
from flask_login import login_required
from app.admin.routes.decorator import admin_required
from app.admin import admin_bp
from app.extensions import db

@admin_bp.route('/testimonials')
@login_required
@admin_required
def list_testimonials():
    """List all testimonials."""
    approved_filter = request.args.get('approved', '')
    search_query = request.args.get('search', '')
    
    # Base query
    query = Testimonial.query
    
    # Apply filters
    if approved_filter == 'true':
        query = query.filter(Testimonial.is_approved == True)
    elif approved_filter == 'false':
        query = query.filter(Testimonial.is_approved == False)
        
    if search_query:
        query = query.filter(
            (Testimonial.client_name.ilike(f'%{search_query}%')) |
            (Testimonial.content.ilike(f'%{search_query}%'))
        )
    
    testimonials = query.order_by(Testimonial.created_at.desc()).all()
    
    # Get stats
    total_testimonials = Testimonial.query.count()
    approved_testimonials = Testimonial.query.filter_by(is_approved=True).count()
    pending_testimonials = Testimonial.query.filter_by(is_approved=False).count()
    
    return render_template('admin/content/testimonials/list.html',
                           testimonials=testimonials,
                           approved_filter=approved_filter,
                           search_query=search_query,
                           total_testimonials=total_testimonials,
                           approved_testimonials=approved_testimonials,
                           pending_testimonials=pending_testimonials,
                           title='Testimonial Management')

@admin_bp.route('/testimonials/<int:testimonial_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_testimonial(testimonial_id):
    """Approve a testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.is_approved = True
    try:
        db.session.commit()
        # other = current_user
        # notify(other, 
        #     title=f"Testimonial #{testimonial.id} by {testimonial.user.username} has been approved by {current_user.get_name()}", 
        #     message="Testimonial approved successfully", 
        #     type='info', 
        #     link=None)
        # notify(testimonial.user, 
        #     title=f"Testimonial #{testimonial.id} by {testimonial.user.username} has been approved by {current_user.get_name()}", 
        #     message="Testimonial approved successfully", 
        #     type='info', 
        #     link=None)
        flash('Testimonial approved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while approving the testimonial.', 'danger')
    return redirect(url_for('admin.list_testimonials'))

@admin_bp.route('/testimonials/<int:testimonial_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_testimonial(testimonial_id):
    """Reject a testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.is_approved = False
    try:
        db.session.commit()
        # other = current_user
        # notify(other, 
        #     title=f"Testimonial #{testimonial.id} by {testimonial.user.username} has not been approved by {current_user.get_name()}", 
        #     message="Testimonial rejected", 
        #     type='info', 
        #     link=None)
        # notify(testimonial.user, 
        #     title=f"Testimonial #{testimonial.id} by {testimonial.user.username} has not been approved by {current_user.get_name()}", 
        #     message="Testimonial rejected", 
        #     type='info', 
        #     link=None)

        flash('Testimonial rejected', 'success')
        return redirect(url_for('admin.list_testimonials'))
    except Exception as e:
        db.session.rollback()
        flash('Daabase error while rejecting testimonial', 'error')
        return redirect(url_for('admin.list_testimonials'))

@admin_bp.route('/testimonials/<int:testimonial_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_testimonial(testimonial_id):
    """Delete a testimonial."""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    try:
        db.session.delete(testimonial)
        db.session.commit()
        # other = current_user
        # notify(other, 
        #     title=f"Testimonial #{testimonial.id} by {testimonial.user.username} has been deleted by {current_user.get_name()}", 
        #     message="Testimonial deleted", 
        #     type='info', 
        #     link=None)
        # notify(testimonial.user, 
        #     title=f"Testimonial #{testimonial.id} by {testimonial.user.username} has been deleted by {current_user.get_name()}", 
        #     message="Testimonial deleted", 
        #     type='info', 
        #     link=None)
        
        flash('Testimonial deleted successfully', 'success')
        return redirect(url_for('admin.list_testimonials'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the testimonial.', 'danger')
        return redirect(url_for('admin.list_testimonials'))
