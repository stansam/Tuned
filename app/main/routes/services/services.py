from app.main import main_bp
from flask import render_template, request
from app.models.service import Service, ServiceCategory
from app.models.content import Sample
from app.models.service import AcademicLevel

@main_bp.route('/services')
def services():
    service_category_id = request.args.get('service_category_id', type=int)
    selected_category = None
    if service_category_id:
        selected_category = ServiceCategory.query.get_or_404(service_category_id)
    samples = Sample.query.all()
    categories = ServiceCategory.query.all()

    return render_template('main/services/services.html',
                           categories=categories, 
                          title="Our Services",
                          sample_papers=samples,
                          service_category_id=service_category_id if service_category_id else None,
                          selected_category=selected_category)

@main_bp.route('/service/<slug>')
def service_detail(slug):
    # service = Service.query.get_or_404(service_id)
    service = Service.query.filter_by(slug=slug).first_or_404()
    academic_levels = AcademicLevel.query.order_by("order" )
    return render_template('main/services/service_details.html', 
                           service=service,
                           academic_levels=academic_levels)

