from application import app
from flask import render_template, flash, redirect, url_for, request
from application.forms import LoginForm, RegisterForm
from . import db
from .models import User
from .forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from application.models import Post, Comment
from application.forms import PostForm, CommentForm
from flask_login import login_required, current_user, LoginManager


@app.route("/sign_up", methods=['GET', 'POST'])
def sign_up():
    form = RegisterForm()

    # Проверяем, существует ли пользователь с таким email
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует!', 'danger')
            return redirect(url_for('sign_up'))
        
        existing_user_by_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_by_username:
            flash('Пользователь с таким именем уже существует!', 'danger')
            return redirect(url_for('sign_up'))
    
        username = form.username.data
        email = form.email.data
        password = form.password.data
        reply_password = form.reply_password.data

        # Проверка на совпадение паролей
        if password != reply_password:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('sign_up'))

        # Логика сохранения данных пользователя в базе данных
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')

        # После успешной регистрации редиректим пользователя
        flash('Вы успешно зарегистрированы!', 'success')
        return redirect(url_for('private_content'))

    return render_template("sign_up.html", title="Регистрация", form=form)


@app.route("/sign_in", methods=['GET', 'POST'])
def sign_in():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            flash('Login successful!', 'success')
            return redirect(url_for('private_content'))
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    return render_template('sign_in.html', form=form)


@app.route("/") # avaliable_contant
def main_page():
    return render_template("main_page.html")


@app.route("/private_content")
@login_required
def private_content():
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Пост опубликован!', 'success')
        return redirect(url_for('private_content'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()  # Получаем все посты (новые сверху)
    return render_template('private_content.html', form=form, posts=posts)


@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    form = CommentForm()
    post = Post.query.get_or_404(post_id)  # Проверяем, существует ли пост
    if form.validate_on_submit():
        new_comment = Comment(content=form.content.data, user_id=current_user.id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Комментарий добавлен!', 'success')
    return redirect(url_for('private_content'))


@app.route("/admin")
def admin():
    return "<p>admin_panel</p>"