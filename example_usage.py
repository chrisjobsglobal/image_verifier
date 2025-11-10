"""
Example usage of the Image Verifier API
"""

import requests
from pathlib import Path


# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = None  # Set if authentication is enabled


def verify_photo(image_path: str, detailed: bool = False):
    """
    Verify a personal photo for ICAO compliance
    
    Args:
        image_path: Path to the photo file
        detailed: Include detailed metrics in response
    """
    url = f"{API_BASE_URL}/api/v1/photo/verify"
    
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"include_detailed_metrics": detailed}
        
        response = requests.post(url, files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Photo Verification Results for: {image_path}")
        print(f"  Valid: {result['is_valid']}")
        print(f"  Compliance Score: {result['compliance_score']}%")
        
        if result['errors']:
            print(f"\n  ❌ Errors:")
            for error in result['errors']:
                print(f"    - {error}")
        
        if result['warnings']:
            print(f"\n  ⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"    - {warning}")
        
        if result['recommendations']:
            print(f"\n  💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"    - {rec}")
        
        if detailed and result.get('face_metrics'):
            print(f"\n  📊 Face Metrics:")
            metrics = result['face_metrics']
            print(f"    Face Percentage: {metrics.get('face_percentage', 'N/A')}%")
            print(f"    Head Tilt: {metrics.get('head_tilt_degrees', 'N/A')}°")
            print(f"    Eyes Open: {metrics.get('eyes_open', 'N/A')}")
            print(f"    Looking at Camera: {metrics.get('looking_at_camera', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())


def verify_passport(image_path: str, read_mrz: bool = True):
    """
    Verify a passport document
    
    Args:
        image_path: Path to the passport image
        read_mrz: Extract MRZ data
    """
    url = f"{API_BASE_URL}/api/v1/passport/verify"
    
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"read_mrz": read_mrz}
        
        response = requests.post(url, files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Passport Verification Results for: {image_path}")
        print(f"  Valid: {result['is_valid']}")
        print(f"  Document Detected: {result['document_detected']}")
        print(f"  MRZ Found: {result['mrz_found']}")
        
        if result.get('mrz_data'):
            print(f"\n  📄 Passport Data:")
            mrz = result['mrz_data']
            print(f"    Type: {mrz.get('type')}")
            print(f"    Country: {mrz.get('country')}")
            print(f"    Surname: {mrz.get('surname')}")
            print(f"    Names: {mrz.get('names')}")
            print(f"    Passport Number: {mrz.get('passport_number')}")
            print(f"    Date of Birth: {mrz.get('date_of_birth')}")
            print(f"    Expiration: {mrz.get('expiration_date')}")
            print(f"    Valid: {result.get('passport_valid')}")
        
        if result['errors']:
            print(f"\n  ❌ Errors:")
            for error in result['errors']:
                print(f"    - {error}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())


def check_health():
    """Check API health status"""
    url = f"{API_BASE_URL}/health"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Health Check")
        print(f"  Status: {result['status']}")
        print(f"  Version: {result['version']}")
        print(f"\n  Services:")
        for service, status in result['services'].items():
            icon = "✓" if "available" in status else "✗"
            print(f"    {icon} {service}: {status}")
    else:
        print(f"❌ Health check failed: {response.status_code}")


if __name__ == "__main__":
    # Check API health first
    check_health()
    
    # Example: Verify a photo
    # verify_photo("path/to/your/photo.jpg", detailed=True)
    
    # Example: Verify a passport
    # verify_passport("path/to/your/passport.jpg")
    
    print("\n" + "="*50)
    print("To use this script:")
    print("1. Ensure the API is running (python -m app.main)")
    print("2. Uncomment the example calls above")
    print("3. Replace paths with your actual image files")
    print("="*50)
