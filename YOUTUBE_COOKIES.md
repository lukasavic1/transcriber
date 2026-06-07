# YouTube Cookies for Vercel (If Needed)

If you get "Sign in to confirm you're not a bot" error on Vercel, you may need to provide YouTube cookies.

## Quick Fix First

Try this:
1. Update to latest yt-dlp: `pip install --upgrade yt-dlp`
2. Restart Flask
3. Try a different YouTube video

## If That Doesn't Work

YouTube sometimes requires cookies on serverless platforms. Here's how:

### Option 1: Use Cookie Extension (Easiest)

1. Install a browser extension:
   - **Firefox**: [Get cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
   - **Chrome**: [Get cookies.txt](https://chrome.google.com/webstore/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkogohlkj)

2. Visit **https://www.youtube.com** while logged in

3. Click the extension icon → Export as cookies.txt

4. Place `cookies.txt` in your project folder

5. Update `app.py` line 85:
   ```python
   'cookiefile': 'cookies.txt',
   ```

6. Restart Flask and try again

### Option 2: Provide Cookies Manually

In your `.env` add:
```
YOUTUBE_COOKIES=your-cookies-here
```

Then in `app.py`:
```python
if os.getenv('YOUTUBE_COOKIES'):
    with open('cookies.txt', 'w') as f:
        f.write(os.getenv('YOUTUBE_COOKIES'))
    ydl_opts['cookiefile'] = 'cookies.txt'
```

### Option 3: Use Built-in Transcripts (No Download)

If YouTube videos have captions, use YouTube's built-in transcripts instead of downloading audio.

---

## For Vercel Deployment

If using cookies on Vercel:

1. Add environment variable in Vercel:
   ```
   YOUTUBE_COOKIES = (your-cookies-from-txt-file)
   ```

2. Update `app.py` to write cookies from env var

3. Redeploy

---

## Testing Locally with Same Database

1. Make sure you're using Neon database (.env has DATABASE_URL)
2. Test locally: `python app.py`
3. If it works locally with cookies, same setup works on Vercel

---

## Alternative: Use Different Service

If YouTube keeps blocking, consider:
- **AssemblyAI** (free tier for testing)
- **Rev.com** API
- **Whisper OpenAI** via file upload (what you're doing now)

---

For now, try the improved headers first (already updated in code).
If that doesn't work, use cookies method above.
