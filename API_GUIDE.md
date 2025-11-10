# API Quick Reference Guide

## Base URL
```
http://localhost:8000
```

## Authentication (Optional)
```bash
-H "X-API-Key: your-api-key"
```

---

## 📸 Photo Verification

### Verify Personal Photo
```bash
curl -X POST "http://localhost:8000/api/v1/photo/verify" \
  -F "file=@photo.jpg" \
  -F "include_detailed_metrics=false" \
  -F "strict_mode=false"
```

**PowerShell:**
```powershell
$uri = "http://localhost:8000/api/v1/photo/verify"
$filePath = "C:\path\to\photo.jpg"
$form = @{
    file = Get-Item -Path $filePath
    include_detailed_metrics = "false"
}
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

### Get Photo Requirements
```bash
curl "http://localhost:8000/api/v1/photo/requirements"
```

---

## 📄 Passport Verification

### Verify Passport Document
```bash
curl -X POST "http://localhost:8000/api/v1/passport/verify" \
  -F "file=@passport.jpg" \
  -F "read_mrz=true" \
  -F "validate_expiration=true" \
  -F "include_detailed_metrics=false"
```

**PowerShell:**
```powershell
$uri = "http://localhost:8000/api/v1/passport/verify"
$filePath = "C:\path\to\passport.jpg"
$form = @{
    file = Get-Item -Path $filePath
    read_mrz = "true"
    validate_expiration = "true"
}
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

### Extract MRZ Only (Fast)
```bash
curl -X POST "http://localhost:8000/api/v1/passport/extract-mrz" \
  -F "file=@passport.jpg"
```

### Get Passport Requirements
```bash
curl "http://localhost:8000/api/v1/passport/requirements"
```

---

## 🏥 Health & Info

### Health Check
```bash
curl "http://localhost:8000/health"
```

### API Information
```bash
curl "http://localhost:8000/api/v1/info"
```

### Root
```bash
curl "http://localhost:8000/"
```

---

## 📊 Response Examples

### Photo Verification Success
```json
{
  "success": true,
  "is_valid": true,
  "compliance_score": 95.0,
  "errors": [],
  "warnings": ["Face slightly off-center"],
  "recommendations": ["Center face in frame"],
  "face_metrics": {
    "face_detected": true,
    "face_percentage": 75.2,
    "is_centered": true,
    "head_tilt_degrees": 2.5,
    "eyes_open": true,
    "looking_at_camera": true,
    "glasses_detected": false
  }
}
```

### Photo Verification Failed
```json
{
  "success": true,
  "is_valid": false,
  "compliance_score": 45.0,
  "errors": [
    "Image is blurry (score: 85.5, threshold: 100.0)",
    "Face is too small (65.3%). Face should occupy 70-80% of the image",
    "Background is not uniform. Use a plain, light-colored background"
  ],
  "warnings": [],
  "recommendations": [
    "Use a camera with better focus",
    "Adjust distance so face occupies 70-80% of frame",
    "Use a plain, light-colored background"
  ]
}
```

### Passport Verification with MRZ
```json
{
  "success": true,
  "is_valid": true,
  "document_detected": true,
  "mrz_found": true,
  "mrz_data": {
    "type": "P",
    "country": "USA",
    "surname": "SMITH",
    "names": "JOHN MICHAEL",
    "passport_number": "123456789",
    "nationality": "USA",
    "date_of_birth": "850115",
    "sex": "M",
    "expiration_date": "300115",
    "personal_number": ""
  },
  "passport_valid": true,
  "errors": [],
  "warnings": [],
  "recommendations": []
}
```

### Error Response
```json
{
  "success": false,
  "error": "Invalid image format",
  "error_code": "INVALID_FORMAT",
  "details": {
    "supported_formats": ["image/jpeg", "image/png"]
  }
}
```

---

## 🔍 Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_FORMAT` | Unsupported image format |
| `FILE_TOO_LARGE` | Image exceeds size limit |
| `VALIDATION_ERROR` | Request validation failed |
| `INTERNAL_ERROR` | Server error |
| `UNAUTHORIZED` | Invalid or missing API key |

---

## 💡 Tips

### Photo Verification
- Use high-quality images (minimum 1920×1080)
- Ensure good lighting, no shadows
- Plain light background (white/light gray)
- Face should occupy 70-80% of frame
- Head straight, eyes open, neutral expression

### Passport Verification
- Capture entire document with margins
- Document should fill 70-80% of frame
- Avoid glare and reflections (no flash)
- Ensure MRZ area (bottom text) is clear
- Place on contrasting background

### Performance
- Smaller images process faster
- `extract-mrz` endpoint is faster than full `verify`
- Disable `include_detailed_metrics` for faster responses
- Enable caching for repeated verifications

---

## 📚 Interactive Documentation

For full API documentation with try-it-now interface:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
