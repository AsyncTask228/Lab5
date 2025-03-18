import os
from application import app, db
from flask import render_template, flash, redirect, url_for, request
from application.forms import LoginForm, RegisterForm, PostForm, CommentForm
from application.models import User, Post, Comment, Report
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/private_content", methods=['GET', 'POST'])
@login_required
def private_content():
    post_form = PostForm()
    comment_form = CommentForm()

    if post_form.validate_on_submit() and request.form.get('form_name') == 'post_form':
        post = Post(
            title=post_form.title.data,
            content=post_form.content.data,
            user_id=current_user.id
        )
        if 'media' in request.files:
            file = request.files['media']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post.media_path = filename
        db.session.add(post)
        db.session.commit()
        flash('Пост успешно опубликован!', 'success')
        return redirect(url_for('private_content'))

    if comment_form.validate_on_submit() and request.form.get('form_name') == 'comment_form':
        post_id = request.form.get('post_id')
        comment = Comment(
            content=comment_form.content.data,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен!', 'success')
        return redirect(url_for('private_content'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('private_content.html', 
                          post_form=post_form, 
                          comment_form=comment_form, 
                          posts=posts)

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
        # Проверяем, первый ли это пользователь
        is_admin = User.query.count() == 0  # True, если пользователей ещё нет
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            is_admin=is_admin  # Первый пользователь становится админом
        )
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
            login_user(user)  # Авторизуем пользователя
            flash('Login successful!', 'success')
            return redirect(url_for('private_content'))  # Перенаправляем на private_content
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    return render_template('sign_in.html', form=form)

@app.route("/") # avaliable_contant
def main_page():
    return render_template("main_page.html")

def admin_required(f):
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('Доступ только для администраторов!', 'danger')
            return redirect(url_for('private_content'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Сохраняем имя функции для Flask
    return wrapper

@app.route("/admin")
@admin_required
def admin():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    return render_template('admin.html', posts=posts, reports=reports)

@app.route("/delete_post/<int:post_id>", methods=['POST'])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Удаляем связанные комментарии и жалобы
    Comment.query.filter_by(post_id=post_id).delete()
    Report.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    flash('Пост удалён!', 'success')
    return redirect(url_for('admin'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта!', 'success')
    return redirect(url_for('sign_in'))

@app.route("/report", methods=['POST'])
@login_required
def report():
    post_id = request.form.get('post_id')
    comment_id = request.form.get('comment_id')
    reason = request.form.get('reason', 'Нарушение правил')

    if not post_id and not comment_id:
        flash('Не указан объект жалобы!', 'danger')
        return redirect(url_for('private_content'))

    report = Report(
        user_id=current_user.id,
        post_id=post_id if post_id else None,
        comment_id=comment_id if comment_id else None,
        reason=reason
    )
    db.session.add(report)
    db.session.commit()
    flash('Жалоба отправлена!', 'success')
    return redirect(url_for('private_content'))