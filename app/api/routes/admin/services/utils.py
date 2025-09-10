from flask import current_app, request, jsonify, redirect, url_for, flash
from functools import wraps


def handle_request_type(func):
    """Decorator to handle both AJAX and regular requests"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Check if this is an AJAX request
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                request.is_json or
                'application/json' in request.headers.get('Accept', '')
            )
            
            if is_ajax:
                # Return the result as-is for AJAX (should be JSON)
                return result
            else:
                # For regular requests, check if result is a dict (success case)
                if isinstance(result, dict) and result.get('success'):
                    flash(result.get('message', 'Operation completed successfully'), 'success')
                    return redirect(url_for('admin.services_management'))
                elif isinstance(result, dict):
                    flash(result.get('message', 'Operation failed'), 'danger')
                    return redirect(url_for('admin.services_management'))
                else:
                    # Result is already a redirect or response
                    return result
                    
        except Exception as e:
            current_app.logger.exception(f"Error in {func.__name__}: {str(e)}")
            
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                request.is_json or
                'application/json' in request.headers.get('Accept', '')
            )
            
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'An unexpected error occurred',
                    'error': str(e) if current_app.debug else 'Internal server error'
                }), 500
            else:
                flash('An unexpected error occurred', 'danger')
                return redirect(url_for('admin.services_management'))
    
    return wrapper
