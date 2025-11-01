import pytest


def test_proccess_youtube_quiz(monkeypatch):
    """
    End-to-end happy-path test for process_youtube_quiz with all dependencies mocked.
    Ensures JSON is parsed and mapped to the expected Python structure.
    """
    # Stub the heavy I/O and model calls to make the test fast and deterministic
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.download_audio",
        lambda url: "fake_audio.mp3",
    )
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.transcribe_audio",
        lambda audio: "This is a transcript",
    )
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.generate_quiz_from_transcript",
        lambda transcript: '{"title": "Test", "description": "Desc", "questions": []}',
    )

    # Import after monkeypatching so the function under test uses our fakes
    from quiz_managment_app.api.functions import process_youtube_quiz

    result = process_youtube_quiz("https://youtu.be/fake")

    # Validate the parsed structure
    assert result["title"] == "Test"
    assert result["description"] == "Desc"
    assert result["questions"] == []


@pytest.mark.parametrize("transcript", ["hello world"])
def test_generate_quiz_from_transcript_happy(monkeypatch, settings, transcript):
    """
    Verifies that generate_quiz_from_transcript:
      - uses the API key from Django settings,
      - calls the expected Gemini model,
      - includes the transcript in the prompt,
      - and returns the raw text provided by the fake client.
    """
    # 1) Configure settings (pytest-django fixture)
    settings.GEMINI_API_KEY = "test-key"

    # 2) Build a fake client/response to capture calls without hitting the network
    calls = {}  # collect call arguments for assertions

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

    # 3) Patch genai.Client in the target module (where it is used)
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.genai.Client",
        FakeClient,
    )

    # 4) Import and execute the function under test
    from quiz_managment_app.api.functions import generate_quiz_from_transcript

    out = generate_quiz_from_transcript(transcript)

    # 5) Assertions: API key, model name, prompt content, and raw return value
    assert calls["api_key"] == "test-key"
    assert calls["model"] == "gemini-2.5-flash"
    assert transcript in calls["contents"]
    assert out == '{"title":"OK","description":"D","questions":[]}'


def test_transcribe_audio(monkeypatch):
    """
    Ensures transcribe_audio returns the 'text' field from Whisper's output.
    """

    class FakeModel:
        def transcribe(self, audio):
            # Return a stable fake transcription for the given audio path
            return {"text": "FAKE_TEXT"}

    # Patch whisper.load_model to return our fake model instance
    monkeypatch.setattr(
        "quiz_managment_app.api.functions.whisper.load_model",
        lambda name: FakeModel(),
    )

    from quiz_managment_app.api.functions import transcribe_audio

    result = transcribe_audio("fakefile.mp3")

    assert result == "FAKE_TEXT"
