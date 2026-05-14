from flask import Flask, render_template, redirect, jsonify, request, flash, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import requests
import os

from data import db_session
from data.users import User
from data.login_from import LoginForm
from data.register_form import RegisterForm
from data.favorites import Favorite
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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
    user = db_sess.get(User, int(user_id))
    db_sess.close()
    return user


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
        'kinopoiskId': film.get('kinopoiskId'),
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
            db_sess.close()
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
        db_sess.close()
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
            login_user(user)
            db_sess.close()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        db_sess.close()
        return render_template(
            "login.html", message="Неверный логин или пароль", form=form
        )
    return render_template("login.html", title="Авторизация", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "info")
    return redirect(url_for("login"))


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


@app.route("/film/<int:film_id>")
@login_required
def film_detail(film_id):
    url = f"{API_BASE}/{film_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            flash("Фильм не найден", "error")
            return redirect(url_for('index'))

        film = response.json()

        countries = ', '.join([c.get('country', '')
                              for c in film.get('countries', []) if c.get('country')])
        genres = ', '.join([g.get('genre', '')
                           for g in film.get('genres', []) if g.get('genre')])
        rating = film.get('ratingKinopoisk') or film.get('ratingImdb') or 'N/A'
        age_limit = film.get('ratingAgeLimits', '').replace(
            'age', '') if film.get('ratingAgeLimits') else 'Не указано'

        film_data = {
            'kinopoiskId': film.get('kinopoiskId'),
            'nameRu': film.get('nameRu') or film.get('nameEn') or 'Без названия',
            'nameOriginal': film.get('nameOriginal'),
            'year': film.get('year', ''),
            'posterUrl': film.get('posterUrl') or film.get('posterUrlPreview'),
            'countries': countries if countries else 'Страна не указана',
            'genres': genres if genres else 'Жанр не указан',
            'rating': rating,
            'ratingVoteCount': film.get('ratingKinopoiskVoteCount', 0),
            'filmLength': film.get('filmLength', 0),
            'slogan': film.get('slogan', ''),
            'description': film.get('description', ''),
            'shortDescription': film.get('shortDescription', ''),
            'ageLimit': age_limit,
            'webUrl': film.get('webUrl', '')
        }

        web_url = film.get('webUrl', '')
        if web_url:
            film_data['watchUrl'] = web_url.replace(
                'kinopoisk.ru', 'sspoisk.ru')
        else:
            film_data['watchUrl'] = '#'

        return render_template("film.html", title=film_data['nameRu'], film=film_data)

    except Exception as e:
        flash("Ошибка при загрузке информации о фильме", "error")
        return redirect(url_for('index'))


@app.route("/api/profile/check/<int:film_id>")
@login_required
def check_favorite(film_id):
    try:
        db_sess = db_session.create_session()
        exists = db_sess.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.kinopoisk_id == film_id
        ).first() is not None
        db_sess.close()
        return jsonify({'in_favorites': exists})
    except Exception as e:
        print(f"Error in check_favorite: {e}")
        return jsonify({'in_favorites': False}), 500


@app.route("/api/profile/toggle/<int:film_id>", methods=["POST"])
@login_required
def toggle_favorite(film_id):
    try:
        print(
            f"Toggle called for film_id={film_id}, user_id={current_user.id}")
        db_sess = db_session.create_session()
        favorite = db_sess.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.kinopoisk_id == film_id
        ).first()

        if favorite:
            db_sess.delete(favorite)
            db_sess.commit()
            message = "Фильм удалён из избранного"
            in_favorites = False
        else:
            new_fav = Favorite(user_id=current_user.id, kinopoisk_id=film_id)
            db_sess.add(new_fav)
            db_sess.commit()
            message = "Фильм добавлен в избранное"
            in_favorites = True

        db_sess.close()
        return jsonify({'success': True, 'message': message, 'in_favorites': in_favorites})
    except Exception as e:
        print(f"Error in toggle_favorite: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route("/api/profile/remove/<int:film_id>", methods=["POST"])
@login_required
def remove_favorite(film_id):
    try:
        print(
            f"Remove called for film_id={film_id}, user_id={current_user.id}")
        db_sess = db_session.create_session()
        favorite = db_sess.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.kinopoisk_id == film_id
        ).first()

        if favorite:
            db_sess.delete(favorite)
            db_sess.commit()
            db_sess.close()
            return jsonify({'success': True, 'message': 'Фильм удалён из избранного'})

        db_sess.close()
        return jsonify({'success': False, 'message': 'Фильм не найден в избранном'}), 404
    except Exception as e:
        print(f"Error in remove_favorite: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route("/profile")
@login_required
def show_favorites():
    db_sess = db_session.create_session()
    favorite_ids = [item[0] for item in db_sess.query(Favorite.kinopoisk_id)
                    .filter(Favorite.user_id == current_user.id).all()]
    db_sess.close()

    favorite_films_data = []
    for kp_id in favorite_ids:
        url = f"{API_BASE}/{kp_id}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                film = response.json()
                formatted = format_card(film)
                formatted['kinopoiskId'] = kp_id
                web_url = film.get('webUrl', '')
                if web_url:
                    formatted['watchUrl'] = web_url.replace(
                        'kinopoisk.ru', 'sspoisk.ru')
                else:
                    formatted['watchUrl'] = '#'
                favorite_films_data.append(formatted)
        except Exception:
            continue

    return render_template("profile.html", title="Моё избранное", cards=favorite_films_data)


def main():
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'db', 'users.sqlite')
    db_session.global_init(db_path)
    app.run(debug=True)


if __name__ == "__main__":
    main()
