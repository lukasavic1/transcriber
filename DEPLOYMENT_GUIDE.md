# Complete Deployment Guide with Vercel Blob

This guide walks you through deploying the transcription app with Vercel Blob support for handling files larger than 4.5MB.

## Architecture Overview

### How It Works

**Small Files (<4.5MB) - Local & Vercel:**
```
User selects file → Upload to Flask → Transcribe with Assembly AI → Save to DB
```

**Large Files (>4.5MB) - Vercel Only:**
```
User selects file → 
  Request token from Flask → 
  Upload directly to Vercel Blob → 
  Get download URL → 
  Send URL to Flask → 
  Flask downloads and transcribes → 
  Save to DB
```

## Prerequisites

You need:
1. Vercel account with a project deployed
2. Neon PostgreSQL database URL (DATABASE_URL)
3. Assembly AI API key (ASSEMBLY_AI_API_KEY)
4. A Vercel Blob token (VERCEL_BLOB_READ_WRITE_TOKEN)

## Step 1: Get Your Vercel Blob Token

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click on your **transcribe project**
3. Navigate to **Settings → Storage → Blob**
4. Click **Create Database** (if not already created)
5. Once created, go to **Settings → Tokens**
6. Click **Create Token**
7. Name it: `VERCEL_BLOB_READ_WRITE_TOKEN`
8. Scope: Select your **transcribe** project
9. Expiration: Choose based on your preference (or never)
10. **Copy the token value** (shown only once!)

**Save this token somewhere safe!**

## Step 2: Update Environment Variables

### Local Development

Add to your `.env` file:
```
ASSEMBLY_AI_API_KEY=your_assembly_ai_key
DATABASE_URL=your_neon_database_url
SECRET_KEY=your_secret_key
VERCEL_BLOB_READ_WRITE_TOKEN=your_blob_token
```

### Vercel Production

1. Go to your project in [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Settings → Environment Variables**
3. Add a new variable:
   - **Name**: `VERCEL_BLOB_READ_WRITE_TOKEN`
   - **Value**: Paste your token from Step 1
   - **Environments**: Select `Production`
4. Click **Save**
5. Go to **Deployments**
6. Click the three dots on the latest deployment
7. Select **Redeploy** (this ensures the new env var is used)

## Step 3: Deploy Your Code

### Option A: Git Push
```bash
cd /path/to/transcribe
git add .
git commit -m "Add Vercel Blob support for large file uploads"
git push origin main
```

Vercel will automatically deploy. Watch the deployment logs to ensure it succeeds.

### Option B: Deploy from Dashboard
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your **transcribe** project
3. Click **Deployments**
4. Find the latest deployment and click **Redeploy**

## Step 4: Verify Deployment

### Check Health Endpoint

```bash
curl https://your-app.vercel.app/api/health
```

You should see:
```json
{
  "status": "ok",
  "max_file_size_mb": 500,
  "environment": "vercel",
  "blob_storage_configured": true
}
```

If `blob_storage_configured` is `false`, the token isn't set. Go back to Step 2 and redeploy.

## Step 5: Test Large File Upload

### Prepare Test File

Create a test file larger than 5MB:
```bash
# Create a 10MB test file
dd if=/dev/urandom of=test_audio.mp3 bs=1M count=10
```

### Test the Upload

1. Open your app at `https://your-app.vercel.app`
2. Login with your credentials (admin / Tesla123#)
3. Click "Upload" and select your 10MB test file
4. Enter a name like "Test Large File"
5. Click "Transcribe"
6. **Watch the browser console** for logs:

**You should see:**
```
[CLIENT] File is 10.XX MB - using Vercel Blob
[CLIENT] Got upload token, uploading file to: https://blob.vercelusercontent.com?filename=...
[CLIENT] Blob upload complete: https://blob.vercelusercontent.com/...
[CLIENT] Sending POST request to /api/transcribe
```

### Check Server Logs

In Vercel Dashboard:
1. Go to your project
2. Click **Logs → Function Logs**
3. Look for entries with `[BLOB]` tag

**You should see:**
```
📋 [BLOB] Generating upload token...
✅ Upload token generated
📥 Downloading from: https://blob.vercelusercontent.com/...
✅ Downloaded (X.XXMB)
✅ Transcription complete!
```

## Troubleshooting

### Problem: "blob_storage_configured: false"

**Cause**: `VERCEL_BLOB_READ_WRITE_TOKEN` environment variable not set

**Fix**:
1. Go to Vercel Dashboard → Your Project → Settings
2. Check Environment Variables
3. Add `VERCEL_BLOB_READ_WRITE_TOKEN` if missing
4. Redeploy the project

### Problem: Upload fails with 413 error

**Cause**: File is large but Blob token isn't being used

**Fix**:
1. Check that you're on Vercel (not localhost)
2. Verify `blob_storage_configured: true` in /api/health
3. Check file size is actually >4.5MB
4. Look at Vercel function logs for specific error

### Problem: Upload succeeds but transcription fails

**Cause**: Assembly AI can't process the file from Blob URL

**Fix**:
1. Check server logs for `[BLOB]` entries
2. Verify the download URL is accessible
3. Check Assembly AI API key is valid
4. Try with a smaller test file first

### Problem: "Failed to get upload token"

**Cause**: Backend endpoint error

**Fix**:
1. Check Vercel function logs
2. Verify DATABASE_URL is set (some endpoints need it)
3. Verify authentication is working (can you login?)

### Problem: Large file upload is slow

**Normal behavior**: Uploading 100MB+ files takes time depending on connection speed
- 5MB: ~1 second
- 50MB: ~10-15 seconds
- 100MB: ~20-30 seconds

This is uploading directly to Vercel Blob, so speed depends on your internet connection.

## What's New in This Version?

✨ **Features**:
- Support for files up to 5TB on Vercel (was 4.5MB)
- Automatic detection of large files on Vercel
- Smart fallback to direct upload for small files
- Progress feedback during upload
- Detailed logging for debugging

🔧 **Technical**:
- New endpoint: `/api/blob-upload-token`
- Updated endpoint: `/api/transcribe` now accepts `blob_url` parameter
- Frontend automatically chooses optimal upload path
- Uses Vercel Blob REST API with Authorization header

## File Size Guide

| Scenario | Max Size |
|----------|----------|
| Local development | 500MB |
| Vercel (direct upload) | 4.5MB |
| Vercel (with Blob) | 5TB* |

*Practical limit depends on your Vercel Blob quota and timeout (300s free tier)

## Cost Considerations

### Vercel Blob Pricing
- **Free tier**: 100GB/month free
- **Per GB**: $0.50 after free tier
- **Auto-cleanup**: Files automatically deleted after 24 hours

### Your Typical Usage
If you transcribe:
- 10 files of 50MB each = 500MB/month
- **Cost**: FREE (within 100GB/month limit)

## Next Steps

1. ✅ Get and save your Blob token
2. ✅ Add token to Vercel environment variables
3. ✅ Redeploy your project
4. ✅ Test with a large file
5. ✅ Monitor first few uploads in Vercel logs
6. ✅ Start using with real files!

## Support

If you encounter issues:
1. Check Vercel function logs for errors
2. Verify all environment variables are set
3. Test health endpoint to confirm Blob is configured
4. Check browser console for client-side errors
5. Try the test steps with a fresh 5-10MB file

## Additional Resources

- [Vercel Blob Documentation](https://vercel.com/docs/storage/vercel-blob)
- [Assembly AI API Documentation](https://www.assemblyai.com/docs)
- [Vercel Environment Variables Guide](https://vercel.com/docs/projects/environment-variables)
