import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'slojneyshaya>domashka,blin'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # Для SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False