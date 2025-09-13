def get_minimal_sitemap():
    """Minimal sitemap for client subdomain when no public pages exist"""
    from datetime import datetime
    
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Empty sitemap - client portal has no public pages to index
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <!-- Client portal contains only private, authenticated pages -->
    <!-- No public pages available for indexing -->
</urlset>'''
    
    return sitemap_xml

def get_main_sitemap(Blog=None, Service=None, Sample=None, BlogCategory=None):
    """Generate sitemap"""
    from datetime import datetime
    
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
    
    # Static pages
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'weekly'},
        {'url': '/services', 'priority': '0.9', 'changefreq': 'monthly'},
        {'url': '/blogs', 'priority': '0.8', 'changefreq': 'daily'},
        {'url': '/samples', 'priority': '0.7', 'changefreq': 'weekly'},
        {'url': '/testimonials', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/faqs', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/contact', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/privacy', 'priority': '0.3', 'changefreq': 'yearly'},
        {'url': '/terms', 'priority': '0.3', 'changefreq': 'yearly'},
        {'url': '/refund', 'priority': '0.3', 'changefreq': 'yearly'},
    ]
    
    for page in static_pages:
        full_url = f"https://tunedessays.com{page['url']}"
        sitemap_xml += f'''
    <url>
        <loc>{full_url}</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>{page['changefreq']}</changefreq>
        <priority>{page['priority']}</priority>
    </url>'''
    
    # Dynamic content
    if Blog:
        try:
            blogs = Blog.query.filter_by(is_published=True).all()
            for blog in blogs:
                last_mod = blog.published_at.strftime('%Y-%m-%dT%H:%M:%S+00:00') if hasattr(blog, 'published_at') and blog.published_at else current_time
                sitemap_xml += f'''
    <url>
        <loc>https://yourdomain.com/blog/{blog.slug}</loc>
        <lastmod>{last_mod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>'''
        except Exception:
            pass
    
    if Service:
        try:
            services = Service.query.filter_by(active=True).all()
            for service in services:
                last_mod = current_time
                sitemap_xml += f'''
    <url>
        <loc>https://yourdomain.com/service/{service.slug}</loc>
        <lastmod>{last_mod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>'''
        except Exception:
            pass
    
    if Sample:
        try:
            samples = Sample.query.all()
            for sample in samples:
                last_mod = sample.created_at.strftime('%Y-%m-%dT%H:%M:%S+00:00') if hasattr(sample, 'created_at') and sample.created_at else current_time
                sitemap_xml += f'''
    <url>
        <loc>https://yourdomain.com/samples/{sample.slug}</loc>
        <lastmod>{last_mod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>'''
        except Exception:
            pass
    
    if BlogCategory:
        try:
            categories = BlogCategory.query.all()
            for category in categories:
                sitemap_xml += f'''
    <url>
        <loc>https://yourdomain.com/blogs/category/{category.slug}</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>'''
        except Exception:
            pass
    
    sitemap_xml += '''
</urlset>'''
    
    return sitemap_xml