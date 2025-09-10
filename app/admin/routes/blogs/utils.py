from slugify import slugify

def generate_unique_slug(title, model, current_id=None):
    base_slug = slugify(title)
    slug = base_slug
    count = 1
    
    while True:
        existing = model.query.filter_by(slug=slug).first()
        
        if not existing or (current_id and existing.id == current_id):
            return slug
        
        slug = f"{base_slug}-{count}"
        count += 1