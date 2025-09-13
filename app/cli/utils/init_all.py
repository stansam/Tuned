"""CLI command to initialize all database data at once."""

import click
from flask import current_app
from flask.cli import with_appcontext
from .init_users import init_users_cmd
from .init_academic_data import init_academic_data_cmd
from .init_pricing import init_pricing_cmd
from .init_services import init_services_cmd
from .init_content import init_content_cmd
from .init_blog import init_blog_cmd


@click.command('init-all')
@click.option('--force', is_flag=True, help='Force recreation of all data')
@with_appcontext
def init_all_cmd(force):
    """Initialize all database data in the correct order."""
    try:
        current_app.logger.info("Starting complete database initialization...")
        click.echo("🚀 Starting complete database initialization...")
        
        # Execute commands in dependency order
        commands = [
            ("Users", init_users_cmd),
            ("Academic Data", init_academic_data_cmd),
            ("Pricing", init_pricing_cmd),
            ("Services", init_services_cmd),
            ("Content", init_content_cmd),
            ("Blog", init_blog_cmd),
        ]
        
        for step_name, command_func in commands:
            try:
                click.echo(f"\nInitializing {step_name}...")
                # Create context for the command
                ctx = click.Context(command_func)
                ctx.params = {'force': force}
                
                # Invoke the command with the context
                command_func.invoke(ctx)
                
            except click.Abort:
                current_app.logger.error(f"Failed to initialize {step_name}")
                click.echo(f"✗ Failed to initialize {step_name}")
                raise
            except Exception as e:
                current_app.logger.error(f"Unexpected error initializing {step_name}: {str(e)}")
                click.echo(f"✗ Unexpected error initializing {step_name}: {str(e)}", err=True)
                raise click.Abort()
        
        current_app.logger.info("--- ALL DATABASE INITIALIZATION COMPLETED ---")
        click.echo("\nAll database initialization completed successfully!")
        click.echo("\nYou can now:")
        click.echo("• Start your application")
        click.echo("• Log in with admin credentials: yatich@tunedessays.com / YatichBonn1!")
        click.echo("• Test with user credentials: john@example.com / johnpassword")
        
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {str(e)}")
        click.echo(f"\n✗ Database initialization failed: {str(e)}", err=True)
        raise click.Abort()