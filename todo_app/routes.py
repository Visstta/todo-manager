"""HTTP-маршруты приложения."""

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from .auth import login_required

from .models import (
    create_task,
    delete_task,
    get_stats,
    get_task,
    list_tasks,
    toggle_task,
    update_task,
    validate_task,
)

bp = Blueprint("tasks", __name__)


@bp.get("/")
@login_required
def index():
    """Показать список задач и статистику."""
    status = request.args.get("status", "all")
    priority = request.args.get("priority", "all")
    query = request.args.get("q", "").strip()
    return render_template(
        "index.html",
        tasks=list_tasks(g.user["id"], status, priority, query),
        stats=get_stats(g.user["id"]),
        filters={"status": status, "priority": priority, "q": query},
    )


@bp.post("/tasks")
@login_required
def add_task():
    """Добавить задачу."""
    task, error = validate_task(request.form)
    if error:
        flash(error, "error")
    else:
        create_task(task, g.user["id"])
        flash("Задача добавлена.", "success")
    return redirect(url_for("tasks.index"))


@bp.route("/tasks/<int:task_id>/edit", methods=("GET", "POST"))
@login_required
def edit_task(task_id: int):
    """Показать форму или сохранить изменения задачи."""
    current = get_task(task_id, g.user["id"])
    if current is None:
        abort(404)
    if request.method == "POST":
        task, error = validate_task(request.form)
        if error:
            flash(error, "error")
        else:
            update_task(task_id, task, g.user["id"])
            flash("Изменения сохранены.", "success")
            return redirect(url_for("tasks.index"))
    return render_template("edit.html", task=current)


@bp.post("/tasks/<int:task_id>/toggle")
@login_required
def toggle(task_id: int):
    """Переключить выполнение задачи."""
    if get_task(task_id, g.user["id"]) is None:
        abort(404)
    toggle_task(task_id, g.user["id"])
    return redirect(request.referrer or url_for("tasks.index"))


@bp.post("/tasks/<int:task_id>/delete")
@login_required
def remove(task_id: int):
    """Удалить задачу."""
    if get_task(task_id, g.user["id"]) is None:
        abort(404)
    delete_task(task_id, g.user["id"])
    flash("Задача удалена.", "success")
    return redirect(url_for("tasks.index"))
