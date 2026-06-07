import os
import tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production-12345')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

DATABASE_URL = os.getenv('DATABASE_URL')
AUDIO_DIR = Path(tempfile.gettempdir()) / 'transcribe_audio'
AUDIO_DIR.mkdir(exist_ok=True)

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('Tesla123#')


class User(UserMixin):
    """Simple user class for authentication."""
    def __init__(self, username):
        self.id = username
        self.username = username


@login_manager.user_loader
def load_user(username):
    """Load user by username."""
    if username == ADMIN_USERNAME:
        return User(username)
    return None


def get_db():
    """Get database connection."""
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    """Initialize the database."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transcriptions
                     (id SERIAL PRIMARY KEY,
                      name TEXT NOT NULL,
                      youtube_url TEXT NOT NULL,
                      transcript TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database init error: {e}")


def extract_audio_from_youtube(youtube_url: str) -> str:
    """Download audio from YouTube video and return path to MP3 file."""
    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(AUDIO_DIR / '%(id)s'),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 60,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.youtube.com/',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                    'player_skip': ['js', 'configs'],
                }
            },
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_file = AUDIO_DIR / f"{info['id']}.mp3"

            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not created")

            return str(audio_file)
    except Exception as e:
        raise Exception(f"Failed to download audio: {str(e)}")


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper API."""
    try:
        with open(audio_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        return transcript.text
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = request.json or request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            user = User(username)
            login_user(user, remember=True)

            if request.is_json:
                return jsonify({'success': True})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            return redirect(url_for('login'))

    return send_from_directory('.', 'login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Serve the index.html file."""
    return send_from_directory('.', 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info."""
    return jsonify({'username': current_user.username})


@app.route('/api/transcribe', methods=['POST'])
@login_required
def transcribe():
    """Transcribe a YouTube video and save to database."""
    try:
        data = request.json
        youtube_url = data.get('url', '').strip()
        name = data.get('name', '').strip()

        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # Validate YouTube URL
        if 'youtube.com' not in youtube_url and 'youtu.be' not in youtube_url:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Extract audio
        audio_path = extract_audio_from_youtube(youtube_url)

        # Transcribe
        transcript = transcribe_audio(audio_path)

        # Save to database
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO transcriptions (name, youtube_url, transcript) VALUES (%s, %s, %s) RETURNING id',
                  (name, youtube_url, transcript))
        transcription_id = c.fetchone()[0]
        conn.commit()
        conn.close()

        # Clean up
        try:
            Path(audio_path).unlink()
        except:
            pass

        return jsonify({
            'success': True,
            'id': transcription_id,
            'transcript': transcript,
            'url': youtube_url,
            'name': name
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/transcriptions', methods=['GET'])
@login_required
def get_transcriptions():
    """Get all transcriptions."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, name, youtube_url, created_at FROM transcriptions ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()

        transcriptions = [{
            'id': row[0],
            'name': row[1],
            'youtube_url': row[2],
            'created_at': row[3].isoformat() if row[3] else None
        } for row in rows]

        return jsonify({'transcriptions': transcriptions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transcriptions/<int:transcription_id>', methods=['GET'])
@login_required
def get_transcription(transcription_id):
    """Get a specific transcription."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, name, youtube_url, transcript, created_at FROM transcriptions WHERE id = %s',
                  (transcription_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Transcription not found'}), 404

        return jsonify({
            'id': row[0],
            'name': row[1],
            'youtube_url': row[2],
            'transcript': row[3],
            'created_at': row[4].isoformat() if row[4] else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transcriptions/<int:transcription_id>', methods=['DELETE'])
@login_required
def delete_transcription(transcription_id):
    """Delete a transcription."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM transcriptions WHERE id = %s', (transcription_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
