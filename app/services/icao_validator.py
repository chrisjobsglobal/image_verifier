"""ICAO 9303 Compliance Validator Service"""

from typing import Dict, List
import cv2
import numpy as np
from app.core.config import settings
from app.services.image_quality import image_quality_service
from app.services.face_detection import face_detection_service


class ICAOValidatorService:
    """Service for validating compliance with ICAO 9303 standards"""
    
    def __init__(self):
        self.image_quality_service = image_quality_service
        self.face_detection_service = face_detection_service
    
    def validate_photo_compliance(self, image: np.ndarray) -> Dict:
        """
        Validate personal photo compliance with ICAO 9303 standards.
        
        Args:
            image: Image as numpy array in BGR format
            
        Returns:
            Dictionary with comprehensive ICAO compliance results
        """
        results = {
            "is_compliant": True,
            "compliance_score": 100.0,
            "errors": [],
            "warnings": [],
            "validations": {}
        }
        
        # 1. Image Quality Validation
        quality_results = self.image_quality_service.assess_quality(image)
        results["validations"]["image_quality"] = quality_results
        
        if not quality_results["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(quality_results["errors"])
        
        results["warnings"].extend(quality_results.get("warnings", []))
        
        # 2. Face Detection and Analysis
        face_results = self.face_detection_service.analyze_face(image)
        results["validations"]["face_analysis"] = face_results
        
        if not face_results["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(face_results["errors"])
        
        results["warnings"].extend(face_results.get("warnings", []))
        
        # 3. Background Validation
        background_validation = self._validate_background(image, face_results)
        results["validations"]["background"] = background_validation
        
        if not background_validation["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(background_validation["errors"])
        
        results["warnings"].extend(background_validation.get("warnings", []))
        
        # 4. Lighting Validation
        lighting_validation = self._validate_lighting(image)
        results["validations"]["lighting"] = lighting_validation
        
        if not lighting_validation["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(lighting_validation["errors"])
        
        # 5. Head Covering and Glasses Validation
        accessories_validation = self._validate_accessories(image, face_results)
        results["validations"]["accessories"] = accessories_validation
        
        if not accessories_validation["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(accessories_validation["errors"])
        
        results["warnings"].extend(accessories_validation.get("warnings", []))
        
        # 6. Additional ICAO Requirements
        additional_checks = self._perform_additional_icao_checks(image)
        results["validations"]["additional_checks"] = additional_checks
        
        if not additional_checks["is_valid"]:
            results["warnings"].extend(additional_checks.get("warnings", []))
        
        # Calculate compliance score
        results["compliance_score"] = self._calculate_compliance_score(results)
        
        return results
    
    def validate_passport_document(self, image: np.ndarray) -> Dict:
        """
        Validate passport document image compliance with ICAO standards.
        
        Args:
            image: Image as numpy array in BGR format
            
        Returns:
            Dictionary with passport document validation results
        """
        results = {
            "is_compliant": True,
            "errors": [],
            "warnings": [],
            "validations": {}
        }
        
        # 1. Document Positioning Validation
        positioning = self._validate_document_positioning(image)
        results["validations"]["positioning"] = positioning
        
        if not positioning["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(positioning["errors"])
        
        # 2. Document Quality Validation
        quality = self.image_quality_service.assess_quality(image)
        results["validations"]["quality"] = quality
        
        if not quality["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(quality["errors"])
        
        # 3. Lighting and Reflections
        lighting = self._validate_document_lighting(image)
        results["validations"]["lighting"] = lighting
        
        if not lighting["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(lighting["errors"])
        
        return results
    
    def _validate_background(self, image: np.ndarray, face_results: Dict) -> Dict:
        """Validate background requirements"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not face_results.get("face_detected"):
            validation["errors"].append("Cannot validate background without detected face")
            validation["is_valid"] = False
            return validation
        
        # Get face location
        face_location = face_results["metrics"].get("face_location", {})
        if not face_location:
            validation["errors"].append("Face location not available for background analysis")
            validation["is_valid"] = False
            return validation
        
        # Analyze background regions (areas outside face)
        height, width = image.shape[:2]
        
        # Define background sampling regions (top corners and sides)
        background_regions = [
            (0, 0, width//4, height//4),  # Top-left
            (3*width//4, 0, width//4, height//4),  # Top-right
            (0, height//3, width//6, height//3),  # Left-middle
            (5*width//6, height//3, width//6, height//3),  # Right-middle
        ]
        
        background_colors = []
        for x, y, w, h in background_regions:
            region = image[y:y+h, x:x+w]
            avg_color = np.mean(region, axis=(0, 1))
            background_colors.append(avg_color)
        
        # Check uniformity across regions
        color_variance = np.var(background_colors, axis=0)
        is_uniform = all(var < 400 for var in color_variance)  # Threshold for uniformity
        
        if not is_uniform:
            validation["errors"].append("Background is not uniform. Use a plain, light-colored background")
            validation["is_valid"] = False
        
        # Check background color (should be light)
        avg_background = np.mean(background_colors, axis=0)
        avg_brightness = np.mean(avg_background)
        
        if avg_brightness < 180:  # Should be light colored
            validation["errors"].append("Background is too dark. Use a light-colored (white or light gray) background")
            validation["is_valid"] = False
        
        # Check contrast between face and background
        face_region = image[
            face_location["top"]:face_location["bottom"],
            face_location["left"]:face_location["right"]
        ]
        avg_face_brightness = np.mean(face_region)
        contrast = abs(avg_brightness - avg_face_brightness)
        
        if contrast < 30:
            validation["warnings"].append("Low contrast between face and background")
        
        return validation
    
    def _validate_lighting(self, image: np.ndarray) -> Dict:
        """Validate lighting requirements"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for shadows
        has_shadows, shadow_percentage = self.image_quality_service.detect_shadows(image)
        
        if has_shadows:
            validation["errors"].append(
                f"Shadows detected ({shadow_percentage:.1f}% of image). "
                "Ensure uniform lighting with no shadows on face or background"
            )
            validation["is_valid"] = False
        
        # Check for flash reflections
        has_reflection, reflection_regions = self.image_quality_service.detect_flash_reflection(image)
        
        if has_reflection:
            validation["errors"].append(
                f"Flash reflections detected ({len(reflection_regions)} spots). "
                "Avoid using flash and ensure no glare"
            )
            validation["is_valid"] = False
        
        return validation
    
    def _validate_accessories(self, image: np.ndarray, face_results: Dict) -> Dict:
        """Validate glasses and head covering requirements"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for glasses
        glasses_detected = face_results.get("metrics", {}).get("glasses_detected", False)
        
        if glasses_detected:
            validation["warnings"].append(
                "Glasses detected. Ensure: "
                "(1) Eyes are clearly visible, "
                "(2) No flash reflections on lenses, "
                "(3) No tinted or dark lenses, "
                "(4) Frames do not cover eyes"
            )
            # Note: Glasses are allowed if they meet criteria, so not marking as invalid
        
        # Head coverings check would require additional ML model
        # For now, add warning about head covering requirements
        validation["warnings"].append(
            "Verify no head coverings except for religious reasons. "
            "If religious head covering, facial features from chin to forehead must be visible"
        )
        
        return validation
    
    def _perform_additional_icao_checks(self, image: np.ndarray) -> Dict:
        """Perform additional ICAO compliance checks"""
        validation = {
            "is_valid": True,
            "warnings": []
        }
        
        # Check image age (metadata would be needed - add warning)
        validation["warnings"].append(
            "Verify photo is no more than 6 months old"
        )
        
        # Check print quality recommendation
        validation["warnings"].append(
            "Ensure photo is printed on high-quality photo paper if submitting physical copy"
        )
        
        # Check color requirements
        if not self._is_color_photo(image):
            validation["warnings"].append(
                "Image appears to be grayscale. Photo should be in color with natural skin tones"
            )
        
        return validation
    
    def _validate_document_positioning(self, image: np.ndarray) -> Dict:
        """Validate passport document positioning"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Detect document edges
        document_region = self._detect_document_edges(image)
        
        if document_region is None:
            validation["errors"].append("Could not detect document boundaries")
            validation["is_valid"] = False
            return validation
        
        x, y, w, h = document_region
        
        # Calculate document percentage of image
        doc_area = w * h
        img_area = image.shape[0] * image.shape[1]
        doc_percentage = (doc_area / img_area) * 100
        
        min_doc_pct = settings.min_document_percentage
        max_doc_pct = settings.max_document_percentage
        
        if doc_percentage < min_doc_pct or doc_percentage > max_doc_pct:
            validation["errors"].append(
                f"Document occupies {doc_percentage:.1f}% of image. "
                f"Should be between {min_doc_pct}% and {max_doc_pct}%"
            )
            validation["is_valid"] = False
        
        # Check document angle/tilt
        angle = self._calculate_document_angle(image, document_region)
        
        if abs(angle) > settings.max_document_tilt_degrees:
            validation["errors"].append(
                f"Document is tilted {abs(angle):.1f}°. "
                f"Maximum allowed tilt: {settings.max_document_tilt_degrees}°"
            )
            validation["is_valid"] = False
        
        return validation
    
    def _validate_document_lighting(self, image: np.ndarray) -> Dict:
        """Validate passport document lighting"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for reflections/glare
        has_reflection, _ = self.image_quality_service.detect_flash_reflection(image)
        
        if has_reflection:
            validation["errors"].append(
                "Glare or reflections detected on document. "
                "Do not use flash and avoid reflective surfaces"
            )
            validation["is_valid"] = False
        
        return validation
    
    def _detect_document_edges(self, image: np.ndarray) -> tuple:
        """Detect document boundaries in image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest rectangular contour (likely the document)
        largest_area = 0
        largest_rect = None
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > largest_area:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                # Check if contour has 4 corners (rectangle)
                if len(approx) == 4:
                    largest_area = area
                    largest_rect = cv2.boundingRect(contour)
        
        return largest_rect
    
    def _calculate_document_angle(self, image: np.ndarray, document_region: tuple) -> float:
        """Calculate document tilt angle"""
        x, y, w, h = document_region
        
        # Extract document region
        doc_img = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(doc_img, cv2.COLOR_BGR2GRAY)
        
        # Detect lines using Hough transform
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
        
        if lines is None:
            return 0.0
        
        # Calculate average angle of detected lines
        angles = []
        for line in lines[:10]:  # Use first 10 lines
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            angles.append(angle)
        
        if angles:
            avg_angle = np.median(angles)
            return avg_angle
        
        return 0.0
    
    def _is_color_photo(self, image: np.ndarray) -> bool:
        """Check if image is in color"""
        if len(image.shape) < 3:
            return False
        
        # Check if color channels have variance (not grayscale)
        b, g, r = cv2.split(image)
        
        # If all channels are very similar, it's likely grayscale
        bg_diff = np.mean(np.abs(b.astype(int) - g.astype(int)))
        gr_diff = np.mean(np.abs(g.astype(int) - r.astype(int)))
        
        # If differences are very small, it's grayscale
        return bg_diff > 5 or gr_diff > 5
    
    def _calculate_compliance_score(self, results: Dict) -> float:
        """Calculate overall compliance score (0-100)"""
        total_checks = 0
        passed_checks = 0
        
        for validation_key, validation in results.get("validations", {}).items():
            total_checks += 1
            if validation.get("is_valid", True):
                passed_checks += 1
        
        if total_checks == 0:
            return 0.0
        
        base_score = (passed_checks / total_checks) * 100
        
        # Deduct points for warnings (minor issues)
        num_warnings = len(results.get("warnings", []))
        warning_penalty = min(num_warnings * 2, 20)  # Max 20 points deduction
        
        final_score = max(0, base_score - warning_penalty)
        
        return round(final_score, 2)


# Create global instance
icao_validator_service = ICAOValidatorService()
