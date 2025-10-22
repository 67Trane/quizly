import pytest


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