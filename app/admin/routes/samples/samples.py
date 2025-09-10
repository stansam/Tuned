from app.admin.routes.samples.utils import validate_sample_data, process_image, extract_word_count
from flask import request, render_template, redirect, flash, url_for, jsonify, current_app
from app.admin.routes.decorator import admin_required
from flask_login import login_required, current_user
from werkzeug.exceptions import RequestEntityTooLarge
from app.models.service import Service
from app.models.content import Sample
from app.models.user import User
from app.admin import admin_bp
from app.extensions import db
from datetime import datetime
import os


@admin_bp.route('/samples')
@login_required
@admin_required
def list_samples():
    """List all writing samples."""
    featured_filter = request.args.get('featured', '')
    search_query = request.args.get('search', '')
    service_filter = request.args.get('service', '')
    
    # Base query
    query = Sample.query
    
    # Apply filters
    if featured_filter == 'true':
        query = query.filter(Sample.featured == True)
    elif featured_filter == 'false':
        query = query.filter(Sample.featured == False)
        
    if search_query:
        query = query.filter(
            (Sample.title.ilike(f'%{search_query}%')) |
            (Sample.description.ilike(f'%{search_query}%')) |
            (Sample.content.ilike(f'%{search_query}%'))
        )
    
    if service_filter:
        query = query.filter(Sample.service_id == service_filter)
    
    samples = query.order_by(Sample.created_at.desc()).all()
    
    # Get all services for filter dropdown
    services = Service.query.all()
    
    return render_template('admin/content/samples/list.html',
                           samples=samples,
                           services=services,
                           featured_filter=featured_filter,
                           search_query=search_query,
                           service_filter=service_filter,
                           title='Sample Management')

@admin_bp.route('/samples/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_sample():
    """Create a new writing sample."""
    if request.method == 'POST':
        try:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            form_data = request.form.to_dict()
            uploaded_file = request.files.get('image')
            validation_errors = validate_sample_data(form_data, uploaded_file)
            if validation_errors:
                error_message = ' '.join(validation_errors)
                if is_ajax:
                    return jsonify({
                        'success': False,
                        'message': error_message,
                        'errors': validation_errors
                    }), 400
                else:
                    flash(error_message, 'error')
                    return redirect(url_for('admin.create_sample'))
                
            image_filename = None
            if uploaded_file and uploaded_file.filename:
                upload_folder = os.path.join('app', 'static', 'uploads', 'samples')
                os.makedirs(upload_folder, exist_ok=True)
                image_filename = process_image(uploaded_file, upload_folder)
                
                if not image_filename:
                    error_msg = 'Failed to process uploaded image. Please try again.'
                    if is_ajax:
                        return jsonify({'success': False, 'message': error_msg}), 400
                    else:
                        flash(error_msg, 'error')
                        return redirect(url_for('admin.create_sample'))
            content = form_data.get('content', '')
            word_count = form_data.get('word_count')
            if word_count:
                try:
                    word_count = int(word_count)
                except (ValueError, TypeError):
                    word_count = extract_word_count(content)
            else:
                word_count = extract_word_count(content)

            title=form_data.get('title', '').strip()
            # slug = Sample.generate_slug(title)
            # Create new sample
            sample = Sample(
                title=form_data.get('title', '').strip(),
                content=content,
                excerpt=form_data.get('excerpt', '').strip() or None,
                service_id=int(form_data.get('service_id')),
                word_count=word_count,
                featured=form_data.get('featured', '0') == '1',
                tags=form_data.get('tags').strip() or None,
                image=image_filename,
                # slug=slug,
                created_at=datetime.now()
            )
                        
            try:
                db.session.add(sample)
                db.session.commit()
                # notify(current_user,
                #     title=f"Sample #{sample.title} has been created by {current_user.get_name()}", 
                #     message="Sample created successfully", 
                #     type='info', 
                #     link=url_for('main.sample_detail', slug=sample.slug))
                # all_users = User.query.all()
                # for user in all_users:
                #     notify(user,
                #         title=f"Sample #{sample.title} has been created by {current_user.get_name()}", 
                #         message="Sample created successfully", 
                #         type='info', 
                #         link=url_for('main.sample_detail', slug=sample.slug))
                current_app.logger.info(f"Sample created successfully: {sample.title} (ID: {sample.id})")
                
                # Return success response
                success_message = f'Sample \"{sample.title}\" has been created successfully!'
                
                if is_ajax:
                    return jsonify({
                        'success': True,
                        'message': success_message,
                        'sample_id': sample.id,
                        'redirect_url': url_for('main.sample_detail', slug=sample.slug)
                    })
                else:
                    flash(success_message, 'success')
                    return redirect(url_for('main.sample_detail', slug=sample.slug))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error saving sample: {str(e)}")
                error_message = 'An error occurred while saving the sample. Please try again.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_message}), 500
                else:
                    flash(error_message, 'error')
                    return redirect(url_for('admin.create_sample'))
            # flash('Sample created successfully', 'success')
            # return redirect(url_for('admin.list_samples'))
        except RequestEntityTooLarge:
            error_msg = 'Uploaded file is too large. Maximum size allowed is 5MB.'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 413
            else:
                flash(error_msg, 'error')
                return redirect(url_for('admin.create_sample'))
        except Exception as e:
            db.session.rollback()  
            current_app.logger.error(f"Error creating sample: {str(e)}")
            if 'image_filename' in locals() and image_filename:
                try:
                    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'samples')
                    file_path = os.path.join(upload_folder, image_filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as cleanup_error:
                    current_app.logger.error(f"Error cleaning up uploaded file: {str(cleanup_error)}")
            error_message = 'An error occurred while creating the sample. Please try again.'

            if is_ajax:
                return jsonify({'success': False, 'message': error_message}), 500
            else:
                flash(error_message, 'error')
                return redirect(url_for('admin.create_sample'))
            # flash('An error occurred while creating the sample. Please try again.', 'danger')
            # return redirect(url_for('admin.list_samples'))
    elif request.method == 'GET':
        try:
            # GET request - render form
            services = Service.query.all()
            
            return render_template('admin/content/samples/create.html',
                                services=services,
                                title='Create Sample')
        except Exception as e:
            current_app.logger.error(f"Error rendering sample creation form: {str(e)}")
            flash('An error occurred while loading the form. Please try again.', 'danger')
            return redirect(url_for('admin.list_samples'))
        
@admin_bp.route('/samples/<int:sample_id>/toggle-featured', methods=['POST'])
@login_required
@admin_required
def toggle_sample_featured(sample_id):
    """Toggle featured status of a sample."""
    sample = Sample.query.get_or_404(sample_id)
    sample.featured = not sample.featured
    try:
        db.session.commit()
        status = 'featured' if sample.featured else 'unfeatured'
        flash(f'Sample {status} successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the sample status.', 'danger')
    return redirect(url_for('admin.list_samples'))

@admin_bp.route('/samples/<int:sample_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_sample(sample_id):
    """Delete a writing sample."""
    sample = Sample.query.get_or_404(sample_id)
    # notify(current_user,
    #         title=f"Sample #{sample.title} has been deleted by {current_user.get_name()}",
    #         message="Sample deleted successfully",
    #         type='info',
    #         link=None)
    # all_users = User.query.all()
    # for user in all_users:
    #     notify(user,
    #            title=f"Sample #{sample.title} has been deleted by {current_user.get_name()}",
    #             message="Sample deleted successfully",
    #             type='info',
    #             link=None)
    try:
        db.session.delete(sample)
        db.session.commit()
        flash('Sample deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the sample.', 'danger')
    return redirect(url_for('admin.list_samples'))


