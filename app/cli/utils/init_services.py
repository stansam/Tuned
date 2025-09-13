import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models.service import Service, ServiceCategory
from app.models.price import PricingCategory


@click.command('init-services')
@click.option('--force', is_flag=True, help='Force recreation of service data')
@with_appcontext
def init_services_cmd(force):
    """Initialize service categories and services."""
    try:
        existing_categories = ServiceCategory.query.first()
        existing_services = Service.query.first()
        
        if (existing_categories or existing_services) and not force:
            current_app.logger.info("Service data already exists. Use --force to recreate.")
            click.echo("Service data already exists. Use --force to recreate.")
            return

        if force:
            Service.query.delete()
            ServiceCategory.query.delete()
            db.session.commit()
            current_app.logger.info("Existing service data removed due to --force flag")

        existing_pricing_categories = {pc.name: pc for pc in PricingCategory.query.all()}
        
        if not existing_pricing_categories:
            current_app.logger.error("No pricing categories found. Run 'flask init-pricing' first.")
            click.echo("✗ No pricing categories found. Run 'flask init-pricing' first.", err=True)
            raise click.Abort()

        from app.cli.utils.data.services import categories, category_descriptions, service_to_pricing_category, SYNONYMS 

        created_categories = 0
        created_services = 0
        
        for category_name, services in categories.items():
            cat_desc = category_descriptions.get(category_name)
            category = ServiceCategory(
                name=category_name,
                description=cat_desc
            )
            db.session.add(category)
            db.session.flush()  
            created_categories += 1
            
            for service_name, service_description in services:
                pricing_category_name = service_to_pricing_category.get(service_name)
                pricing_cat_id = None

                if pricing_category_name and pricing_category_name in existing_pricing_categories:
                    pricing_cat_id = existing_pricing_categories[pricing_category_name].id

                service_key = service_name.lower()
                tags_list = SYNONYMS.get(service_key, [service_key])

                service = Service(
                    name=service_name,
                    description=service_description,
                    category=category,
                    featured=True,
                    tags=" ".join(tags_list),
                    pricing_category_id=pricing_cat_id
                )

                db.session.add(service)
                created_services += 1
        
        db.session.commit()
        
        success_msg = "--- SERVICES DATA CREATED SUCCESSFULLY ---"
        current_app.logger.info(success_msg)
        click.echo(f"✓ {success_msg}")
        
        click.echo("\nCreated service categories:")
        for category_name in categories.keys():
            click.echo(f"  • {category_name}")
            
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error initializing services: {str(e)}"
        current_app.logger.error(error_msg)
        click.echo(f"✗ {error_msg}", err=True)
        raise click.Abort()