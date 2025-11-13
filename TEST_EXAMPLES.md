# API Testing Examples

## Authentication
All requests require an API key in the header:
```
X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy
```

## Passport Verification

### Option 1: Upload File (Recommended)

```bash
# Upload a passport image file
curl -X POST "http://104.167.8.60:27000/api/v1/passport/verify/upload" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -F "file=@/path/to/passport.jpg" \
  -F "read_mrz=true" \
  -F "validate_expiration=true" \
  -F "include_detailed_metrics=false"
```

### Option 2: Provide Image URL (Recommended)

```bash
# Verify passport from URL using JSON body
curl -X POST "http://104.167.8.60:27000/api/v1/passport/verify/url" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/passport.jpg",
    "read_mrz": true,
    "validate_expiration": true,
    "include_detailed_metrics": false
  }'
```

### Legacy Endpoint (Deprecated)

```bash
# Old endpoint - still works but deprecated
curl -X POST "http://104.167.8.60:27000/api/v1/passport/verify" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -F "image_url=https://example.com/passport.jpg" \
  -F "read_mrz=true"
```

### Upload PDF Document

```bash
# Upload a PDF passport document (first page will be extracted)
curl -X POST "http://104.167.8.60:27000/api/v1/passport/verify/upload" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -F "file=@/path/to/passport.pdf" \
  -F "read_mrz=true" \
  -F "validate_expiration=true"
```

### Extract MRZ Only

```bash
# Quick MRZ extraction from file upload
curl -X POST "http://104.167.8.60:27000/api/v1/passport/extract-mrz/upload" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -F "file=@/path/to/passport.jpg"

# Quick MRZ extraction from URL
curl -X POST "http://104.167.8.60:27000/api/v1/passport/extract-mrz/url" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/passport.jpg"
  }'
```

## Photo Verification

### Option 1: Upload File (Recommended)

```bash
# Upload a personal photo
curl -X POST "http://104.167.8.60:27000/api/v1/photo/verify/upload" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -F "file=@/path/to/photo.jpg" \
  -F "strict_mode=true" \
  -F "include_detailed_metrics=false"
```

### Option 2: Provide Image URL (Recommended)

```bash
# Verify photo from URL using JSON body
curl -X POST "http://104.167.8.60:27000/api/v1/photo/verify/url" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "strict_mode": true,
    "include_detailed_metrics": false
  }'
```

### Legacy Endpoint (Deprecated)

```bash
# Old endpoint - still works but deprecated
curl -X POST "http://104.167.8.60:27000/api/v1/photo/verify" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -F "image_url=https://example.com/photo.jpg" \
  -F "strict_mode=true"
```

## API Endpoints Summary

### Passport Endpoints
- **POST /api/v1/passport/verify/upload** - Upload file (multipart/form-data)
- **POST /api/v1/passport/verify/url** - Provide URL (application/json)
- **POST /api/v1/passport/extract-mrz/upload** - MRZ extraction from file
- **POST /api/v1/passport/extract-mrz/url** - MRZ extraction from URL
- ~~POST /api/v1/passport/verify~~ - Legacy (deprecated)
- ~~POST /api/v1/passport/extract-mrz~~ - Legacy (deprecated)

### Photo Endpoints
- **POST /api/v1/photo/verify/upload** - Upload file (multipart/form-data)
- **POST /api/v1/photo/verify/url** - Provide URL (application/json)
- ~~POST /api/v1/photo/verify~~ - Legacy (deprecated)

## Parameters

### Passport Verification (Upload)
- `file`: Binary file upload (JPEG, PNG, or PDF) - **required**
- `read_mrz`: Boolean (default: true)
- `validate_expiration`: Boolean (default: true)
- `include_detailed_metrics`: Boolean (default: false)

### Passport Verification (URL)
JSON body:
```json
{
  "image_url": "https://example.com/passport.jpg",
  "read_mrz": true,
  "validate_expiration": true,
  "include_detailed_metrics": false
}
```

### Photo Verification (Upload)
- `file`: Binary file upload (JPEG or PNG) - **required**
- `strict_mode`: Boolean (default: false)
- `include_detailed_metrics`: Boolean (default: false)

### Photo Verification (URL)
JSON body:
```json
{
  "image_url": "https://example.com/photo.jpg",
  "strict_mode": false,
  "include_detailed_metrics": false
}

## Response Examples

### Successful Passport Verification

```json
{
  "success": true,
  "is_valid": true,
  "document_detected": true,
  "mrz_found": true,
  "passport_valid": true,
  "mrz_data": {
    "type": "P",
    "country": "USA",
    "surname": "DOE",
    "names": "JOHN",
    "passport_number": "123456789",
    "nationality": "USA",
    "date_of_birth": "1990-01-15",
    "sex": "M",
    "expiration_date": "2030-12-31",
    "raw_mrz_text": "P<USADOE<<JOHN<<<<<<<<<<<<<<<<<<<<<..."
  },
  "errors": [],
  "warnings": [],
  "recommendations": []
}
```

### Failed Validation

```json
{
  "success": true,
  "is_valid": false,
  "document_detected": true,
  "mrz_found": false,
  "errors": [
    "Document appears blurred (score: 45.2, threshold: 100)",
    "Document tilt angle exceeds maximum (12.3° > 10°)",
    "Image too dark (brightness: 45, recommended: 80-180)"
  ],
  "warnings": [
    "Possible glare or reflection detected on document"
  ],
  "recommendations": [
    "Ensure camera is stable and document is in focus",
    "Place document flat and capture from directly above",
    "Use good, even lighting - not too dark or too bright",
    "Avoid flash and ensure no light reflections on document surface"
  ]
}
```

## Testing via Swagger UI

Access the interactive API docs:
- **Swagger UI**: http://104.167.8.60:27000/docs
- **ReDoc**: http://104.167.8.60:27000/redoc

### How to Use Swagger UI:

1. **Authenticate**:
   - Click the "Authorize" button at the top right
   - Enter your API key: `308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy`
   - Click "Authorize" then "Close"

2. **For File Upload Endpoints** (`/verify/upload`, `/extract-mrz/upload`):
   - Expand the endpoint (e.g., `/api/v1/passport/verify/upload`)
   - Click "Try it out"
   - Click "Choose File" and select your image
   - Set other parameters as needed
   - Click "Execute"

3. **For URL Endpoints** (`/verify/url`, `/extract-mrz/url`):
   - Expand the endpoint (e.g., `/api/v1/passport/verify/url`)
   - Click "Try it out"
   - Edit the JSON body with your image URL
   - Click "Execute"

**Benefits of Separate Endpoints**:
- ✅ Clear distinction between file upload and URL methods
- ✅ No confusion with empty file fields in Swagger UI
- ✅ URL endpoints use clean JSON bodies
- ✅ Better API documentation and discoverability
- ✅ Type safety and validation

**Note**: Legacy endpoints (`/verify`, `/extract-mrz`) still work but are deprecated.

## Python Examples

### Passport Verification - File Upload

```python
import requests

# Using file upload
with open('passport.jpg', 'rb') as f:
    response = requests.post(
        'http://104.167.8.60:27000/api/v1/passport/verify/upload',
        headers={'X-API-Key': '308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy'},
        files={'file': f},
        data={
            'read_mrz': 'true',
            'validate_expiration': 'true'
        }
    )

print(response.json())
```

### Passport Verification - URL

```python
import requests

response = requests.post(
    'http://104.167.8.60:27000/api/v1/passport/verify/url',
    headers={'X-API-Key': '308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy'},
    json={
        'image_url': 'https://example.com/passport.jpg',
        'read_mrz': True,
        'validate_expiration': True
    }
)

print(response.json())
```

### Photo Verification - File Upload

```python
import requests

with open('photo.jpg', 'rb') as f:
    response = requests.post(
        'http://104.167.8.60:27000/api/v1/photo/verify/upload',
        headers={'X-API-Key': '308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy'},
        files={'file': f},
        data={
            'strict_mode': 'true',
            'include_detailed_metrics': 'false'
        }
    )

print(response.json())
```

### Photo Verification - URL

```python
import requests

response = requests.post(
    'http://104.167.8.60:27000/api/v1/photo/verify/url',
    headers={'X-API-Key': '308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy'},
    json={
        'image_url': 'https://example.com/photo.jpg',
        'strict_mode': True,
        'include_detailed_metrics': False
    }
)

print(response.json())
```

## Error Codes

- **200**: Success (verification completed)
- **400**: Bad Request (invalid input, missing required field, unsupported format)
- **401**: Unauthorized (missing or invalid API key)
- **404**: Not Found (MRZ not found - extract-mrz endpoint only)
- **413**: Payload Too Large (file exceeds 10MB limit)
- **422**: Unprocessable Entity (validation error in request format)
- **500**: Internal Server Error (processing error)

## Troubleshooting

### "Expected UploadFile, received: <class 'str'>"
- **Solution**: Use the new separate endpoints
  - For file uploads: Use `/verify/upload` endpoint
  - For URLs: Use `/verify/url` endpoint with JSON body
- **Legacy endpoint workaround**: Leave file field completely empty in Swagger UI when using image_url

### "Either 'file' or 'image_url' must be provided"
- Check that you're providing the correct parameter for the endpoint:
  - `/verify/upload` requires `file` parameter
  - `/verify/url` requires `image_url` in JSON body

### "Invalid content type"
- Supported types: image/jpeg, image/png, application/pdf
- Make sure file extension matches content type

### "File too large"
- Maximum file size: 10MB
- Compress or resize images before uploading

### Which Endpoint Should I Use?

**For File Uploads**: Use `/upload` endpoints
- POST /api/v1/passport/verify/upload
- POST /api/v1/passport/extract-mrz/upload
- POST /api/v1/photo/verify/upload

**For URLs**: Use `/url` endpoints
- POST /api/v1/passport/verify/url
- POST /api/v1/passport/extract-mrz/url
- POST /api/v1/photo/verify/url

**Legacy Endpoints** (still work but deprecated):
- POST /api/v1/passport/verify
- POST /api/v1/passport/extract-mrz
- POST /api/v1/photo/verify
