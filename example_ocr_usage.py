"""
Example Usage: OCR Text Extraction API
Extract text from various document types using the OCR endpoints
"""

import requests
import json
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:27000"
API_KEY = "308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy"

HEADERS = {
    "X-API-Key": API_KEY
}


def extract_text_from_url(document_url: str, max_pages: int = 50, include_blocks: bool = False):
    """
    Extract text from a document by providing a URL
    
    Works with:
    - Passports (bio page, visas, endorsements)
    - National IDs and driver's licenses
    - Birth/marriage certificates
    - Academic transcripts
    - Employment letters
    - Any document with text
    """
    print(f"\n{'='*80}")
    print(f"Extracting text from URL: {document_url}")
    print(f"Max pages: {max_pages}")
    print(f"{'='*80}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ocr/extract-text/url"
    
    payload = {
        "image_url": document_url,
        "include_detailed_blocks": include_blocks,
        "max_pages": max_pages
    }
    
    response = requests.post(
        endpoint,
        headers=HEADERS,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"📄 Total Pages: {result['total_pages']}")
        print(f"⚡ Processing Time: {result['processing_time_seconds']:.2f}s")
        print(f"🔧 OCR Method: {result['ocr_method']}")
        
        # Show text from each page
        for page in result['pages']:
            print(f"\n--- Page {page['page_number']} ---")
            print(f"Confidence: {page['confidence']:.1f}%")
            print(f"Text preview (first 200 chars):")
            print(page['text'][:200] + "..." if len(page['text']) > 200 else page['text'])
        
        # Show combined text
        print(f"\n--- Combined Text ---")
        print(f"Total characters: {len(result['combined_text'])}")
        print(f"Preview (first 300 chars):")
        print(result['combined_text'][:300] + "..." if len(result['combined_text']) > 300 else result['combined_text'])
        
        if result.get('warnings'):
            print(f"\n⚠️ Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return None


def extract_text_from_file(file_path: str, max_pages: int = 50, include_blocks: bool = False):
    """
    Extract text from a local document file
    """
    print(f"\n{'='*80}")
    print(f"Extracting text from file: {file_path}")
    print(f"Max pages: {max_pages}")
    print(f"{'='*80}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ocr/extract-text/upload"
    
    # Prepare file
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_path_obj.name, f, 'application/octet-stream')
        }
        data = {
            'include_detailed_blocks': str(include_blocks).lower(),
            'max_pages': str(max_pages)
        }
        
        response = requests.post(
            endpoint,
            headers=HEADERS,
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"📄 Total Pages: {result['total_pages']}")
        print(f"⚡ Processing Time: {result['processing_time_seconds']:.2f}s")
        
        # Show text from each page
        for page in result['pages']:
            print(f"\n--- Page {page['page_number']} ---")
            print(f"Confidence: {page['confidence']:.1f}%")
            print(f"Text blocks: {len(page.get('text_blocks', []))}")
            print(f"Text preview:")
            print(page['text'][:200] + "..." if len(page['text']) > 200 else page['text'])
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return None


def extract_with_detailed_blocks(document_url: str):
    """
    Extract text with detailed block information (coordinates and confidence)
    Useful for:
    - Building structured data extraction
    - Finding specific fields by position
    - Creating overlays on images
    """
    print(f"\n{'='*80}")
    print(f"Extracting text with detailed blocks from: {document_url}")
    print(f"{'='*80}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ocr/extract-text/url"
    
    payload = {
        "image_url": document_url,
        "include_detailed_blocks": True,
        "max_pages": 3
    }
    
    response = requests.post(
        endpoint,
        headers=HEADERS,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        
        # Show detailed blocks from first page
        if result['pages'] and result['pages'][0].get('text_blocks'):
            print(f"\n--- Text Blocks from Page 1 ---")
            for i, block in enumerate(result['pages'][0]['text_blocks'][:5]):  # Show first 5 blocks
                print(f"\nBlock {i+1}:")
                print(f"  Text: {block['text']}")
                print(f"  Confidence: {block['confidence']:.1f}%")
                print(f"  Bounding Box: {block['bbox']}")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return None


if __name__ == "__main__":
    print("OCR Text Extraction API - Example Usage")
    print("========================================\n")
    
    # Example 1: Extract text from passport PDF (3 pages)
    print("\n📘 Example 1: Extract text from passport PDF")
    passport_result = extract_text_from_url(
        "https://hub.jobsglobal.com/storage/tree/e1c/bHvP0zaGonDXXwSGaqOJEvFZz7DrR6Ju1z80oav6.pdf",
        max_pages=3
    )
    
    # Example 2: Extract text from single passport image
    print("\n\n📘 Example 2: Extract text from single passport image")
    single_passport_result = extract_text_from_url(
        "https://hub.jobsglobal.com/storage/tree/6d4/UOPNXW3KojhBpCsFMm7xvuT7n5Y5F5J14RZiYYjc.jpeg",
        max_pages=1
    )
    
    # Example 3: Extract with detailed text blocks and coordinates
    print("\n\n📘 Example 3: Extract with detailed text blocks")
    blocks_result = extract_with_detailed_blocks(
        "https://hub.jobsglobal.com/storage/tree/6d4/UOPNXW3KojhBpCsFMm7xvuT7n5Y5F5J14RZiYYjc.jpeg"
    )
    
    # Example 4: File upload (uncomment if you have a local file)
    # print("\n\n📘 Example 4: Extract from local file")
    # file_result = extract_text_from_file(
    #     "/path/to/your/document.pdf",
    #     max_pages=10
    # )
    
    print("\n\n" + "="*80)
    print("Examples completed!")
    print("="*80)
