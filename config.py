class Config:
    DEBUG = True 
    
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://smilecook:smilecook@localhost/smilecook'
    SQLALCHEMY_TRACK_MODIFICATIONS = False