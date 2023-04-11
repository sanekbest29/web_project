from flask import Flask, render_template, request, redirect, flash
from flask_login import *
import json
from data import db_session
from data.users import User
from data.news import News
from pathlib import Path
import os
from forms.user import RegisterForm, LoginForm
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/website.db")

@app.route("/", methods=['GET'])
@app.route("/main", methods=['GET'])
@app.route("/index", methods=['GET'])
def index():
    with open('posts.json') as json_file:
        data = json.load(json_file)

    return render_template("index.html", posts=data)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    if current_user.is_authenticated:
        return redirect("/")
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            return redirect("/")
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route("/profile", methods=['GET', "POST"])
def profile():
    if request.method == 'POST':
        file = request.files["avatar"]
        current_time = datetime.datetime.now()
        path = Path("static", "avatars")
        folder = str(current_time.date())
        filename = str(current_user.id) \
                   + str(current_time.time()).replace(":", "-").replace(".", "-") \
                   + ".png"
        # Если файл не выбран, то браузер может
        # отправить пустой файл без имени.
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)

        # сохраняем файл
        path = Path("static", "avatars", folder)
        if not os.path.exists(path):
            os.makedirs(path)
        file.save(os.path.join(path, filename))

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.avatar_im_path = os.path.join(folder, filename)
        db_sess.commit()
        return redirect(request.url)
    if current_user.is_authenticated:
        last_page = request.args.get("last_page")
        if current_user.avatar_im_path:
            avatar_path = Path("static", "avatars", current_user.avatar_im_path)
        else:
            avatar_path = 'static\avatars\\standart.png'
        return render_template("profile.html", avatar=avatar_path,
                               last_page=last_page, title=current_user.email)
    else:
        return redirect("/login")

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')