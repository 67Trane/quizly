import json
from django.conf import settings
import yt_dlp
import whisper
import os
from google import genai
import re


def process_youtube_quiz(url):
    audio_path = download_audio(url)
    transcript = transcribe_audio(audio_path)
    quiz_json = generate_quiz_from_transcript(transcript)

    match = re.search(r"```(?:json)?\s*(.*?)```", quiz_json, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = quiz_json.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def download_audio(url):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts = {
        "format": "bestaudio",
        "restrictfilenames": True,
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {  # nach dem Download MP3 daraus machen
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        audio_path = ydl.prepare_filename(info)
        base, _ = os.path.splitext(audio_path)

        # Prüfen, welche Datei wirklich existiert:
        for ext in (".mp3", ".m4a", ".webm", ".opus"):
            if os.path.exists(base + ext):
                audio_path = base + ext
                break
        return audio_path


def transcribe_audio(audio):
    model = whisper.load_model("turbo")
    result = model.transcribe(audio)
    return result["text"]


def generate_quiz_from_transcript(transcript):
    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
        Based on the following transcript, generate a quiz in valid JSON format.
        The quiz must follow this exact structure:
        {{
        "title": "Create a concise quiz title based on the topic of the transcript.",
        "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
        "questions": [
            {{
            "question_title": "The question goes here.",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "The correct answer from the above options"
            }},
            ...
            (exactly 10 questions)
        ]
        }}
        Requirements:
        - Each question must have exactly 4 distinct answer options.
        - Only one correct answer is allowed per question, and it must be present in 'question_options'.
        - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
        - Do not include explanations, comments, or any text outside the JSON. 
        the transcript is:"{transcript}"
        """,
    )
    return response.text
