# YouTube → Quiz API (Django REST + Whisper + Gemini)

Creates a quiz from a YouTube video via a REST API.  
Audio is downloaded using **yt-dlp**, extracted/converted with **FFmpeg**, transcribed with **Whisper**, and then turned into a 10-question quiz by **Google Gemini**.  
The API is protected using **JWT (HTTP-Only Cookies)**.

## ✨ Features

- **/quizzes**: Full CRUD for quizzes (Django REST Framework `ModelViewSet`)
- **/quizzes:create**: POST a YouTube URL → automatically generates a quiz
- **JWT Cookie Auth**: Registration, login, logout, and token refresh (HTTP-Only Cookies)
- Clean JSON schema with 10 questions (4 options each, 1 correct answer)

## 🧱 Tech Stack

- Django 5 / Django REST Framework
- djangorestframework-simplejwt (Cookies)
- yt-dlp, FFmpeg (Audio handling)
- Whisper (Speech-to-text transcription)
- Google Generative AI (`google-genai`) – Model: `gemini-2.5-flash`

## 📦 Requirements

- **Python 3.10+** (recommended)
- **FFmpeg** (mandatory)
- Git (optional)
- Google Gemini API Key

### Install and Verify FFmpeg

- macOS (brew): `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`
- Windows (choco): `choco install ffmpeg`

Verify installation:

```bash
ffmpeg -version
```

> Without FFmpeg, audio extraction will fail (required for Whisper and yt-dlp postprocessing).

## 🚀 Quick Start (Development)

```bash
# 1) Clone the repository
git clone https://github.com/67Trane/quizly.git youtube-quiz-api
cd youtube-quiz-api

# 2) Virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4) Create and configure environment file
# macOS/Linux:
cp .env.template .env
# Add your GEMINI_API_KEY and Django secrets

# 5) Database setup
python manage.py migrate
python manage.py createsuperuser

# 6) Run the server
python manage.py runserver
```

> Default server runs on http://127.0.0.1:8000

## 🔐 Authentication (JWT via HTTP-Only Cookies)

This project uses JWTs stored in **HTTP-Only cookies**. Typical endpoints:

- `POST /api/auth/register` – Register a new user
- `POST /api/auth/login` – Log in; sets `access` and `refresh` cookies
- `POST /api/auth/logout` – Clears cookies
- `POST /api/auth/refresh` – Refreshes the access token

> All protected endpoints require `IsAuthenticated`.  
> For Postman/Insomnia, enable “Cookie Jar” to handle cookies automatically.

## 🧩 API Endpoints (Quiz)

- `POST /api/quizzes/create` → Generates a quiz from a YouTube URL (**protected**)
- `GET /api/quizzes/` → List all quizzes (**protected**)
- `GET /api/quizzes/{id}/` → Retrieve a quiz and its questions (**protected**)

> Exact routes may differ depending on your `urls.py`. The above are examples for your `CreateQuizView` and `QuizViewSet`.

### Example: Create a Quiz

Request:

```http
POST /api/quizzes/create
Content-Type: application/json
Cookie: <your JWT cookies>

{
  "url": "https://www.youtube.com/watch?v=..."
}
```

Response (`201 Created`):

```json
{
  "id": 1,
  "title": "Concise title generated from the video",
  "description": "Short summary (<=150 characters)",
  "video_url": "https://www.youtube.com/watch?v=...",
  "questions": [
    {
      "id": 11,
      "question_title": "Sample question...",
      "question_options": ["A", "B", "C", "D"],
      "answer": "B"
    }
  ]
}
```

### Error Cases

- `400 Bad Request` → Missing `url`
- `500`/`4xx` → Download, transcription, or LLM failure (see logs)

## 🧠 How It Works (Pipeline)

1. **Download**: `yt_dlp` downloads the best available audio stream.
2. **Postprocessing**: FFmpeg extracts/converts it (e.g., MP3, 64 kbit/s).
3. **Transcription**: `whisper.load_model("turbo")` transcribes the audio.
   - You can also use other models like `"base"`, `"small"`, `"medium"`.
4. **Quiz Generation**: Google Gemini (`gemini-2.5-flash`) generates a valid JSON with 10 questions.
5. **Persistence**: `Quiz` and `Question` objects are saved (`bulk_create` for efficiency).
6. **Response**: The quiz is serialized with `QuizSerializer`.

## 🔧 Project Structure (simplified)

```
app/
├─ api/
│  ├─ views.py        # CreateQuizView, QuizViewSet
│  ├─ functions.py    # download_audio, transcribe_audio, generate_quiz_from_transcript
│  ├─ serializers.py  # QuizSerializer
│  └─ urls.py         # API routes
├─ models.py          # Quiz, Question
├─ settings.py        # DRF, JWT, CORS, etc.
└─ ...
```

## 🔑 Environment Variables

Create a `.env` file (or export variables in your environment):

```
# 🐍 Django Settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 🌐 CORS / CSRF Configuration
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200,http://localhost:5500,http://127.0.0.1:5500
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200,http://localhost:5500,http://127.0.0.1:5500

# 🤖 Google Generative AI
GEMINI_API_KEY=your-key

```

> `settings.py` should read `GEMINI_API_KEY` from environment variables (like in your code via `settings.GEMINI_API_KEY`).  
> You can use `python-dotenv` for local development.

## 📥 Example `requirements.txt`

```
Django>=5.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-cors-headers>=4.3
python-dotenv>=1.0

# Audio / Transcription
yt-dlp>=2024.7.1
openai-whisper>=20231117
ffmpeg-python>=0.2  # optional

# LLM (Google)
google-genai>=0.3.0
```

## 🧪 Tips & Troubleshooting

- **FFmpeg not found**: Run `ffmpeg -version` to verify installation and PATH.
- **yt-dlp errors (YouTube changes)**: Run `pip install -U yt-dlp`.
- **Whisper model unavailable**: Switch to `"base"`, `"small"`, `"medium"`, or `"large"`.
- **Long videos**: Use short clips for testing — transcription time scales with length.
- **Gemini API limits**: Check usage quotas and ensure valid JSON output (you already strip backticks correctly).
- **CORS**: Configure `django-cors-headers` for your frontend.
- **File sizes**: Adjust yt-dlp/FFmpeg settings to control output size.

## 🔒 Security

- Use **HTTP-Only, Secure cookies** for JWTs (HTTPS in production).
- Never commit your `SECRET_KEY`.
- Keep your Gemini API key in environment variables.
- Protect upload/download directories from public access.

## 🗺️ Roadmap (Ideas)

- Retry/backoff for network errors
- Real-time progress (WebSockets) for download/transcription
- Multilingual transcription support (Whisper config)
- Quiz scoring & leaderboard system
- Admin UI for editing generated questions

## 📄 License

MIT (or customize as needed)
