# import click
# from flask import current_app
# from flask.cli import with_appcontext
# from app.extensions import db
# from app.utils.db_init import init_db

# @click.command("init-db")
# @with_appcontext
# def init_db_command():
#     """Initialize the database (create tables + seed defaults)."""
#     db.create_all()
#     init_db(current_app, db)
#     click.echo("✅ Database initialized and seeded.")

from app.cli.utils.init_users import init_users_cmd
from app.cli.utils.init_academic_data import init_academic_data_cmd
from app.cli.utils.init_pricing import init_pricing_cmd
from app.cli.utils.init_services import init_services_cmd
from app.cli.utils.init_content import init_content_cmd
from app.cli.utils.init_blog import init_blog_cmd
from app.cli.utils.init_all import init_all_cmd
from app.cli.utils.drop_table import drop_table_cmd


def register_cli_commands(app):
    app.cli.add_command(init_users_cmd)
    app.cli.add_command(init_academic_data_cmd)
    app.cli.add_command(init_pricing_cmd)
    app.cli.add_command(init_services_cmd)
    app.cli.add_command(init_content_cmd)
    app.cli.add_command(init_blog_cmd)
    app.cli.add_command(init_all_cmd)
    app.cli.add_command(drop_table_cmd)
