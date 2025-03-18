from flask import Flask
from config import Config
from .models import db, User
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'sign_in'  # Куда перенаправлять неавторизованных пользователей

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

from application import routes