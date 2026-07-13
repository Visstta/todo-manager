"""Фабрика приложения «Менеджер списка дел»."""

import os
from pathlib import Path

from flask import Flask

from .database import close_db, init_db
from .auth import bp as auth_bp
from .routes import bp


def create_app(test_config: dict | None = None) -> Flask:
    """Создать и настроить экземпляр Flask-приложения."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-key-change-me"),
        DATABASE=Path(app.instance_path) / "todo.sqlite3",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bp)

    with app.app_context():
        init_db()
    return app
