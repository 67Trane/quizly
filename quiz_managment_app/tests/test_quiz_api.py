import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_quizzes_list(client):
    r = client.get("/api/quizzes/")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_quiz_requires_auth(client):
    r = client.post(
        "/api/createQuiz/",
        data={"url": "https://youtu.be/xyz"},
        content_type="application/json",
    )
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_quiz_missing_url(auth_client):
    r = auth_client.post("/api/createQuiz/", data={},
                         content_type="application/json")
    assert r.status_code == 400
    assert r.json().get("detail") == "no url found"


@pytest.mark.django_db
def test_create_quiz(auth_client):
    response = auth_client.post(
        "/api/createQuiz/",
        data={"url": "https://www.youtube.com/watch?v=example"},
        content_type="application/json",
    )
    assert response.status_code in (200, 201)


@pytest.mark.django_db
def test_create_quiz_happy_path(auth_client, monkeypatch):
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
        assert url.startswith("https://")
        return fake_data

    monkeypatch.setattr(
        "quiz_managment_app.api.views.process_youtube_quiz", fake_process
    )

    payload = {"url": "https://www.youtube.com/watch?v=example"}
    url = reverse("create-quiz")
    response = auth_client.post(
        url, data=payload, content_type="application/json")

    assert response.status_code == 201
    data = response.json()
    assert data.get("title") == "Quiz Title"
    assert data.get("video_url") == "https://www.youtube.com/watch?v=example"


def test_proccess_youtube_quiz(monkeypatch):
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.download_audio", lambda url: "fake_audio.mp3")
    monkeypatch.setattr("quiz_managment_app.api.functions.transcribe_audio",
                        lambda audio: "This is a transcript")
    monkeypatch.setattr("quiz_managment_app.api.functions.generate_quiz_from_transcript",
                        lambda transcript: '{"title": "Test", "description": "Desc", "questions": []}')

    from quiz_managment_app.api.functions import process_youtube_quiz
    result = process_youtube_quiz("https://youtu.be/fake")

    assert result["title"] == "Test"
    assert result["description"] == "Desc"
    assert result["questions"] == []


@pytest.mark.parametrize("transcript", ["hello world"])
def test_generate_quiz_from_transcript_happy(monkeypatch, settings, transcript):
    # 1) Settings vorbereiten (pytest-django Fixture)
    settings.GEMINI_API_KEY = "test-key"

    # 2) Fake Response / Client bauen
    calls = {}  # zum Mitschneiden der Aufrufe

    class FakeResponse:
        def __init__(self, text):
            self.text = text

    class FakeModels:
        def generate_content(self, *, model, contents):
            calls["model"] = model
            calls["contents"] = contents
            return FakeResponse('{"title":"OK","description":"D","questions":[]}')

    class FakeClient:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.models = FakeModels()

    # 3) genai.Client im Zielmodul ersetzen (wo du es verwendest!)
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.genai.Client", FakeClient)

    # 4) Funktion importieren & aufrufen
    from quiz_managment_app.api.functions import generate_quiz_from_transcript
    out = generate_quiz_from_transcript(transcript)

    # 5) Asserts: richtiger Key, richtiges Modell, Transcript im Prompt, Rückgabe passt
    assert calls["api_key"] == "test-key"
    assert calls["model"] == "gemini-2.5-flash"
    assert transcript in calls["contents"]
    assert out == '{"title":"OK","description":"D","questions":[]}'


def test_transcribe_audio(monkeypatch):
    class FakeModel:
        def transcribe(self, audio):
            return {"text": "FAKE_TEXT"}

    monkeypatch.setattr(
        "quiz_managment_app.api.functions.whisper.load_model", lambda name: FakeModel())

    from quiz_managment_app.api.functions import transcribe_audio
    result = transcribe_audio("fakefile.mp3")

    assert result == "FAKE_TEXT"
