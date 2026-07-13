"""Регистрация, вход и управление пользовательской сессией."""

from functools import wraps
from typing import Callable

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .database import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user() -> None:
    """Загрузить текущего пользователя из сессии."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view: Callable) -> Callable:
    """Ограничить маршрут только авторизованными пользователями."""

    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Сначала войдите в аккаунт.", "error")
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Создать новый аккаунт и выполнить вход."""
    if g.user is not None:
        return redirect(url_for("tasks.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = validate_credentials(username, password, confirm)
        if error is None:
            db = get_db()
            exists = db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if exists:
                error = "Пользователь с таким именем уже существует."
        if error is None:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            user_id = cursor.lastrowid
            # Первый аккаунт получает задачи из прежней однопользовательской версии.
            db.execute(
                "UPDATE tasks SET user_id = ? WHERE user_id IS NULL", (user_id,)
            )
            db.commit()
            session.clear()
            session["user_id"] = user_id
            flash("Аккаунт создан. Добро пожаловать!", "success")
            return redirect(url_for("tasks.index"))
        flash(error, "error")
    return render_template("register.html")


def validate_credentials(
    username: str, password: str, confirm: str
) -> str | None:
    """Проверить данные формы регистрации."""
    if not 3 <= len(username) <= 40:
        return "Имя пользователя должно содержать от 3 до 40 символов."
    if not username.replace("_", "").isalnum():
        return "В имени допустимы буквы, цифры и знак подчёркивания."
    if len(password) < 8:
        return "Пароль должен содержать не менее 8 символов."
    if password != confirm:
        return "Пароли не совпадают."
    return None


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Выполнить вход по имени и паролю."""
    if g.user is not None:
        return redirect(url_for("tasks.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Неверное имя пользователя или пароль.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("tasks.index"))
    return render_template("login.html")


@bp.post("/logout")
def logout():
    """Завершить пользовательскую сессию."""
    session.clear()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("auth.login"))
