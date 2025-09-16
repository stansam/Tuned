from flask import Flask
from app.config import Config
import logging
import os
# from flask_assets import Environment

def create_app():
    app = Flask(__name__, subdomain_matching=True, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.config.from_object(Config)
    from app.extensions import (
        db, migrate, csrf, mail, limiter, login_manager, cors, socketio
    )
    
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    #limiter.init_app(app)
    socketio.init_app(app)
    cors.init_app(app, supports_credentials=True, origins=[
        "http://tunedessays.com:5000",
        "http://client.tunedessays.com:5000",
        "http://api.tunedessays.com:5000",
        "http://admin.tunedessays.com:5000"
    ])
    from app.sockets import init_socketio_events
    init_socketio_events(socketio)

    from app.sitemap_robots import bp as sitemap_robots_bp
    app.register_blueprint(sitemap_robots_bp)

    # assets = Environment()
    # assets.init_app(app)

    # from app.assets import setup_global_assets
    # setup_global_assets(app)

    # with app.app_context():
    from app.main import main_bp, setup_main_assets
    from app.client import client_bp, setup_client_assets
    from app.admin import admin_bp, setup_admin_assets
    from app.auth import auth_bp, setup_auth_assets
    from app.api import api_bp
    from app.main.routes.filters import remove_headings_filter

    app.jinja_env.filters['remove_headings'] = remove_headings_filter

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, subdomain="auth")
    app.register_blueprint(api_bp, subdomain="api")
    app.register_blueprint(client_bp, subdomain="client")
    app.register_blueprint(admin_bp, subdomain="admin")

    from app.utils.assets import init_assets
    project_root = os.path.dirname(os.path.dirname(__file__))
    init_assets(app, project_root)



    content_uploads_dir = os.path.join(app.static_folder, 'uploads')
    os.makedirs(content_uploads_dir, exist_ok=True)
    os.makedirs(os.path.join(content_uploads_dir, 'blog'), exist_ok=True)
    os.makedirs(os.path.join(content_uploads_dir, 'samples'), exist_ok=True)

    # print(app.url_map)
    
    @app.shell_context_processor
    def make_shell_context():
        """Shell access to models and DB."""
        from app.models import (
            User, Service, ServiceCategory, 
            AcademicLevel, Deadline,
            Sample, FAQ, Testimonial,
            BlogCategory, BlogPost, BlogComment,
            Order, OrderComment, OrderFile,
            PricingCategory, PriceRate, 
            Payment, Invoice, Transaction, Refund, Discount,
            OrderDelivery, OrderDeliveryFile,
            Referral,
            Notification, Chat, ChatMessage, NewsletterSubscriber
        )
        from app.extensions import db
        from datetime import datetime
        
        return {
            'db': db,
            
            'U': User,                    
            'O': Order,                   
            'S': Service,                 
            'B': BlogPost,                
            'P': Payment,                 
            'N': Notification,            
            'C': Chat,                    
            
            'User': User,
            'Order': Order,
            'Service': Service,
            'BlogPost': BlogPost,
            'Payment': Payment,
            'Sample': Sample,
            'FAQ': FAQ,
            'Testimonial': Testimonial,
            'ServiceCategory': ServiceCategory,
            'AcademicLevel': AcademicLevel,
            'Deadline': Deadline,
            'BlogCategory': BlogCategory,
            'BlogComment': BlogComment,
            'OrderComment': OrderComment,
            'OrderFile': OrderFile,
            'PricingCategory': PricingCategory,
            'PriceRate': PriceRate,
            'Invoice': Invoice,
            'Transaction': Transaction,
            'Refund': Refund,
            'Discount': Discount,
            'OrderDelivery': OrderDelivery,
            'OrderDeliveryFile': OrderDeliveryFile,
            'Referral': Referral,
            'Notification': Notification,
            'Chat': Chat,
            'ChatMessage': ChatMessage,
            'NewsletterSubscriber': NewsletterSubscriber,
            
            # Utilities
            'dt': datetime,
            'now': datetime.now(),
        }

    with app.app_context():
        # logging.basicConfig(
        #     filename='logs/app.log',
        #     level=logging.INFO,
        #     format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        # )

        from logging.handlers import RotatingFileHandler

        log_dir = os.path.join(app.root_path, '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        if app.config.get('DEBUG', False):
            app.logger.setLevel(logging.DEBUG)
        else:
            app.logger.setLevel(logging.INFO)
    
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=1_000_000,  # ~1MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        if app.config.get('DEBUG', False):
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)

        if app.config.get('DEBUG', False):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
            ))
            console_handler.setLevel(logging.DEBUG)
            
            if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
                app.logger.addHandler(console_handler)

        if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
            app.logger.addHandler(file_handler)

        from app.cli import register_cli_commands
        register_cli_commands(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @app.context_processor
    def tags_context_processor():
        from app.models import ServiceCategory
        return {
            'service_categories': ServiceCategory.query.all()
        }
    
    # @app.context_processor
    # def inject_assets():
    #     return dict(assets=assets)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # assets, bundles = setup_assets(app, blueprint_name=None)
    
    return app