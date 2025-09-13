import click
from flask.cli import with_appcontext
from app.extensions import db
from app import models

@click.command("drop-table")
@click.option("--all", "drop_all", is_flag=True, help="Drop data from all tables.")
@click.option("--table", "tables", multiple=True, help="Specify table(s) to drop, e.g. --table User --table Service")
@with_appcontext
def drop_table_cmd(drop_all, tables):
    """
    Drop (clear) data from specific tables or all tables.

    Usage:
      flask drop-table --table User
      flask drop-table --table User --table Service
      flask drop-table --all
    """
    if not drop_all and not tables:
        click.echo("❌ Please provide either --all or one/more --table options.")
        return

    if drop_all:
        confirm = click.prompt(
            "⚠️ This will DELETE ALL DATA from ALL tables. Type 'yes' to continue",
            default="no"
        )
        if confirm.lower() != "yes":
            click.echo("Aborted.")
            return

        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        click.echo("✅ All tables cleared successfully.")
        return

    # Handle specific tables
    for table_name in tables:
        model = getattr(models, table_name, None)
        if model is None:
            click.echo(f"❌ No model found with name '{table_name}'. Skipping.")
            continue

        confirm = click.prompt(
            f"⚠️ This will DELETE ALL DATA from '{table_name}'. Type 'yes' to continue",
            default="no"
        )
        if confirm.lower() != "yes":
            click.echo(f"Skipped {table_name}.")
            continue

        try:
            db.session.query(model).delete()
            db.session.commit()
            click.echo(f"✅ Cleared table '{table_name}'.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"❌ Failed to clear '{table_name}': {e}")
