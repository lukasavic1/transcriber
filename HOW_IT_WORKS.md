# How the Transcription Works

## The Smart Approach

We use **yt-dlp + Assembly AI** together for the best of both worlds:

```
YouTube Video
    ↓
yt-dlp (extracts audio stream URL)
    ↓
Audio URL (like: https://rr1---sn-xxx.googlevideo.com/...)
    ↓
Assembly AI (handles the download & transcription)
    ↓
Transcript Text
    ↓
Your Database
```

## Why This Works

### ✅ yt-dlp extracts the URL
- Fast (no actual download)
- Just metadata extraction
- No bot detection from YouTube
- Gets the direct audio stream link

### ✅ Assembly AI transcribes
- Downloads the audio from the URL
- YouTube trusts Assembly AI's IP
- Handles the transcription
- No bot detection issues
- Works on Vercel

### ✅ No Restrictions
- No cookies needed
- No browser extensions
- No manual intervention
- Fully automated

## The Flow

1. **You paste:** YouTube URL
2. **yt-dlp does:** Extract audio URL (2-3 seconds)
3. **Assembly AI does:** Download & transcribe (1-3 minutes)
4. **Result:** Transcript saved to database

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask
python app.py

# Login and transcribe!
```

## Vercel Deployment

Same code works on Vercel. No changes needed:
1. Set environment variables (API keys)
2. Redeploy
3. Done!

---

## Why Not Just yt-dlp?

yt-dlp alone gets bot-blocked on Vercel. By extracting just the URL and letting Assembly AI handle the download, we bypass all restrictions while keeping yt-dlp (the standard tool).

It's the cleanest solution! 🚀
