# Debug Endpoint Documentation

## Purpose
The debug endpoint allows you to see exactly what image is produced when a PDF is converted. This helps troubleshoot why document positioning validation might be failing.

## Endpoints

### 1. Convert PDF to Image and Save

**POST** `/api/v1/debug/pdf-to-image`

Converts a PDF (or image URL) to an image file, saves it to the public folder, and returns the URL.

#### Request

```bash
curl -X POST "http://104.167.8.60:27000/api/v1/debug/pdf-to-image" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/passport.pdf"
  }'
```

#### Response

```json
{
  "success": true,
  "message": "Image converted and saved successfully",
  "image_url": "/static/debug/debug_20241112_144530_a1b2c3d4.jpg",
  "full_url": "http://104.167.8.60:27000/static/debug/debug_20241112_144530_a1b2c3d4.jpg",
  "image_info": {
    "width": 2480,
    "height": 3508,
    "channels": 3,
    "file_size_bytes": 1245678,
    "file_size_mb": 1.19
  },
  "file_path": "/home/chris/projects/live/image_verifier/public/debug/debug_20241112_144530_a1b2c3d4.jpg",
  "was_pdf": true
}
```

You can then open the `full_url` in your browser to see the actual converted image.

### 2. List Saved Debug Images

**GET** `/api/v1/debug/list-debug-images`

Lists all debug images that have been saved.

#### Request

```bash
curl -X GET "http://104.167.8.60:27000/api/v1/debug/list-debug-images" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy"
```

#### Response

```json
{
  "success": true,
  "count": 3,
  "images": [
    {
      "filename": "debug_20241112_144530_a1b2c3d4.jpg",
      "url": "/static/debug/debug_20241112_144530_a1b2c3d4.jpg",
      "full_url": "http://104.167.8.60:27000/static/debug/debug_20241112_144530_a1b2c3d4.jpg",
      "size_mb": 1.19,
      "modified": "2024-11-12T14:45:30.123456"
    }
  ]
}
```

### 3. Clear All Debug Images

**DELETE** `/api/v1/debug/clear-debug-images`

Deletes all debug images from the public folder.

#### Request

```bash
curl -X DELETE "http://104.167.8.60:27000/api/v1/debug/clear-debug-images" \
  -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy"
```

#### Response

```json
{
  "success": true,
  "deleted": 3,
  "message": "Deleted 3 debug images"
}
```

## Usage Workflow

1. **Convert your problematic PDF**:
   ```bash
   curl -X POST "http://104.167.8.60:27000/api/v1/debug/pdf-to-image" \
     -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy" \
     -H "Content-Type: application/json" \
     -d '{"image_url": "YOUR_PDF_URL_HERE"}'
   ```

2. **Copy the `full_url` from the response**

3. **Open it in your browser** to see the exact image that was produced

4. **Analyze the image** to see:
   - Are there white borders? (This causes scan detection to fail)
   - Is the document centered?
   - Is the image quality good?
   - Does it look like what you expected?

5. **Clean up when done**:
   ```bash
   curl -X DELETE "http://104.167.8.60:27000/api/v1/debug/clear-debug-images" \
     -H "X-API-Key: 308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy"
   ```

## Python Example

```python
import requests

url = "http://104.167.8.60:27000/api/v1/debug/pdf-to-image"
headers = {
    "X-API-Key": "308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy",
    "Content-Type": "application/json"
}
data = {
    "image_url": "https://example.com/passport.pdf"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

if result["success"]:
    print(f"Image saved! View it at: {result['full_url']}")
    print(f"Dimensions: {result['image_info']['width']}x{result['image_info']['height']}")
    print(f"Was PDF: {result['was_pdf']}")
else:
    print(f"Error: {result.get('detail', 'Unknown error')}")
```

## Notes

- All debug images are saved to `/home/chris/projects/live/image_verifier/public/debug/`
- Files are named with timestamp and unique ID: `debug_YYYYMMDD_HHMMSS_XXXXXXXX.jpg`
- The endpoint works with both PDFs and regular images
- Static files are served at `/static/debug/` prefix
- Images are always saved as JPG format
- The `was_pdf` field in the response tells you if the input was a PDF or image
