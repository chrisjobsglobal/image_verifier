#!/usr/bin/env python3
"""Test PaddleOCR MRZ reading improvements"""

import sys
import requests
import json

API_URL = "http://104.167.8.60:27000/api/v1/passport/verify/url"
API_KEY = "308yDoLK03hDLF5Xsg5aKfmhzaFKq2fy"

def test_mrz_reading(pdf_url):
    """Test MRZ reading with given PDF URL"""
    
    print(f"\n{'='*80}")
    print(f"Testing MRZ Reading with AI-Enhanced OCR")
    print(f"{'='*80}\n")
    
    print(f"📄 PDF URL: {pdf_url}\n")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "image_url": pdf_url,
        "read_mrz": True,
        "validate_expiration": True
    }
    
    print("🔄 Sending request to API...\n")
    
    try:
        response = requests.post(API_URL, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Response received!\n")
        print(f"{'─'*80}")
        print(f"📊 RESULTS:")
        print(f"{'─'*80}\n")
        
        # Overall status
        print(f"✓ Valid: {result.get('is_valid', False)}")
        print(f"✓ MRZ Found: {result.get('mrz_found', False)}")
        print(f"✓ OCR Method: {result.get('ocr_method', 'unknown').upper()}")
        
        if result.get('mrz_found'):
            mrz = result.get('mrz_data', {})
            print(f"\n{'─'*80}")
            print(f"📋 MRZ DATA:")
            print(f"{'─'*80}\n")
            
            print(f"👤 Name:")
            print(f"   Surname: {mrz.get('surname', 'N/A')}")
            print(f"   Given Names: {mrz.get('names', 'N/A')}")
            print(f"\n📍 Document Info:")
            print(f"   Passport Number: {mrz.get('passport_number', 'N/A')}")
            print(f"   Country: {mrz.get('country', 'N/A')}")
            print(f"   Nationality: {mrz.get('nationality', 'N/A')}")
            print(f"\n📅 Dates:")
            print(f"   Date of Birth: {mrz.get('date_of_birth', 'N/A')}")
            print(f"   Expiration: {mrz.get('expiration_date', 'N/A')}")
            print(f"   Sex: {mrz.get('sex', 'N/A')}")
            
            if mrz.get('raw_mrz_text'):
                print(f"\n📝 Raw MRZ:")
                for line in mrz['raw_mrz_text'].split('\n'):
                    print(f"   {line}")
        
        # Errors and warnings
        if result.get('errors'):
            print(f"\n{'─'*80}")
            print(f"❌ ERRORS:")
            print(f"{'─'*80}\n")
            for error in result['errors']:
                print(f"   • {error}")
        
        if result.get('warnings'):
            print(f"\n{'─'*80}")
            print(f"⚠️  WARNINGS:")
            print(f"{'─'*80}\n")
            for warning in result['warnings']:
                print(f"   • {warning}")
        
        print(f"\n{'='*80}\n")
        
        # Save full response
        with open('/tmp/mrz_test_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Full response saved to: /tmp/mrz_test_result.json\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_mrz.py <PDF_URL>")
        print("\nExample:")
        print("  python test_mrz.py https://hub.jobsglobal.com/storage/tree/b1a/QLPNp8G0Jnjc290C7LtNnKyNYjZ6pQOYlZvoFKV6.pdf")
        sys.exit(1)
    
    pdf_url = sys.argv[1]
    test_mrz_reading(pdf_url)
