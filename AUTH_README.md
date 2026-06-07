# Authentication & Login

Your transcriber app now has login protection.

## Login Credentials

```
Username: admin
Password: Tesla123#
```

## What Changed

✅ **Login page** — Before accessing transcriptions, users must login  
✅ **Session management** — Sessions persist (stays logged in)  
✅ **Logout button** — Click logout button in top-right  
✅ **Protected APIs** — All transcription endpoints require login  
✅ **Username display** — Shows logged-in user in header  

## Files Added/Changed

- `login.html` — Beautiful login page ✨
- `app.py` — Added Flask-Login and authentication
- `index.html` — Added logout button and username display
- `requirements.txt` — Added Flask-Login and werkzeug

## How to Test Locally

1. Upgrade dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Stop old Flask server (Ctrl+C)

3. Start app:
   ```bash
   python app.py
   ```

4. Open: `http://localhost:8000`

5. You'll see login page:
   - Username: `admin`
   - Password: `Tesla123#`

6. After login, you can transcribe videos as before

## Changing the Password

Edit `app.py` line 33:
```python
ADMIN_PASSWORD_HASH = generate_password_hash('YOUR_NEW_PASSWORD')
```

Then restart the app.

## For Your Designer

Just give them:
- **URL**: `http://localhost:8000` (or your Vercel link)
- **Username**: `admin`
- **Password**: `Tesla123#`

They login and then transcribe videos like normal.

## Session Management

- Sessions last **30 days** by default
- Login with "Remember Me" enabled (it is by default)
- Click "Logout" button to end session
- Old sessions auto-expire after 30 days

## Security Notes

- Passwords are **hashed** using werkzeug
- Never expose password in code (use environment variables in production)
- All API endpoints check authentication
- Session tokens are secure and httponly cookies

## Production (Vercel)

When deploying:
1. Set environment variable:
   ```
   SECRET_KEY = some-random-string-here
   ```
2. Keep password in `app.py` or move to environment variable
3. Follow `VERCEL_DEPLOYMENT.md` guide

---

That's it! Your app is now protected. 🔒
