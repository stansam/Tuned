from app.models import ServiceCategory, AcademicLevel
from flask import jsonify
from app.api import api_bp

@api_bp.route("/client/new-order/services-with-categories")
def services_with_categories():
    categories = ServiceCategory.query.order_by(ServiceCategory.order).all()
    result = []
    for category in categories:
        result.append({
            "id": category.id,
            "name": category.name,
            "services": [s.to_dict() for s in category.services]
        })
    return jsonify(result)

@api_bp.route("/client/new-order/project-level")
def project_levels():
    levels = AcademicLevel.query.order_by(AcademicLevel.order).all()
    result = []
    for level in levels:
        result.append({
            "id": level.id,
            "name": level.name,
        })
    return jsonify(result)