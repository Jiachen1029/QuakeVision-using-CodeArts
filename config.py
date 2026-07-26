import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    # PostgreSQL configuration (Uncomment and modify to use PostgreSQL)
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost/earthquakedb'
    
    # SQLite configuration (Default for development/testing)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
