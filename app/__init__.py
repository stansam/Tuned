from flask import Flask
from app.config import Config
import logging
import os

def create_app():
    app = Flask(__name__, subdomain_matching=True, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    # app.config["SERVER_NAME"] = "tunedessays.com:5000"
    # app.config["SESSION_COOKIE_DOMAIN"] = ".tunedessays.com"
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
        "http://main.tunedessays.com:5000",
        "http://client.tunedessays.com:5000",
        "http://api.tunedessays.com:5000",
        "http://admin.tunedessays.com:5000"
    ])
    from app.sockets import init_socketio_events
    init_socketio_events(socketio)

    

    from app.main import main_bp
    from app.client import client_bp
    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.api import api_bp
    from app.main.routes.filters import remove_headings_filter

    app.jinja_env.filters['remove_headings'] = remove_headings_filter

    # app.register_blueprint(main_bp)
    # app.register_blueprint(client_bp)
    # app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp, url_prefix="/main")
    app.register_blueprint(auth_bp, subdomain="auth")
    app.register_blueprint(api_bp, subdomain="api")
    app.register_blueprint(client_bp, subdomain="client")
    app.register_blueprint(admin_bp, subdomain="admin")

    # print(app.url_map)
    
    
    with app.app_context():
        # from app.models.user import User
        # from app.models.service import Service, ServiceCategory, AcademicLevel, Deadline
        # from app.models.content import Sample, FAQ, Testimonial
        # from app.models.blog import BlogCategory, BlogPost, BlogComment
        # from app.models.order import Order, OrderComment, OrderFile
        # from app.models.price  import PricingCategory, PriceRate
        # from app.models.payment import Payment, Invoice, Transaction, Refund, Discount
        # from app.models.order_delivery import OrderDelivery, OrderDeliveryFile
        # from app.models.referral import Referral 
        # from app.models.communication import Notification, Chat, ChatMessage, NewsletterSubscriber 

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

        db.create_all()
        logging.basicConfig(
            filename='logs/app.log',
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        # Initialize database with default data
        from app.utils.db_init import init_db
        init_db(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @app.context_processor
    def tags_context_processor():
        from app.models import ServiceCategory
        return {
            'service_categories': ServiceCategory.query.all()
        }

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    return app