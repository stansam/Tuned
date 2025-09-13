# robots.py - Add this to your main Flask app or create a separate blueprint

from flask import Blueprint, Response, request

# Create a blueprint for robots.txt routes
robots_bp = Blueprint('robots', __name__)

def get_main_robots():
    """Main domain robots.txt - permissive for public marketing content"""
    robots_txt = """User-agent: *
# Allow all public content
Allow: /
Allow: /static/main/
Allow: /static/main/css/
Allow: /static/main/js/
Allow: /static/main/assets/

# Allow all main public pages
Allow: /blogs
Allow: /blog/
Allow: /samples
Allow: /services
Allow: /service/
Allow: /testimonials
Allow: /faqs
Allow: /search
Allow: /contact
Allow: /privacy
Allow: /terms
Allow: /refund

# Disallow subdomains and sensitive areas
Disallow: /api/
Disallow: /admin/
Disallow: /client/
Disallow: /auth/
Disallow: /.env
Disallow: /config/
Disallow: /uploads/
Disallow: /temp/
Disallow: /.git/
Disallow: /venv/
Disallow: /__pycache__/

# Disallow duplicate paginated content (let crawlers find via links)
Disallow: /blogs/page/
Disallow: /blogs/category/*/page/

# Disallow search results and dynamic pages
Disallow: /search?*
Disallow: /*?*

# Standard crawl delay for marketing site
Crawl-delay: 1

# Sitemap location
Sitemap: https://tunedessays.com/sitemap.xml
"""
    return robots_txt

def get_admin_robots():
    """Admin subdomain robots.txt - completely restricted"""
    robots_txt = """User-agent: *
Disallow: /
Disallow: /admin/
Disallow: /api/
Disallow: /auth/
Disallow: /client/
Disallow: /.env
Disallow: /config/
Disallow: /uploads/
Disallow: /temp/
Disallow: /.git/
Disallow: /venv/
Disallow: /__pycache__/

# No search engines should index admin areas
"""
    return robots_txt

def get_auth_robots():
    """Auth subdomain robots.txt - restricted for security"""
    robots_txt = """User-agent: *
Disallow: /

# Authentication pages should not be indexed
# for security and user privacy
"""
    return robots_txt

def get_api_robots():
    """API subdomain robots.txt - selective permissions"""
    robots_txt = """User-agent: *

# Disallow all API endpoints and private docs
Disallow: /
Disallow: /admin/
Disallow: /api/
Disallow: /auth/
Disallow: /client/
Disallow: /.env
Disallow: /config/
Disallow: /uploads/
Disallow: /temp/
Disallow: /.git/
Disallow: /venv/
Disallow: /__pycache__/

# Specific crawl delay for API
Crawl-delay: 2
"""
    return robots_txt

def get_client_robots():
    """Client subdomain robots.txt - public facing, more permissive"""
    robots_txt = """User-agent: *
Allow: /static/
Allow: /static/main/css/
Allow: /static/main/js/
Allow: /static/main/assets/

# Disallow user-specific or sensitive areas
Disallow: /
Disallow: /orders/
Disallow: /order-details/
Disallow: /download-order-files/
Disallow: /download_delivery_file/
Disallow: /download_file/
Disallow: /profile/
Disallow: /settings/
Disallow: /checkout/
Disallow: /static/sounds/
Disallow: /admin/
Disallow: /api/
Disallow: /auth/
Disallow: /client/
Disallow: /.env
Disallow: /config/
Disallow: /uploads/
Disallow: /temp/
Disallow: /.git/
Disallow: /venv/
Disallow: /__pycache__/

Disallow: /orders/refresh
Disallow: /dashboard/refresh
Disallow: /orders/status-counts

# Standard crawl delay
Crawl-delay: 2

# Sitemap for client subdomain
Sitemap: https://client.tunedessays.com/sitemap.xml
"""
    return robots_txt