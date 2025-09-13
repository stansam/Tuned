import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models.content import Sample, FAQ, Testimonial
from app.models.service import Service
from app.models.user import User


@click.command('init-content')
@click.option('--force', is_flag=True, help='Force recreation of content data')
@with_appcontext
def init_content_cmd(force):
    """Initialize samples, testimonials, and FAQs."""
    try:
        existing_samples = Sample.query.first()
        existing_testimonials = Testimonial.query.first()
        existing_faqs = FAQ.query.first()
        
        if (existing_samples or existing_testimonials or existing_faqs) and not force:
            current_app.logger.info("Content data already exists. Use --force to recreate.")
            click.echo("Content data already exists. Use --force to recreate.")
            return

        if force:
            Sample.query.delete()
            Testimonial.query.delete()
            FAQ.query.delete()
            db.session.commit()
            current_app.logger.info("Existing content data removed due to --force flag")

        services = Service.query.all()
        if not services:
            current_app.logger.error("No services found. Run 'flask init-services' first.")
            click.echo("✗ No services found. Run 'flask init-services' first.", err=True)
            raise click.Abort()

        users = User.query.all()
        if not users:
            current_app.logger.error("No users found. Run 'flask init-users' first.")
            click.echo("✗ No users found. Run 'flask init-users' first.", err=True)
            raise click.Abort()

        service_lookup = {s.name: s for s in services}
        
        samples = [
            Sample(
                title="Edited Journal Article: Linguistic Precision in Sociolinguistics",
                content="<p>This copyedited article refines academic tone, grammar, and consistency while preserving authorial voice...</p><p>Changes adhere to APA style and enhance clarity in theoretical discussions...</p>",
                excerpt="Professional copyediting of a sociolinguistics article focusing on clarity and APA style.",
                service=service_lookup.get("Copyediting"),
                word_count=2200,
                tags="Copy-Editing, article",
                featured=True,
                slug="edited-journal-article-linguistic-precision-in-sociolinguistics"
            ),
            Sample(
                title="The Role of Civil Disobedience in Democratic Societies",
                content="<p>This essay explores the philosophical and historical implications of civil disobedience with references to Thoreau, Gandhi, and King...</p><p>The argument develops a nuanced stance on lawful protest and moral responsibility...</p>",
                excerpt="An argumentative essay on the legitimacy and legacy of civil disobedience.",
                service=service_lookup.get("Essays"),
                tags="Essay, paper-writing",
                word_count=1800,
                featured=True,
                slug="role-of-civil-disobedience-in-democratic-societies"
            ),
            Sample(
                title="Quantitative Analysis of Student Performance using SPSS",
                content="<p>This SPSS-based research applies descriptive and inferential statistics to educational data...</p><p>Includes regression analysis, ANOVA, and reliability testing...</p>",
                excerpt="A statistical report analyzing academic performance data using SPSS.",
                service=service_lookup.get("SPSS"),
                word_count=2600,
                tags="statistics, research",
                featured=True,
                slug="quantitative-analysis-of-student-performance-using-spss"
            )
        ]
        
        valid_samples = [s for s in samples if s.service is not None]
        db.session.add_all(valid_samples)

        testimonials = [
            Testimonial(
                user_id=users[min(2, len(users)-1)].id,
                service=services[0],
                content="The essay I received was exceptionally well-written and delivered ahead of the deadline. The writer addressed all my requirements and provided valuable insights I hadn't considered.",
                rating=5,
                is_approved=True
            ),
            Testimonial(
                user_id=users[min(1, len(users)-1)].id,
                service=services[min(1, len(services)-1)],
                content="I was impressed by the depth of research and quality of references in my paper. The structure was logical, and the arguments were well-developed. Highly recommend!",
                rating=5,
                is_approved=True
            ),
            Testimonial(
                user_id=users[0].id,
                service=services[min(2, len(services)-1)],
                content="Working with this service on my dissertation was a game-changer. The writer's expertise in my subject area was evident, and they were responsive to all my feedback during the process.",
                rating=4,
                is_approved=True
            )
        ]
        
        db.session.add_all(testimonials)

        faqs = [
            FAQ(
                question="How does the ordering process work?",
                answer="Our ordering process is simple: select the type of paper you need, specify your academic level, choose a deadline, provide your instructions, and make a payment. Once we receive your order, we'll assign it to a writer with expertise in your subject area.",
                category="Ordering",
                order=1
            ),
            FAQ(
                question="Can I communicate with my writer?",
                answer="Yes, you can communicate with your writer through our messaging system. You can provide additional instructions, ask questions, or request updates on your order's progress.",
                category="Communication",
                order=1
            ),
            FAQ(
                question="Are revisions included in the price?",
                answer="Yes, we offer free revisions within 14 days after delivery. If you need any changes to your paper, simply submit a revision request with clear instructions on what needs to be modified.",
                category="Revisions",
                order=1
            )
        ]
        
        db.session.add_all(faqs)
        db.session.commit()
        
        current_app.logger.info("--- CONTENT DATA CREATED ---")
        click.echo(f"✓ Created {len(valid_samples)} samples, {len(testimonials)} testimonials, and {len(faqs)} FAQs")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating content data: {str(e)}")
        click.echo(f"✗ Error creating content data: {str(e)}", err=True)
        raise click.Abort()