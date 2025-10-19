import pytest
from django.contrib.auth import get_user_model

LOGIN_URL = "/api/login/"


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="tester", password="strong123!")


@pytest.fixture
def auth_client(client, user):
    payload = {"username": "tester", "password": "strong123!"}
    r = client.post(LOGIN_URL, data=payload, content_type="application/json")
    assert r.status_code in (
        200,
        201,
    ), f"Login fehlgeschlagen: {r.status_code} {getattr(r, 'data', r.content)}"
    return client
