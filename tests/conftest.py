import pytest

from todo_app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": tmp_path / "test.sqlite3"})


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth(client):
    class AuthActions:
        def register(self, username="student", password="password123"):
            return client.post(
                "/auth/register",
                data={
                    "username": username,
                    "password": password,
                    "confirm": password,
                },
                follow_redirects=True,
            )

        def login(self, username="student", password="password123"):
            return client.post(
                "/auth/login",
                data={"username": username, "password": password},
                follow_redirects=True,
            )

        def logout(self):
            return client.post("/auth/logout", follow_redirects=True)

    return AuthActions()
