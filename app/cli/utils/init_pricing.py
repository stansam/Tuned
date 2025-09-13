import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models.price import PricingCategory, PriceRate
from app.models.service import AcademicLevel, Deadline


@click.command('init-pricing')
@click.option('--force', is_flag=True, help='Force recreation of pricing data')
@with_appcontext
def init_pricing_cmd(force):
    """Initialize pricing categories and rates."""
    try:
        # Check if pricing data already exists
        existing_categories = PricingCategory.query.first()
        existing_rates = PriceRate.query.first()
        
        if (existing_categories or existing_rates) and not force:
            current_app.logger.info("Pricing data already exists. Use --force to recreate.")
            click.echo("Pricing data already exists. Use --force to recreate.")
            return

        if force:
            # Remove existing pricing data
            PriceRate.query.delete()
            PricingCategory.query.delete()
            db.session.commit()
            current_app.logger.info("Existing pricing data removed due to --force flag")

        # Create pricing categories
        categories = [
            PricingCategory(name="Writing", description="Standard pricing for all services.", display_order=1),
            PricingCategory(name="Proofreading & Editing", description="Premium pricing for high-demand services.", display_order=2),
            PricingCategory(name="Technical & Calculations", description="Standard pricing for all technical services.", display_order=3),
            PricingCategory(name="Humanizing AI", description="Premium pricing for high-demand services.", display_order=4)
        ]
        
        db.session.add_all(categories)
        db.session.commit()

        # Get required data for price rates
        academic_levels = {level.name: level for level in AcademicLevel.query.all()}
        deadlines = {deadline.name: deadline for deadline in Deadline.query.all()}
        pricing_categories = {cat.name: cat for cat in PricingCategory.query.all()}

        if not academic_levels:
            current_app.logger.error("No academic levels found. Run 'flask init-academic-data' first.")
            click.echo("✗ No academic levels found. Run 'flask init-academic-data' first.", err=True)
            raise click.Abort()

        if not deadlines:
            current_app.logger.error("No deadlines found. Run 'flask init-academic-data' first.")
            click.echo("✗ No deadlines found. Run 'flask init-academic-data' first.", err=True)
            raise click.Abort()

        # Create price rates
        from app.cli.utils.data.pricing import PRICE_RATES_DATA as price_rates_data, LEVEL_NAMES as level_names 

        rates_created = 0
        for category_name, deadline_data in price_rates_data.items():
            if category_name not in pricing_categories:
                current_app.logger.error(f"Pricing category '{category_name}' not found. Skipping...")
                continue
                
            category = pricing_categories[category_name]
            
            for deadline_name, prices in deadline_data.items():
                if deadline_name not in deadlines:
                    current_app.logger.error(f"Deadline '{deadline_name}' not found. Skipping...")
                    continue
                    
                deadline = deadlines[deadline_name]
                
                for i, level_name in enumerate(level_names):
                    if level_name not in academic_levels:
                        current_app.logger.error(f"Academic level '{level_name}' not found. Skipping...")
                        continue
                        
                    academic_level = academic_levels[level_name]
                    
                    # Check if this price rate already exists
                    existing_rate = PriceRate.query.filter_by(
                        pricing_category_id=category.id,
                        academic_level_id=academic_level.id,
                        deadline_id=deadline.id
                    ).first()

                    if existing_rate:
                        current_app.logger.info(f"Price rate already exists for {category_name} - {level_name} - {deadline_name}")
                        continue
                    
                    if i < len(prices):
                        price = prices[i]
                        
                        price_rate = PriceRate(
                            pricing_category_id=category.id,
                            academic_level_id=academic_level.id,
                            deadline_id=deadline.id,
                            price_per_page=price
                        )
                        db.session.add(price_rate)
                        rates_created += 1
        
        db.session.commit()
        current_app.logger.info("--- PRICING DATA CREATED ---")
        click.echo(f"✓ Created {len(categories)} pricing categories and {rates_created} price rates")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating pricing data: {str(e)}")
        click.echo(f"✗ Error creating pricing data: {str(e)}", err=True)
        raise click.Abort()