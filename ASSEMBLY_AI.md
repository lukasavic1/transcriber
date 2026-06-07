# Assembly AI Transcription

Your app now uses **Assembly AI** instead of yt-dlp. This solves all YouTube bot detection issues.

## Why Assembly AI?

✅ **No YouTube bot detection** — Assembly AI handles YouTube directly  
✅ **No FFmpeg needed** — No local dependencies  
✅ **Fully automated** — Just pass a URL, get transcript  
✅ **Works everywhere** — Local dev, Vercel, doesn't matter  
✅ **Cheap** — ~$0.49/hour of audio (free tier: 1 hour/month)  
✅ **Reliable** — No cookies, no browser extensions needed  

## Setup

### 1. Get Your API Key (Already Done!)

You already have: `ASSEMBLY_AI_API_KEY=c1d8d829f941465abff68ad4546947ae`

If you need a new one:
1. Go to **https://www.assemblyai.com**
2. Sign up (free)
3. Go to Settings → API Token
4. Copy your key
5. Add to `.env`: `ASSEMBLY_AI_API_KEY=your-key`

### 2. How It Works

```
Your App
   ↓
   → Assembly AI API
      ↓
      → Assembly AI downloads from YouTube (using their trusted IP)
      ↓
      → Assembly AI transcribes with AI
      ↓
   ← Returns transcript text
   ↓
Your Database
```

**No YouTube bot detection because Assembly AI is a legitimate service.**

## Testing Locally

```bash
# 1. Make sure you have the API key in .env
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py

# 4. Go to http://localhost:8000
# 5. Login: admin / Tesla123#
# 6. Try transcribing a YouTube video
```

The first transcription might take 1-3 minutes while Assembly AI processes it. That's normal.

## Pricing

**Assembly AI:**
- Free tier: 1 hour/month
- Paid: ~$0.49/hour of audio
- No YouTube video downloads = much faster processing

**vs Whisper:**
- ~$0.36/hour but requires downloading video first

## What's Different?

### Before (yt-dlp)
1. Download video from YouTube ❌ (bot detection)
2. Convert to MP3 (FFmpeg needed)
3. Send to Whisper API
4. Get transcript

### Now (Assembly AI)
1. Send YouTube URL to Assembly AI ✅
2. Assembly AI handles everything
3. Get transcript back
4. Save to database

**Much simpler, no bot detection, works everywhere.**

## Vercel Deployment

No changes needed! Just make sure `ASSEMBLY_AI_API_KEY` is set in Vercel environment variables:

1. Go to Vercel dashboard
2. Project Settings → Environment Variables
3. Add: `ASSEMBLY_AI_API_KEY=your-key`
4. Redeploy

## If Transcription Takes Too Long

Assembly AI processes videos in ~1-3 minutes depending on length.

Progress is shown in the UI as "⏳ Waiting for transcription to complete..."

Max timeout: **10 minutes** (plenty for most videos)

## Changing API Key Later

1. Update `.env` with new key
2. Restart Flask (local) or redeploy (Vercel)
3. Done!

## Troubleshooting

**"Failed to transcribe: ..."**
- Check API key is correct
- Make sure URL is a valid YouTube link
- Check you have free tier hours left (or paid plan active)

**"Transcription timed out after 10 minutes"**
- Very rare
- Usually means video is extremely long
- Increase timeout in app.py line 84

**"401 Unauthorized"**
- API key is wrong
- Check `.env` file

## Monitoring Usage

Go to **https://www.assemblyai.com** → Dashboard to see:
- How many hours you've used
- Remaining free tier hours
- Billing info

---

You're all set! No more YouTube hassles. 🚀
