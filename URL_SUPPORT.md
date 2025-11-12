# URL Support - Feature Update

## Overview
Both photo and passport verification endpoints now support **image URLs** in addition to file uploads.

## What Changed

### 1. **Request Models Updated** (`app/models/request.py`)
- Added `image_url` field to base `VerificationRequest` model
- Accepts `HttpUrl` type (validated URL format)
- Optional field - provide either file OR URL

### 2. **Image Utilities Enhanced** (`app/utils/image_utils.py`)
- New function: `download_image_from_url(url, timeout=30)`
- Validates content-type is an image
- Enforces 10MB size limit
- Handles timeouts and network errors
- Returns image bytes for processing

### 3. **Photo Endpoint Updated** (`app/api/endpoints/photo.py`)
- `/api/v1/verify/photo` now accepts `image_url` parameter
- Validates that only file OR URL is provided (not both)
- Downloads image if URL provided
- All existing validations apply to URL images

### 4. **Passport Endpoints Updated** (`app/api/endpoints/passport.py`)
- `/api/v1/verify/passport` now accepts `image_url` parameter
- `/api/v1/extract/mrz` now accepts `image_url` parameter
- Same validation logic as photo endpoint

## API Usage

### Method 1: File Upload (existing)
```bash
curl -X POST "http://localhost:8000/api/v1/verify/photo" \
  -H "X-API-Key: your-key" \
  -F "file=@photo.jpg" \
  -F "include_detailed_metrics=true"
```

### Method 2: URL (NEW)
```bash
curl -X POST "http://localhost:8000/api/v1/verify/photo" \
  -H "X-API-Key: your-key" \
  -F "image_url=https://example.com/photo.jpg" \
  -F "include_detailed_metrics=true"
```

### Using Python (httpx)
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/verify/photo",
        data={
            "image_url": "https://example.com/photo.jpg",
            "include_detailed_metrics": "true"
        },
        headers={"X-API-Key": "your-key"}
    )
    result = response.json()
```

## Validation Rules

### URL Requirements
- ✅ Must be a valid HTTP/HTTPS URL
- ✅ Must return `image/*` content-type
- ✅ Maximum size: 10MB
- ✅ Request timeout: 30 seconds
- ✅ Supported formats: JPEG, PNG (same as file upload)

### Mutually Exclusive
- ❌ Cannot provide both `file` and `image_url`
- ❌ Must provide at least one (file OR url)
- ✅ All other parameters work the same

## Error Handling

### URL-Specific Errors
```json
{
  "detail": "Failed to download image: HTTP 404"
}
```
```json
{
  "detail": "URL does not point to an image (content-type: text/html)"
}
```
```json
{
  "detail": "Image too large (12.5MB). Maximum size: 10MB"
}
```
```json
{
  "detail": "Request timeout after 30 seconds"
}
```

### Validation Errors
```json
{
  "detail": "Either 'file' or 'image_url' must be provided"
}
```
```json
{
  "detail": "Provide either 'file' or 'image_url', not both"
}
```

## Example Files

- **`example_url_usage.py`** - Python examples using httpx
- Test the feature using the interactive docs at http://localhost:8000/docs

## Benefits

1. **Easier Integration** - No need to download and re-upload images
2. **Performance** - Direct processing from source URLs
3. **Flexibility** - Works with CDNs, S3 buckets, or any public image URL
4. **Backward Compatible** - Existing file upload still works

## Security Considerations

- URLs must be publicly accessible (no authentication)
- Server makes HTTP request to provided URL
- Consider rate limiting to prevent abuse
- Validate URLs in production environments
- Set appropriate timeouts to prevent hanging requests

## Testing

Try it in the Swagger UI:
1. Go to http://localhost:8000/docs
2. Expand `/api/v1/verify/photo` endpoint
3. Click "Try it out"
4. Provide an `image_url` instead of uploading a file
5. Execute and view results

## Dependencies

- **httpx** - Already in requirements.txt for async HTTP requests
- No additional packages needed

---

**All endpoints now support URL-based verification! 🚀**
