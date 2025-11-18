# OCR Text Extraction Feature

## Overview
Dedicated OCR endpoints for extracting text from various document types, not limited to passports.

## Endpoints

### 1. **POST** `/api/v1/ocr/extract-text/upload`
Extract text from uploaded document files.

**Supported Formats:**
- Single images: JPEG, PNG
- Multi-page PDFs

**Parameters:**
- `file` (required): Document file to process
- `include_detailed_blocks` (optional, default: false): Include text block coordinates
- `max_pages` (optional, default: 50): Maximum number of PDF pages to process

### 2. **POST** `/api/v1/ocr/extract-text/url`
Extract text from documents by providing a URL.

**Request Body:**
```json
{
  "image_url": "https://example.com/document.pdf",
  "include_detailed_blocks": false,
  "max_pages": 50
}
```

## Document Types Supported

✅ **Identity Documents**
- Passports (bio page, visas, endorsements)
- National ID cards
- Driver's licenses

✅ **Certificates**
- Birth certificates
- Marriage certificates  
- Death certificates

✅ **Education**
- Academic transcripts
- Diplomas and degrees
- Certificate of enrollment

✅ **Employment**
- Employment letters
- Contracts
- Pay stubs

✅ **General**
- Any document with printed/typed text
- Forms and applications
- Invoices and receipts

## Response Format

```json
{
  "success": true,
  "is_valid": true,
  "total_pages": 3,
  "pages": [
    {
      "page_number": 1,
      "text": "Extracted text content...",
      "confidence": 95.5,
      "text_blocks": [  // Only if include_detailed_blocks=true
        {
          "text": "PASSPORT",
          "bbox": [100, 50, 200, 80],
          "confidence": 98.2
        }
      ]
    }
  ],
  "combined_text": "All text from all pages...",
  "ocr_method": "easyocr",
  "processing_time_seconds": 21.5,
  "errors": [],
  "warnings": []
}
```

## Features

- **Multi-page support**: Processes all pages in PDFs (up to max_pages limit)
- **Smart limiting**: If PDF has 3 pages but max_pages=100, returns only 3 pages
- **Confidence scores**: Per-page OCR confidence percentage
- **Text blocks**: Optional detailed block info with coordinates
- **Combined output**: All text merged with page breaks
- **Warnings**: Low confidence or no text detected alerts

## Usage Examples

See `example_ocr_usage.py` for complete examples.

### Quick Example - Python

```python
import requests

url = "http://localhost:27000/api/v1/ocr/extract-text/url"
headers = {"X-API-Key": "your-api-key"}
payload = {
    "image_url": "https://example.com/document.pdf",
    "max_pages": 10
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print(f"Total pages: {result['total_pages']}")
print(f"Combined text: {result['combined_text']}")
```

### Quick Example - cURL

```bash
curl -X POST "http://localhost:27000/api/v1/ocr/extract-text/url" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/document.pdf",
    "max_pages": 10
  }'
```

## Technical Details

- **OCR Engine**: EasyOCR (CPU mode)
- **Languages**: English (can be extended)
- **PDF Conversion**: 300 DPI for high quality
- **Max File Size**: Configurable (default 10MB)
- **Processing**: Async/await for scalability

## Migration from Passport Endpoints

The old passport text extraction endpoints still exist for backward compatibility, but new integrations should use the dedicated OCR endpoints:

**Old (deprecated):**
- `/api/v1/passport/extract-text/upload`
- `/api/v1/passport/extract-text/url`

**New (recommended):**
- `/api/v1/ocr/extract-text/upload`
- `/api/v1/ocr/extract-text/url`

Both endpoints have identical functionality, but the OCR endpoints better reflect the broader use case.

## Future Enhancements

Planned features:
- [ ] Multi-language support
- [ ] Table extraction
- [ ] Handwriting recognition
- [ ] Form field detection
- [ ] Document classification
- [ ] Named entity recognition (NER)
