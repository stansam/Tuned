import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class with common settings"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development').lower()
    
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_TIME_LIMIT = None
    
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'tunedessays_dev')
    
    # SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    PIC_UPLOAD_FOLDER = 'profile_pics'
    DELIVERY_UPLOAD_FOLDER = 'uploads/delivery/'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_SIZE = (800, 800)
    
    ALLOWED_PIC_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_PIC_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'ico'}
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    
    # Mail configuration
    MAIL_SERVER = os.environ.get("EMAIL_HOST")
    MAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() in ['true', '1']
    MAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() in ['true', '1']
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    
    # Cache configuration
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "simple")
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Rate limiting
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "False").lower() in ['true', '1']
    
    # Assets configuration
    ASSETS_AUTO_BUILD = os.environ.get("ASSETS_AUTO_BUILD", "True").lower() in ['true', '1']
    ASSETS_DEBUG = os.environ.get("ASSETS_DEBUG", "False").lower() in ['true', '1']

    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        pass


class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    ENVIRONMENT = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    SERVER_NAME = os.environ.get("DEV_SERVER_NAME", "tunedessays.com:5000")
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', '.tunedessays.com') 
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    
    WTF_CSRF_TRUSTED_ORIGINS = [
        "http://tunedessays.com:5000",
        "http://auth.tunedessays.com:5000",
        "http://admin.tunedessays.com:5000",
        "http://api.tunedessays.com:5000",
        "http://app.tunedessays.com:5000",
    ]
    
    CACHE_TYPE = "NullCache"
    
    ASSETS_DEBUG = True
    ASSETS_AUTO_BUILD = True
    
    SSL_REDIRECT = False


class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    ENVIRONMENT = 'production'

    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'tunedessays_dev')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SERVER_NAME = os.environ.get("SERVER_NAME", "tunedessays.com")
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', '.tunedessays.com')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    WTF_CSRF_TRUSTED_ORIGINS = [
        "https://tunedessays.com",
        "https://app.tunedessays.com",
        "https://api.tunedessays.com",
        "https://auth.tunedessays.com",
        "https://admin.tunedessays.com",
    ]
    
    CACHE_TYPE = "RedisCache"
    
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = False
    
    SSL_REDIRECT = os.environ.get("SSL_REDIRECT", "True").lower() in ['true', '1']
    
    @staticmethod
    def init_app(app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class TestingConfig(Config):
    """Testing environment configuration"""
    
    TESTING = True
    DEBUG = True
    ENVIRONMENT = 'testing'
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    WTF_CSRF_ENABLED = False
    
    CACHE_TYPE = "NullCache"
    
    RATELIMIT_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration class based on environment variable"""
    env = os.environ.get('ENVIRONMENT', 'development').lower()
    return config.get(env, config['default'])