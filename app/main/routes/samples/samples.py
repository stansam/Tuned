from app.main import main_bp
from flask import render_template, request
from app.models.content import Sample
from app.models.service import Service

@main_bp.route('/samples')
def samples():
    samples = Sample.query.all()
    services = Service.query.all()

    return render_template('main/samples/samples.html', 
                          samples=samples, 
                          services=services,
                          title="Sample Papers")

@main_bp.route('/samples/<slug>')
def sample_detail(slug: str) -> str:
    # sample = Sample.query.get_or_404(sample_id)
    sample = Sample.query.filter_by(slug=slug).first_or_404()

    return render_template('main/samples/sample_details.html', 
                          sample=sample,
                          title=sample.title)