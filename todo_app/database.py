"""Подключение к SQLite и создание структуры базы данных."""

import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """Вернуть соединение с БД для текущего запроса."""
    if "db" not in g:
        database = Path(current_app.config["DATABASE"])
        g.db = sqlite3.connect(database)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error: BaseException | None = None) -> None:
    """Закрыть соединение после обработки запроса."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    """Создать таблицы и безопасно обновить старую схему."""
    connection = get_db()
    schema_path = Path(__file__).with_name("schema.sql")
    connection.executescript(schema_path.read_text(encoding="utf-8"))
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(tasks)")
    }
    if "user_id" not in columns:
        connection.execute(
            "ALTER TABLE tasks ADD COLUMN user_id INTEGER REFERENCES users(id)"
        )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)"
    )
    connection.commit()
