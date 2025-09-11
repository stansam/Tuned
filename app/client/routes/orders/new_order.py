from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from app.client.routes.orders.utils import validate_uploaded_files
from app.services.triggers.triggers import handle_new_order_creation
from flask_login import login_required, current_user
from app.models.order import Order, OrderFile
from app.models.service import Service, AcademicLevel, Deadline
from app.models.user import User
from app.extensions import db
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename
from app.client import client_bp

@client_bp.route('/orders/new', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'POST':        
        try:
            service_id = request.form.get('service')
            academic_level_id = request.form.get('academic_level')
            deadline_time = request.form.get('deadline')
            title = request.form.get('title')
            description = request.form.get('description')
            word_count = request.form.get('word_count')
            citation_style = request.form.get('citation_style')
            report_type = request.form.get("report_type", '')
            due_date = request.form.get('due_date')

            if not all([service_id, academic_level_id, deadline_time, title, word_count]):
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                    return jsonify({"success": False, "message": "Please fill in all required fields"}), 400
                else:
                    flash('Please fill in all required fields', 'danger')
                    return redirect(url_for('client.create_order'))

            
            is_valid, error_message, validated_files = validate_uploaded_files()
            if not is_valid:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                    return jsonify({"success": False, "message": error_message}), 400
                else:
                    flash(error_message, 'danger')
                    return redirect(url_for('client.create_order'))

            try:
                service = Service.query.get(service_id)
                if not service:
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                        return jsonify({"success": False, "message": f"Service not found"}), 404
                    else:
                        flash("Service not found", 'danger')
                        return redirect(url_for('client.create_order'))
                    
                academic_level = AcademicLevel.query.get(academic_level_id)
                if not academic_level:
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                        return jsonify({"success": False, "message": "Academic Level not found"}), 404
                    else:
                        flash("Academic Level not found", 'danger')
                        return redirect(url_for('client.create_order'))
                
                import math
                page_count = math.ceil(int(word_count) // 275) 
                
                from app.api.routes.calculate_price import calculate_price_internal  
                price_result = calculate_price_internal(
                    service_id=service.id,
                    academic_level_id=academic_level.id,
                    hours_until_deadline=float(deadline_time),
                    word_count=int(word_count),
                    report_type=report_type
                )
                
                total_price = price_result.get("total_price")
                selected_date = price_result.get("selected_deadline")
                
                if not selected_date or not selected_date.get('id'):
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                        return jsonify({"success": False, "message": "Please enter a valid deadline"}), 404
                    else:
                        flash('Please enter a valid deadline', 'danger')
                        return redirect(url_for('client.create_order'))
                
                deadline = Deadline.query.get(selected_date['id'])
                if not deadline:
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                        return jsonify({"success": False, "message": "Deadline not found"}), 404
                    else:
                        flash("Deadline not found", 'danger')
                        return redirect(url_for('client.create_order'))

                if due_date:
                    try:
                        date_due = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
                    except ValueError:
                        try:
                            date_due = datetime.strptime(due_date, "%Y-%m-%d, %H:%M")
                        except ValueError:
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                                return jsonify({"success": False, "message": "Invalid due date format"}), 404
                            else:
                                flash('Invalid due date format', 'danger')
                                return redirect(url_for('client.create_order'))
                else:
                    date_due = datetime.now() + timedelta(hours=deadline.hours)

                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                new_order = Order(
                    order_number=order_number,
                    client_id=current_user.id,
                    service_id=service.id,
                    academic_level_id=academic_level.id,
                    deadline_id=deadline.id,
                    title=title,
                    description=description,
                    word_count=word_count,
                    page_count=page_count,
                    total_price=total_price,
                    format_style=citation_style,
                    report_type=report_type,
                    due_date=date_due
                )

                db.session.add(new_order)
                db.session.flush()  

                saved_files = [] 
                
                for file, file_type in validated_files:
                    try:
                        filename = secure_filename(file.filename)

                        # Timestamp to prevent filename conflicts
                        name, ext = os.path.splitext(filename)
                        unique_filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                        
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        os.makedirs(upload_folder, exist_ok=True)
                        file_path = os.path.join(upload_folder, unique_filename)
                        
                        file.save(file_path)
                        saved_files.append(file_path)  
                        
                        order_file = OrderFile(
                            order_id=new_order.id,
                            filename=unique_filename,
                            file_path=file_path,
                        )
                        db.session.add(order_file)
                        
                    except Exception as file_error:
                        for saved_file in saved_files:
                            try:
                                if os.path.exists(saved_file):
                                    os.remove(saved_file)
                            except:
                                pass
                        raise Exception(f"File upload failed for {file.filename}: {str(file_error)}")

                db.session.commit()
                
                try:
                    handle_new_order_creation(new_order.id)
                except Exception as notification_error:
                    current_app.logger.warning(f'Notification error: {str(notification_error)}')
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                    return jsonify({
                        "success": True,
                        "message": "Order created successfully! Confirm the details before proceeding.",
                        "redirect_url": url_for('client.order_details', order_id=new_order.id)
                    }), 201
                else:
                    flash('Order created successfully! Confirm the details before proceeding.', 'success')
                    return redirect(url_for('client.order_details', order_id=new_order.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Order creation error: {str(e)}', exc_info=True)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                    return jsonify({
                        "success": False,
                        "message": "Error creating order. Please try again.",
                        "redirect_url": url_for('client.create_order')
                    }), 400
                else:
                    flash('Error creating order. Please try again.', 'danger')
                    return redirect(url_for('client.create_order'))

        except Exception as e:
            current_app.logger.error(f'Order form processing error: {str(e)}', exc_info=True)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({
                    "success": False,
                    "message": "Error processing form. Please try again.",
                    "redirect_url": url_for('client.create_order')
                }), 400
            else:
                flash('Error processing form. Please try again.', 'danger')
                return redirect(url_for('client.create_order'))

    elif request.method == "GET":
        try:
            services = Service.query.all()
            services_data = [service.to_dict() for service in services]
            academic_levels = AcademicLevel.query.order_by(AcademicLevel.order).all()
            levels_data = [level.to_dict() for level in academic_levels]
            deadlines = Deadline.query.order_by(Deadline.order).all()
            deadline_data = [deadline.to_dict() for deadline in deadlines]
            
            template_vars = {
                'services': services_data,
                'academic_levels': levels_data,
                'deadlines': deadline_data,
                'title': "Place Order"
            }

            if request.args:
                service_id = request.args.get('service_id')
                due_date = request.args.get('due_date')
                deadline_data = request.args.get('deadline')
                academic_level_id = request.args.get('academic_level_id')
                word_cnt = request.args.get('word_count')
                pages = request.args.get('pages')
                
                if service_id:
                    selected_service = Service.query.get(service_id)
                    if selected_service:
                        template_vars['selected_service'] = selected_service.to_dict()

                if academic_level_id:
                    selected_academic_level = AcademicLevel.query.get(academic_level_id)
                    if selected_academic_level:
                        template_vars['selected_academic_level'] = selected_academic_level.to_dict()

                if deadline_data and float(deadline_data) > 3:
                    template_vars['hoursUntilDeadline'] = deadline_data

                if word_cnt:
                    try:
                        template_vars['word_count'] = int(word_cnt)
                    except (ValueError, TypeError):
                        pass
                        
                if pages:
                    try:
                        template_vars['pages'] = int(pages)
                    except (ValueError, TypeError):
                        pass
                            
                if due_date:
                    template_vars['due_date'] = due_date

                template_vars['title'] = "Complete Order"

            return render_template('client/orders/create_order/create_order.html', **template_vars)
            
        except Exception as e:
            current_app.logger.error(f'Order form display error: {str(e)}', exc_info=True)
            
            flash('Error loading order page. Please try again.', 'danger')
            return redirect(url_for('client.dashboard'))  
