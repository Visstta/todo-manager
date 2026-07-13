"""Модель и операции с задачами."""

from dataclasses import dataclass
from datetime import date
import sqlite3

from .database import get_db


@dataclass(frozen=True)
class TaskInput:
    """Проверенные данные формы задачи."""

    title: str
    description: str
    priority: str
    due_date: str | None


def validate_task(form: dict[str, str]) -> tuple[TaskInput | None, str | None]:
    """Проверить поля формы и вернуть данные либо текст ошибки."""
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    priority = form.get("priority", "medium")
    due_date = form.get("due_date", "").strip() or None
    if not title:
        return None, "Введите название задачи."
    if len(title) > 120:
        return None, "Название не должно превышать 120 символов."
    if len(description) > 1000:
        return None, "Описание не должно превышать 1000 символов."
    if priority not in {"low", "medium", "high"}:
        return None, "Выбрано недопустимое значение приоритета."
    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError:
            return None, "Укажите корректную дату."
    return TaskInput(title, description, priority, due_date), None


def list_tasks(
    user_id: int, status: str, priority: str, query: str
) -> list[sqlite3.Row]:
    """Получить задачи с фильтрами и поиском."""
    conditions: list[str] = ["user_id = ?"]
    values: list[object] = [user_id]
    if status in {"active", "completed"}:
        conditions.append("is_completed = ?")
        values.append(1 if status == "completed" else 0)
    if priority in {"low", "medium", "high"}:
        conditions.append("priority = ?")
        values.append(priority)
    if query:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        pattern = f"%{query}%"
        values.extend((pattern, pattern))
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT * FROM tasks {where}
        ORDER BY is_completed ASC,
                 CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                 due_date IS NULL, due_date ASC, created_at DESC
    """
    return list(get_db().execute(sql, values).fetchall())


def get_task(task_id: int, user_id: int) -> sqlite3.Row | None:
    """Найти задачу по идентификатору."""
    return get_db().execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
    ).fetchone()


def create_task(task: TaskInput, user_id: int) -> None:
    """Сохранить новую задачу."""
    db = get_db()
    db.execute(
        """INSERT INTO tasks
        (title, description, priority, due_date, user_id)
        VALUES (?, ?, ?, ?, ?)""",
        (task.title, task.description, task.priority, task.due_date, user_id),
    )
    db.commit()


def update_task(task_id: int, task: TaskInput, user_id: int) -> None:
    """Изменить существующую задачу."""
    db = get_db()
    db.execute(
        """UPDATE tasks SET title = ?, description = ?, priority = ?,
        due_date = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?""",
        (task.title, task.description, task.priority, task.due_date, task_id, user_id),
    )
    db.commit()


def toggle_task(task_id: int, user_id: int) -> None:
    """Переключить статус выполнения задачи."""
    db = get_db()
    db.execute(
        """UPDATE tasks SET is_completed = 1 - is_completed,
        updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?""",
        (task_id, user_id),
    )
    db.commit()


def delete_task(task_id: int, user_id: int) -> None:
    """Удалить задачу."""
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    db.commit()


def get_stats(user_id: int) -> sqlite3.Row:
    """Вернуть общую статистику списка."""
    return get_db().execute(
        """SELECT COUNT(*) AS total,
        COALESCE(SUM(is_completed = 0), 0) AS active,
        COALESCE(SUM(is_completed = 1), 0) AS completed,
        COALESCE(SUM(is_completed = 0 AND due_date < date('now')), 0) AS overdue
        FROM tasks WHERE user_id = ?""",
        (user_id,),
    ).fetchone()
