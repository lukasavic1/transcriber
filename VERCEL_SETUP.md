# Deploy to Vercel

Your app is ready to deploy! Here's how:

## Step 1: Push to GitHub (if not already)

```bash
git add .
git commit -m "Ready for Vercel deployment"
git push
```

## Step 2: Deploy on Vercel

1. Go to **https://vercel.com/new**
2. Click **"Import Git Repository"**
3. Select your `transcriber` repo
4. Click **Import**

## Step 3: Set Environment Variables

In Vercel dashboard, go to **Settings → Environment Variables** and add:

```
ASSEMBLY_AI_API_KEY = c1d8d829f941465abff68ad4546947ae
DATABASE_URL = postgresql://neondb_owner:npg_0aHiTyLDSYX6@ep-old-waterfall-aptyauf0-pooler.c-7.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require
SECRET_KEY = (generate a random string, e.g., $(python -c "import secrets; print(secrets.token_urlsafe(32))"))
```

## Step 4: Deploy

Click **Deploy** and wait 3-5 minutes for it to build and deploy.

You'll get a URL like: `https://transcriber-xyz.vercel.app`

## Step 5: Test

1. Visit your Vercel URL
2. Login: `admin` / `Tesla123#`
3. Try transcribing a video!

---

## How It Works on Vercel

- `vercel.json` — Tells Vercel how to build and run the app
- `build.sh` — Installs FFmpeg (needed for audio download)
- `api/index.py` — Entry point for Vercel's serverless functions
- `app.py` — Your Flask app (handles all the logic)

Everything else is the same as local development!

---

## Troubleshooting

### "Build failed: FFmpeg not found"
- Vercel might not support custom build scripts yet
- Fallback: Remove the `build.sh` approach and use a buildpack
- See alternative below

### "Function timed out"
- Vercel serverless has 10 second timeout by default
- Long transcriptions might timeout
- Workaround: Increase timeout in `vercel.json` (max 900 seconds)

### "Database connection refused"
- Make sure `DATABASE_URL` is set correctly in Vercel environment
- Check it matches your Neon connection string exactly

---

## Alternative: If FFmpeg Build Fails

If Vercel can't install FFmpeg, you can use an external audio conversion service:

1. Keep yt-dlp to extract audio URL
2. Use Assembly AI to download and transcribe directly (might work better than before)

Update `app.py` to use audio URL instead of file:

```python
# Instead of downloading, just get the URL
audio_url = get_audio_url_from_youtube(youtube_url)
transcript = transcribe_with_assembly_ai_url(audio_url)
```

Let me know if you need this fallback!

---

## Your Deployment is Ready!

Push to GitHub and Vercel will auto-deploy on every commit. 🚀

Questions? Check `VERCEL_DEPLOYMENT.md` or `HOW_IT_WORKS.md`
