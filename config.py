from datetime import timedelta

ACCESS_EXPIRES = timedelta(hours=1)

class Config:
    DEBUG = True 
    
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://smilecook:smilecook@localhost/smilecook'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = 'super-secret-key'
    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_ACCESS_TOKEN_EXPIRES = ACCESS_EXPIRES
    
    UPLOADED_IMAGES_DEST = 'static/images'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 10 * 60
    
    RATELIMIT_HEADERS_ENABLED = True 