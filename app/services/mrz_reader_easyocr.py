"""Enhanced MRZ Reader Service using EasyOCR

This service uses EasyOCR instead of PaddleOCR for better performance and stability.
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class EnhancedMRZReaderService:
    """Service for reading MRZ from passport images using EasyOCR"""
    
    def __init__(self):
        self._easyocr_reader = None
        logger.info("🔧 EnhancedMRZReaderService initialized (EasyOCR mode)")
    
    @property
    def easyocr_reader(self):
        """Lazy load EasyOCR reader"""
        if self._easyocr_reader is None:
            logger.info("📦 Loading EasyOCR (CPU mode)...")
            import easyocr
            self._easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("✅ EasyOCR is ready")
        return self._easyocr_reader
    
    def read_passport_mrz(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Read MRZ from passport image using EasyOCR
        
        Args:
            image: OpenCV image (numpy array)
            
        Returns:
            Dict with mrz_found, ocr_method, mrz_data, and raw_text
        """
        logger.info(f"📸 Starting MRZ detection on image shape: {image.shape}")
        
        result = self._read_mrz_with_easyocr(image)
        
        if result["mrz_found"]:
            logger.info(f"✅ MRZ successfully extracted using {result['ocr_method']}")
        else:
            logger.warning(f"❌ No MRZ detected using {result['ocr_method']}")
        
        return result
    
    def _read_mrz_with_easyocr(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Try to read MRZ using EasyOCR with multiple preprocessing strategies
        
        Args:
            image: Input image
            
        Returns:
            Dict with detection results
        """
        logger.info(f"📐 Image shape: {image.shape}, dtype: {image.dtype}")
        
        # Extract bottom region where MRZ typically is
        bottom_region = self._extract_bottom_region(image, 0.30)
        
        try:
            # Run EasyOCR on bottom region
            logger.info(f"🔍 Running EasyOCR on bottom 30% of image")
            results = self.easyocr_reader.readtext(bottom_region)
            
            logger.info(f"📊 EasyOCR detected {len(results)} text regions")
            
            # Extract all text and combine nearby fragments
            all_detections = []
            for bbox, text, conf in results:
                clean_text = text.replace(' ', '').upper()
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                x_left = bbox[0][0]
                
                all_detections.append({
                    'text': clean_text,
                    'conf': conf,
                    'y': y_center,
                    'x': x_left,
                    'bbox': bbox
                })
                
                logger.debug(f"  - '{clean_text}' (conf: {conf:.2f}, len: {len(clean_text)}, y: {y_center:.1f})")
            
            # Combine text fragments on the same line
            mrz_lines = self._combine_text_by_lines(all_detections)
            
            logger.info(f"🎯 Combined into {len(mrz_lines)} potential MRZ lines")
            for i, (line_text, line_conf) in enumerate(mrz_lines, 1):
                logger.info(f"   Line {i}: '{line_text}' ({len(line_text)} chars, conf: {line_conf:.2f})")
            
            # Filter for MRZ-like lines
            p_angle_lines = []  # Lines starting with P< (highest priority)
            passport_num_lines = []  # Lines with passport number pattern
            
            for i, (line_text, line_conf) in enumerate(mrz_lines):
                if not self._is_mrz_line(line_text):
                    continue
                
                # Pad to 44 chars
                padded = line_text[:44].ljust(44, '<')
                
                # TD3 passport MRZ Line 1: starts with P<
                if padded.startswith('P<') and len(line_text) >= 30:
                    p_angle_lines.append((padded, line_conf, i))
                    logger.info(f"   ✓ P< line: '{padded}' (line {i+1}, conf: {line_conf:.2f})")
                # TD3 passport MRZ Line 2: passport number + dates
                elif len(line_text) >= 35 and self._is_passport_number_line(line_text):
                    passport_num_lines.append((padded, line_conf, i))
                    logger.info(f"   ✓ Passport# line: '{padded}' (line {i+1}, conf: {line_conf:.2f})")
            
            # Combine: prefer P< lines first, then passport number lines
            mrz_candidates = []
            
            # If we have P< lines, use them (should be line 1)
            if p_angle_lines:
                # Use the LAST P< line (closest to bottom)
                mrz_candidates.append(p_angle_lines[-1])
            
            # If we have passport number lines, use them (should be line 2)
            if passport_num_lines:
                # Use the LAST passport number line (closest to bottom)
                mrz_candidates.append(passport_num_lines[-1])
            
            logger.info(f"🎯 Selected {len(mrz_candidates)} MRZ candidates (need 2)")
            
            if len(mrz_candidates) >= 2:
                logger.info(f"📝 Found valid MRZ pair, attempting parse")
                
                # Sort by line number to preserve top-to-bottom order
                mrz_candidates.sort(key=lambda x: x[2])
                mrz_text_lines = [text for text, conf, idx in mrz_candidates[:2]]
                
                logger.info(f"Selected MRZ lines: {mrz_candidates[0][2]+1} and {mrz_candidates[1][2]+1}")
                
                # Calculate average confidence from the MRZ lines
                avg_confidence = sum(conf for text, conf, idx in mrz_candidates[:2]) / 2
                avg_confidence_pct = avg_confidence * 100  # Convert to percentage
                
                mrz_data = self._parse_mrz_lines(mrz_text_lines)
                
                if mrz_data:
                    logger.info(f"✅ MRZ parsed successfully (confidence: {avg_confidence_pct:.1f}%)")
                    return {
                        "mrz_found": True,
                        "ocr_method": "easyocr",
                        "mrz_data": mrz_data,
                        "raw_text": "\n".join(mrz_text_lines),
                        "confidence": avg_confidence_pct,
                        "errors": [],
                        "warnings": []
                    }
                else:
                    logger.warning(f"⚠️  Found MRZ lines but parsing failed")
            else:
                logger.warning(f"⚠️  Only found {len(mrz_candidates)} valid MRZ lines (need 2)")
            
        except Exception as e:
            logger.error(f"❌ EasyOCR error: {str(e)}", exc_info=True)
        
        return {
            "mrz_found": False,
            "ocr_method": "easyocr_failed",
            "mrz_data": None,
            "raw_text": None,
            "errors": ["MRZ not detected or parsing failed"],
            "warnings": []
        }
    
    def _combine_text_by_lines(self, detections: List[Dict]) -> List[Tuple[str, float]]:
        """
        Combine text fragments that are on the same horizontal line
        
        Args:
            detections: List of detection dicts with text, conf, y, x
            
        Returns:
            List of (combined_text, avg_confidence) tuples
        """
        if not detections:
            return []
        
        # Group by Y-coordinate (within 15 pixels tolerance)
        lines = []
        
        for det in detections:
            # Find existing line within Y tolerance
            found_line = False
            for line in lines:
                if abs(det['y'] - line['y_avg']) < 15:
                    line['items'].append(det)
                    line['y_avg'] = sum(item['y'] for item in line['items']) / len(line['items'])
                    found_line = True
                    break
            
            if not found_line:
                lines.append({
                    'y_avg': det['y'],
                    'items': [det]
                })
        
        # Sort lines by Y (top to bottom)
        lines.sort(key=lambda line: line['y_avg'])
        
        # Combine text in each line (left to right)
        result = []
        for line in lines:
            # Sort items by X (left to right)
            line['items'].sort(key=lambda item: item['x'])
            
            # Combine text
            combined_text = ''.join(item['text'] for item in line['items'])
            avg_conf = sum(item['conf'] for item in line['items']) / len(line['items'])
            
            if combined_text:  # Skip empty lines
                result.append((combined_text, avg_conf))
        
        return result
    
    def _extract_bottom_region(self, image: np.ndarray, fraction: float) -> np.ndarray:
        """Extract bottom portion of image where MRZ is typically located"""
        height = image.shape[0]
        start_row = int(height * (1 - fraction))
        return image[start_row:, :]
    
    def _is_mrz_line(self, text: str) -> bool:
        """Check if text line looks like MRZ (mostly uppercase, numbers, and <)"""
        if not text or len(text) < 20:
            return False
        
        # MRZ contains mostly uppercase letters, numbers, and <
        mrz_chars = sum(1 for c in text if c.isupper() or c.isdigit() or c == '<')
        ratio = mrz_chars / len(text)
        
        # Check for typical MRZ patterns
        has_chevrons = '<' in text
        has_uppercase = any(c.isupper() for c in text)
        
        # Lowered threshold from 0.7 to 0.6 to catch more MRZ lines
        return ratio > 0.6 and has_uppercase
    
    def _is_passport_number_line(self, text: str) -> bool:
        """Check if line looks like TD3 line 2 (starts with passport number)"""
        if len(text) < 20:
            return False
        
        # Line 2 typically starts with alphanumeric passport number (9 chars)
        # followed by country code (3 chars), date (6 digits), etc.
        first_part = text[:15]
        
        # Should have mix of letters and numbers in first part
        has_letters = any(c.isupper() for c in first_part)
        has_numbers = any(c.isdigit() for c in first_part)
        
        # Check for date pattern (YYMMDD) around position 13-19
        middle_part = text[10:20] if len(text) > 20 else text[10:]
        has_date_pattern = any(
            middle_part[i:i+6].isdigit() if i+6 <= len(middle_part) else False
            for i in range(len(middle_part) - 5)
        )
        
        return has_letters and has_numbers and (has_date_pattern or '<' in text)
    
    def _parse_mrz_lines(self, mrz_lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse TD3 (passport) MRZ format
        
        Args:
            mrz_lines: List of 2 MRZ text lines (44 chars each)
            
        Returns:
            Dict with parsed MRZ data or None if parsing fails
        """
        if not mrz_lines or len(mrz_lines) < 2:
            logger.warning(f"Need 2 MRZ lines, got {len(mrz_lines) if mrz_lines else 0}")
            return None
        
        try:
            line1 = mrz_lines[0][:44].ljust(44, '<')
            line2 = mrz_lines[1][:44].ljust(44, '<')
            
            logger.info(f"Parsing MRZ Line 1: {line1}")
            logger.info(f"Parsing MRZ Line 2: {line2}")
            
            # Line 1: Type(1) Country(3) Name(39)
            doc_type = line1[0:1]
            country = line1[2:5]
            name_field = line1[5:44].rstrip('<')
            
            # Fix common OCR error: << is often misread as KK
            # MALLICKK< should become MALLICK<< (KK< -> K<<)
            name_field = name_field.replace('KK<', 'K<<')
            
            # Parse name (SURNAME<<GIVEN NAMES)
            name_parts = name_field.split('<<')
            surname = name_parts[0].replace('<', ' ').strip()
            given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
            
            # Line 2: Passport(9) Nationality(3) DOB(6) Sex(1) Expiry(6) Personal(14) Check(2)
            passport_number = line2[0:9].rstrip('<')
            nationality = line2[10:13]
            dob = line2[13:19]  # YYMMDD
            sex = line2[20:21]
            expiry = line2[21:27]  # YYMMDD
            personal_number = line2[28:42].rstrip('<')
            
            # Format dates
            def format_date(date_str: str) -> str:
                if len(date_str) == 6 and date_str.isdigit():
                    yy, mm, dd = date_str[0:2], date_str[2:4], date_str[4:6]
                    # Assume 20xx for years 00-50, 19xx for 51-99
                    year = f"20{yy}" if int(yy) <= 50 else f"19{yy}"
                    return f"{year}-{mm}-{dd}"
                return date_str
            
            mrz_data = {
                "document_type": doc_type,
                "country": country,
                "surname": surname,
                "given_names": given_names,
                "full_name": f"{given_names} {surname}".strip(),
                "passport_number": passport_number,
                "nationality": nationality,
                "date_of_birth": format_date(dob),
                "sex": sex,
                "expiry_date": format_date(expiry),
                "personal_number": personal_number,
                "raw_mrz": f"{line1}\n{line2}"
            }
            
            logger.info(f"✅ Parsed MRZ: {mrz_data['full_name']} ({mrz_data['passport_number']})")
            return mrz_data
            
        except Exception as e:
            logger.error(f"Error parsing MRZ: {str(e)}", exc_info=True)
            return None


# Global singleton instance
enhanced_mrz_reader_service = EnhancedMRZReaderService()
