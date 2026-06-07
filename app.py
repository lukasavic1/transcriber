import os
import time
import tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests
import subprocess

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production-12345')

# File upload config
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'm4a', 'webm', 'flac', 'ogg', 'aac'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
UPLOAD_FOLDER = tempfile.gettempdir()

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ASSEMBLY_AI_API_KEY = os.getenv('ASSEMBLY_AI_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('Tesla123#')

# Assembly AI API endpoints
ASSEMBLY_AI_BASE_URL = 'https://api.assemblyai.com/v2'


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

        # Check if old table exists with youtube_url column
        c.execute("""SELECT column_name FROM information_schema.columns
                     WHERE table_name='transcriptions'""")
        existing_columns = [row[0] for row in c.fetchall()]

        if existing_columns and 'youtube_url' in existing_columns:
            # Drop old table and recreate with new schema
            print("🔄 Updating database schema...")
            c.execute('DROP TABLE IF EXISTS transcriptions CASCADE')
            conn.commit()

        # Create new table
        c.execute('''CREATE TABLE IF NOT EXISTS transcriptions
                     (id SERIAL PRIMARY KEY,
                      name TEXT NOT NULL,
                      transcript TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database init error: {e}")


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_wav(audio_file_path: str) -> str:
    """Convert audio file to WAV format using ffmpeg."""
    try:
        file_ext = Path(audio_file_path).suffix.lower()

        # If already WAV, no conversion needed
        if file_ext == '.wav':
            return audio_file_path

        print(f"🔄 Converting {file_ext} to WAV...")

        wav_path = audio_file_path.replace(file_ext, '.wav')

        # Use ffmpeg to convert
        cmd = [
            'ffmpeg',
            '-i', audio_file_path,
            '-acodec', 'pcm_s16le',  # PCM 16-bit LE (standard WAV codec)
            '-ar', '16000',  # 16kHz sample rate (Assembly AI friendly)
            '-ac', '1',  # Mono
            '-y',  # Overwrite output
            wav_path
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=300)

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr.decode()}")

        print(f"✅ Converted to WAV: {wav_path}")

        # Delete original file
        try:
            os.remove(audio_file_path)
        except:
            pass

        return wav_path

    except Exception as e:
        raise Exception(f"Audio conversion failed: {str(e)}")


def transcribe_with_assembly_ai(audio_file_path: str) -> str:
    """Transcribe audio file using Assembly AI."""
    try:
        print(f"📤 [ASSEMBLY] Starting upload to Assembly AI...")
        file_size_mb = os.path.getsize(audio_file_path) / (1024*1024)
        print(f"📊 File size: {file_size_mb:.2f}MB")

        # Upload file to Assembly AI
        headers = {
            'Authorization': ASSEMBLY_AI_API_KEY,
        }

        # Determine correct MIME type based on file extension
        file_ext = Path(audio_file_path).suffix.lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.mp4': 'video/mp4',
            '.webm': 'audio/webm',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac'
        }
        mime_type = mime_types.get(file_ext, 'audio/mpeg')
        print(f"🏷️  MIME type: {mime_type}")

        with open(audio_file_path, 'rb') as f:
            file_data = f.read()

        print(f"📤 Uploading {len(file_data)} bytes to Assembly AI...")

        # Set Content-Type header explicitly
        upload_headers = headers.copy()
        upload_headers['Content-Type'] = mime_type

        print(f"🌐 POST {ASSEMBLY_AI_BASE_URL}/upload")
        upload_response = requests.post(
            f'{ASSEMBLY_AI_BASE_URL}/upload',
            headers=upload_headers,
            data=file_data,
            timeout=60
        )

        print(f"📡 Upload response status: {upload_response.status_code}")
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.text}")
            raise Exception(f"Upload failed: {upload_response.text}")

        audio_url = upload_response.json()['upload_url']
        print(f"✅ Uploaded! Starting transcription...")

        # Submit transcription job
        headers['Content-Type'] = 'application/json'
        data = {
            'audio_url': audio_url
        }

        response = requests.post(
            f'{ASSEMBLY_AI_BASE_URL}/transcript',
            json=data,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Submission failed: {response.text}")

        transcript_id = response.json()['id']
        print(f"✅ Job submitted: {transcript_id}")

        # Poll for completion
        print("⏳ Waiting for transcription...")
        max_attempts = 120  # 10 minutes
        attempt = 0

        while attempt < max_attempts:
            result_response = requests.get(
                f'{ASSEMBLY_AI_BASE_URL}/transcript/{transcript_id}',
                headers={'Authorization': ASSEMBLY_AI_API_KEY},
                timeout=30
            )

            if result_response.status_code != 200:
                raise Exception(f"Status check failed: {result_response.text}")

            result = result_response.json()

            if result['status'] == 'completed':
                print("✅ Transcription completed!")
                return result.get('text', '')

            elif result['status'] == 'error':
                raise Exception(f"Transcription error: {result.get('error', 'Unknown')}")

            attempt += 1
            if attempt % 12 == 0:  # Log every 60 seconds
                print(f"⏳ Processing... ({attempt * 5} seconds)")

            time.sleep(5)

        raise Exception("Transcription timed out")

    except Exception as e:
        raise Exception(f"Assembly AI transcription failed: {str(e)}")


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
    return jsonify({
        'status': 'ok',
        'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
        'environment': 'vercel' if IS_VERCEL else 'local'
    })


@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info."""
    return jsonify({'username': current_user.username})


@app.route('/api/transcribe', methods=['POST'])
@login_required
def transcribe():
    """Transcribe uploaded audio file and save to database."""
    try:
        print(f"\n{'='*60}")
        print(f"📡 [TRANSCRIBE START] Received request")
        print(f"Content-Length: {request.content_length}")
        print(f"{'='*60}")

        # Check if file was uploaded
        if 'file' not in request.files:
            print("❌ No file in request")
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        name = request.form.get('name', '').strip()

        print(f"📝 File name: {file.filename}")
        print(f"📝 Transcription name: {name}")

        if not name:
            print("❌ No name provided")
            return jsonify({'error': 'Please enter a name for this transcription'}), 400

        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            print(f"❌ File type not allowed: {file.filename}")
            return jsonify({'error': f'File type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        print(f"\n{'='*60}")
        print(f"🎯 Transcribing: {name}")
        print(f"📁 File: {file.filename}")
        print(f"{'='*60}")

        # Save temp file
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{int(time.time())}_{filename}")

        print(f"💾 Saving file to: {temp_path}")
        file.save(temp_path)
        file_size = os.path.getsize(temp_path)
        print(f"✅ File saved ({file_size / (1024*1024):.2f}MB)")

        try:
            print(f"🔄 Starting transcription with Assembly AI...")
            # Transcribe with Assembly AI (send in native format)
            transcript = transcribe_with_assembly_ai(temp_path)

            # Save to database
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO transcriptions (name, transcript) VALUES (%s, %s) RETURNING id',
                      (name, transcript))
            transcription_id = c.fetchone()[0]
            conn.commit()
            conn.close()

            print(f"✅ Saved to database (ID: {transcription_id})")
            print(f"{'='*60}\n")

            return jsonify({
                'success': True,
                'id': transcription_id,
                'transcript': transcript,
                'name': name
            })

        finally:
            # Always delete temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            print("✅ Cleaned up temp file")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
        c.execute('SELECT id, name, created_at FROM transcriptions ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()

        transcriptions = [{
            'id': row[0],
            'name': row[1],
            'created_at': row[2].isoformat() if row[2] else None
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
        c.execute('SELECT id, name, transcript, created_at FROM transcriptions WHERE id = %s',
                  (transcription_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Transcription not found'}), 404

        return jsonify({
            'id': row[0],
            'name': row[1],
            'transcript': row[2],
            'created_at': row[3].isoformat() if row[3] else None
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


@app.errorhandler(413)
def request_too_large(e):
    return jsonify({'error': 'File too large. Vercel limit is ~10MB per file. Try a smaller file.', 'success': False}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(e):
    print(f"Server error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


@app.before_request
def log_request():
    print(f"Request: {request.method} {request.path}")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
