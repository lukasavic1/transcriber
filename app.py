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
import urllib.request

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
BLOB_READ_WRITE_TOKEN = os.getenv('BLOB_READ_WRITE_TOKEN')
IS_VERCEL = os.getenv('VERCEL') == '1'

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('Tesla123#')

# Assembly AI API endpoints
ASSEMBLY_AI_BASE_URL = 'https://api.assemblyai.com/v2'

# Vercel Blob API endpoint
VERCEL_BLOB_BASE_URL = 'https://blob.vercelusercontent.com'


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
        'environment': 'vercel' if IS_VERCEL else 'local',
        'blob_storage_configured': bool(BLOB_READ_WRITE_TOKEN)
    })


@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info."""
    return jsonify({'username': current_user.username})




import json

def get_session_meta_path(session_id: str) -> str:
    """Get path to session metadata file."""
    return os.path.join(UPLOAD_FOLDER, f".session_{session_id}.json")

def save_session_meta(session_id: str, meta: dict):
    """Save session metadata to file (persists across Vercel invocations)."""
    try:
        with open(get_session_meta_path(session_id), 'w') as f:
            json.dump(meta, f)
    except Exception as e:
        print(f"⚠️  Failed to save session metadata: {e}")

def load_session_meta(session_id: str) -> dict:
    """Load session metadata from file."""
    try:
        meta_path = get_session_meta_path(session_id)
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                meta['received_chunks'] = set(meta.get('received_chunks', []))
                return meta
    except Exception as e:
        print(f"⚠️  Failed to load session metadata: {e}")
    return None


@app.route('/api/upload-session', methods=['POST'])
@login_required
def create_upload_session():
    """Create session for chunked file upload."""
    try:
        print(f"\n{'='*60}")
        print(f"📋 [CHUNKS] Creating upload session...")
        print(f"{'='*60}")

        data = request.get_json()
        filename = data.get('filename', '').strip()
        file_size = data.get('size', 0)
        total_chunks = data.get('chunks', 0)

        if not filename or not allowed_file(filename):
            return jsonify({'error': 'Invalid file'}), 400

        session_id = f"{int(time.time())}_{os.urandom(8).hex()}"
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Save session metadata to file (persists across Vercel invocations)
        session_meta = {
            'filename': filename,
            'size': file_size,
            'total_chunks': total_chunks,
            'received_chunks': [],
            'session_dir': session_dir,
            'created_at': time.time()
        }
        save_session_meta(session_id, session_meta)

        print(f"📝 Filename: {filename}")
        print(f"📊 Size: {file_size / (1024*1024):.2f}MB in {total_chunks} chunks")
        print(f"✅ Session: {session_id}")
        print(f"{'='*60}\n")

        return jsonify({'session_id': session_id, 'success': True})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-chunk', methods=['POST'])
@login_required
def upload_chunk():
    """Receive a chunk of a file."""
    try:
        session_id = request.form.get('session_id', '').strip()
        chunk_num = int(request.form.get('chunk_number', 0))
        total_chunks = int(request.form.get('total_chunks', 0))

        # Load session from file (works across Vercel invocations)
        session = load_session_meta(session_id)
        if not session:
            print(f"❌ Session not found: {session_id}")
            return jsonify({'error': 'Invalid session'}), 400

        if 'chunk' not in request.files:
            return jsonify({'error': 'No chunk data'}), 400

        chunk = request.files['chunk']
        session_dir = session['session_dir']

        # Save chunk
        chunk_path = os.path.join(session_dir, f"chunk_{chunk_num:05d}")
        chunk.save(chunk_path)

        # Update session metadata
        if chunk_num not in session['received_chunks']:
            session['received_chunks'].append(chunk_num)
            save_session_meta(session_id, session)

        chunk_size_mb = os.path.getsize(chunk_path) / (1024*1024)
        print(f"✅ Chunk {chunk_num}/{total_chunks} ({chunk_size_mb:.2f}MB)")

        return jsonify({'success': True})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def assemble_and_upload_chunks(session_id: str) -> str:
    """Assemble chunks and upload to Vercel Blob."""
    try:
        print(f"🔗 [CHUNKS] Assembling session {session_id}...")

        # Load session from file
        session = load_session_meta(session_id)
        if not session:
            raise Exception("Session not found")

        session_dir = session['session_dir']
        total_chunks = session['total_chunks']
        filename = session['filename']

        print(f"📊 Expected {total_chunks} chunks, received {len(session['received_chunks'])}")

        # Assemble file from chunks
        final_path = os.path.join(UPLOAD_FOLDER, f"assembled_{int(time.time())}_{secure_filename(filename)}")

        with open(final_path, 'wb') as final_file:
            for i in range(1, total_chunks + 1):
                chunk_path = os.path.join(session_dir, f"chunk_{i:05d}")
                if not os.path.exists(chunk_path):
                    raise Exception(f"Missing chunk {i}")

                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())

        final_size = os.path.getsize(final_path)
        print(f"✅ Assembled: {final_size / (1024*1024):.2f}MB")

        # Cleanup chunks and session metadata
        try:
            import shutil
            shutil.rmtree(session_dir)
            os.remove(get_session_meta_path(session_id))
        except:
            pass

        # Upload to Vercel Blob if token is available
        if BLOB_READ_WRITE_TOKEN and IS_VERCEL:
            print(f"📤 [BLOB] Uploading to Vercel Blob...")
            blob_url = upload_file_to_blob(final_path, filename)
            if blob_url:
                print(f"✅ Blob URL: {blob_url}")
                return blob_url

        # If no Blob, return local path (won't work on Vercel but useful for testing)
        return final_path

    except Exception as e:
        print(f"❌ Assembly failed: {str(e)}")
        raise


def upload_file_to_blob(file_path: str, filename: str) -> str:
    """Upload file to Vercel Blob."""
    try:
        if not BLOB_READ_WRITE_TOKEN:
            return None

        file_size = os.path.getsize(file_path)
        print(f"📊 File size: {file_size / (1024*1024):.2f}MB")

        # Generate blob filename
        blob_filename = f"uploads/{int(time.time())}-{secure_filename(filename)}"

        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Upload via REST API
        headers = {
            'Authorization': f'Bearer {BLOB_READ_WRITE_TOKEN}',
            'Content-Type': 'application/octet-stream'
        }

        blob_url = f"https://blob.vercelusercontent.com?filename={blob_filename}"
        print(f"📡 Uploading to: {blob_url}")

        response = requests.post(blob_url, headers=headers, data=file_data, timeout=300)

        if response.status_code == 200:
            result = response.json()
            url = result.get('url')
            print(f"✅ Uploaded: {url}")
            return url
        else:
            print(f"⚠️  Status {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"⚠️  Blob upload failed: {str(e)}")
        return None




@app.route('/api/transcribe', methods=['POST'])
@login_required
def transcribe():
    """Transcribe audio file and save to database."""
    try:
        print(f"\n{'='*60}")
        print(f"📡 [TRANSCRIBE START] Received request")
        print(f"Content-Length: {request.content_length}")
        print(f"{'='*60}")

        name = request.form.get('name', '').strip()
        session_id = request.form.get('session_id', '').strip()

        if not name:
            print("❌ No name provided")
            return jsonify({'error': 'Please enter a name for this transcription'}), 400

        temp_path = None

        try:
            # Check if using chunked upload or direct file upload
            if session_id:
                print(f"📦 Assembling chunks from session: {session_id}")
                print(f"🎯 Transcribing: {name}")
                print(f"{'='*60}")

                # Assemble chunks and upload to Blob
                temp_path = assemble_and_upload_chunks(session_id)

            elif 'file' in request.files:
                print(f"📁 Using direct file upload")
                file = request.files['file']

                if file.filename == '':
                    print("❌ Empty filename")
                    return jsonify({'error': 'No file selected'}), 400

                if not allowed_file(file.filename):
                    print(f"❌ File type not allowed: {file.filename}")
                    return jsonify({'error': f'File type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

                print(f"📝 File name: {file.filename}")
                print(f"🎯 Transcribing: {name}")
                print(f"{'='*60}")

                # Save temp file
                filename = secure_filename(file.filename)
                temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{int(time.time())}_{filename}")

                print(f"💾 Saving file to: {temp_path}")
                file.save(temp_path)
                file_size = os.path.getsize(temp_path)
                print(f"✅ File saved ({file_size / (1024*1024):.2f}MB)")

            else:
                print("❌ No file or blob_url provided")
                return jsonify({'error': 'No file uploaded'}), 400

            print(f"🔄 Starting transcription with Assembly AI...")
            # Transcribe with Assembly AI
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
            if temp_path:
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
