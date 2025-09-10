from flask import jsonify
from app.api import api_bp
from app.models.blog import BlogPost, BlogCategory


@api_bp.route('/blog/featured', methods=['GET'])
def get_featured_blog_posts():
    """
    API endpoint to get featured blog posts for the homepage carousel
    Returns the most recent published blog posts
    """
    try:
        # Query for published blog posts, ordered by publish date (most recent first)
        posts = BlogPost.query.filter_by(is_published=True) \
                            .order_by(BlogPost.published_at.desc()) \
                            .limit(6) \
                            .all()
        
        # Format the posts for the frontend
        formatted_posts = []
        for post in posts:          
            # Get category information
            category_info = None
            if post.category_id:
                category = BlogCategory.query.get(post.category_id)
                if category:
                    category_info = {
                        'name': category.name,
                        'slug': category.slug
                    }
            
            # Format post data
            post_data = {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt,
                'tags': post.tags,
                'featured_image': post.featured_image,
                'created_at': post.created_at.isoformat(),
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'author': post.author,
                'category': category_info or {'name': 'Uncategorized', 'slug': 'uncategorized'}
            }
            
            formatted_posts.append(post_data)
        
        return jsonify(formatted_posts)
    
    except Exception as e:
        # Log the error (you should implement proper logging)
        print(f"Error fetching blog posts: {str(e)}")
        return jsonify({"error": "Failed to fetch blog posts"}), 500

@api_bp.route('/services')
def get_services():
    from app.models import Service
    services = Service.query.all()
    if not services:
        return jsonify([])
    
    return jsonify([{
        'id': service.id,
        'name': service.name,
    } for service in services])