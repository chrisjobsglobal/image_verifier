"""Unit tests for verification services"""

import pytest
import numpy as np
import cv2
from app.services.image_quality import ImageQualityService
from app.services.face_detection import FaceDetectionService


class TestImageQualityService:
    """Tests for ImageQualityService"""
    
    @pytest.fixture
    def service(self):
        return ImageQualityService()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        # Create a 1920x1080 color image
        image = np.ones((1080, 1920, 3), dtype=np.uint8) * 200  # Light gray
        return image
    
    def test_check_blur_sharp_image(self, service, sample_image):
        """Test blur detection on sharp image"""
        # Add some edges to make it sharp
        cv2.rectangle(sample_image, (400, 300), (1500, 700), (100, 100, 100), 2)
        
        blur_score, is_blurry = service.check_blur(sample_image)
        
        assert isinstance(blur_score, float)
        assert isinstance(is_blurry, bool)
        assert blur_score > 0
    
    def test_check_brightness(self, service, sample_image):
        """Test brightness detection"""
        brightness, status = service.check_brightness(sample_image)
        
        assert isinstance(brightness, float)
        assert status in ["too_dark", "too_bright", "good"]
        assert brightness > 0
    
    def test_check_contrast(self, service, sample_image):
        """Test contrast detection"""
        # Add some contrast
        cv2.rectangle(sample_image, (400, 300), (1500, 700), (50, 50, 50), -1)
        
        contrast, has_good_contrast = service.check_contrast(sample_image)
        
        assert isinstance(contrast, float)
        assert isinstance(has_good_contrast, bool)
    
    def test_assess_quality(self, service, sample_image):
        """Test complete quality assessment"""
        results = service.assess_quality(sample_image)
        
        assert "is_valid" in results
        assert "errors" in results
        assert "warnings" in results
        assert "metrics" in results
        
        assert isinstance(results["is_valid"], bool)
        assert isinstance(results["errors"], list)
        assert isinstance(results["metrics"], dict)
    
    def test_detect_shadows(self, service, sample_image):
        """Test shadow detection"""
        has_shadows, shadow_percentage = service.detect_shadows(sample_image)
        
        assert isinstance(has_shadows, bool)
        assert isinstance(shadow_percentage, float)
        assert 0 <= shadow_percentage <= 100
    
    def test_detect_flash_reflection(self, service, sample_image):
        """Test flash reflection detection"""
        # Add a bright spot
        cv2.circle(sample_image, (960, 540), 50, (255, 255, 255), -1)
        
        has_reflection, reflection_regions = service.detect_flash_reflection(sample_image)
        
        assert isinstance(has_reflection, bool)
        assert isinstance(reflection_regions, list)


class TestFaceDetectionService:
    """Tests for FaceDetectionService"""
    
    @pytest.fixture
    def service(self):
        return FaceDetectionService()
    
    @pytest.fixture
    def sample_image_with_face(self):
        """Create a sample image (actual face detection requires real images)"""
        # For real testing, you'd load actual face images
        # This is a placeholder
        image = np.ones((1080, 1920, 3), dtype=np.uint8) * 200
        return image
    
    def test_calculate_face_percentage(self, service, sample_image_with_face):
        """Test face percentage calculation"""
        face_location = (200, 1200, 800, 400)  # (top, right, bottom, left)
        
        percentage = service.calculate_face_percentage(sample_image_with_face, face_location)
        
        assert isinstance(percentage, float)
        assert 0 <= percentage <= 100
    
    def test_check_face_centering(self, service, sample_image_with_face):
        """Test face centering check"""
        # Face centered in middle
        face_location = (390, 1110, 690, 810)  # Roughly centered
        
        is_centered, offset = service.check_face_centering(sample_image_with_face, face_location)
        
        assert isinstance(is_centered, bool)
        assert isinstance(offset, float)
        assert offset >= 0
    
    def test_analyze_face_no_face(self, service, sample_image_with_face):
        """Test face analysis with no face detected"""
        results = service.analyze_face(sample_image_with_face)
        
        assert "is_valid" in results
        assert "face_detected" in results
        assert "errors" in results
        assert "warnings" in results
        assert "metrics" in results
        
        # With blank image, no face should be detected
        assert results["face_detected"] == False


def test_service_initialization():
    """Test that services can be initialized"""
    image_quality_service = ImageQualityService()
    face_detection_service = FaceDetectionService()
    
    assert image_quality_service is not None
    assert face_detection_service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
