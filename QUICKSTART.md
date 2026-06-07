# Quick Start (5 minutes)

## Step 1: Prerequisites ✅

Make sure you have:
- Python 3.8+
- FFmpeg installed

Check:
```bash
python --version
ffmpeg -version
```

If FFmpeg is missing:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

## Step 2: Setup 🚀

```bash
# Navigate to project
cd /path/to/transcribe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Get OpenAI Key 🔑

1. Visit https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (shown only once)

## Step 4: Configure

```bash
# Create .env file
cp .env.example .env

# Edit .env and paste your API key:
# OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

Edit the `.env` file:
- Open it in your editor
- Paste your OpenAI key where it says `your-openai-api-key-here`
- Save

## Step 5: Run 🎬

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

## Step 6: Use 🎥

Open browser to: **http://localhost:5000**

Done! Paste a YouTube URL and click "Transcribe".

---

## Cost Estimate

- ~$0.01 per 1-minute video
- ~$0.06 per 10-minute video
- ~$0.36 per 1-hour video

OpenAI gives you $5 free credit when you sign up (enough for ~14 hours of transcription).

## Troubleshooting

**"Command not found: python"**
- You might need `python3` instead

**"ModuleNotFoundError"**
- Make sure you activated the venv: `source venv/bin/activate`

**"OpenAI API Error"**
- Check your key is pasted correctly in `.env`
- Make sure it starts with `sk-`

**"FFmpeg not found"**
- Install it (see Step 1 above)
- Restart your terminal after installing

**Still stuck?** Check the full README.md for more details.
