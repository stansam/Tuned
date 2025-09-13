import click
from flask import current_app
from flask.cli import with_appcontext
from datetime import datetime, timedelta
from app.extensions import db
from app.models.blog import BlogCategory, BlogPost


@click.command('init-blog')
@click.option('--force', is_flag=True, help='Force recreation of blog data')
@with_appcontext
def init_blog_cmd(force):
    """Initialize blog categories and posts."""
    try:
        # Check if blog data already exists
        existing_categories = BlogCategory.query.first()
        existing_posts = BlogPost.query.first()
        
        if (existing_categories or existing_posts) and not force:
            current_app.logger.info("Blog data already exists. Use --force to recreate.")
            click.echo("Blog data already exists. Use --force to recreate.")
            return

        if force:
            # Remove existing blog data
            BlogPost.query.delete()
            BlogCategory.query.delete()
            db.session.commit()
            current_app.logger.info("Existing blog data removed due to --force flag")

        # Create blog categories
        categories = [
            BlogCategory(name="Academic Writing", slug="academic-writing", description="Tips and guides for academic writing"),
            BlogCategory(name="Research Methods", slug="research-methods", description="Insights into effective research methodologies"),
            BlogCategory(name="Student Life", slug="student-life", description="Advice for balancing academics and personal life")
        ]
        
        db.session.add_all(categories)
        db.session.commit()

        # Create blog posts
        posts = [
            BlogPost(
                title="How to Write an Effective Thesis Statement",
                slug="how-to-write-effective-thesis-statement",
                content="<p>A strong thesis statement is essential for any academic paper...</p><p>This article provides step-by-step guidance on crafting clear, concise, and compelling thesis statements...</p>",
                excerpt="Learn how to create powerful thesis statements that effectively communicate your paper's main argument.",
                author="Vin Vincent",
                category=categories[0],
                tags="thesis statement, academic writing, essay tips",
                is_published=True,
                published_at=datetime.now()
            ),
            BlogPost(
                title="Quantitative vs. Qualitative Research: Choosing the Right Approach",
                slug="quantitative-vs-qualitative-research",
                content="<p>Understanding the differences between quantitative and qualitative research is crucial for designing effective studies...</p><p>This article compares the methodologies, data collection techniques, and analysis methods of both approaches...</p>",
                excerpt="A comprehensive comparison of quantitative and qualitative research methodologies to help you choose the right approach for your study.",
                author="Mark Twain",
                category=categories[1],
                tags="quantitative research, qualitative research, research methods",
                is_published=True,
                published_at=datetime.now()
            ),
            BlogPost(
                title="Time Management Strategies for Academic Success",
                slug="time-management-strategies-academic-success",
                content="<p>Effective time management is the cornerstone of academic achievement. Students who master the art of balancing study schedules, assignment deadlines, and personal commitments often find themselves less stressed and more productive.</p><p>This comprehensive guide explores proven techniques such as the Pomodoro Technique, time-blocking methods, and priority matrix frameworks. We'll also discuss how to create realistic study schedules that accommodate your learning style and lifestyle demands.</p><p>From utilizing digital tools like calendar apps and task managers to developing healthy study habits, this article provides actionable strategies that can transform your academic performance and overall well-being.</p>",
                excerpt="Discover proven time management techniques and strategies to enhance your academic performance while maintaining a healthy work-life balance.",
                author="Barry Allan",
                category=categories[2],
                tags="time management, study tips, productivity, student life, academic success",
                is_published=True,
                published_at=datetime.now() - timedelta(days=7)
            ),
            BlogPost(
                title="The Art of Citation: Mastering APA, MLA, and Chicago Styles",
                slug="mastering-citation-styles-apa-mla-chicago",
                content="<p>Proper citation is more than just academic courtesy—it's a fundamental skill that demonstrates scholarly integrity and helps readers trace the sources of your arguments and evidence.</p><p>This detailed guide breaks down the three most commonly used citation styles in academic writing: APA (American Psychological Association), MLA (Modern Language Association), and Chicago Manual of Style. Each style serves different disciplines and has unique formatting requirements for in-text citations, reference lists, and bibliographies.</p><p>We'll explore practical examples, common mistakes to avoid, and tools that can streamline your citation process. Whether you're writing a psychology research paper, a literature analysis, or a historical thesis, understanding these citation styles will elevate the professionalism of your work.</p><p>Additionally, we'll discuss the importance of avoiding plagiarism and how proper citation practices protect both your academic integrity and intellectual property rights.</p>",
                excerpt="A comprehensive guide to mastering APA, MLA, and Chicago citation styles with practical examples and tips for avoiding common formatting mistakes.",
                author="Billy The Kid",
                category=categories[0],
                tags="citation styles, APA, MLA, Chicago, academic writing, referencing, plagiarism",
                is_published=True,
                published_at=datetime.now() - timedelta(days=14)
            )
        ]
        
        db.session.add_all(posts)
        db.session.commit()
        
        current_app.logger.info("--- BLOG DATA CREATED ---")
        click.echo(f"✓ Created {len(categories)} blog categories and {len(posts)} blog posts")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating blog data: {str(e)}")
        click.echo(f"✗ Error creating blog data: {str(e)}", err=True)
        raise click.Abort()