def test_empty_page(client, auth):
    auth.register()
    response = client.get("/")
    assert response.status_code == 200
    assert "Здесь пока пусто" in response.text


def test_create_and_search_task(client, auth):
    auth.register()
    response = client.post(
        "/tasks",
        data={
            "title": "Сдать проект",
            "description": "До пятницы",
            "priority": "high",
            "due_date": "2026-07-17",
        },
        follow_redirects=True,
    )
    assert "Сдать проект" in response.text
    assert "Высокий" in response.text
    assert "Сдать проект" in client.get("/?q=Сдать").text
    assert "Сдать проект" not in client.get("/?q=Несуществующая").text


def test_validation(client, auth):
    auth.register()
    response = client.post(
        "/tasks",
        data={"title": "", "priority": "medium"},
        follow_redirects=True,
    )
    assert "Введите название задачи" in response.text


def test_full_lifecycle(client, auth):
    auth.register()
    client.post("/tasks", data={"title": "Черновик", "priority": "low"})
    response = client.post(
        "/tasks/1/edit",
        data={"title": "Готово", "priority": "medium"},
        follow_redirects=True,
    )
    assert "Готово" in response.text
    response = client.post("/tasks/1/toggle", follow_redirects=True)
    assert 'class="task-card priority-medium done"' in response.text
    response = client.post("/tasks/1/delete", follow_redirects=True)
    assert "Здесь пока пусто" in response.text


def test_not_found(client, auth):
    auth.register()
    assert client.post("/tasks/999/toggle").status_code == 404


def test_login_required(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_users_have_separate_tasks(client, auth):
    auth.register("alice", "password123")
    client.post("/tasks", data={"title": "Задача Алисы", "priority": "high"})
    auth.logout()
    auth.register("bob", "password456")
    response = client.get("/")
    assert "Задача Алисы" not in response.text
    client.post("/tasks", data={"title": "Задача Боба", "priority": "low"})
    assert "Задача Боба" in client.get("/").text
    auth.logout()
    auth.login("alice", "password123")
    response = client.get("/")
    assert "Задача Алисы" in response.text
    assert "Задача Боба" not in response.text


def test_registration_validation(client):
    response = client.post(
        "/auth/register",
        data={"username": "ab", "password": "short", "confirm": "other"},
        follow_redirects=True,
    )
    assert "от 3 до 40 символов" in response.text
