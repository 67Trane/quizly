import json
import yt_dlp
import whisper
import os


def download_and_extract_audio():
    URL = 'https://www.youtube.com/watch?v=r2RvhnR6Gtw'

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

        info = ydl.extract_info(URL, download=True)

        audio_path = ydl.prepare_filename(info)
        base, _ = os.path.splitext(audio_path)

        # Prüfen, welche Datei wirklich existiert:
        for ext in (".mp3", ".m4a", ".webm", ".opus"):
            if os.path.exists(base + ext):
                audio_path = base + ext
                break

        print(f"Audio gepsiechter unter : {audio_path}")

        create_transcribe(audio_path)


def create_transcribe(audio):
    model = whisper.load_model("turbo")
    result = model.transcribe(audio)
    print(result["text"])


download_and_extract_audio()
