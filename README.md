# Image Verifier API

A high-performance FastAPI service for verifying passport photos and documents according to ICAO 9303 standards. This service provides comprehensive image quality assessment, face detection, MRZ reading, and compliance validation.

## 🌟 Features

### Photo Verification
- **Face Detection & Analysis**: 468-point facial landmark detection using MediaPipe
- **ICAO 9303 Compliance**: Complete validation against international passport photo standards
- **Image Quality Assessment**: Blur detection, brightness/contrast analysis, resolution validation
- **Background Validation**: Uniform background and proper lighting checks
- **Accessories Detection**: Glasses and head covering detection with compliance checks
- **Detailed Feedback**: Actionable recommendations for improving photo quality

### Passport Document Verification
- **MRZ Reading**: Automatic extraction of Machine Readable Zone data using PassportEye
- **Document Positioning**: Tilt angle and centering validation
- **Quality Checks**: Focus, lighting, and reflection detection
- **Data Validation**: Check digit verification and expiration date checking
- **Multi-page Support**: Handle both single and two-page passport captures

## 📋 Requirements

- Python 3.9+
- Tesseract OCR (for MRZ reading)
- Windows/Linux/MacOS

## 🚀 Quick Start

### 1. Install Tesseract OCR

#### Windows
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Default installation path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### MacOS
```bash
brew install tesseract
```

### 2. Clone the Repository

```bash
cd c:\projects\backend\image_verifier
```

### 3. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

**Note**: Installing `dlib` and `face_recognition` on Windows may require Visual Studio Build Tools:
- Download: https://visualstudio.microsoft.com/downloads/ (Build Tools for Visual Studio)
- Or use pre-built wheels: `pip install dlib-19.24.2-cp39-cp39-win_amd64.whl`

### 5. Configure Environment

```powershell
copy .env.example .env
```

Edit `.env` and configure settings (especially `TESSERACT_CMD` path if different from default).

### 6. Run the Application

```powershell
python -m app.main
```

Or using uvicorn directly:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Health Check
```
GET /health
```

Returns service health and availability status.

#### Photo Verification
```
POST /api/v1/photo/verify
```

**Parameters:**
- `file`: Image file (multipart/form-data) - JPEG or PNG
- `include_detailed_metrics`: boolean (optional) - Include technical metrics
- `strict_mode`: boolean (optional) - Treat warnings as errors

**Response:**
```json
{
  "success": true,
  "is_valid": true,
  "compliance_score": 95.0,
  "errors": [],
  "warnings": ["Face is slightly off-center"],
  "recommendations": ["Center face in frame"],
  "face_metrics": {
    "face_detected": true,
    "face_percentage": 75.0,
    "head_tilt_degrees": 2.5,
    "eyes_open": true,
    "looking_at_camera": true
  }
}
```

#### Passport Document Verification
```
POST /api/v1/passport/verify
```

**Parameters:**
- `file`: Passport image file (multipart/form-data)
- `read_mrz`: boolean (default: true) - Extract MRZ data
- `validate_expiration`: boolean (default: true) - Check expiration
- `include_detailed_metrics`: boolean (optional)

**Response:**
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
    "names": "JOHN",
    "passport_number": "123456789",
    "date_of_birth": "850115",
    "expiration_date": "300115"
  },
  "passport_valid": true
}
```

#### MRZ Extraction Only
```
POST /api/v1/passport/extract-mrz
```

Lightweight endpoint for quick MRZ extraction without full validation.

## 🔐 Authentication

API key authentication can be enabled by setting `API_KEY` in `.env`:

```bash
API_KEY=your-secret-api-key-here
```

Then include the API key in requests:

```bash
curl -H "X-API-Key: your-secret-api-key-here" \
     -F "file=@photo.jpg" \
     http://localhost:8000/api/v1/photo/verify
```

## 🧪 Testing

Run the test suite:

```powershell
pytest tests/ -v
```

Run with coverage:

```powershell
pytest tests/ --cov=app --cov-report=html
```

## 📝 Photo Requirements (ICAO 9303)

### Image Specifications
- **Resolution**: Minimum 1920×1080 (Full HD)
- **Format**: JPEG or PNG
- **Age**: Photo must be no more than 6 months old
- **Quality**: High resolution, sharp focus, no blur

### Face Requirements
- **Coverage**: Face occupies 70-80% of photograph
- **Position**: Looking directly at camera, head not tilted
- **Eyes**: Open, clearly visible, no hair obstruction
- **Expression**: Neutral, mouth closed
- **Tilt**: Maximum 10° angle deviation

### Background
- **Color**: Plain light-colored (white or light gray)
- **Uniformity**: No patterns, objects, or busy backgrounds
- **Shadows**: No shadows on face or behind head

### Lighting
- **Quality**: Uniform, diffused lighting
- **Flash**: Avoid flash reflections
- **Exposure**: Natural skin tones, proper brightness

### Accessories
- **Glasses**: Permitted if:
  - Eyes clearly visible
  - No flash reflections
  - No tinted lenses
  - Frames don't cover eyes
- **Head Coverings**: Not permitted except for religious reasons

## 📦 Project Structure

```
image_verifier/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── photo.py        # Photo verification endpoint
│   │   │   └── passport.py     # Passport verification endpoint
│   ├── core/
│   │   ├── config.py           # Configuration settings
│   │   └── security.py         # Authentication
│   ├── models/
│   │   ├── request.py          # Request models
│   │   └── response.py         # Response models
│   ├── services/
│   │   ├── image_quality.py    # Image quality checks
│   │   ├── face_detection.py   # Face detection & analysis
│   │   ├── mrz_reader.py       # MRZ extraction
│   │   └── icao_validator.py   # ICAO compliance
│   └── utils/
│       └── image_utils.py      # Image processing utilities
├── tests/
│   ├── test_api.py             # API endpoint tests
│   └── test_services.py        # Service unit tests
├── requirements.txt
├── .env.example
└── README.md
```

## 🛠️ Configuration

Key configuration options in `.env`:

```bash
# Application
APP_NAME=Image Verifier API
DEBUG=False

# Upload Limits
MAX_UPLOAD_SIZE=10485760  # 10MB

# Image Requirements
MIN_IMAGE_WIDTH=1920
MIN_IMAGE_HEIGHT=1080
MIN_FACE_PERCENTAGE=70.0
MAX_FACE_PERCENTAGE=80.0
MAX_TILT_ANGLE_DEGREES=10.0

# Quality Thresholds
BLUR_THRESHOLD=100.0
MIN_BRIGHTNESS=50
MAX_BRIGHTNESS=200
MIN_CONTRAST=40.0

# Tesseract Path
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Security
API_KEY=  # Leave empty to disable authentication
```

## 🔧 Troubleshooting

### Tesseract Not Found
If you get "Tesseract not found" errors:
1. Verify Tesseract is installed: `tesseract --version`
2. Update `TESSERACT_CMD` in `.env` with correct path
3. On Windows, add Tesseract to PATH environment variable

### dlib Installation Fails (Windows)
```powershell
# Option 1: Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/

# Option 2: Use pre-built wheel
pip install dlib-19.24.2-cp39-cp39-win_amd64.whl
```

### MediaPipe Issues
If MediaPipe fails to load:
```powershell
pip uninstall mediapipe
pip install mediapipe --no-cache-dir
```

### Memory Issues with Large Images
Increase max upload size or implement image resizing:
```python
# In .env
MAX_UPLOAD_SIZE=20971520  # 20MB
```

## 📊 Performance

- Photo verification: ~2-5 seconds
- Passport verification: ~3-7 seconds
- MRZ extraction only: ~1-3 seconds

Performance depends on:
- Image size and quality
- CPU performance
- Enabled features (face detection, MRZ reading)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 References

- [ICAO 9303 Standards](https://www.icao.int/publications/pages/publication.aspx?docnum=9303)
- [PassportEye Documentation](https://pypi.org/project/PassportEye/)
- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📧 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/chrisjobsglobal/image_verifier/issues)
- Documentation: http://localhost:8000/docs

---

**Built with** ❤️ **using FastAPI, OpenCV, MediaPipe, and PassportEye**
