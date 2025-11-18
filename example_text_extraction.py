"""
Example usage of the passport text extraction endpoint
"""

import requests
import json

# Configuration
API_URL = "https://document-verifier.jobsglobal.com"
API_KEY = "308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy"

# Example 1: Extract text from a PDF using URL
def extract_text_from_url():
    """Extract text from a multi-page passport PDF via URL"""
    
    url = f"{API_URL}/api/v1/passport/extract-text/url"
    
    payload = {
        "image_url": "https://hub.jobsglobal.com/storage/tree/b1a/QLPNp8G0Jnjc290C7LtNnKyNYjZ6pQOYlZvoFKV6.pdf",
        "include_detailed_blocks": False  # Set to True for text block coordinates
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("🔍 Extracting text from passport PDF (URL)...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success! Extracted text from {data['total_pages']} page(s)")
        print(f"OCR Method: {data['ocr_method']}")
        print(f"Processing Time: {data['processing_time_seconds']}s")
        print("\n" + "="*60)
        print("COMBINED TEXT FROM ALL PAGES:")
        print("="*60)
        print(data['combined_text'])
        print("\n" + "="*60)
        
        # Show individual pages
        print("\nPAGES BREAKDOWN:")
        for page in data['pages']:
            print(f"\n--- Page {page['page_number']} (confidence: {page['confidence']}%) ---")
            print(page['text'][:200] + "..." if len(page['text']) > 200 else page['text'])
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


# Example 2: Extract text from an uploaded file
def extract_text_from_file(file_path):
    """Extract text from a local passport file"""
    
    url = f"{API_URL}/api/v1/passport/extract-text/upload"
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    # Form data
    data = {
        "include_detailed_blocks": "false"  # Set to "true" for detailed blocks
    }
    
    # File upload
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_path.split('/')[-1], f, 'application/pdf')
        }
        
        print(f"📄 Uploading and extracting text from: {file_path}")
        response = requests.post(url, data=data, files=files, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success! Extracted text from {data['total_pages']} page(s)")
        print(f"OCR Method: {data['ocr_method']}")
        print(f"Processing Time: {data['processing_time_seconds']}s")
        print("\n" + "="*60)
        print("COMBINED TEXT:")
        print("="*60)
        print(data['combined_text'])
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


# Example 3: Extract text with detailed blocks (coordinates and confidence)
def extract_text_with_blocks():
    """Extract text with detailed block information"""
    
    url = f"{API_URL}/api/v1/passport/extract-text/url"
    
    payload = {
        "image_url": "https://hub.jobsglobal.com/storage/tree/e1c/bHvP0zaGonDXXwSGaqOJEvFZz7DrR6Ju1z80oav6.pdf",
        "include_detailed_blocks": True  # Get coordinates and confidence per block
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("🔍 Extracting text with detailed blocks...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Success! Extracted text from {data['total_pages']} page(s)")
        
        # Show text blocks for first page
        if data['pages'] and 'text_blocks' in data['pages'][0]:
            print("\n📍 Text Blocks from Page 1:")
            for i, block in enumerate(data['pages'][0]['text_blocks'][:5], 1):
                print(f"\nBlock {i}:")
                print(f"  Text: {block['text']}")
                print(f"  Confidence: {block['confidence']}%")
                print(f"  BBox: {block['bbox']}")  # [x1, y1, x2, y2]
        
        print(f"\n📝 Full text preview:")
        print(data['combined_text'][:500] + "...")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("Passport Text Extraction Examples")
    print("=" * 60)
    
    # Run example 1: Extract from URL
    print("\nExample 1: Extract text from PDF URL")
    print("-" * 60)
    extract_text_from_url()
    
    # Run example 3: Extract with detailed blocks
    print("\n\nExample 3: Extract with detailed text blocks")
    print("-" * 60)
    extract_text_with_blocks()
    
    # Uncomment to test file upload:
    # print("\n\nExample 2: Extract from uploaded file")
    # print("-" * 60)
    # extract_text_from_file("path/to/your/passport.pdf")
