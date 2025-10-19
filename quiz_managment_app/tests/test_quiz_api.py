import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_quizzes_list(client):
    r = client.get("/api/quizzes/")
    assert r.status_code in (401, 403)
    
    
@pytest.mark.django_db
def test_create_quiz_requires_auth(client):
    r = client.post("/api/createQuiz/", data={"url": "https://youtu.be/xyz"}, content_type="application/json")
    assert r.status_code in (401, 403)

@pytest.mark.django_db
def test_create_quiz_missing_url(auth_client):
    r = auth_client.post("/api/createQuiz/", data={}, content_type="application/json")
    assert r.status_code == 400
    assert r.json().get("detail") == "no url found"
    
@pytest.mark.django_db
def test_create_quiz(auth_client):
    response = auth_client.post("/api/createQuiz/", data={"url": "https://www.youtube.com/watch?v=example"}, content_type="application/json")
    assert response.status_code in (200, 201)