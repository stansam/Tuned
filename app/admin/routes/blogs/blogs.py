from flask import request, render_template, current_app, redirect, flash, url_for
from app.models.blog import BlogCategory, BlogPost, BlogComment
from app.admin.routes.blogs.utils import generate_unique_slug
from flask_login import login_required, current_user
from app.admin.routes.decorator import admin_required
from werkzeug.utils import secure_filename
from app.admin import admin_bp
from app.extensions import db
from datetime import datetime
import json
import uuid
import os


@admin_bp.route('/blog')
@login_required
@admin_required
def list_blog_posts():
    """Display all blog posts with filtering options."""
    published_filter = request.args.get('published', '')
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    
    # Base query
    query = BlogPost.query
    
    # Apply filters
    if published_filter == 'true':
        query = query.filter(BlogPost.is_published == True)
    elif published_filter == 'false':
        query = query.filter(BlogPost.is_published == False)
        
    if search_query:
        query = query.filter(
            (BlogPost.title.ilike(f'%{search_query}%')) |
            (BlogPost.content.ilike(f'%{search_query}%'))
        )
    
    if category_filter:
        query = query.filter(BlogPost.category_id == category_filter)
    
    # Get the sorted posts
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(getattr(BlogPost, sort_by).desc())
    else:
        query = query.order_by(getattr(BlogPost, sort_by).asc())
    
    posts = query.all()
    
    # Get all categories for filter dropdown
    categories = BlogCategory.query.all()
    
    # Get stats for the sidebar
    total_posts = BlogPost.query.count()
    published_posts = BlogPost.query.filter_by(is_published=True).count()
    draft_posts = BlogPost.query.filter_by(is_published=False).count()
    
    return render_template('admin/content/blog/list.html', 
                           posts=posts,
                           categories=categories,
                           published_filter=published_filter,
                           search_query=search_query,
                           category_filter=category_filter,
                           sort_by=sort_by,
                           sort_order=sort_order,
                           total_posts=total_posts,
                           published_posts=published_posts,
                           draft_posts=draft_posts,
                           title='Blog Management')

@admin_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_blog_post():
    """Create a new blog post."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt', '')
        category_id = request.form.get('category_id')
        published = True if request.form.get('published') == 'true' else False
        meta_description = request.form.get('meta_description', '')
        # tags = request.form.get('tags', '').strip()
        tags = ','.join([tag['value'].strip() for tag in json.loads(request.form.get('tags', '[]')) if tag.get('value')]) or None
        author = request.form.get('author')
        # tags = [tag.strip() for tag in tags if tag.strip()]
        # if tags and len(tags) > 0:
        #     for tag in tags:
        #         content += f"\n{tag}\n"
        if tags:
            cleaned_tags = [tag.strip() for tag in tags if tag.strip()]
        else:
            cleaned_tags = []
            
        # Generate slug from title
        slug = generate_unique_slug(title, BlogPost)
        
        # Handle featured image upload
        featured_image = None
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                # Create directory if it doesn't exist
                upload_dir = os.path.join('app', 'static', 'uploads', 'blog')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save the file
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)
                
                # Save the path relative to static directory
                featured_image = os.path.join('uploads', 'blog', unique_filename).replace('\\', '/')
        
        # Create new blog post
        post = BlogPost(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            featured_image=featured_image,
            tags = tags,
            author=author,
            meta_description=meta_description,
            category_id=category_id,
            is_published=published,
            published_at=datetime.now() if published else None
        )
        try:
            db.session.add(post)
            db.session.commit()
            # other = current_user
            # notify(other, 
            #     title=f"New blog has been created by {current_user.get_name()}", 
            #     message=post.excerpt[:50], 
            #     type='info', 
            #     link=url_for('admin.view_blog_post', post_id=post.id))
            # all_users = User.query.all()
            # for user in all_users:
            #     if user.id != current_user.id:      
            #         notify(user, 
            #             title=f"New blog has been created by {current_user.get_name()}", 
            #             message=post.excerpt[:50], 
            #             type='info', 
            #             link=url_for('blog.post', slug=post.slug))
            flash('Blog post created successfully', 'success')
            return redirect(url_for('admin.view_blog_post', post_id=post.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating blog post: {str(e)}")
            flash('An error occurred while creating the blog post. Please try again.', 'danger')
            return redirect(url_for('admin.create_blog_post'))
    
    # GET request - render form
    categories = BlogCategory.query.all()
    
    return render_template('admin/content/blog/create.html',
                           categories=categories,
                           title='Create Blog Post')

@admin_bp.route('/blog/<int:post_id>')
@login_required
@admin_required
def view_blog_post(post_id):
    """View a specific blog post."""
    post = BlogPost.query.get_or_404(post_id)
    comments = BlogComment.query.filter_by(post_id=post_id).order_by(BlogComment.created_at.desc()).all()
    all_approved = all(comment.approved for comment in comments)
    
    return render_template('admin/content/blog/view.html',
                           post=post,
                           all_approved=all_approved,
                           comments=comments,
                           title=post.title)

@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog_post(post_id):
    """Edit a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt', '')
        category_id = request.form.get('category_id')
        author = request.form.get('author', current_user.get_name())
        published = True if request.form.get('published') == 'true' else False
        meta_description = request.form.get('meta_description', '')
        tags = request.form.get('tags', '')
        
        # Validate required fields
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('admin.edit_blog_post', post_id=post.id))
        
        try:
            # Update post details
            post.title = title
            post.content = content
            post.excerpt = excerpt
            post.author = author
            post.meta_description = meta_description
            post.tags = tags  # Store as comma-separated string
            
            # Update category if provided
            if category_id:
                try:
                    post.category_id = int(category_id)
                except (ValueError, TypeError):
                    post.category_id = None
            else:
                post.category_id = None
            
            # Update slug if title changed
            if post.title != title:
                post.slug = generate_unique_slug(title, BlogPost, post.id)
            
            # Update published status
            if post.is_published != published:
                post.is_published = published
                if published and not post.published_at:
                    post.published_at = datetime.now()
                elif not published:
                    post.published_at = None
            
            # Handle featured image upload
            if 'featured_image' in request.files:
                file = request.files['featured_image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join('app', 'static', 'uploads', 'blog')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save the file
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    
                    # Delete old image if exists
                    if post.featured_image:
                        old_path = os.path.join('app', 'static', post.featured_image)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass  # File doesn't exist or can't be removed
                    
                    # Save the path relative to static directory
                    post.featured_image = os.path.join('uploads', 'blog', unique_filename).replace('\\', '/')
            
            # Commit changes
            db.session.commit()
            
            # Send notifications
            # notify(current_user, 
            #     title=f"Post '{post.title}' has been updated", 
            #     message="Blog post updated successfully", 
            #     type='info', 
            #     link=url_for('admin.view_blog_post', post_id=post.id))
            
            # # Notify other admin users
            # admin_users = User.query.filter(User.is_admin == True, User.id != current_user.id).all()
            # for user in admin_users:
            #     notify(user, 
            #         title=f"Post '{post.title}' has been updated by {current_user.get_name()}", 
            #         message="Blog post updated successfully", 
            #         type='info', 
            #         link=url_for('admin.view_blog_post', post_id=post.id))
            
            flash('Blog post updated successfully', 'success')
            
            # Redirect based on publish status
            if published:
                return redirect(url_for('admin.view_blog_post', post_id=post.id))
            else:
                return redirect(url_for('admin.list_blog_posts'))

        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update blog post: {str(e)}', 'error')
            return redirect(url_for('admin.edit_blog_post', post_id=post.id))
    
    
    categories = BlogCategory.query.order_by(BlogCategory.name).all()
    
    return render_template('admin/content/blog/edit.html', 
                         post=post, 
                         categories=categories)

@admin_bp.route('/blog/<int:post_id>/toggle-published', methods=['POST'])
@login_required
@admin_required
def toggle_post_published(post_id):
    """Toggle the published status of a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    
    # Toggle the published status
    post.is_published = not post.is_published
    
    # Update published_at timestamp if being published
    if post.is_published and not post.published_at:
        post.published_at = datetime.now()
    
    # Create notification message based on new status
    status_message = "published" if post.is_published else "unpublished"
    
    # Notify the current user
    try:
        db.session.commit()
        # notify(current_user, 
        #     title=f"Post '{post.title}' has been {status_message} by {current_user.get_name()}", 
        #     message=f"Blog post {status_message}.", 
        #     type='info', 
        #     link=url_for('admin.view_blog_post', post_id=post.id))
        
        # # Notify all users
        # all_users = User.query.all()
        # for user in all_users:
        #     if user.id != current_user.id:  # Avoid duplicate notification for current user
        #         notify(user, 
        #             title=f"Post '{post.title}' has been {status_message} by {current_user.get_name()}", 
        #             message=f"Blog post {status_message}.", 
        #             type='info', 
        #             link=url_for('admin.view_blog_post', post_id=post.id))
        
        
        flash(f'Blog post {status_message} successfully', 'success')
        return redirect(url_for('admin.view_blog_post', post_id=post.id))
    except Exception as e:
        db.session.rollback()
        flash("Error updating featured status", "error")
        return redirect(url_for("admin.view_blog_post", post_id=post.id))


@admin_bp.route('/blog/<int:post_id>/duplicate', methods=['POST'])
@login_required
@admin_required
def duplicate_blog_post(post_id):
    """Create a duplicate of a blog post."""
    original_post = BlogPost.query.get_or_404(post_id)
    
    # Create a copy of the post with a modified title
    duplicate_title = f"{original_post.title} (Copy)"
    
    # Generate a unique slug for the duplicate
    duplicate_slug = generate_unique_slug(duplicate_title, BlogPost)
    
    # Create the duplicate post (unpublished by default)
    duplicate_post = BlogPost(
        title=duplicate_title,
        slug=duplicate_slug,
        content=original_post.content,
        excerpt=original_post.excerpt,
        featured_image=original_post.featured_image,  # Same image reference
        author_id=current_user.id,  # Current user becomes the author
        category_id=original_post.category_id,
        is_published=False,  # Always start as draft
        published_at=None    # Reset published date
    )
    try:
        db.session.add(duplicate_post)
        db.session.commit()
        
        # Notify the current user
        # notify(current_user, 
        #     title=f"Post '{original_post.title}' has been duplicated by {current_user.get_name()}", 
        #     message=f"A draft copy has been created.", 
        #     type='info', 
        #     link=url_for('admin.edit_blog_post', post_id=duplicate_post.id))
        
        flash('Blog post duplicated successfully. You can now edit the copy.', 'success')
        return redirect(url_for('admin.edit_blog_post', post_id=duplicate_post.id))
    except Exception as e:
        db.session.rollback()
        flash("Error duplicating pos", "error")
        return redirect(url_for("admin.view_blog_post",post_id=duplicate_post.id))
    
@admin_bp.route('/blog/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blog_post(post_id):
    """Delete a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    
    # Delete featured image if exists
    if post.featured_image:
        image_path = os.path.join('app', 'static', post.featured_image)
        if os.path.exists(image_path):
            os.remove(image_path)
    try:    
        db.session.delete(post)
        db.session.commit()
        # all_users = User.query.all()
        # for user in all_users:
        #     notify(user, 
        #         title=f"Post #{post.title} has been deleted by {current_user.get_name()}", 
        #         message="Blog post deleted successfully", 
        #         type='info', 
        #         link=None)
        
        flash('Blog post deleted successfully', 'success')
        return redirect(url_for('admin.list_blog_posts'))
    except Exception as e:
        db.session.rollback()
        flash("Fialed to delete post", "error")
        return redirect(url_for('admin.list_blog_posts'))

# Blog Categories
@admin_bp.route('/blog/categories')
@login_required
@admin_required
def list_blog_categories():
    """List all blog categories."""
    categories = BlogCategory.query.all()
    return render_template('admin/content/blog/categories.html',
                           categories=categories,
                           title='Blog Categories')

 
    

@admin_bp.route('/blog/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog_category(category_id):
    """Edit a blog category."""
    category = BlogCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        parent_id = request.form.get('parent_id', None)
        
        if not parent_id or parent_id == '0':
            parent_id = None
        
        # Prevent setting parent to self or any of its descendants
        if parent_id and int(parent_id) == category_id:
            flash('Category cannot be its own parent', 'danger')
            return redirect(url_for('admin.edit_blog_category', category_id=category_id))
        
        # Update category
        category.name = name
        category.description = description
        category.parent_id = parent_id
        
        # Update slug if name changed
        if category.name != name:
            category.slug = generate_unique_slug(name, BlogCategory, category.id)
        # other = current_user
        # notify(other, 
        #     title=f"Blog category #{category.name} has been edited by {current_user.get_name()}", 
        #     message="Category edited successfully", 
        #     type='info', 
        #     link=None)
        
        try:
            db.session.commit()
            flash('Category updated successfully', 'success')
            return redirect(url_for('admin.list_blog_categories'))
        except Exception as e:
            db.session.rollback()
            flash('Database error occurred while updating the category', 'danger')
            return redirect(url_for('admin.edit_blog_category', category_id=category_id))
    
    # GET request - render form
    categories = BlogCategory.query.all()
    
    return render_template('admin/content/blog/edit_category.html',
                           category=category,
                           categories=categories,
                           title=f'Edit Category: {category.name}')

@admin_bp.route('/blog/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blog_category(category_id):
    """Delete a blog category."""
    category = BlogCategory.query.get_or_404(category_id)
    
    # Check if category has posts
    if category.posts:
        flash('Cannot delete category with associated posts', 'danger')
        return redirect(url_for('admin.list_blog_categories'))
    
    # Check if category has subcategories
    if category.subcategories:
        flash('Cannot delete category with subcategories', 'danger')
        return redirect(url_for('admin.list_blog_categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        # other = current_user
        # notify(other, 
        #     title=f"Blog category #{category.name} has been deleted by {current_user.get_name()}", 
        #     message="Category deleted successfully", 
        #     type='info', 
        #     link=None)
        flash('Category deleted successfully', 'success')
        return redirect(url_for('admin.list_blog_categories'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the category.', 'danger')
        return redirect(url_for('admin.list_blog_categories'))