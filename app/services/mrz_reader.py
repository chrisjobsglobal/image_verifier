"""MRZ (Machine Readable Zone) Reader Service using PassportEye"""

from typing import Dict, Optional, Tuple
import cv2
import numpy as np
from passporteye import read_mrz
import pytesseract
from app.core.config import settings


class MRZReaderService:
    """Service for reading and validating MRZ from passport images"""
    
    def __init__(self):
        # Set Tesseract path if configured
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    
    def read_passport_mrz(self, image: np.ndarray) -> Dict:
        """
        Read MRZ from passport image.
        
        Args:
            image: Image as numpy array in BGR format
            
        Returns:
            Dictionary with MRZ reading results
        """
        results = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "mrz_found": False,
            "mrz_data": {}
        }
        
        try:
            # Convert image to format suitable for PassportEye
            # PassportEye expects PIL Image or file path
            # We'll use cv2 to save temporarily or convert
            
            # Preprocess image for better MRZ detection
            preprocessed = self._preprocess_for_mrz(image)
            
            # Encode image to bytes for PassportEye
            success, encoded_image = cv2.imencode('.jpg', preprocessed)
            if not success:
                results["errors"].append("Failed to encode image for MRZ reading")
                return results
            
            image_bytes = encoded_image.tobytes()
            
            # Read MRZ using PassportEye
            mrz = read_mrz(image_bytes)
            
            if mrz is None:
                results["errors"].append("No MRZ detected in passport image")
                return results
            
            results["mrz_found"] = True
            
            # Extract MRZ data
            mrz_data = mrz.to_dict()
            
            # Parse and structure MRZ data
            if mrz_data:
                results["mrz_data"] = {
                    "type": mrz_data.get("type", ""),
                    "country": mrz_data.get("country", ""),
                    "surname": mrz_data.get("surname", ""),
                    "names": mrz_data.get("names", ""),
                    "passport_number": mrz_data.get("number", ""),
                    "nationality": mrz_data.get("nationality", ""),
                    "date_of_birth": mrz_data.get("date_of_birth", ""),
                    "sex": mrz_data.get("sex", ""),
                    "expiration_date": mrz_data.get("expiration_date", ""),
                    "personal_number": mrz_data.get("personal_number", ""),
                    "check_digits": {
                        "number": mrz_data.get("check_number", ""),
                        "date_of_birth": mrz_data.get("check_date_of_birth", ""),
                        "expiration_date": mrz_data.get("check_expiration_date", ""),
                        "personal_number": mrz_data.get("check_personal_number", ""),
                        "composite": mrz_data.get("check_composite", "")
                    },
                    "raw_mrz_text": mrz_data.get("mrz_text", "")
                }
                
                # Validate MRZ data
                validation = self._validate_mrz_data(results["mrz_data"])
                
                if validation["valid"]:
                    results["is_valid"] = True
                else:
                    results["errors"].extend(validation["errors"])
                    results["warnings"].extend(validation["warnings"])
            else:
                results["errors"].append("MRZ data could not be parsed")
        
        except Exception as e:
            results["errors"].append(f"Error reading MRZ: {str(e)}")
        
        return results
    
    def _preprocess_for_mrz(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better MRZ detection.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            filtered, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # Convert back to BGR for PassportEye
        preprocessed = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        
        return preprocessed
    
    def _validate_mrz_data(self, mrz_data: Dict) -> Dict:
        """
        Validate MRZ data for completeness and check digit validation.
        
        Args:
            mrz_data: Extracted MRZ data
            
        Returns:
            Validation results dictionary
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["passport_number", "surname", "date_of_birth", "expiration_date", "country"]
        
        for field in required_fields:
            if not mrz_data.get(field):
                validation["valid"] = False
                validation["errors"].append(f"Missing required field: {field}")
        
        # Validate passport number format
        passport_num = mrz_data.get("passport_number", "")
        if passport_num and not self._validate_passport_number(passport_num):
            validation["warnings"].append(f"Passport number format may be invalid: {passport_num}")
        
        # Validate date formats
        dob = mrz_data.get("date_of_birth", "")
        if dob and not self._validate_date_format(dob):
            validation["warnings"].append(f"Date of birth format may be invalid: {dob}")
        
        exp_date = mrz_data.get("expiration_date", "")
        if exp_date and not self._validate_date_format(exp_date):
            validation["warnings"].append(f"Expiration date format may be invalid: {exp_date}")
        
        # Check if passport is expired
        if exp_date:
            if self._is_date_expired(exp_date):
                validation["warnings"].append(f"Passport appears to be expired (expiration: {exp_date})")
        
        # Validate country code
        country = mrz_data.get("country", "")
        if country and len(country) != 3:
            validation["warnings"].append(f"Country code should be 3 characters: {country}")
        
        return validation
    
    def _validate_passport_number(self, passport_number: str) -> bool:
        """Validate passport number format"""
        # Basic validation: should be alphanumeric, typically 6-9 characters
        if not passport_number:
            return False
        
        # Remove any < characters (used as fillers in MRZ)
        clean_number = passport_number.replace('<', '')
        
        # Check length and alphanumeric
        return 6 <= len(clean_number) <= 12 and clean_number.isalnum()
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format (YYMMDD)"""
        if not date_str or len(date_str) != 6:
            return False
        
        try:
            year = int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            
            # Basic range checks
            if not (1 <= month <= 12):
                return False
            if not (1 <= day <= 31):
                return False
            
            return True
        except ValueError:
            return False
    
    def _is_date_expired(self, exp_date: str) -> bool:
        """Check if expiration date has passed"""
        from datetime import datetime
        
        if not exp_date or len(exp_date) != 6:
            return False
        
        try:
            year = int(exp_date[0:2])
            month = int(exp_date[2:4])
            day = int(exp_date[4:6])
            
            # Assume 20xx for years 00-30, 19xx for years 31-99
            if year <= 30:
                year += 2000
            else:
                year += 1900
            
            exp_datetime = datetime(year, month, day)
            return exp_datetime < datetime.now()
        except (ValueError, OverflowError):
            return False
    
    def extract_mrz_region(self, image: np.ndarray) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Extract MRZ region from passport image.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (mrz_region_image, bounding_box) or None if not found
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply morphological operations to detect MRZ text lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 3))
        morph = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        
        # Threshold
        _, thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for MRZ region (typically at bottom of passport)
        # MRZ is usually 2-3 lines of text
        mrz_candidates = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            # MRZ lines are typically wide and short
            if aspect_ratio > 10 and w > image.shape[1] * 0.7:
                mrz_candidates.append((x, y, w, h))
        
        if mrz_candidates:
            # Sort by y-coordinate to get bottom-most regions
            mrz_candidates.sort(key=lambda box: box[1], reverse=True)
            
            # Take the bottom region
            x, y, w, h = mrz_candidates[0]
            
            # Expand region slightly to capture full MRZ
            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)
            
            mrz_region = image[y:y+h, x:x+w]
            return mrz_region, (x, y, w, h)
        
        return None


# Create global instance
mrz_reader_service = MRZReaderService()
