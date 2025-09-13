from flask import request, Response
from app.sitemap_robots import bp

@bp.route('/robots.txt')
def robots_txt():
    """Route handler that serves appropriate robots.txt based on subdomain"""
    from app.sitemap_robots.routes.utils.robots import get_admin_robots, get_auth_robots, get_api_robots, get_client_robots, get_main_robots
    host = request.host.lower()
    
    if 'admin.' in host:
        content = get_admin_robots()
    elif 'auth.' in host:
        content = get_auth_robots()
    elif 'api.' in host:
        content = get_api_robots()
    elif 'client.' in host:
        content = get_client_robots()
    else:
        content = get_main_robots()
    
    return Response(content, mimetype='text/plain')

@bp.route('/sitemap.xml')
def sitemap_xml():
    """Route handler that serves appropriate sitemap.xml based on subdomain"""
    from app.sitemap_robots.routes.utils.sitemaps import get_main_sitemap, get_minimal_sitemap
    from app.models import BlogPost, BlogCategory, Sample, Service
    host = request.host.lower()

    if 'admin.' in host:
        content = get_minimal_sitemap()

    elif 'auth.' in host:
        content = get_minimal_sitemap()

    elif 'api.' in host:
        content = get_minimal_sitemap()

    elif 'client.' in host:
        content = get_minimal_sitemap()

    else:
        content = get_main_sitemap(Blog=BlogPost, Service=Service, Sample=Sample, BlogCategory=BlogCategory)

    return Response(content, mimetype='application/xml')