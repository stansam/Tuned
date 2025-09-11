from app.models.order_delivery import OrderDelivery, OrderDeliveryFile
from app.models.order import Order, OrderFile, OrderComment, SupportTicket 
from app.services.triggers.triggers import *
from app.api import api_bp
from datetime import datetime 
from app.admin.routes.decorator import admin_required
from flask_login import login_required, current_user
from app.extensions import db
from flask import jsonify, request, current_app
from app.utils.file_upload import allowed_file
from app.admin.routes.orders.utils import MAX_FILE_SIZE, get_file_format
from werkzeug.utils import secure_filename
import uuid
import os 

@api_bp.route('/admin/delivery/<int:order_id>/upload-additional-files', methods=['POST'])
@login_required
@admin_required
def upload_additional_delivery_files(order_id):
    """
    Upload additional files to an existing delivery without changing status
    """
    try:
        # Verify delivery exists
        # ord_id = Order.query.get_or_404(order_id)
        # if ord_id:

        delivery = OrderDelivery.query.filter_by(order_id=order_id).first()
        if not delivery:
            try:
                delivery = OrderDelivery(
                        order_id=order_id,
                        delivery_status='delivered',
                        delivered_at=datetime.now()
                    )
            
                db.session.add(delivery)
                db.session.flush()

                handle_order_delivery(order_id)

            except Exception as e:
                import logging 
                db.session.rollback()
                logging.error(f"ERROR occured while creating delivery instance: {e}") 
                return jsonify({
                    'success', False,
                    'message', f'ERROR: {e}'
                }), 500
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No files provided'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'success': False,
                'message': 'No files selected'
            }), 400
        
        # Get form data
        file_type = request.form.get('file_type', 'supplementary')
        description = request.form.get('description', '')
        
        # Validate file type
        if file_type not in ['delivery', 'plagiarism_report', 'supplementary']:
            file_type = 'supplementary'
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'deliveries', str(delivery.order_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Validate file
            if not allowed_file(file.filename):
                errors.append(f"File '{file.filename}' has invalid extension")
                continue
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            
            if file_size > MAX_FILE_SIZE:
                errors.append(f"File '{file.filename}' exceeds maximum size limit (16MB)")
                continue
            
            if file_size == 0:
                errors.append(f"File '{file.filename}' is empty")
                continue
            
            try:
                # Generate unique filename
                original_filename = secure_filename(file.filename)
                file_extension = get_file_format(original_filename)
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # Save file
                file.save(file_path)
                
                # Create database record
                delivery_file = OrderDeliveryFile(
                    delivery_id=delivery.id,
                    filename=unique_filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_type=file_type,
                    file_format=file_extension,
                    uploaded_at=datetime.now(),
                    description=description if description else None
                )
                
                db.session.add(delivery_file)
                uploaded_files.append({
                    'filename': original_filename,
                    'size': round(file_size / (1024 * 1024), 2),
                    'type': file_type
                })
                
            except Exception as e:
                errors.append(f"Failed to upload '{file.filename}': {str(e)}")
                # Clean up file if it was saved
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
        
        # Commit changes if any files were uploaded successfully
        if uploaded_files:
            try:
                order = Order.query.filter_by(id=order_id).first()
                if order.status != 'completed pending review':
                    if order.status == 'revision':
                        handle_revised_order_delivery(order_id)
                    order.status = 'completed pending review'
                
                db.session.commit()

                
                
                # send_order_completed_email(order, order.client)
            except Exception as e:
                db.session.rollback()
                # Clean up uploaded files
                for file_info in uploaded_files:
                    file_path = os.path.join(upload_dir, file_info['filename'])
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass
                
                return jsonify({
                    'success': False,
                    'message': f'Database error: {str(e)}'
                }), 500
        
        # Return response
        if uploaded_files and not errors:
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'uploaded_files': uploaded_files
            }), 200
        elif uploaded_files and errors:
            return jsonify({
                'success': True,
                'message': f'Uploaded {len(uploaded_files)} file(s) with some errors',
                'uploaded_files': uploaded_files,
                'errors': errors
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No files were uploaded',
                'errors': errors
            }), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error uploading additional delivery files: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500
    


@api_bp.route('/admin/request-deadline-extension', methods=['POST'])
@login_required
@admin_required
def request_deadline_extension():
    try:
        # Get data from request
        data = request.get_json()
        order_id = data.get('order_id')
        description = data.get('description', '').strip()
        
        # Validate required fields
        if not order_id:
            return jsonify({
                'success': False, 
                'message': 'Order ID is required'
            }), 400
            
        if not description:
            return jsonify({
                'success': False, 
                'message': 'Description is required'
            }), 400
            
        admin_user_id = current_user.id
        
        # Verify order exists
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False, 
                'message': 'Order not found'
            }), 404
        
        # Check if extension is already requested
        if order.extension_requested:
            return jsonify({
                'success': False, 
                'message': 'Deadline extension has already been requested for this order'
            }), 400
        
        # Update order with extension request
        order.extension_requested = True
        order.extension_requested_at = datetime.now()
        
        # Create support ticket
        support_ticket = SupportTicket(
            order_id=order_id,
            user_id=order.client_id,  # Assign to the order's client
            subject="Deadline Extension Request",
            message=f"Writer has requested a deadline extension for Order #{order.order_number}.\n\nReason: {description}",
            status='open'
        )
        
        # Save to database
        db.session.add(support_ticket)
        db.session.commit()

        handle_deadline_extension_request(order.id, reason=description)
        # send_extension_request_email(order, order.client)
        return jsonify({
            'success': True,
            'message': 'Deadline extension request submitted successfully',
            'ticket_id': support_ticket.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@api_bp.route('/admin/get-extension-status/<int:order_id>', methods=['GET'])
@login_required
@admin_required
def get_extension_status(order_id):
    """Get the current extension request status for an order"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False, 
                'message': 'Order not found'
            }), 404
            
        return jsonify({
            'success': True,
            'extension_requested': order.extension_requested,
            'extension_requested_at': order.extension_requested_at.isoformat() if order.extension_requested_at else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500