import os
from flask import Flask, current_app
from flask.cli import with_appcontext
import click
from app.utils.assets import compile_all_assets

@click.group()
def assets_cli():
    """Asset management commands."""
    pass


@assets_cli.command()
@with_appcontext
def build():
    """Build all asset bundles for production."""
    click.echo("Building all asset bundles...")
    
    try:
        # Force build all assets
        compile_all_assets(current_app.assets, force_build=True)
        click.echo(click.style("✓ All assets built successfully!", fg='green'))
    except Exception as e:
        click.echo(click.style(f"✗ Error building assets: {e}", fg='red'))
        raise click.ClickException(f"Asset build failed: {e}")


@assets_cli.command()
@with_appcontext
def clean():
    """Clean built asset files."""
    click.echo("Cleaning built assets...")
    
    try:
        # Get output directory from config or use default
        output_dir = os.path.join(current_app.static_folder, 'dist')
        
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
            click.echo(f"Cleaned directory: {output_dir}")
        
        click.echo(click.style("✓ Assets cleaned successfully!", fg='green'))
    except Exception as e:
        click.echo(click.style(f"✗ Error cleaning assets: {e}", fg='red'))


@assets_cli.command()
@click.option('--blueprint', help='Build assets for specific blueprint only')
@with_appcontext
def watch():
    """Watch for changes and rebuild assets automatically."""
    click.echo("Starting asset watcher...")
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        import time
        
        class AssetHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and (event.src_path.endswith('.js') or event.src_path.endswith('.css')):
                    click.echo(f"File changed: {event.src_path}")
                    click.echo("Rebuilding assets...")
                    compile_all_assets(current_app.assets, force_build=True)
        
        observer = Observer()
        # Watch static directories for changes
        static_dirs = [
            os.path.join(current_app.root_path, 'static'),
            os.path.join(current_app.root_path, 'assets')
        ]
        
        for static_dir in static_dirs:
            if os.path.exists(static_dir):
                observer.schedule(AssetHandler(), static_dir, recursive=True)
                click.echo(f"Watching: {static_dir}")
        
        observer.start()
        click.echo(click.style("✓ Asset watcher started. Press Ctrl+C to stop.", fg='green'))
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            click.echo("\nAsset watcher stopped.")
        
        observer.join()
        
    except ImportError:
        click.echo(click.style("✗ Watchdog package not installed. Install with: pip install watchdog", fg='red'))
    except Exception as e:
        click.echo(click.style(f"✗ Error starting watcher: {e}", fg='red'))


def register_assets_cli(app: Flask) -> None:
    """Register asset management CLI commands."""
    app.cli.add_command(assets_cli, "assets")


# Production deployment helper
def ensure_production_assets(app: Flask) -> bool:
    """
    Ensure assets are built for production deployment.
    Returns True if assets are ready, False otherwise.
    """
    if app.config.get('ENVIRONMENT') != 'production':
        return True
    
    try:
        with app.app_context():
            # Check if critical bundles exist
            required_bundles = ['main_js', 'main_css', 'global_js', 'global_css']
            missing_bundles = []
            
            for bundle_name in required_bundles:
                try:
                    bundle = app.assets.get(bundle_name)
                    if not bundle or not bundle.urls():
                        missing_bundles.append(bundle_name)
                except KeyError:
                    missing_bundles.append(bundle_name)
            
            if missing_bundles:
                app.logger.error(f"Missing production bundles: {missing_bundles}")
                return False
            
            return True
    except Exception as e:
        app.logger.error(f"Error checking production assets: {e}")
        return False