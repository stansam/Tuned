from flask import jsonify, current_app, request
from app.api import api_bp
from app.models.service import Service, AcademicLevel, Deadline
from app.models.price import PriceRate, PricingCategory
from bs4 import BeautifulSoup

def calculate_price_internal(service_id, academic_level_id, hours_until_deadline, word_count=0, report_type=None):
    """
    Internal function to calculate order price
    Returns: dict with price data or raises exception
    """
    try:
        # Convert and validate data types
        service_id = int(service_id)
        academic_level_id = int(academic_level_id)
        hours_until_deadline = float(hours_until_deadline)
        word_count = int(word_count)
    except (ValueError, TypeError) as e:
        raise ValueError("Invalid data types provided")
    
    # Calculate report price
    if report_type:
        if report_type == "standard":
            report_price = 4.99
        elif report_type == "turnitin":
            report_price = 9.99
        else:
            report_price = 0
    else:
        report_price = 0
    
    # Validate deadline
    if hours_until_deadline <= 0:
        raise ValueError("Deadline cannot be less than or equal to zero hours from current time!")
    
    # Find appropriate deadline
    deadlines = Deadline.query.order_by(Deadline.hours.asc()).all()
    if not deadlines:
        raise RuntimeError("No deadlines configured in system")
        
    deadline_id = None 
    selected_deadline = None
    
    for deadline in deadlines:
        if hours_until_deadline <= (deadline.hours + 1):
            deadline_id = deadline.id
            selected_deadline = deadline
            break
    
    # If no matching deadline found, use the longest available deadline
    if deadline_id is None:
        selected_deadline = deadlines[-1]
        deadline_id = selected_deadline.id
    
    # Calculate page count (with safety check for division by zero)
    # words_per_page = getattr(Config, 'WORDS_PER_PAGE', 275)
    words_per_page = current_app.config.get('WORDS_PER_PAGE', 275)
    if words_per_page <= 0:
        words_per_page = 275  # Default fallback
        
    page_count = max(1, round(word_count / words_per_page, 2))
    
    # Get service
    service = Service.query.get(service_id)
    if not service:
        raise ValueError("Service not found")
    
    # Look up the price rate
    price_rate = PriceRate.query.filter_by(
        pricing_category_id=service.pricing_category_id,
        academic_level_id=academic_level_id,
        deadline_id=deadline_id
    ).first()
    
    # Validate price rate exists
    if not price_rate:
        raise ValueError("Price rate not found for the given combination of service, academic level, and deadline")
    
    # Calculate prices
    price_per_page = price_rate.price_per_page
    pages_price = price_per_page * page_count
    total_price = pages_price + report_price
    
    return {
        "price_per_page": price_per_page,
        "page_count": page_count,
        "pages_price": pages_price,
        "report_price": report_price,
        "total_price": total_price,
        "selected_deadline": selected_deadline.to_dict(),
        "hours_until_deadline": round(hours_until_deadline, 2)
    }


@api_bp.route('/calculate-price', methods=['POST'])
def calculate_price():
    """
    API endpoint to calculate order price based on service, academic level, deadline, and page count
    """
    data = request.json
    
    try:
        # Validate required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        service_id = data.get('service_id')
        academic_level_id = data.get('academic_level_id')
        hours_until_deadline = data.get('deadline_data')
        word_count = data.get('word_count', 0)
        report_type = data.get('report_type')
        
        # Validate required fields
        if service_id is None or academic_level_id is None or hours_until_deadline is None:
            return jsonify({"error": "Missing required fields: service_id, academic_level_id, deadline_data"}), 400
        
        # Call the internal function
        result = calculate_price_internal(
            service_id=service_id,
            academic_level_id=academic_level_id,
            hours_until_deadline=hours_until_deadline,
            word_count=word_count,
            report_type=report_type
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error calculating price: {str(e)}")
        return jsonify({"error": "Internal server error occurred while calculating price"}), 500

##################################################################################################################################
############################### API Endpoints for Services, Academic Levels, and Deadlines for hero-sec #######################################

@api_bp.route('/get-services')
def api_get_services():
    """
    API endpoint to fetch all services
    Returns services organized by category
    """
    try:
        services = Service.query.all()
        services_data = []
        
        for service in services:
            services_data.append({
                'id': service.id,
                'name': service.name,
                'pricing_category_id': service.pricing_category_id,
                'description': getattr(service, 'description', ''),  # Include if available
                'created_at': service.created_at.isoformat() if hasattr(service, 'created_at') else None
            })
        
        return jsonify(services_data), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch services',
            'message': str(e)
        }), 500


@api_bp.route('/academic-levels')
def api_get_academic_levels():
    """
    API endpoint to fetch all academic levels
    """
    try:
        academic_levels = AcademicLevel.query.all()
        levels_data = []
        
        for level in academic_levels:
            levels_data.append({
                'id': level.id,
                'name': level.name,
                'description': getattr(level, 'description', ''),  # Include if available
                'order': getattr(level, 'order', level.id)  # Use order if available, otherwise use id
            })
        
        # Sort by order if available
        levels_data.sort(key=lambda x: x['order'])
        
        return jsonify(levels_data), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch academic levels',
            'message': str(e)
        }), 500


@api_bp.route('/deadlines')
def api_get_deadlines():
    """
    API endpoint to fetch all deadlines
    """
    try:
        deadlines = Deadline.query.all()
        deadlines_data = []
        
        for deadline in deadlines:
            deadlines_data.append({
                'id': deadline.id,
                'name': deadline.name,
                'hours': deadline.hours,
                'order': getattr(deadline, 'order', deadline.id),
                'multiplier': getattr(deadline, 'multiplier', 1.0)  # Include if available
            })
        
        # Sort by order
        deadlines_data.sort(key=lambda x: x['order'])
        
        return jsonify(deadlines_data), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch deadlines',
            'message': str(e)
        }), 500


@api_bp.route('/form-data')
def api_get_all_form_data():
    """
    API endpoint to fetch all form data in one request
    This is more efficient if you want to minimize API calls
    """
    try:
        # Fetch all required data
        services = Service.query.all()
        academic_levels = AcademicLevel.query.all()
        deadlines = Deadline.query.all()
        
        # Organize services by category
        services_by_category = {
            'writing': [],
            'proofreading': [],
            'technical': [],
            'humanizing_ai': []
        }
        
        for service in services:
            service_data = {
                'id': service.id,
                'name': service.name,
                'pricing_category_id': service.pricing_category_id,
                'description': getattr(service, 'description', '')
            }
            
            if service.pricing_category_id == 1:
                services_by_category['writing'].append(service_data)
            elif service.pricing_category_id == 2:
                services_by_category['proofreading'].append(service_data)
            elif service.pricing_category_id == 3:
                services_by_category['technical'].append(service_data)
            elif service.pricing_category_id == 4:
                services_by_category['humanizing_ai'].append(service_data)
        
        # Prepare academic levels data
        levels_data = []
        for level in academic_levels:
            levels_data.append({
                'id': level.id,
                'name': level.name,
                'description': getattr(level, 'description', ''),
                'order': getattr(level, 'order', level.id)
            })
        levels_data.sort(key=lambda x: x['order'])
        
        # Prepare deadlines data
        deadlines_data = []
        for deadline in deadlines:
            deadlines_data.append({
                'id': deadline.id,
                'name': deadline.name,
                'hours': deadline.hours,
                'order': getattr(deadline, 'order', deadline.id),
                'multiplier': getattr(deadline, 'multiplier', 1.0)
            })
        deadlines_data.sort(key=lambda x: x['order'])
        
        return jsonify({
            'services': services_by_category,
            'academic_levels': levels_data,
            'deadlines': deadlines_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch form data',
            'message': str(e)
        }), 500





@api_bp.route('/services/cached')
# @cache.cached(timeout=300)  # Cache for 5 minutes
def api_get_services_cached():
    """
    Cached version of services endpoint
    """
    return api_get_services()


@api_bp.route('/academic-levels/cached')
# @cache.cached(timeout=300)
def api_get_academic_levels_cached():
    """
    Cached version of academic levels endpoint
    """
    return api_get_academic_levels()