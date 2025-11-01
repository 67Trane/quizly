import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_quizzes_list(client):
    """Unauthenticated users should receive 401/403 when listing quizzes."""
    r = client.get("/api/quizzes/")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_quiz_requires_auth(client):
    """Creating a quiz without authentication should be forbidden (401/403)."""
    r = client.post(
        "/api/createQuiz/",
        data={"url": "https://youtu.be/xyz"},
        content_type="application/json",
    )
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_quiz_missing_url(auth_client):
    """Missing 'url' in payload should return 400 with a clear error message."""
    r = auth_client.post("/api/createQuiz/", data={}, content_type="application/json")
    assert r.status_code == 400
    assert r.json().get("detail") == "no url found"


@pytest.mark.django_db
def test_create_quiz(auth_client):
    """
    Smoke test: with authentication and a payload, the endpoint should respond
    with 200/201 (actual status may vary by implementation).
    """
    response = auth_client.post(
        "/api/createQuiz/",
        data={"url": "https://www.youtube.com/watch?v=example"},
        content_type="application/json",
    )
    assert response.status_code in (200, 201)


@pytest.mark.django_db
def test_create_quiz_happy_path(auth_client, monkeypatch):
    """
    Happy path: monkeypatch the quiz processing function to return a fixed dataset,
    then assert the response structure and selected fields.
    """
    fake_data = {
        "id": 1,
        "title": "Quiz Title",
        "description": "Quiz Description",
        "created_at": "2023-07-29T12:34:56.789Z",
        "updated_at": "2023-07-29T12:34:56.789Z",
        "video_url": "https://www.youtube.com/watch?v=example",
        "questions": [
            {
                "id": 1,
                "question_title": "Question 1",
                "question_options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A",
                "created_at": "2023-07-29T12:34:56.789Z",
                "updated_at": "2023-07-29T12:34:56.789Z",
            }
        ],
    }

    def fake_process(url: str):
        """Fake processing: ensure URL shape and return deterministic test data."""
        assert url.startswith("https://")
        return fake_data

    # Patch the function used by the view so the test is fast and deterministic
    monkeypatch.setattr(
        "quiz_managment_app.api.views.process_youtube_quiz", fake_process
    )

    payload = {"url": "https://www.youtube.com/watch?v=example"}
    url = reverse("create-quiz")
    response = auth_client.post(url, data=payload, content_type="application/json")

    assert response.status_code == 201
    data = response.json()
    assert data.get("title") == "Quiz Title"
    assert data.get("video_url") == "https://www.youtube.com/watch?v=example"
