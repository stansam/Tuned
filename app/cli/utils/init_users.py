import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.user import User, GenderEnum


@click.command('init-users')
@click.option('--force', is_flag=True, help='Force creation even if users exist')
@with_appcontext
def init_users_cmd(force):
    """Initialize admin and test users."""
    try:
        # Check if admin exists
        admin_exists = User.query.filter_by(is_admin=True).first()
        if admin_exists and not force:
            current_app.logger.info("Admin user already exists. Use --force to recreate.")
            click.echo("Admin user already exists. Use --force to recreate.")
            return

        if force and admin_exists:
            # Remove existing users if force is used
            User.query.delete()
            db.session.commit()
            current_app.logger.info("Existing users removed due to --force flag")

        # Create admin user
        admin = User(
            username="TunedOps",
            email="yatich@tunedessays.com",
            password_hash=generate_password_hash("YatichBonn1!"),
            first_name="Bonniface",
            last_name="Yatich",
            gender=GenderEnum.male,
            is_admin=True,
            email_verified=False
        )

        # Create test users
        user1 = User(
            username="johndoe",
            email="john@example.com",
            password_hash=generate_password_hash("johnpassword"),
            first_name="John",
            last_name="Doe",
            gender=GenderEnum.male,
            is_admin=False,
            email_verified=True
        )

        user2 = User(
            username="janedoe",
            email="jane@example.com",
            password_hash=generate_password_hash("janepassword"),
            first_name="Jane",
            last_name="Doe",
            gender=GenderEnum.female,
            is_admin=False,
            email_verified=True
        )

        db.session.add_all([admin, user1, user2])
        db.session.commit()
        
        current_app.logger.info("--- ADMIN AND TEST USERS CREATED ---")
        click.echo("✓ Admin and test users created successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating users: {str(e)}")
        click.echo(f"✗ Error creating users: {str(e)}", err=True)
        raise click.Abort()