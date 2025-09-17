"""
Flask-Assets configuration for multi-blueprint application with subdomains.
Loads bundle configurations from YAML files and creates context-aware bundles.
"""

import os
import yaml
from typing import Dict, List, Any
from flask import Flask, current_app
from flask_assets import Environment, Bundle


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    :param file_path: Path to YAML file
    :returns: Dictionary containing YAML data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        current_app.logger.warning(f"Asset config file not found: {file_path}")
        return {}
    except yaml.YAMLError as e:
        current_app.logger.error(f"Error parsing YAML file {file_path}: {e}")
        return {}


def create_bundle_from_config(bundle_name: str, bundle_config: Dict[str, Any]) -> Bundle:
    """
    Create a Flask-Assets Bundle from YAML configuration.
    
    :param bundle_name: Name of the bundle
    :param bundle_config: Bundle configuration dictionary
    :returns: Configured Bundle object
    """
    contents = bundle_config.get('contents', [])
    filters = bundle_config.get('filters', '')
    output = bundle_config.get('output', f'dist/{bundle_name}.min.js')
    
    # Handle both string and list filters
    if isinstance(filters, list):
        filters = ','.join(filters)
    
    # Create bundle with contents and configuration
    bundle = Bundle(
        *contents,
        filters=filters,
        output=output
    )
    
    return bundle


def load_blueprint_assets(blueprint_name: str, data_dir: str) -> Dict[str, Bundle]:
    """
    Load asset bundles for a specific blueprint from its YAML file.
    
    :param blueprint_name: Name of the blueprint
    :param data_dir: Directory containing YAML configuration files
    :returns: Dictionary of bundle name to Bundle object
    """
    yaml_file = os.path.join(data_dir, f'{blueprint_name}.yaml')
    config = load_yaml_config(yaml_file)
    
    bundles = {}
    bundle_configs = config.get('bundles', {})
    
    for bundle_name, bundle_config in bundle_configs.items():
        try:
            bundle = create_bundle_from_config(bundle_name, bundle_config)
            bundles[bundle_name] = bundle
            current_app.logger.info(f"Created bundle '{bundle_name}' for blueprint '{blueprint_name}'")
        except Exception as e:
            current_app.logger.error(f"Error creating bundle '{bundle_name}' for blueprint '{blueprint_name}': {e}")
    
    return bundles


def compile_global_assets(assets: Environment, data_dir: str) -> Environment:
    """
    Compile global assets that are shared across all blueprints.
    
    :param assets: Flask-Assets Environment
    :param data_dir: Directory containing YAML configuration files
    :returns: Updated Environment
    """
    global_bundles = load_blueprint_assets('global', data_dir)
    
    for bundle_name, bundle in global_bundles.items():
        assets.register(bundle_name, bundle)
        
        current_app.logger.info(f"Registered global bundle: {bundle_name}")
    
    # Build bundles in development environment
    if current_app.config.get('ENVIRONMENT') == 'development' or current_app.debug:
        for bundle_name, bundle in global_bundles.items():
            try:
                bundle.build()
                current_app.logger.info(f"Built global bundle: {bundle_name}")
            except Exception as e:
                current_app.logger.error(f"Error building global bundle '{bundle_name}': {e}")
    
    return assets


def compile_blueprint_assets(assets: Environment, blueprint_name: str, data_dir: str) -> Environment:
    """
    Compile assets for a specific blueprint.
    
    :param assets: Flask-Assets Environment
    :param blueprint_name: Name of the blueprint
    :param data_dir: Directory containing YAML configuration files
    :returns: Updated Environment
    """
    blueprint_bundles = load_blueprint_assets(blueprint_name, data_dir)
    
    for bundle_name, bundle in blueprint_bundles.items():
        # Create a unique bundle name to avoid conflicts
        unique_bundle_name = f"{blueprint_name}_{bundle_name}"
        assets.register(unique_bundle_name, bundle)
        
        current_app.logger.info(f"Registered {blueprint_name} bundle: {unique_bundle_name}")
    
    # Build bundles in development environment
    if current_app.config.get('ENVIRONMENT') == 'development' or current_app.debug:
        for bundle_name, bundle in blueprint_bundles.items():
            try:
                bundle.build()
                current_app.logger.info(f"Built {blueprint_name} bundle: {bundle_name}")
            except Exception as e:
                current_app.logger.error(f"Error building {blueprint_name} bundle '{bundle_name}': {e}")
    
    return assets


def compile_all_assets(assets: Environment, project_root: str = None) -> Environment:
    """
    Compile all assets for the Flask application including global and blueprint-specific assets.
    
    :param assets: Flask-Assets Environment
    :param project_root: Root directory of the project (defaults to parent of current app instance path)
    :returns: Updated Environment with all bundles registered
    """
    if project_root is None:
        # Default to parent directory of Flask app instance path
        project_root = os.path.dirname(current_app.instance_path)
    
    data_dir = os.path.join(project_root, 'data', 'assets')
    
    if not os.path.exists(data_dir):
        current_app.logger.error(f"Data directory not found: {data_dir}")
        return assets
    
    current_app.logger.info(f"Loading asset configurations from: {data_dir}")
    
    # List of blueprints to compile assets for
    blueprints = ['admin', 'main', 'client', 'auth']
    
    try:
        # Compile global assets first
        current_app.logger.info("Compiling global assets...")
        assets = compile_global_assets(assets, data_dir)
        
        # Compile blueprint-specific assets
        for blueprint_name in blueprints:
            current_app.logger.info(f"Compiling assets for blueprint: {blueprint_name}")
            assets = compile_blueprint_assets(assets, blueprint_name, data_dir)
        
        current_app.logger.info("All assets compiled successfully!")
        
    except Exception as e:
        current_app.logger.error(f"Error during asset compilation: {e}")
        raise
    
    return assets


def get_bundle_url(bundle_name: str, blueprint_name: str = None) -> str:
    """
    Get the URL for a specific bundle, considering blueprint context.
    
    :param bundle_name: Name of the bundle
    :param blueprint_name: Name of the blueprint (optional)
    :returns: URL path to the bundle
    """
    if blueprint_name:
        unique_bundle_name = f"{blueprint_name}_{bundle_name}"
    else:
        unique_bundle_name = bundle_name
    
    try:
        # Get the bundle from the assets environment
        bundle = current_app.assets[unique_bundle_name]
        return bundle.urls()[0] if bundle.urls() else ''
    except KeyError:
        current_app.logger.warning(f"Bundle not found: {unique_bundle_name}")
        return ''


def init_assets(app: Flask, project_root: str = None) -> Environment:
    """
    Initialize Flask-Assets for the application.
    
    :param app: Flask application instance
    :param project_root: Root directory of the project
    :returns: Configured Environment
    """
    assets = Environment(app)
    
    # Set up asset configuration
    app.config.setdefault('ASSETS_DEBUG', app.debug)
    app.config.setdefault('ASSETS_AUTO_BUILD', True)
    
    with app.app_context():
        # Compile all assets
        assets = compile_all_assets(assets, project_root)
        
        # Make the get_bundle_url function available in templates
        app.jinja_env.globals['get_bundle_url'] = get_bundle_url
    
    return assets


def register_assets_cli(app: Flask, assets: Environment) -> None:
    """Attach flask-assets CLI commands to `flask`."""
    from flask_assets import ManageAssets
    app.cli.add_command(ManageAssets(assets), "assets")