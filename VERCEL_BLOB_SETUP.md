# Vercel Blob Storage Setup Guide

This guide explains how to set up Vercel Blob storage for handling file uploads larger than 4.5MB on Vercel.

## Why Vercel Blob?

- **Problem**: Vercel's serverless functions have a 4.5MB request body limit
- **Solution**: Upload large files directly to Vercel Blob storage, then process them
- **Benefit**: Supports files up to 5TB
- **Cost**: Free tier includes 100GB/month

## Setup Steps

### 1. Create a Vercel Blob Token

1. Go to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to **Settings → Tokens**
3. Click **Create Token**
4. Choose:
   - **Token name**: `VERCEL_BLOB_READ_WRITE_TOKEN`
   - **Scope**: Select your project
   - **Expiration**: Set to never expire (or your preference)
5. Click **Create**
6. **Copy the token value** (you won't see it again)

### 2. Add Token to Your Project

#### For Local Development:
Add to your `.env` file:
```
VERCEL_BLOB_READ_WRITE_TOKEN=your_token_here
```

#### For Vercel Deployment:
1. Go to your project in the [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Settings → Environment Variables**
3. Add new variable:
   - **Name**: `VERCEL_BLOB_READ_WRITE_TOKEN`
   - **Value**: Paste your token
   - **Environments**: Select `Production` (or all)
4. Click **Save**
5. Redeploy your project

### 3. How It Works

#### On Local Development:
- Files are uploaded directly to the Flask backend
- No Blob storage is used (files stay under 4.5MB limit locally)

#### On Vercel:
- **Small files (<4.5MB)**: Uploaded directly to Flask backend
- **Large files (>4.5MB)**: 
  1. Frontend detects large file size
  2. Uploads file to Vercel Blob
  3. Gets back a Blob URL
  4. Sends Blob URL to Flask backend (tiny request)
  5. Backend downloads from Blob URL
  6. Transcribes with Assembly AI
  7. Blob file is automatically cleaned up after 24 hours

## Testing

### 1. Check Configuration:
```bash
curl https://your-vercel-app.vercel.app/api/health
# Look for "blob_storage_configured": true
```

### 2. Test Large File Upload:
1. Go to your app
2. Login with credentials
3. Select a file larger than 5MB
4. Check browser console for logs:
   - Should see: `[CLIENT] File is X.XXMB - using Vercel Blob`
   - Should see: `[CLIENT] Uploading to Blob storage...`

### 3. Check Server Logs:
In Vercel dashboard, go to **Logs → Function Logs** and look for:
```
📤 [BLOB] Starting upload to Vercel Blob...
✅ Uploaded to Blob! URL: https://blob.vercelusercontent.com/...
```

## Troubleshooting

### Token Not Set
**Error**: `Blob upload failed: Invalid token`
- **Fix**: Make sure token is properly set in Vercel environment variables
- Redeploy after setting variables

### Upload Still Fails
**Error**: `413 Request Entity Too Large`
- **Cause**: Token not configured, so large files bypass Blob and hit request limit
- **Fix**: Check that `VERCEL_BLOB_READ_WRITE_TOKEN` is set in Vercel environment

### Files Not Being Deleted
- Vercel Blob automatically deletes files after 24 hours
- This is by design (backup mechanism)
- No manual cleanup needed

## File Size Limits

| Environment | Direct Upload | With Blob |
|------------|---------------|-----------|
| Local | 500MB | N/A (not needed) |
| Vercel | 4.5MB | 5TB |

## Security

- **Token**: Keep your `VERCEL_BLOB_READ_WRITE_TOKEN` secret
- **Never** commit it to git (should be in `.env` which is gitignored)
- **Only** stored in Vercel's encrypted environment variables
- **Scope**: Token is scoped to your project only

## Cost

- **Free tier**: 100GB per month
- **Beyond free**: $0.50 per GB
- **Automatic cleanup**: Files deleted after 24 hours free

## References

- [Vercel Blob Documentation](https://vercel.com/docs/storage/vercel-blob)
- [Vercel Blob Token Documentation](https://vercel.com/docs/storage/vercel-blob/tokens-and-access-control)
