from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


# Модель для постов
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # Заголовок поста
    content = db.Column(db.Text, nullable=False)  # Текст поста
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # Время публикации
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Автор поста

    user = db.relationship('User', backref=db.backref('posts', lazy=True))  # Отношение к пользователю


# Модель для комментариев
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # Текст комментария
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # Время публикации
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Автор комментария
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)  # Пост, к которому относится комментарий

    user = db.relationship('User', backref=db.backref('comments', lazy=True))  # Отношение к пользователю
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))  # Отношение к посту
