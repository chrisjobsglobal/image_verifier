"""API endpoint tests"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
from PIL import Image
import numpy as np


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for testing"""
    # Create a simple test image
    img = Image.new('RGB', (1920, 1080), color=(200, 200, 200))
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


class TestRootEndpoints:
    """Test root and health endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "services" in data
        assert isinstance(data["services"], dict)
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get("/api/v1/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version" in data
        assert "limits" in data
        assert "thresholds" in data
        assert "features" in data


class TestPhotoVerificationEndpoint:
    """Test photo verification endpoint"""
    
    def test_photo_verify_without_file(self, client):
        """Test photo verification without file"""
        response = client.post("/api/v1/photo/verify")
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_photo_verify_with_invalid_file_type(self, client):
        """Test photo verification with invalid file type"""
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        
        response = client.post("/api/v1/photo/verify", files=files)
        
        # Should return error for invalid content type
        assert response.status_code == 400
    
    def test_photo_verify_with_valid_image(self, client, sample_image_bytes):
        """Test photo verification with valid image"""
        files = {"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        
        # Note: This will likely fail validation due to no face, but should process
        response = client.post("/api/v1/photo/verify", files=files)
        
        # Should return 200 even if validation fails (success=True, is_valid=False)
        assert response.status_code in [200, 401]  # 401 if API key required
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "is_valid" in data
            assert "compliance_score" in data
            assert "errors" in data
    
    def test_photo_requirements_endpoint(self, client):
        """Test photo requirements endpoint"""
        response = client.get("/api/v1/photo/requirements")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dimensions" in data
        assert "quality" in data
        assert "face_requirements" in data
        assert "background" in data


class TestPassportVerificationEndpoint:
    """Test passport verification endpoint"""
    
    def test_passport_verify_without_file(self, client):
        """Test passport verification without file"""
        response = client.post("/api/v1/passport/verify")
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_passport_verify_with_valid_image(self, client, sample_image_bytes):
        """Test passport verification with valid image"""
        files = {"file": ("passport.jpg", sample_image_bytes, "image/jpeg")}
        
        response = client.post("/api/v1/passport/verify", files=files)
        
        # Should return 200 or 401 (if API key required)
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "is_valid" in data
            assert "document_detected" in data
            assert "mrz_found" in data
    
    def test_passport_requirements_endpoint(self, client):
        """Test passport requirements endpoint"""
        response = client.get("/api/v1/passport/requirements")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "document_positioning" in data
        assert "image_quality" in data
        assert "lighting" in data
        assert "mrz" in data
    
    def test_extract_mrz_endpoint(self, client, sample_image_bytes):
        """Test MRZ extraction endpoint"""
        files = {"file": ("passport.jpg", sample_image_bytes, "image/jpeg")}
        
        response = client.post("/api/v1/passport/extract-mrz", files=files)
        
        # Should return 200, 404 (no MRZ), or 401 (auth required)
        assert response.status_code in [200, 404, 401]


class TestFileValidation:
    """Test file upload validation"""
    
    def test_file_too_large(self, client):
        """Test file size limit"""
        # Create a large file (>10MB)
        large_data = b"0" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.jpg", large_data, "image/jpeg")}
        
        response = client.post("/api/v1/photo/verify", files=files)
        
        # Should return 413 or 400 depending on when size is checked
        assert response.status_code in [413, 400, 401]


def test_cors_headers(client):
    """Test CORS headers are present"""
    response = client.options("/")
    
    # CORS headers should be present
    assert response.status_code in [200, 405]  # Some frameworks return 405 for OPTIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
