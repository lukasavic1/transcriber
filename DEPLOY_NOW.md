# Deploy to Vercel NOW (With Your Neon Database)

You have everything ready! Just 3 steps to go live.

## Step 1: Create a Secret Key

Generate a random secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output (e.g., `eJ9kL_2xP8q...`)

## Step 2: Deploy on Vercel

1. Go to **https://vercel.com/new**
2. Click **"Import Git Repository"**
3. Search for `transcriber` and select it
4. Click **Import**
5. Set **Environment Variables**:
   ```
   OPENAI_API_KEY = (your OpenAI API key)
   DATABASE_URL = postgresql://neondb_owner:npg_0aHiTyLDSYX6@ep-old-waterfall-aptyauf0-pooler.c-7.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require
   SECRET_KEY = (paste the secret key you generated above)
   ```
6. Click **Deploy**

Done! Your app is live! 🚀

Wait 2-3 minutes for deployment to finish, then you'll get a URL like:
```
https://your-project-name.vercel.app
```

## Step 3: Test It

1. Visit your Vercel URL
2. Login with:
   - **Username**: `admin`
   - **Password**: `Tesla123#`
3. Try transcribing a YouTube video
4. Refresh the page — data should persist!

---

## What You Have

✅ **Authentication** — Protected with username/password  
✅ **Database** — Neon PostgreSQL (data persists forever)  
✅ **Videos** — YouTube download + Whisper transcription  
✅ **History** — All transcriptions saved and browsable  
✅ **Deployed** — Live on Vercel serverless  

## Share with Your Designer

Once deployed, share this info:
```
URL: https://your-project.vercel.app
Username: admin
Password: Tesla123#
```

They can start transcribing immediately!

---

## Troubleshooting

**"Database Error"**
- Check DATABASE_URL is pasted correctly
- Make sure no extra spaces

**"Connection Refused"**
- Wait 2-3 minutes for Vercel deployment
- Check Neon status at console.neon.tech

**"YouTube Download Failed"**
- Try a different video
- Check your internet connection
- YouTube might be blocking temporarily

---

## Changing Password Later

Edit `app.py` line 33:
```python
ADMIN_PASSWORD_HASH = generate_password_hash('NEW_PASSWORD')
```

Then push to GitHub (Vercel redeploys automatically).

---

## Monitoring Your Database

View transcriptions in Neon:
1. Go to **https://console.neon.tech**
2. Select your project
3. Click **SQL Editor**
4. Run:
   ```sql
   SELECT * FROM transcriptions;
   ```

---

That's it! You're live! 🎉

Questions? Check `README.md` or `VERCEL_DEPLOYMENT.md`
