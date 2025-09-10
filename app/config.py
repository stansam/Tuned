import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1']

    SERVER_NAME = os.environ.get("SERVER_NAME", "tunedessays.com:5000")
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOWED_PIC_EXT ={'png', 'jpg', 'jpeg', 'gif', 'webp'}

    MAIL_SERVER =os.environ.get("EMAIL_HOST")
    MAIL_PORT = os.environ.get("EMAIL_PORT")
    MAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() in ['true', '1']
    MAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() in ['true', '1']
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", False).lower() in ['true', '1']
    WTF_CSRF_ENABLED = True

    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", False).lower() in ['true', '1']

    UPLOAD_FOLDER = 'uploads'
    PIC_UPLOAD_FOLDER = 'profile_pics'
    DELIVERY_UPLOAD_FOLDER = 'uploads/delivery/'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    MAX_IMAGE_SIZE = (800, 800)

    ALLOWED_PIC_EXTENSIONS ={'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'}
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

    CACHE_TYPE = os.environ.get("CACHE_TYPE", "null")
    CACHE_DEFAULT_TIMEOUT = 300

    SSL_REDIRECT = os.environ.get("SSL_REDIRECT", False).lower() in ['true', '1']

    # Cache (for production)
    # CACHE_TYPE = "redis"
    # CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL') or 'redis://localhost:6379/0'