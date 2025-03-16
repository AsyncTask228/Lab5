from flask import Flask
from config import Config
from .models import db
from flask_login import LoginManager


app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)

with app.app_context():
    db.create_all()  # Создание всех таблиц в базе данных

from application import routes