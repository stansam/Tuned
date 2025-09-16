import click
import yaml
import os
import sys
from pathlib import Path
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask.cli import with_appcontext
from flask import current_app
from app.extensions import db
from app.models import FAQ



def load_faqs_from_yaml(file_path):
    """
    Load FAQs from a YAML file with validation.
    
    Args:
        file_path (str): Path to the YAML file
        
    Returns:
        list: List of FAQ dictionaries
        
    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
        ValueError: If the YAML structure is invalid
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"FAQ file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            
        if not isinstance(data, dict) or 'faqs' not in data:
            raise ValueError("YAML file must contain a 'faqs' key with a list of FAQs")
            
        faqs = data['faqs']
        if not isinstance(faqs, list):
            raise ValueError("'faqs' must be a list")
            
        # Validate each FAQ entry
        required_fields = ['question', 'answer']
        for i, faq in enumerate(faqs):
            if not isinstance(faq, dict):
                raise ValueError(f"FAQ entry {i+1} must be a dictionary")
                
            for field in required_fields:
                if field not in faq or not faq[field]:
                    raise ValueError(f"FAQ entry {i+1} missing required field: {field}")
                    
            # Set defaults for optional fields
            faq.setdefault('category', 'General')
            faq.setdefault('order', 0)
            
            # Validate field lengths based on your model constraints
            if len(faq['question']) > 255:
                raise ValueError(f"FAQ entry {i+1}: question exceeds 255 characters")
                
        return faqs
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")


def create_faq_objects(faqs_data):
    """
    Create FAQ model objects from FAQ data.
    
    Args:
        faqs_data (list): List of FAQ dictionaries
        
    Returns:
        list: List of FAQ model objects
    """
    faq_objects = []
    
    for faq_data in faqs_data:
        faq = FAQ(
            question=faq_data['question'].strip(),
            answer=faq_data['answer'].strip(),
            category=faq_data.get('category', 'General').strip(),
            order=faq_data.get('order', 0)
        )
        faq_objects.append(faq)
        
    return faq_objects


def backup_existing_faqs():
    """
    Create a backup of existing FAQs before initialization.
    
    Returns:
        str: Backup file path or None if no FAQs exist
    """
    try:
        existing_faqs = FAQ.query.all()
        if not existing_faqs:
            return None
            
        backup_data = {
            'faqs': [
                {
                    'question': faq.question,
                    'answer': faq.answer,
                    'category': faq.category,
                    'order': faq.order
                }
                for faq in existing_faqs
            ]
        }
        
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'faqs_backup_{timestamp}.yaml'
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            yaml.dump(backup_data, f, default_flow_style=False, allow_unicode=True)
            
        current_app.logger.info(f"Backup created: {backup_file}")
        return str(backup_file)
        
    except Exception as e:
        current_app.logger.warning(f"Failed to create backup: {e}")
        return None


@click.command('init-faqs')
@click.option(
    '--file', '-f',
    default='data/FAQs.yaml',
    help='Path to the FAQs YAML file (default: data/FAQs.yaml)'
)
@click.option(
    '--replace', '-r',
    is_flag=True,
    help='Replace existing FAQs instead of skipping duplicates'
)
@click.option(
    '--backup/--no-backup',
    default=True,
    help='Create backup of existing FAQs before initialization (default: True)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be done without making changes'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@with_appcontext
def init_faqs_command(file, replace, backup, dry_run, verbose):
    """
    Initialize FAQs from a YAML file.
    
    This command loads FAQs from a YAML file and populates the database.
    By default, it will skip FAQs with duplicate questions unless --replace is used.
    """        
    try:
        # Validate file path
        yaml_file = Path(file)
        if not yaml_file.is_absolute():
            # Make relative to app root
            yaml_file = Path(current_app.root_path).parent / yaml_file
            
        click.echo(f"Loading FAQs from: {yaml_file}")
        
        # Load and validate FAQs
        try:
            faqs_data = load_faqs_from_yaml(yaml_file)
            click.echo(f"Loaded {len(faqs_data)} FAQs from YAML file")
        except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
            click.echo(f"Error loading FAQs: {e}", err=True)
            sys.exit(1)
            
        # Create FAQ objects
        faq_objects = create_faq_objects(faqs_data)
        
        if dry_run:
            click.echo("\n--- DRY RUN MODE ---")
            click.echo("The following FAQs would be processed:")
            for i, faq in enumerate(faq_objects, 1):
                click.echo(f"{i}. [{faq.category}] {faq.question[:60]}...")
            click.echo(f"\nTotal: {len(faq_objects)} FAQs")
            return
            
        # Create backup if requested and FAQs exist
        backup_file = None
        if backup:
            backup_file = backup_existing_faqs()
            
        # Process FAQs
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        try:
            for faq in faq_objects:
                existing_faq = FAQ.query.filter_by(question=faq.question).first()
                
                if existing_faq:
                    if replace:
                        # Update existing FAQ
                        existing_faq.answer = faq.answer
                        existing_faq.category = faq.category
                        existing_faq.order = faq.order
                        updated_count += 1
                        
                        if verbose:
                            click.echo(f"Updated: {faq.question[:60]}...")
                    else:
                        skipped_count += 1
                        if verbose:
                            click.echo(f"Skipped (exists): {faq.question[:60]}...")
                else:
                    # Add new FAQ
                    db.session.add(faq)
                    db.session.commit()
                    added_count += 1
                    
                    if verbose:
                        click.echo(f"Added: {faq.question[:60]}...")
                            
        except SQLAlchemyError as e:
            db.session.rollback()
            click.echo(f"Database error: {e}", err=True)
            if backup_file:
                click.echo(f"Backup available at: {backup_file}")
            sys.exit(1)
            
        # Summary
        click.echo(f"\n--- Summary ---")
        click.echo(f"Added: {added_count} FAQs")
        if replace:
            click.echo(f"Updated: {updated_count} FAQs")
        else:
            click.echo(f"Skipped: {skipped_count} FAQs (use --replace to update)")
            
        if backup_file:
            click.echo(f"Backup created: {backup_file}")
            
        click.echo("✅ FAQ initialization completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Unexpected error during FAQ initialization")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@click.command('list-faqs')
@click.option(
    '--category', '-c',
    help='Filter by category'
)
@click.option(
    '--format', 'output_format',
    type=click.Choice(['table', 'json', 'yaml']),
    default='table',
    help='Output format'
)
@with_appcontext
def list_faqs_command(category, output_format):
    """List all FAQs in the database."""
    try:
        query = FAQ.query
        if category:
            query = query.filter_by(category=category)
            
        faqs = query.order_by(FAQ.category, FAQ.order, FAQ.id).all()
        
        if not faqs:
            click.echo("No FAQs found in the database.")
            return
            
        if output_format == 'table':
            from tabulate import tabulate
            headers = ['ID', 'Category', 'Order', 'Question', 'Answer']
            rows = [
                [
                    faq.id,
                    faq.category,
                    faq.order,
                    faq.question[:50] + '...' if len(faq.question) > 50 else faq.question,
                    faq.answer[:100] + '...' if len(faq.answer) > 100 else faq.answer
                ]
                for faq in faqs
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            
        elif output_format == 'json':
            import json
            data = [
                {
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'category': faq.category,
                    'order': faq.order
                }
                for faq in faqs
            ]
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
            
        elif output_format == 'yaml':
            data = {
                'faqs': [
                    {
                        'question': faq.question,
                        'answer': faq.answer,
                        'category': faq.category,
                        'order': faq.order
                    }
                    for faq in faqs
                ]
            }
            click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True))
            
        click.echo(f"\nTotal: {len(faqs)} FAQs")
        
    except Exception as e:
        click.echo(f"Error listing FAQs: {e}", err=True)
        sys.exit(1)


@click.command('clear-faqs')
@click.option(
    '--category', '-c',
    help='Only clear FAQs from specific category'
)
@click.option(
    '--backup/--no-backup',
    default=True,
    help='Create backup before clearing (default: True)'
)
@click.confirmation_option(
    prompt='Are you sure you want to clear FAQs from the database?'
)
@with_appcontext
def clear_faqs_command(category, backup):
    """Clear FAQs from the database."""
    try:
        # Create backup if requested
        if backup:
            backup_file = backup_existing_faqs()
            if backup_file:
                click.echo(f"Backup created: {backup_file}")
                
        # Clear FAQs
        query = FAQ.query
        if category:
            query = query.filter_by(category=category)
            
        count = query.count()
        query.delete()
        db.session.commit()
        
        if category:
            click.echo(f"Cleared {count} FAQs from category '{category}'")
        else:
            click.echo(f"Cleared {count} FAQs from database")
            
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error clearing FAQs: {e}", err=True)
        sys.exit(1)

    


