from flask import Blueprint, render_template, request, redirect, url_for, Response
from app.main import main_bp
from app.extensions import db
from app.models.blog import BlogPost, BlogCategory
from app.models.service import ServiceCategory, Service
from app.models.content import Sample, Testimonial, FAQ
from app.models.communication import ChatMessage, NewsletterSubscriber, Notification
from app.models.service import AcademicLevel, Deadline
from app.models.price import PriceRate, PricingCategory
import datetime
from bs4 import BeautifulSoup


@main_bp.route('/')
def home():
    services = Service.query.all()
    categories = ServiceCategory.query.all()
    testimonials = Testimonial.query.filter_by(is_approved=True).all()
    samples = Sample.query.filter_by(featured=True).all()

    return render_template('main/home.html',
                            featured_services=services,
                            categories=categories,
                            testimonials=testimonials,
                            samples=samples,
                            title="Academic Writing Services")

@main_bp.route('/testimonails')
def testimonials():
    testimonials = Testimonial.query.filter_by(is_approved=True).all()

    return render_template('main/testimonials/testimonials.html', 
                          testimonials=testimonials,
                          title="Client Testimonials")

@main_bp.route('/faqs')
def faq():
    faqs = FAQ.query.order_by(FAQ.category, FAQ.order).all()
    faq_categories = {}
    for faq in faqs:
        if faq.category not in faq_categories:
            faq_categories[faq.category] = []
        faq_categories[faq.category].append(faq)

    return render_template('main/faq/faq.html', 
                          faq_categories=faq_categories,
                          title="Frequently Asked Questions")

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.home'))
    
    services = Service.query.filter(Service.name.ilike(f'%{query}%')).all()
    
    categories = ServiceCategory.query.filter(ServiceCategory.name.ilike(f'%{query}%')).all()
    blogs = BlogPost.query.filter(BlogPost.title.ilike(f'%{query}%')).all()
    blog_categories = BlogCategory.query.filter(BlogCategory.name.ilike(f'%{query}%')).all()
    
    return render_template('main/search_results.html',
                          services=services,
                          categories=categories,
                          blogs=blogs,
                          blog_categories=blog_categories,
                          query=query,
                          title=f"Search Results for '{query}'")
@main_bp.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    return render_template('main/newsletter/subscribe.html', title="Subscribe to Newsletter")

# Legals Routes
@main_bp.route('/privacy')
def privacy():
    return render_template('main/legals/privacy.html')

@main_bp.route('/refund')
def refund():
    return render_template('main/legals/refund.html')

@main_bp.route('/terms')
def terms():
    return render_template('main/legals/terms.html')


@main_bp.route('/contact')
def contact():
    return render_template('main/legals/contact.html', title="Contact Us")

# @main_bp.route("/robots.txt")
# def robots_txt():
#     return Response("User-agent: *\nAllow: /\nSitemap: https://tunedessays.com/sitemap.xml",
#                     mimetype="text/plain")