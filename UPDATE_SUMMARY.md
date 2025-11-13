# Update Summary - Debug Endpoint & Code Cleanup

**Date**: November 12, 2024  
**Changes**: Added debug endpoint, removed deprecated endpoints, configured static file serving

## Changes Made

### 1. Static File Serving Configuration ✅

**File**: `/app/main.py`

- Added `StaticFiles` import from `fastapi.staticfiles`
- Added `os` import for path manipulation
- Mounted static files at `/static` serving from `public/` directory
- Static files are only mounted if the directory exists

**Created Directory**: `/home/chris/projects/live/image_verifier/public/debug/`

### 2. New Debug Endpoint ✅

**File**: `/app/api/endpoints/debug.py` (NEW)

Created three debug endpoints:

#### POST `/api/v1/debug/pdf-to-image`
- Accepts PDF or image URL
- Converts to image using existing `load_image_from_bytes()` function
- Saves to `public/debug/` with timestamp and unique ID
- Returns:
  - Static URL (`/static/debug/filename.jpg`)
  - Full URL (`http://104.167.8.60:27000/static/debug/filename.jpg`)
  - Image dimensions and file size
  - Whether input was PDF or image

#### GET `/api/v1/debug/list-debug-images`
- Lists all saved debug images
- Shows filename, URLs, size, and modification time
- Sorted by newest first

#### DELETE `/api/v1/debug/clear-debug-images`
- Deletes all debug images from `public/debug/`
- Returns count of deleted files

### 3. Removed Deprecated Endpoints ✅

**File**: `/app/api/endpoints/passport.py`

Removed:
- `POST /verify` (legacy combined file/URL endpoint)
- `POST /extract-mrz` (legacy combined file/URL endpoint)

Kept:
- `POST /verify/upload` - File upload only
- `POST /verify/url` - URL only
- `POST /extract-mrz/upload` - File upload only
- `POST /extract-mrz/url` - URL only

**File**: `/app/api/endpoints/photo.py`

Removed:
- `POST /verify` (legacy combined file/URL endpoint)

Kept:
- `POST /verify/upload` - File upload only
- `POST /verify/url` - URL only

### 4. Registered Debug Router ✅

**File**: `/app/main.py`

- Imported debug router: `from app.api.endpoints import photo, passport, debug`
- Added router: `app.include_router(debug.router, prefix="/api/v1")`

## API Changes

### Removed Endpoints (Breaking Changes)

❌ **Removed**:
- `POST /api/v1/passport/verify` (deprecated)
- `POST /api/v1/passport/extract-mrz` (deprecated)
- `POST /api/v1/photo/verify` (deprecated)

✅ **Use Instead**:
- `POST /api/v1/passport/verify/upload` - For file uploads
- `POST /api/v1/passport/verify/url` - For URLs
- `POST /api/v1/passport/extract-mrz/upload` - For file uploads
- `POST /api/v1/passport/extract-mrz/url` - For URLs
- `POST /api/v1/photo/verify/upload` - For file uploads
- `POST /api/v1/photo/verify/url` - For URLs

### New Endpoints

✅ **Added**:
- `POST /api/v1/debug/pdf-to-image` - Convert and save PDF/image for inspection
- `GET /api/v1/debug/list-debug-images` - List saved debug images
- `DELETE /api/v1/debug/clear-debug-images` - Clear all debug images

## Testing the Debug Endpoint

Test with your problematic PDF:

```bash
curl -X POST "http://104.167.8.60:27000/api/v1/debug/pdf-to-image" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "YOUR_PDF_URL"
  }'
```

The response will include:
- `full_url`: Open this in browser to see the converted image
- `image_info`: Dimensions, file size, channels
- `was_pdf`: Confirms it was a PDF file

## Service Status

✅ Service restarted and running on `http://104.167.8.60:27000`  
✅ All changes active  
✅ Static file serving enabled  
✅ New debug endpoints available  
✅ Deprecated endpoints removed  

## Documentation

Created:
- `/DEBUG_ENDPOINT.md` - Comprehensive debug endpoint usage guide with examples

Updated:
- Service includes all new endpoints in Swagger UI at `http://104.167.8.60:27000/docs`

## Next Steps

1. **Test the debug endpoint** with your PDF to see the converted image
2. **Analyze the image** to understand why document detection might be failing
3. **Fix scan detection logic** in `icao_validator.py` based on findings
   - Current issue: White PDF borders have low std dev (0.00), incorrectly detected as PHOTO
   - Possible fixes:
     - Invert threshold logic (low std dev = scan)
     - Use different detection method (check for PDF flag)
     - Adjust border sampling areas

## Files Modified

- `/app/main.py` - Added static files and debug router
- `/app/api/endpoints/debug.py` - **NEW** debug endpoints
- `/app/api/endpoints/passport.py` - Removed deprecated endpoints
- `/app/api/endpoints/photo.py` - Removed deprecated endpoint
- `/DEBUG_ENDPOINT.md` - **NEW** documentation
- `/public/debug/` - **NEW** directory for debug images

## Breaking Changes Notice

⚠️ **Important**: The legacy combined endpoints (`POST /verify` and `POST /extract-mrz`) have been removed. 

If you have existing clients using these endpoints, update them to use the new `/upload` or `/url` variants:

**Before** (deprecated, no longer works):
```bash
# This will now return 404
POST /api/v1/passport/verify
```

**After** (current):
```bash
# For file uploads
POST /api/v1/passport/verify/upload

# For URLs
POST /api/v1/passport/verify/url
```

See `TEST_EXAMPLES.md` for complete updated API examples.
