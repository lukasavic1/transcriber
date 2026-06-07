# YouTube Transcriber

A production-ready web app to transcribe YouTube videos using OpenAI's Whisper API with persistent storage and history.

## Features

- 🎥 **Transcribe Videos** — Paste YouTube URLs and get instant transcripts
- 💾 **Save History** — All transcriptions stored in SQLite database
- 📋 **Organize** — Name your videos for easy identification
- 🔍 **Browse History** — View, search, and manage all past transcriptions
- ⚡ **Fast** — Uses OpenAI Whisper API (~$0.36/hour)
- 🎨 **Beautiful UI** — Tab-based interface with real-time updates
- 📱 **Responsive** — Works on desktop, tablet, mobile

## What You Get

```
New Transcription Tab
├── Enter video name
├── Paste YouTube URL
├── Get instant transcript
└── Copy to clipboard

History Tab
├── View all transcriptions
├── Click to view full transcript
├── See date created and URL
└── Delete old transcriptions
```

## Prerequisites

- Python 3.8+
- FFmpeg (for audio conversion)
- OpenAI API key

## Quick Setup

### 1. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
```bash
choco install ffmpeg
```

### 2. Setup Python environment

```bash
cd /path/to/transcribe
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Copy it

### 4. Configure

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
```

### 5. Run

```bash
python app.py
```

Open: **http://localhost:8000**

## Database

The app uses **SQLite** to store transcriptions locally. 

Database file: `transcriptions.db` (auto-created on first run)

Stored data:
- Video name (custom)
- YouTube URL
- Full transcript
- Date created

## Pricing

**OpenAI Whisper API:** $0.36 per hour of audio

Examples:
- 10 min video = ~$0.06
- 1 hour video = ~$0.36
- OpenAI gives you $5 free credit (= ~14 hours)

## API Endpoints

### Transcribe
```
POST /api/transcribe
Body: { "name": "string", "url": "string" }
Returns: { "id": 1, "name": "...", "transcript": "...", "url": "..." }
```

### List all
```
GET /api/transcriptions
Returns: { "transcriptions": [...] }
```

### Get one
```
GET /api/transcriptions/:id
Returns: { "id": 1, "name": "...", "transcript": "...", "url": "...", "created_at": "..." }
```

### Delete
```
DELETE /api/transcriptions/:id
```

## Project Structure

```
transcribe/
├── app.py              # Flask backend with database
├── index.html          # Frontend with tabs
├── requirements.txt    # Dependencies
├── .env               # API keys (don't commit!)
├── .gitignore         # Git ignore rules
├── transcriptions.db  # SQLite database (auto-created)
└── README.md          # This file
```

## Deploying to Vercel

### Important: Database Considerations

**SQLite won't persist on Vercel** (serverless has ephemeral filesystem). You have options:

#### Option 1: Use PostgreSQL (Recommended for production)

1. Create a free PostgreSQL database:
   - **Vercel Postgres** (easiest): https://vercel.com/docs/storage/vercel-postgres
   - Or use **Supabase**: https://supabase.com (free tier)

2. Update `app.py` to use PostgreSQL instead of SQLite

#### Option 2: Use Firebase (Simpler setup)

Replace SQLite with Firestore for cloud storage:
```python
from firebase_admin import db
```

#### Option 3: Local SQLite (Development only)

Just deploy as-is for testing. Data won't persist between deploys, but it works for development.

### Deploy Steps (with SQLite, local development only)

1. **Create Vercel account** at https://vercel.com

2. **Push to GitHub**
```bash
git init
git add .
git commit -m "Add transcriber app"
git branch -M main
git remote add origin https://github.com/YOUR_USER/transcribe.git
git push -u origin main
```

3. **Import on Vercel**
   - Go to https://vercel.com/new
   - Import your GitHub repo
   - Set environment variable: `OPENAI_API_KEY`
   - Deploy!

4. **URL**: https://your-project.vercel.app

### Deploy with PostgreSQL

1. **Create Vercel Postgres** database (in Vercel dashboard)

2. **Update app.py** to use PostgreSQL:
```python
import psycopg2
from os import getenv

# Use Vercel's CONNECTION_STRING
DATABASE_URL = getenv('POSTGRES_URL')
```

3. **Set environment variables** in Vercel:
   - `OPENAI_API_KEY`
   - `POSTGRES_URL` (auto-set by Vercel)

4. Deploy as normal

## Troubleshooting

### "FFmpeg not found"
```bash
ffmpeg -version  # Test it
```
Install if missing (see Setup section)

### "OpenAI API Error"
- Check key is correct in `.env`
- Make sure it starts with `sk-`
- Verify you have API credits

### "Database locked" error
- SQLite locks if too many concurrent users
- Use PostgreSQL for production
- See "Deploying to Vercel" section

### Slow transcription
- Whisper API speed depends on audio length
- Long videos (2+ hours) can take 5-10 minutes
- This is normal

## Advanced Usage

### Batch Transcribe

Create `batch.py`:
```python
from app import transcribe_audio, extract_audio_from_youtube
import sqlite3

urls = [
    "https://youtube.com/watch?v=...",
    "https://youtube.com/watch?v=...",
]

conn = sqlite3.connect('transcriptions.db')
c = conn.cursor()

for url in urls:
    print(f"Transcribing: {url}")
    audio = extract_audio_from_youtube(url)
    transcript = transcribe_audio(audio)
    c.execute('INSERT INTO transcriptions (name, youtube_url, transcript) VALUES (?, ?, ?)',
              (url.split('=')[-1], url, transcript))
    
conn.commit()
conn.close()
```

Run: `python batch.py`

### Export Transcriptions

View the `transcriptions.db` file with any SQLite client:
- **Online**: https://sqliteonline.com
- **GUI**: DB Browser for SQLite
- **Python**: 
```python
import sqlite3
conn = sqlite3.connect('transcriptions.db')
c = conn.cursor()
c.execute('SELECT * FROM transcriptions')
for row in c.fetchall():
    print(row)
```

## Future Enhancements

- [ ] Multi-language support
- [ ] Export as PDF/SRT
- [ ] Search transcriptions
- [ ] Timestamp-based transcripts
- [ ] User authentication
- [ ] Sharing transcriptions
- [ ] Auto-generate summaries

## Support

Need help? Check:
1. FFmpeg installed: `ffmpeg -version`
2. API key valid: Log in to OpenAI
3. Internet connection working
4. Python version >= 3.8

Enjoy transcribing! 🎉
