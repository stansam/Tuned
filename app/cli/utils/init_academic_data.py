import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models.service import AcademicLevel, Deadline


@click.command('init-academic-data')
@click.option('--force', is_flag=True, help='Force recreation of academic data')
@with_appcontext
def init_academic_data_cmd(force):
    """Initialize academic levels and deadlines."""
    try:
        # Check if academic data already exists
        existing_levels = AcademicLevel.query.first()
        existing_deadlines = Deadline.query.first()
        
        if (existing_levels or existing_deadlines) and not force:
            current_app.logger.info("Academic data already exists. Use --force to recreate.")
            click.echo("Academic data already exists. Use --force to recreate.")
            return

        if force:
            # Remove existing data
            Deadline.query.delete()
            AcademicLevel.query.delete()
            db.session.commit()
            current_app.logger.info("Existing academic data removed due to --force flag")

        # Create academic levels
        academic_levels = [
            AcademicLevel(name="High School", order=1),
            AcademicLevel(name="Undergraduate", order=2),
            AcademicLevel(name="Personal", order=3),
            AcademicLevel(name="Master's", order=4),
            AcademicLevel(name="Doctorate", order=6),
            AcademicLevel(name="Professional", order=7)
        ]
        
        db.session.add_all(academic_levels)

        # Create deadlines
        deadlines = [
            Deadline(name="3 Hours", hours=3, order=1),
            Deadline(name="6 Hours", hours=6, order=2),
            Deadline(name="12 Hours", hours=12, order=3),
            Deadline(name="24 Hours", hours=24, order=4),
            Deadline(name="48 Hours", hours=48, order=5),
            Deadline(name="3 Days", hours=72, order=6),
            Deadline(name="7 Days", hours=168, order=7),
            Deadline(name="10 Days", hours=240, order=8),
            Deadline(name="14 Days", hours=336, order=9),
            Deadline(name="20 Days", hours=400, order=10)
        ]
        
        db.session.add_all(deadlines)
        db.session.commit()
        
        current_app.logger.info("--- ACADEMIC DATA CREATED ---")
        click.echo(f"✓ Created {len(academic_levels)} academic levels and {len(deadlines)} deadlines")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating academic data: {str(e)}")
        click.echo(f"✗ Error creating academic data: {str(e)}", err=True)
        raise click.Abort()