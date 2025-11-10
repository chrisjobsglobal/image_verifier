"""Image Quality Assessment Service"""

from typing import Dict, List, Tuple
import cv2
import numpy as np
from app.core.config import settings


class ImageQualityService:
    """Service for assessing image quality metrics"""
    
    def __init__(self):
        self.blur_threshold = settings.blur_threshold
        self.min_brightness = settings.min_brightness
        self.max_brightness = settings.max_brightness
        self.min_contrast = settings.min_contrast
    
    def assess_quality(self, image: np.ndarray) -> Dict:
        """
        Perform comprehensive image quality assessment.
        
        Args:
            image: Image as numpy array in BGR format
            
        Returns:
            Dictionary with quality assessment results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        # Check blur
        blur_score, is_blurry = self.check_blur(image)
        results["metrics"]["blur_score"] = blur_score
        results["metrics"]["is_blurry"] = is_blurry
        if is_blurry:
            results["is_valid"] = False
            results["errors"].append(
                f"Image is blurry (score: {blur_score:.2f}, threshold: {self.blur_threshold})"
            )
        
        # Check brightness
        brightness, brightness_status = self.check_brightness(image)
        results["metrics"]["brightness"] = brightness
        results["metrics"]["brightness_status"] = brightness_status
        if brightness_status != "good":
            results["is_valid"] = False
            results["errors"].append(
                f"Image brightness is {brightness_status} (value: {brightness:.2f})"
            )
        
        # Check contrast
        contrast, has_good_contrast = self.check_contrast(image)
        results["metrics"]["contrast"] = contrast
        results["metrics"]["has_good_contrast"] = has_good_contrast
        if not has_good_contrast:
            results["is_valid"] = False
            results["errors"].append(
                f"Image has poor contrast (value: {contrast:.2f}, minimum: {self.min_contrast})"
            )
        
        # Check resolution
        width, height = image.shape[1], image.shape[0]
        results["metrics"]["width"] = width
        results["metrics"]["height"] = height
        results["metrics"]["resolution"] = f"{width}x{height}"
        
        if width < settings.min_image_width or height < settings.min_image_height:
            results["is_valid"] = False
            results["errors"].append(
                f"Image resolution too low ({width}x{height}). "
                f"Minimum required: {settings.min_image_width}x{settings.min_image_height}"
            )
        
        # Check for excessive noise
        noise_level = self.estimate_noise(image)
        results["metrics"]["noise_level"] = noise_level
        if noise_level > 15.0:  # High noise threshold
            results["warnings"].append(
                f"Image has high noise level ({noise_level:.2f})"
            )
        
        # Check sharpness
        sharpness = self.calculate_sharpness(image)
        results["metrics"]["sharpness"] = sharpness
        if sharpness < 50.0:  # Low sharpness threshold
            results["warnings"].append(
                f"Image sharpness is low ({sharpness:.2f})"
            )
        
        return results
    
    def check_blur(self, image: np.ndarray) -> Tuple[float, bool]:
        """
        Detect blur using Laplacian variance method.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (blur_score, is_blurry)
            Higher score = sharper image
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_blurry = laplacian_var < self.blur_threshold
        return laplacian_var, is_blurry
    
    def check_brightness(self, image: np.ndarray) -> Tuple[float, str]:
        """
        Check image brightness level.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (brightness_value, status)
            Status can be: "too_dark", "too_bright", or "good"
        """
        # Convert to LAB color space and extract L channel
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # Calculate mean brightness
        brightness = np.mean(l_channel)
        
        if brightness < self.min_brightness:
            status = "too_dark"
        elif brightness > self.max_brightness:
            status = "too_bright"
        else:
            status = "good"
        
        return brightness, status
    
    def check_contrast(self, image: np.ndarray) -> Tuple[float, bool]:
        """
        Check image contrast level.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (contrast_value, has_good_contrast)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate standard deviation as contrast measure
        contrast = np.std(gray)
        
        has_good_contrast = contrast >= self.min_contrast
        
        return contrast, has_good_contrast
    
    def estimate_noise(self, image: np.ndarray) -> float:
        """
        Estimate noise level in image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Noise level estimate
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use Laplacian to estimate noise
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise = np.std(laplacian)
        
        return noise
    
    def calculate_sharpness(self, image: np.ndarray) -> float:
        """
        Calculate image sharpness using edge detection.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Sharpness score
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use Sobel edge detection
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate magnitude
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        sharpness = np.mean(magnitude)
        
        return sharpness
    
    def detect_shadows(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect shadows in image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (has_shadows, shadow_percentage)
        """
        # Convert to LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # Threshold for dark regions
        _, dark_regions = cv2.threshold(l_channel, 50, 255, cv2.THRESH_BINARY_INV)
        
        # Calculate percentage of dark pixels
        total_pixels = dark_regions.shape[0] * dark_regions.shape[1]
        dark_pixels = np.sum(dark_regions == 255)
        shadow_percentage = (dark_pixels / total_pixels) * 100
        
        # If more than 15% is very dark, likely has shadows
        has_shadows = shadow_percentage > 15.0
        
        return has_shadows, shadow_percentage
    
    def detect_flash_reflection(self, image: np.ndarray) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """
        Detect bright flash reflections in image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (has_reflection, reflection_regions)
            reflection_regions: List of (x, y, width, height) tuples
        """
        # Convert to LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # Threshold for very bright regions
        _, bright_regions = cv2.threshold(l_channel, 220, 255, cv2.THRESH_BINARY)
        
        # Find contours of bright regions
        contours, _ = cv2.findContours(bright_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        reflection_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            # Only consider significant bright spots
            if area > 100:  # Minimum area threshold
                x, y, w, h = cv2.boundingRect(contour)
                reflection_regions.append((x, y, w, h))
        
        has_reflection = len(reflection_regions) > 0
        
        return has_reflection, reflection_regions
    
    def check_uniform_background(self, image: np.ndarray, 
                                 background_region: Tuple[int, int, int, int]) -> Tuple[bool, str]:
        """
        Check if background region is uniform.
        
        Args:
            image: Image as numpy array
            background_region: (x, y, width, height) of background area to check
            
        Returns:
            Tuple of (is_uniform, background_color)
        """
        x, y, w, h = background_region
        background = image[y:y+h, x:x+w]
        
        # Calculate color variance
        std_dev = np.std(background, axis=(0, 1))
        mean_color = np.mean(background, axis=(0, 1))
        
        # Background is uniform if standard deviation is low across all channels
        is_uniform = all(std < 20 for std in std_dev)  # Threshold for uniformity
        
        # Determine background color
        brightness = np.mean(mean_color)
        if brightness > 200:
            bg_color = "white"
        elif brightness > 150:
            bg_color = "light_gray"
        elif brightness > 100:
            bg_color = "gray"
        else:
            bg_color = "dark"
        
        return is_uniform, bg_color


# Create global instance
image_quality_service = ImageQualityService()
