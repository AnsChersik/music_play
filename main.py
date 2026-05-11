from flask import Flask, render_template, redirect, jsonify, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import requests
import os

from data import db_session
from data.users import User
from data.login_from import LoginForm
from data.register_form import RegisterForm

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)

API_KEY = os.getenv('KINOPOISK_API_KEY')
if not API_KEY:
    raise ValueError("API ключ не найден")

API_BASE = 'https://kinopoiskapiunofficial.tech/api/v2.2/films'
HEADERS = {
    'X-API-KEY': API_KEY,
    'Content-Type': 'application/json'
}


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, int(user_id))


def fetch_films(page: int) -> tuple[list[dict], bool]:
    url = f"{API_BASE}"
    params = {
        'page': page,
        'count': 9,
        'order': 'RATING',
        'type': 'ALL',
        'ratingFrom': 6.0
    }

    try:
        response = requests.get(url, headers=HEADERS,
                                params=params, timeout=10)
        if response.status_code != 200:
            return [], False
        data = response.json()
        items = data.get('items', [])[:9]
        total_pages = data.get('totalPages', 10)
        has_more = page < total_pages and len(items) == 9
        return items, has_more
    except Exception:
        return [], False


def format_card(film: dict) -> dict:
    genres_list = film.get('genres', []) or []
    genres = ', '.join([g.get('genre', '')
                       for g in genres_list if g.get('genre')][:2])
    rating = film.get('ratingKinopoisk') or film.get('ratingImdb') or 'N/A'
    return {
        'poster': film.get('posterUrlPreview') or film.get('posterUrl'),
        'title': film.get('nameRu') or film.get('nameEn') or 'Без названия',
        'genres': genres if genres else 'Жанр не указан',
        'rating': rating,
        'year': film.get('year', '')
    }


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Пароли не совпадают",
            )
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Такой пользователь уже есть",
            )

        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template(
            "login.html", message="Неверный логин или пароль", form=form
        )
    return render_template("login.html", title="Авторизация", form=form)


@app.route("/")
@login_required
def index():
    films_raw, has_more = fetch_films(1)
    cards = [format_card(f) for f in films_raw]
    return render_template(
        "main.html",
        title="Главная",
        cards=cards,
        has_more=has_more
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/api/films")
@login_required
def api_films():
    page = request.args.get('page', 2, type=int)
    films_raw, has_more = fetch_films(page)
    cards = [format_card(f) for f in films_raw]
    return jsonify({
        'cards': cards,
        'has_more': has_more,
        'page': page
    })


def main():
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'db', 'users.sqlite')
    db_session.global_init(db_path)
    app.run()


if __name__ == "__main__":
    main()
