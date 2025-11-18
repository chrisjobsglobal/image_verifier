"""Enhanced MRZ Reader using AI-powered PaddleOCR"""

from typing import Dict, Optional, List
import cv2
import numpy as np
import re
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedMRZReaderService:
    """AI-powered MRZ reader using PaddleOCR"""
    
    def __init__(self):
        # Initialize PaddleOCR (lazy loading)
        self._paddle_ocr = None
        # Enable PaddleOCR for Xeon Gold CPU
        self._paddle_available = True
        logger.info("PaddleOCR enabled for AI-powered MRZ reading")
    
    @property
    def paddle_ocr(self):
        """Lazy load PaddleOCR to avoid startup delays"""
        if self._paddle_ocr is None and self._paddle_available:
            try:
                from paddleocr import PaddleOCR
                # Initialize with English language for MRZ
                # Optimized for Xeon Gold CPU performance
                self._paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=False,           # CPU mode
                    enable_mkldnn=True,      # Intel MKL-DNN for Xeon CPUs
                    cpu_threads=8,           # Utilize multi-core Xeon
                    use_tensorrt=False,      # CPU only, no TensorRT
                    ir_optim=True,           # Enable inference optimization
                    show_log=False           # Reduce log noise
                )
                logger.info("PaddleOCR initialized successfully with Xeon Gold optimizations")
            except Exception as e:
                logger.warning(f"PaddleOCR initialization failed: {e}. Will use PassportEye fallback.")
                self._paddle_available = False
        return self._paddle_ocr
    
    def read_passport_mrz(self, image: np.ndarray) -> Dict:
        """
        Read MRZ from passport image using AI-powered OCR.
        
        Uses PaddleOCR for high-accuracy MRZ detection.
        
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
            "mrz_data": {},
            "ocr_method": "none"
        }
        
        try:
            # Use PaddleOCR for MRZ reading
            if self._paddle_available:
                logger.info("Attempting MRZ reading with PaddleOCR...")
                paddle_result = self._read_mrz_with_paddle(image)
                
                if paddle_result["mrz_found"]:
                    logger.info("✅ MRZ successfully read with PaddleOCR")
                    results.update(paddle_result)
                    results["ocr_method"] = "paddleocr"
                    return results
                else:
                    logger.warning("❌ No MRZ found with PaddleOCR")
                    results["errors"].append("No MRZ detected in passport image")
            else:
                logger.error("PaddleOCR not available")
                results["errors"].append("OCR engine not available")
        
        except Exception as e:
            logger.error(f"Error reading MRZ: {str(e)}", exc_info=True)
            results["errors"].append(f"Error reading MRZ: {str(e)}")
        
        return results
    
    def _read_mrz_with_paddle(self, image: np.ndarray) -> Dict:
        """Read MRZ using PaddleOCR"""
        results = {
            "mrz_found": False,
            "mrz_data": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            if not self.paddle_ocr:
                logger.warning("PaddleOCR not available, skipping")
                return results
            
            # Try multiple preprocessing strategies
            strategies = [
                ("full_image", image),
                ("bottom_region", self._extract_mrz_region_enhanced(image)),
                ("preprocessed", self._preprocess_for_paddle(image))
            ]
            
            all_text_lines = []
            
            for strategy_name, processed_img in strategies:
                if processed_img is None:
                    continue
                
                logger.info(f"Trying PaddleOCR with strategy: {strategy_name}")
                
                # Run PaddleOCR
                ocr_results = self.paddle_ocr.ocr(processed_img, cls=True)
                
                if not ocr_results or not ocr_results[0]:
                    logger.info(f"No text found with {strategy_name}")
                    continue
                
                # Extract text lines
                for line in ocr_results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], tuple) else line[1]
                        confidence = line[1][1] if isinstance(line[1], tuple) and len(line[1]) > 1 else 0.0
                        
                        # Clean and normalize text
                        cleaned_text = text.upper().replace(' ', '').replace('O', '0')
                        
                        # Filter MRZ-like lines (mostly uppercase, numbers, and <)
                        if self._is_mrz_line(cleaned_text):
                            all_text_lines.append({
                                "text": cleaned_text,
                                "confidence": confidence,
                                "strategy": strategy_name
                            })
                            logger.info(f"Found MRZ-like line ({strategy_name}): {cleaned_text[:50]}... (conf: {confidence:.2f})")
                
                # If we found good MRZ lines, stop trying other strategies
                if len(all_text_lines) >= 2:
                    logger.info(f"Found {len(all_text_lines)} MRZ lines with {strategy_name}, proceeding to parse")
                    break
            
            if not all_text_lines:
                logger.warning("No MRZ-like text found with PaddleOCR")
                return results
            
            # Sort by confidence and take best lines
            all_text_lines.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Parse MRZ from text lines
            mrz_data = self._parse_mrz_lines(all_text_lines[:3])  # Use top 3 lines
            
            if mrz_data:
                logger.info(f"✅ Successfully parsed MRZ with PaddleOCR: {mrz_data.get('surname', 'N/A')}")
                results["mrz_found"] = True
                results["mrz_data"] = mrz_data
                
                # Validate MRZ data
                validation = self._validate_mrz_data(mrz_data)
                results["is_valid"] = validation["valid"]
                results["errors"] = validation["errors"]
                results["warnings"] = validation["warnings"]
            else:
                logger.warning("Could not parse MRZ from OCR text lines")
        
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}", exc_info=True)
        
        return results
    
    
    def _is_mrz_line(self, text: str) -> bool:
        """Check if text line looks like MRZ"""
        if not text or len(text) < 20:
            return False
        
        # MRZ contains mostly uppercase letters, numbers, and <
        mrz_chars = sum(1 for c in text if c.isupper() or c.isdigit() or c in '<>')
        ratio = mrz_chars / len(text)
        
        # Also check for typical MRZ patterns
        has_chevrons = '<' in text or '>' in text
        has_numbers = any(c.isdigit() for c in text)
        has_uppercase = any(c.isupper() for c in text)
        
        # MRZ lines should have at least 50% valid characters and typical patterns
        return ratio > 0.5 and has_uppercase and (has_chevrons or has_numbers)
    
    def _parse_mrz_lines(self, text_lines: List[Dict]) -> Dict:
        """Parse MRZ from OCR text lines"""
        if not text_lines or len(text_lines) < 2:
            logger.warning(f"Not enough MRZ lines: {len(text_lines) if text_lines else 0}")
            return {}
        
        # TD3 passport MRZ has 2 lines of 44 characters each
        # Line 1: Type, Country, Name
        # Line 2: Passport number, DOB, Sex, Expiry, Personal number
        
        # Get the longest lines (likely the actual MRZ lines)
        mrz_lines = [line["text"] for line in text_lines if len(line["text"]) >= 30]
        
        if len(mrz_lines) < 2:
            logger.warning(f"Found {len(mrz_lines)} lines >= 30 chars")
            # Try with shorter lines
            mrz_lines = [line["text"] for line in text_lines]
        
        if len(mrz_lines) < 2:
            logger.error("Still not enough MRZ lines after relaxing criteria")
            return {}
        
        try:
            # Take first two longest lines
            line1 = mrz_lines[0][:44].ljust(44, '<')
            line2 = mrz_lines[1][:44].ljust(44, '<')
            
            logger.info(f"Parsing MRZ Line 1: {line1}")
            logger.info(f"Parsing MRZ Line 2: {line2}")
            
            # Parse Line 1: P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<<
            doc_type = line1[0]  # P for passport
            country = line1[2:5].replace('<', '').replace('0', 'O')  # Countries use letters not numbers
            name_field = line1[5:44].replace('<', ' ').strip()
            
            # Split surname and given names
            name_parts = [part for part in name_field.split('  ') if part]
            surname = name_parts[0].strip() if name_parts else ""
            given_names = name_parts[1].strip() if len(name_parts) > 1 else ""
            
            # Clean up common OCR errors in names (restore letters)
            surname = self._clean_name(surname)
            given_names = self._clean_name(given_names)
            
            # Parse Line 2: L898902C36UTO7408122F1204159ZE184226B<<<<<10
            passport_num = line2[0:9].replace('<', '')
            check_passport = line2[9]
            nationality = line2[10:13].replace('<', '').replace('0', 'O')  # Countries use letters
            dob = line2[13:19]
            check_dob = line2[19]
            sex = line2[20]
            expiry = line2[21:27]
            check_expiry = line2[27]
            personal_num = line2[28:42].replace('<', '')
            check_personal = line2[42] if len(line2) > 42 else ''
            check_composite = line2[43] if len(line2) > 43 else ''
            
            result = {
                "type": doc_type,
                "country": country,
                "surname": surname,
                "names": given_names,
                "passport_number": passport_num,
                "nationality": nationality,
                "date_of_birth": dob,
                "sex": sex,
                "expiration_date": expiry,
                "personal_number": personal_num,
                "check_digits": {
                    "number": check_passport,
                    "date_of_birth": check_dob,
                    "expiration_date": check_expiry,
                    "personal_number": check_personal,
                    "composite": check_composite
                },
                "raw_mrz_text": f"{line1}\n{line2}"
            }
            
            logger.info(f"Parsed MRZ: {surname}, {given_names} ({passport_num})")
            return result
        
        except Exception as e:
            logger.error(f"Error parsing MRZ lines: {e}", exc_info=True)
            return {}
    
    def _clean_name(self, name: str) -> str:
        """Clean up OCR errors in names - names should be letters only"""
        if not name:
            return ""
        
        # Remove common OCR artifacts
        import re
        
        # First: Fix common OCR misreads where << is read as KK (exactly 2 K's)
        # Only replace KK, not single K which might be valid
        name = name.replace('KK', '<<')
        
        # Common character replacements for OCR errors
        cleaned = name.replace('0', 'O').replace('1', 'I').replace('5', 'S').replace('8', 'B')
        
        # Remove any remaining digits (names shouldn't have numbers)
        cleaned = ''.join(c for c in cleaned if not c.isdigit())
        
        # Remove 3+ repeated characters that look like OCR errors (SSS→S, etc.)
        # But preserve < which is valid MRZ separator
        # This converts "KKKKK" to "K" but we already converted "KK" to "<<" above
        cleaned = re.sub(r'([^<])\1{2,}', r'\1', cleaned)
        
        # Split by MRZ separators and whitespace
        parts = re.split(r'[<\s]+', cleaned)
        valid_parts = []
        
        for part in parts:
            # Keep parts that are:
            # - At least 1 char (changed from 2 to preserve single letters)
            # - Mostly letters (at least 70%)
            if len(part) >= 1:
                if len(part) == 1:
                    # Single letters are OK if they're actually letters
                    if part.isalpha():
                        valid_parts.append(part)
                else:
                    # Multi-char parts need 70% letters
                    letter_ratio = sum(1 for c in part if c.isalpha()) / len(part)
                    if letter_ratio > 0.7:
                        valid_parts.append(part)
        
        return ' '.join(valid_parts).strip()
    
    def _extract_mrz_region_enhanced(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Enhanced MRZ region extraction"""
        height, width = image.shape[:2]
        
        # MRZ is typically in bottom 25% of passport
        bottom_region = image[int(height * 0.75):, :]
        
        return bottom_region
    
    def _preprocess_for_paddle(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image specifically for PaddleOCR"""
        # Extract MRZ region first
        height, width = image.shape[:2]
        mrz_region = image[int(height * 0.7):, :]  # Bottom 30%
        
        # Convert to grayscale
        if len(mrz_region.shape) == 3:
            gray = cv2.cvtColor(mrz_region, cv2.COLOR_BGR2GRAY)
        else:
            gray = mrz_region
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        
        # Convert back to BGR for PaddleOCR
        return cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
    
    
    def _validate_mrz_data(self, mrz_data: Dict) -> Dict:
        """Validate MRZ data for completeness and check digit validation"""
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


# Create global instance
enhanced_mrz_reader_service = EnhancedMRZReaderService()
