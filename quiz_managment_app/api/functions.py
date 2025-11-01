import json
from django.conf import settings
import yt_dlp
import whisper
import os
from google import genai
import re


def process_youtube_quiz(url):
    """
    End-to-end pipeline:
    1) Download audio from a YouTube URL,
    2) Transcribe the audio to text,
    3) Generate a quiz JSON based on the transcript,
    4) Attempt to parse and return the JSON object.

    Returns:
        dict | None: Parsed quiz JSON as a Python dict if successful, otherwise None.
    """
    audio_path = download_audio(url)
    transcript = transcribe_audio(audio_path)
    quiz_json = generate_quiz_from_transcript(transcript)

    # Extract raw JSON even if it's wrapped in Markdown code fences (``` or ```json)
    match = re.search(r"```(?:json)?\s*(.*?)```", quiz_json, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = quiz_json.strip()

    # Attempt to parse to Python dict; return None on invalid JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def download_audio(url):
    """
    Downloads the best available audio stream for a given YouTube URL and converts it to MP3.
    Falls back to common audio extensions when determining the final file path.

    Args:
        url (str): The YouTube video URL.

    Returns:
        str: Absolute filesystem path to the downloaded audio file.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    # See help(yt_dlp.YoutubeDL) for available options and functions
    ydl_opts = {
        "format": "bestaudio",
        "restrictfilenames": True,
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                # After download, convert audio to MP3 with low/voice-friendly bitrate
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Download and extract basic info; also saves the file
        info = ydl.extract_info(url, download=True)

        # Prepare the base filename for extension probing
        audio_path = ydl.prepare_filename(info)
        base, _ = os.path.splitext(audio_path)

        # Determine the actual file that exists on disk after post-processing
        for ext in (".mp3", ".m4a", ".webm", ".opus"):
            if os.path.exists(base + ext):
                audio_path = base + ext
                break
        return audio_path


def transcribe_audio(audio):
    """
    Transcribes an audio file using OpenAI Whisper.

    Args:
        audio (str): Path to the audio file.

    Returns:
        str: The transcribed text.
    """
    # Load a fast Whisper model variant suitable for quick transcriptions
    model = whisper.load_model("turbo")
    result = model.transcribe(audio)
    return result["text"]


def generate_quiz_from_transcript(transcript):
    """
    Sends the transcript to Gemini and requests a structured quiz in JSON format.

    The prompt instructs Gemini to output strictly valid JSON with:
      - title, description
      - exactly 10 questions
      - each question: 4 options and a single correct answer contained in options

    Args:
        transcript (str): The transcribed text used as source material.

    Returns:
        str: The raw text response from Gemini (expected to be JSON or fenced JSON).
    """
    # The client reads the API key from settings (backed by env var `GEMINI_API_KEY`)
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
    # Gemini client returns a response object; `.text` is the textual payload
    return response.text
