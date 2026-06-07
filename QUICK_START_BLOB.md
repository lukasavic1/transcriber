# Quick Start: Vercel Blob for Large Files

**TL;DR**: Setup Vercel Blob in 5 minutes to support files >5MB.

## Step 1: Get Token (2 min)
1. Open [Vercel Dashboard](https://vercel.com/dashboard) → Transcribe project
2. **Settings → Storage → Blob** → Create Database (if needed)
3. **Settings → Tokens** → Create Token
4. Name: `VERCEL_BLOB_READ_WRITE_TOKEN`
5. Scope: Select **transcribe** project
6. **Copy the token**

## Step 2: Add to Vercel (2 min)
1. **Settings → Environment Variables**
2. **New Variable:**
   - Name: `VERCEL_BLOB_READ_WRITE_TOKEN`
   - Value: Paste token from Step 1
   - Environments: **Production**
3. **Save**
4. **Deployments** → **Redeploy** latest deployment

## Step 3: Test (1 min)
1. Create a test file: `dd if=/dev/urandom of=test.mp3 bs=1M count=10`
2. Go to app, login, upload `test.mp3`
3. Watch browser console (F12) for: `[CLIENT] Using Vercel Blob`
4. Check Vercel Logs for: `[BLOB] Upload token generated`

## That's It! ✅

Your app now supports up to **5TB files** on Vercel.

## Quick Diagnostics

**Health check:**
```bash
curl https://your-app.vercel.app/api/health | grep blob_storage_configured
```

Should show: `"blob_storage_configured": true`

**Test logs:**
- Browser: F12 → Console → Look for `[CLIENT]` messages
- Vercel: Dashboard → Logs → Function Logs → Look for `[BLOB]` messages

## Troubleshooting in 30 Seconds

| Problem | Check |
|---------|-------|
| blob_storage_configured: false | Token not set in env vars. Redeploy after setting it |
| 413 error | Token not working. Generate new token in Vercel |
| Slow upload | Normal. Speed depends on your internet. 100MB takes ~30s |
| Upload succeeds, transcription fails | Check Assembly AI logs or file might be corrupted |

## Files Sizes

| Size | Works Where |
|------|------------|
| <4.5MB | Everywhere (local, Vercel, Blob) |
| 4.5-500MB | Local only, Vercel needs Blob |
| 500MB-5TB | Vercel with Blob only |

## Code Changes

What was added to your code:
- **New endpoint:** `/api/blob-upload-token` (returns token for frontend)
- **Updated endpoint:** `/api/transcribe` (accepts `blob_url` parameter)
- **Frontend:** Auto-detects large files and uses Blob
- **UI:** Shows "5TB with Blob" instead of "10MB"

Everything else works exactly the same.

## Questions?

- Read `DEPLOYMENT_GUIDE.md` for detailed instructions
- Read `CHANGELOG.md` for technical details
- Check Vercel docs for Blob: https://vercel.com/docs/storage/vercel-blob

---

**Created:** June 2024  
**Status:** Ready for deployment  
**Next:** Deploy to Vercel!
