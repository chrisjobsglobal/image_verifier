"""ICAO 9303 Compliance Validator Service"""

from typing import Dict, List
import cv2
import numpy as np
import logging
from app.core.config import settings
from app.services.image_quality import image_quality_service
from app.services.face_detection import face_detection_service

logger = logging.getLogger(__name__)


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
        
        # Detect if this is a scanned document vs camera photo
        is_scan = self._is_scanned_document(image)
        results["document_type"] = "SCAN" if is_scan else "PHOTO"
        
        # 1. Document Positioning Validation
        positioning = self._validate_document_positioning(image)
        results["validations"]["positioning"] = positioning
        
        if not positioning["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(positioning["errors"])
        
        # 2. Document Quality Validation (different thresholds for scans)
        quality = self.image_quality_service.assess_quality(image, is_scan=is_scan)
        results["validations"]["quality"] = quality
        
        if not quality["is_valid"]:
            results["is_compliant"] = False
            results["errors"].extend(quality["errors"])
        
        # 3. Lighting and Reflections (skip glare detection for scans)
        lighting = self._validate_document_lighting(image, is_scan=is_scan)
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
            "warnings": [],
            "metrics": {}
        }
        
        # Check if this is a scanned document
        is_scan = self._is_scanned_document(image)
        
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
        
        validation["metrics"]["document_percentage"] = doc_percentage
        validation["metrics"]["is_scanned_document"] = is_scan
        
        # Different thresholds for scanned documents vs photos
        if is_scan:
            # Scanned documents should fill 85-100% of frame
            min_doc_pct = 85.0
            max_doc_pct = 100.0
        else:
            # Photos of documents should be 30-95% with visible margins
            # (more lenient than personal ID photos which need 70-80% face coverage)
            min_doc_pct = settings.min_document_percentage
            max_doc_pct = settings.max_document_percentage
        
        if doc_percentage < min_doc_pct or doc_percentage > max_doc_pct:
            if is_scan:
                # For scans, this is unlikely but could happen if severely cropped
                validation["warnings"].append(
                    f"Scanned document occupies {doc_percentage:.1f}% of image. "
                    f"Expected 85-100% for scanned documents"
                )
            else:
                validation["errors"].append(
                    f"Passport document occupies {doc_percentage:.1f}% of image. "
                    f"Should be between {min_doc_pct}% and {max_doc_pct}% "
                    f"(document should be clearly visible with margins)"
                )
                validation["is_valid"] = False
        
        # Check document angle/tilt (more lenient for scans, strict for photos)
        angle = self._calculate_document_angle(image, document_region)
        validation["metrics"]["tilt_angle"] = angle
        
        # Different tilt thresholds:
        # - Scans: More lenient (warn at 5°, error at 15°) since rotation can be corrected
        # - Photos: Strict (warn at 3°, error at 10°) since it indicates camera handling issues
        if is_scan:
            warn_tilt = 5.0
            max_tilt = 15.0
        else:
            warn_tilt = 3.0
            max_tilt = settings.max_document_tilt_degrees
        
        if abs(angle) > max_tilt:
            validation["errors"].append(
                f"Document is tilted {abs(angle):.1f}°. "
                f"Maximum allowed tilt: {max_tilt}° for {'scans' if is_scan else 'photos'}. "
                f"Consider rotating the document before uploading."
            )
            validation["is_valid"] = False
        elif abs(angle) > warn_tilt:
            validation["warnings"].append(
                f"Document is tilted {abs(angle):.1f}°. "
                f"For best results, rotate the document to be perfectly aligned."
            )
        
        return validation
    
    def _validate_document_lighting(self, image: np.ndarray, is_scan: bool = False) -> Dict:
        """Validate passport document lighting"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Skip glare detection for scanned documents (uniform lighting is expected)
        if not is_scan:
            # Check for reflections/glare (only for camera photos)
            has_reflection, _ = self.image_quality_service.detect_flash_reflection(image)
            
            if has_reflection:
                # For passport documents, reflections are often from security features
                # (holograms, lamination), not just flash - make it a warning, not error
                validation["warnings"].append(
                    "Reflections detected on document. This may be from security features (holograms/lamination) "
                    "or camera flash. If using camera, avoid flash and position document to minimize glare"
                )
        
        return validation
    
    def _detect_document_edges(self, image: np.ndarray) -> tuple:
        """
        Detect document boundaries in image by finding the dominant rectangular region.
        Uses edge detection on border strips to find document edges.
        """
        height, width = image.shape[:2]
        
        # First, check if this looks like a scanned document (fills most of the frame)
        is_scan = self._is_scanned_document(image)
        
        if is_scan:
            # For scanned documents, the document IS the entire image
            # Return the full image dimensions with small margin
            margin = 10
            return (margin, margin, width - 2*margin, height - 2*margin)
        
        # For photos of documents, find the document edges
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply adaptive thresholding to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # No contours found, assume full image is document
            logger.warning("No contours found in document detection")
            return (0, 0, width, height)
        
        # Find the largest contour by area
        largest_contour = max(contours, key=cv2.contourArea)
        largest_area = cv2.contourArea(largest_contour)
        
        # If largest contour is too small (< 10% of image), assume full image
        min_area = (width * height) * 0.1
        if largest_area < min_area:
            logger.warning(f"Largest contour too small: {largest_area} < {min_area}")
            return (0, 0, width, height)
        
        # Get bounding rectangle of the largest contour
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Validate the bounding rectangle makes sense
        # Document should be at least 20% of image in each dimension
        if w < width * 0.2 or h < height * 0.2:
            logger.warning(f"Detected document too small: {w}x{h} in {width}x{height} image")
            return (0, 0, width, height)
        
        logger.info(f"Document detected at ({x}, {y}, {w}, {h}) - {w}x{h} in {width}x{height} image")
        
        return (x, y, w, h)
    
    def _is_scanned_document(self, image: np.ndarray) -> bool:
        """
        Detect if image is a scanned document (fills frame) vs photo of document (with background).
        
        Args:
            image: Input image
            
        Returns:
            True if appears to be a scan, False if photo with background
        """
        height, width = image.shape[:2]
        
        # Sample border regions (top, bottom, left, right edges)
        border_width = max(10, min(width, height) // 20)  # 5% of smallest dimension
        
        top_border = image[:border_width, :]
        bottom_border = image[-border_width:, :]
        left_border = image[:, :border_width]
        right_border = image[:, -border_width:]
        
        # Calculate standard deviation of each border
        # Low std dev suggests uniform background (photo)
        # High std dev suggests content (scan)
        top_std = np.std(cv2.cvtColor(top_border, cv2.COLOR_BGR2GRAY))
        bottom_std = np.std(cv2.cvtColor(bottom_border, cv2.COLOR_BGR2GRAY))
        left_std = np.std(cv2.cvtColor(left_border, cv2.COLOR_BGR2GRAY))
        right_std = np.std(cv2.cvtColor(right_border, cv2.COLOR_BGR2GRAY))
        
        avg_border_std = (top_std + bottom_std + left_std + right_std) / 4
        
        logger.info(f"Border analysis - avg_std: {avg_border_std:.2f}, threshold: 15")
        
        # CORRECTED LOGIC:
        # Low std dev (<15) = uniform borders (white margins from PDF/scan) = SCANNED DOCUMENT
        # High std dev (>15) = content/background variation = PHOTO WITH BACKGROUND
        # 
        # PDFs converted to images have white margins with std dev ~0
        # Photos of documents on tables/backgrounds have variation in borders
        is_scan = avg_border_std < 15
        logger.info(f"Document type detected: {'SCAN' if is_scan else 'PHOTO'}")
        
        return is_scan
    
    def _calculate_document_angle(self, image: np.ndarray, document_region: tuple) -> float:
        """
        Calculate document tilt angle by analyzing ONLY the outermost border pixels.
        This avoids false positives from internal content like flags, photos, or MRZ text.
        We sample only the very edge pixels of the document to determine rotation.
        """
        x, y, w, h = document_region
        
        # Extract document region
        doc_img = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(doc_img, cv2.COLOR_BGR2GRAY)
        
        # Define how many pixels from the edge to sample (very thin border strip)
        border_width = 5  # Only analyze the outermost 5 pixels
        
        # Extract ONLY the border strips (top, bottom, left, right edges)
        top_strip = gray[:border_width, :]
        bottom_strip = gray[-border_width:, :]
        left_strip = gray[:, :border_width]
        right_strip = gray[:, -border_width:]
        
        # Detect edges in each border strip
        all_angles = []
        
        # Top and bottom borders (horizontal edges)
        for strip in [top_strip, bottom_strip]:
            edges = cv2.Canny(strip, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20,
                                   minLineLength=50, maxLineGap=10)
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # For horizontal edges, we expect angles near 0° or 180°
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    all_angles.append(angle)
        
        # Left and right borders (vertical edges)
        for strip in [left_strip, right_strip]:
            edges = cv2.Canny(strip, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20,
                                   minLineLength=50, maxLineGap=10)
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # For vertical edges, convert to rotation angle
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    # Vertical lines should be 90° or -90°, adjust to 0-based rotation
                    if abs(angle - 90) < 45 or abs(angle + 90) < 45:
                        # This is a vertical edge, convert to rotation
                        if angle > 0:
                            rotation = angle - 90
                        else:
                            rotation = angle + 90
                        all_angles.append(rotation)
        
        if not all_angles:
            return 0.0
        
        # Normalize all angles to -90 to 90 range
        normalized_angles = []
        for angle in all_angles:
            while angle > 90:
                angle -= 180
            while angle < -90:
                angle += 180
            # Filter out extreme outliers (likely noise)
            if abs(angle) < 60:  # Only keep reasonable tilt angles
                normalized_angles.append(angle)
        
        if not normalized_angles:
            return 0.0
        
        # Use median to be robust against outliers
        median_angle = np.median(normalized_angles)
        
        # Round to nearest 0.5 degrees
        return round(median_angle * 2) / 2
    
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
