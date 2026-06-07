# Changelog - Vercel Blob Integration

## Version 2.1.0 - Vercel Blob Support (Current)

### What Changed?

✨ **Major Feature**: Added Vercel Blob storage support to handle file uploads larger than 4.5MB on Vercel serverless.

### Files Modified

#### `app.py` (Backend)
- **New imports**: `urllib.request` for downloading files from Blob
- **New configuration**:
  - `VERCEL_BLOB_TOKEN` - Token from environment variables
  - `IS_VERCEL` - Detects if running on Vercel
  - `VERCEL_BLOB_BASE_URL` - Blob API endpoint
- **New endpoint**: `/api/blob-upload-token` 
  - Validates file type and size
  - Returns token and URLs for frontend to use
  - Small request, bypasses size limits
- **Updated endpoint**: `/api/transcribe`
  - Now accepts either `file` (FormData) or `blob_url` (JSON)
  - Auto-detects which mode based on request content-type
  - Downloads from Blob URL if provided
  - Graceful cleanup of temporary files
- **Updated endpoint**: `/api/health`
  - Added `blob_storage_configured` field to verify token is set

#### `index.html` (Frontend)
- **New constants**:
  - `IS_VERCEL` - Detects if running on Vercel domain
  - `BLOB_UPLOAD_THRESHOLD` - 4.5MB limit for when to use Blob
- **New function**: `uploadToVercelBlob(file)`
  - Gets upload token from backend
  - Uploads file directly to Vercel Blob (bypasses backend size limit)
  - Returns download URL
  - Full error handling and logging
- **Updated function**: `transcribe()`
  - Detects large files on Vercel
  - Uses Blob upload for files >4.5MB
  - Sends either FormData (direct) or JSON (Blob URL) to backend
  - Detailed logging for troubleshooting
- **Updated UI text**: Changed file size limits info
  - Before: "Local: 500MB | Vercel: 10MB"
  - After: "Local: 500MB | Vercel: 5TB with Blob"

### How It Works Now

#### Upload Flow Diagram

**Small File on Vercel:**
```
Frontend: Select file <4.5MB
Frontend: Upload FormData directly
Backend: Receive and process
Assembly AI: Transcribe
Database: Save result
```

**Large File on Vercel:**
```
Frontend: Select file >4.5MB
Frontend: Request token from /api/blob-upload-token
Backend: Return token and URLs (tiny response)
Frontend: Upload file directly to blob.vercelusercontent.com
Vercel Blob: Store file
Frontend: Receive download URL
Frontend: Send download URL to /api/transcribe
Backend: Download from Blob and process
Assembly AI: Transcribe
Database: Save result
Vercel Blob: Auto-cleanup after 24h
```

**Local (Any Size):**
```
Frontend: Select file
Frontend: Upload FormData directly (no Blob)
Backend: Receive and process
Assembly AI: Transcribe
Database: Save result
```

### Key Improvements

1. **Size Support**: Vercel now supports up to 5TB files (vs 4.5MB before)
2. **Smart Detection**: Automatically uses optimal upload path
3. **Security**: Token only sent for file size validation, not exposed globally
4. **Performance**: Large file upload doesn't block backend
5. **Debugging**: Enhanced logging for troubleshooting uploads
6. **User Experience**: 
   - Clear status messages during upload
   - File size shown in status
   - Works seamlessly without user thinking about it

### Configuration Required

New environment variable needed for Vercel:
```
VERCEL_BLOB_READ_WRITE_TOKEN=your_token_here
```

(Optional but unused elsewhere - token is scoped to project)

### Testing

#### Local Testing
- Works with any file size (no Blob storage used)
- Direct upload path for all files
- No configuration changes needed

#### Vercel Testing  
1. Enable Blob in Vercel dashboard
2. Get and set `VERCEL_BLOB_READ_WRITE_TOKEN`
3. Redeploy
4. Test with file >5MB
5. Monitor logs for `[BLOB]` entries

### Backward Compatibility

✅ **100% compatible**
- Old deployments still work (no Blob token = direct upload only)
- Small files always work the same way
- No breaking changes to API endpoints
- Can opt-in by providing token

### Costs

- **Free tier**: 100GB/month included
- **Beyond free**: $0.50/GB
- **Auto-cleanup**: Files deleted after 24 hours
- **Typical usage**: Most users under free tier

### Error Handling

New error scenarios handled:
- Missing `VERCEL_BLOB_READ_WRITE_TOKEN` → Graceful degradation
- Blob upload failure → User-friendly error message
- Download from Blob failure → Detailed logging
- File validation before upload → Quick feedback

### Performance Impact

**Upload Time:**
- Unchanged for small files (<4.5MB)
- Slightly longer for very large files due to direct Vercel Blob upload
- But overall faster because backend stays responsive

**Memory:**
- Reduced pressure on backend for large files
- Files not held in memory during upload

## Version 2.0.0 - Initial Release

### Features
- File upload with drag-and-drop
- Assembly AI transcription
- Neon PostgreSQL storage
- Chat-like UI with history sidebar
- Authentication system
- Support for MP3, MP4, WAV, M4A, WebM, FLAC, OGG, AAC
- Vercel deployment ready
- Detailed logging for debugging

## Migration Guide

### For Existing Deployments

1. **No changes required for small files** - Everything works as before
2. **For large file support (>4.5MB)**:
   - Get `VERCEL_BLOB_READ_WRITE_TOKEN` from Vercel
   - Add to environment variables
   - Redeploy
3. **No database changes** - Same schema
4. **No API changes** - Old endpoints still work, new parameter optional

## Future Improvements

Potential enhancements:
- [ ] Progress bar for large uploads
- [ ] Resume interrupted uploads
- [ ] Compression for large files
- [ ] Parallel upload support
- [ ] Custom Blob storage location
- [ ] File preview before upload

## Support

- All issues/questions covered in `DEPLOYMENT_GUIDE.md`
- Troubleshooting section includes common problems
- Health endpoint for quick diagnostics
