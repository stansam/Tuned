import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1']
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')

    SERVER_NAME = os.environ.get("SERVER_NAME", "tunedessays.com")
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", False).lower() in ['true', '1']
    REMEMBER_COOKIE_SECURE = os.environ.get("REMEMBER_COOKIE_SECURE", False).lower() in ['true', '1']
    SESSION_COOKIE_SAMESITE = None
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TRUSTED_ORIGINS = [
        "https://tunedessays.com",
        "https://app.tunedessays.com",
        "https://api.tunedessays.com",
        "https://auth.tunedessays.com",
        "https://admin.tunedessays.com",
    ]
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
    
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
  
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", False).lower() in ['true', '1']

    UPLOAD_FOLDER = 'uploads'
    PIC_UPLOAD_FOLDER = 'profile_pics'
    DELIVERY_UPLOAD_FOLDER = 'uploads/delivery/'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    MAX_IMAGE_SIZE = (800, 800)

    ALLOWED_PIC_EXTENSIONS ={'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'}
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

    CACHE_TYPE = os.environ.get("CACHE_TYPE", "null")
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300

    SSL_REDIRECT = os.environ.get("SSL_REDIRECT", False).lower() in ['true', '1']

    ASSETS_AUTO_BUILD = os.environ.get("ASSETS_AUTO_BUILD", True).lower() in ['true', '1']
    ASSETS_DEBUG = os.environ.get("ASSETS_DEBUG", True).lower() in ['true', '1']
