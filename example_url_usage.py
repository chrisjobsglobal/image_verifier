"""
Example usage of Image Verifier API with URL support

This demonstrates how to verify photos and passports using image URLs
instead of file uploads.
"""

import httpx
import asyncio


async def verify_photo_from_url(image_url: str, api_url: str = "http://localhost:8000"):
    """Verify a photo from URL"""
    
    async with httpx.AsyncClient() as client:
        # Using form data to send URL
        response = await client.post(
            f"{api_url}/api/v1/verify/photo",
            data={
                "image_url": image_url,
                "include_detailed_metrics": "true",
                "strict_mode": "false"
            },
            headers={
                "X-API-Key": "your-api-key-here"  # Set in .env or remove security dependency
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Photo verification successful!")
            print(f"   Valid: {result['is_valid']}")
            print(f"   ICAO Compliant: {result['is_icao_compliant']}")
            print(f"   Errors: {result['errors']}")
            print(f"   Warnings: {result['warnings']}")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None


async def verify_passport_from_url(image_url: str, api_url: str = "http://localhost:8000"):
    """Verify a passport from URL"""
    
    async with httpx.AsyncClient() as client:
        # Using form data to send URL
        response = await client.post(
            f"{api_url}/api/v1/verify/passport",
            data={
                "image_url": image_url,
                "read_mrz": "true",
                "validate_expiration": "true",
                "include_detailed_metrics": "true"
            },
            headers={
                "X-API-Key": "your-api-key-here"  # Set in .env or remove security dependency
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Passport verification successful!")
            print(f"   Valid: {result['is_valid']}")
            print(f"   ICAO Compliant: {result['is_compliant']}")
            print(f"   MRZ Found: {result['mrz_found']}")
            if result.get('mrz_data'):
                print(f"   Document Number: {result['mrz_data'].get('document_number')}")
                print(f"   Country: {result['mrz_data'].get('country_code')}")
            print(f"   Errors: {result['errors']}")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None


async def extract_mrz_from_url(image_url: str, api_url: str = "http://localhost:8000"):
    """Extract MRZ data only from passport URL"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_url}/api/v1/extract/mrz",
            data={
                "image_url": image_url
            },
            headers={
                "X-API-Key": "your-api-key-here"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ MRZ extraction successful!")
            if result.get('mrz_data'):
                mrz = result['mrz_data']
                print(f"   Type: {mrz.get('document_type')}")
                print(f"   Country: {mrz.get('country_code')}")
                print(f"   Document #: {mrz.get('document_number')}")
                print(f"   Name: {mrz.get('names')} {mrz.get('surname')}")
                print(f"   DOB: {mrz.get('date_of_birth')}")
                print(f"   Expires: {mrz.get('expiry_date')}")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None


async def main():
    """Example usage"""
    
    print("=" * 60)
    print("Image Verifier API - URL Support Examples")
    print("=" * 60)
    print()
    
    # Example 1: Verify a photo from URL
    print("Example 1: Photo Verification from URL")
    print("-" * 60)
    photo_url = "https://example.com/path/to/photo.jpg"
    # await verify_photo_from_url(photo_url)
    print(f"Would verify photo from: {photo_url}")
    print()
    
    # Example 2: Verify a passport from URL
    print("Example 2: Passport Verification from URL")
    print("-" * 60)
    passport_url = "https://example.com/path/to/passport.jpg"
    # await verify_passport_from_url(passport_url)
    print(f"Would verify passport from: {passport_url}")
    print()
    
    # Example 3: Extract MRZ only from URL
    print("Example 3: MRZ Extraction from URL")
    print("-" * 60)
    # await extract_mrz_from_url(passport_url)
    print(f"Would extract MRZ from: {passport_url}")
    print()
    
    print("=" * 60)
    print("Usage Notes:")
    print("=" * 60)
    print("1. You can provide either 'file' (upload) OR 'image_url', not both")
    print("2. Image URLs must be publicly accessible")
    print("3. Supported formats: JPEG, PNG")
    print("4. Maximum file size: 10MB")
    print("5. Set X-API-Key header if authentication is enabled")
    print()
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
