from app.models.blog import BlogPost, BlogCategory
from app.main import main_bp
from flask import render_template, request


@main_bp.route('/blogs')
@main_bp.route('/blogs/page/<int:page>')
def index(page=1):
    posts_query = BlogPost.query.filter_by(is_published=True) # .order_by(BlogPost.published_at.desc())

    q = request.args.get("q", "").strip()

    if q:
        posts_query = posts_query.filter(
            BlogPost.title.ilike(f"%{q}%") | BlogPost.content.ilike(f"%{q}%")
        )
    posts_query = posts_query.order_by(BlogPost.published_at.desc())
    
    pagination = posts_query.paginate(page=page, per_page=6, error_out=False)
    posts = pagination.items

    # Get featured post (can be the most recent one)
    featured_post = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).first()

    # Get recent posts for sidebar
    recent_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(5).all()

    # Get all categories
    categories = BlogCategory.query.all()

    return render_template('main/blogs/blogs.html', 
                          posts=posts,
                          pagination=pagination,
                          featured_post=featured_post,
                          recent_posts=recent_posts,
                          categories=categories,
                          request=request,
                          q=q,
                          title="Blog")


@main_bp.route('/blogs/category/<string:slug>')
@main_bp.route('/blogs/category/<string:slug>/page/<int:page>')
def category(slug, page=1):
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    posts_query = BlogPost.query.filter_by(category=category, is_published=True).order_by(BlogPost.published_at.desc())
    pagination = posts_query.paginate(page=page, per_page=6, error_out=False)
    posts = pagination.items

    # Get all categories for sidebar
    categories = BlogCategory.query.all()

    # Get recent posts for sidebar
    recent_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(5).all()

    return render_template('main/blogs/blog_category.html', 
                          category=category, 
                          posts=posts,
                          pagination=pagination,
                          categories=categories,
                          recent_posts=recent_posts,
                          request=request,
                          title=f"Blog - {category.name}")

@main_bp.route('/blog/<string:slug>')
def post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()

    # Get recent posts for sidebar
    recent_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(5).all()

    # Get all categories for sidebar
    categories = BlogCategory.query.all()

    # Get related posts from same category but not the current post
    related_posts = BlogPost.query.filter(
        BlogPost.category_id == post.category_id, 
        BlogPost.id != post.id, 
        BlogPost.is_published == True
    ).order_by(BlogPost.published_at.desc()).limit(2).all()

    return render_template('main/blogs/blog_post.html', 
                          post=post, 
                          recent_posts=recent_posts,
                          related_posts=related_posts,
                          categories=categories,
                          request=request,
                          title=post.title)