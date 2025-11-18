"""
Text Extraction Service using EasyOCR
Extracts all text from passport pages (not just MRZ)
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class TextExtractionService:
    """Service for extracting text from passport pages using OCR"""
    
    def __init__(self):
        """Initialize the text extraction service with lazy loading"""
        self._easyocr_reader = None
        logger.info("TextExtractionService initialized (lazy loading)")
    
    @property
    def easyocr_reader(self):
        """Lazy load EasyOCR reader on first use"""
        if self._easyocr_reader is None:
            try:
                import easyocr
                logger.info("Loading EasyOCR reader (English)...")
                start_time = time.time()
                # Initialize with English language, CPU mode
                self._easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                load_time = time.time() - start_time
                logger.info(f"EasyOCR reader loaded successfully in {load_time:.2f}s")
            except Exception as e:
                logger.error(f"Failed to load EasyOCR: {e}")
                raise RuntimeError(f"EasyOCR initialization failed: {str(e)}")
        
        return self._easyocr_reader
    
    def extract_text_from_image(
        self,
        image: np.ndarray,
        include_detailed_blocks: bool = False
    ) -> Dict[str, Any]:
        """
        Extract all text from a single image using EasyOCR
        
        Args:
            image: Input image as numpy array (BGR format from cv2)
            include_detailed_blocks: Include detailed text block information with coordinates
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            start_time = time.time()
            
            # Convert BGR to RGB for EasyOCR
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Run EasyOCR detection
            logger.info(f"Running EasyOCR on image of shape {image.shape}")
            results = self.easyocr_reader.readtext(image_rgb)
            
            # Process results
            text_blocks = []
            all_text_lines = []
            total_confidence = 0.0
            
            for detection in results:
                bbox, text, confidence = detection
                
                # Store text
                all_text_lines.append(text)
                total_confidence += confidence
                
                # Store detailed block info if requested
                if include_detailed_blocks:
                    # Convert bbox to simple format: [x1, y1, x2, y2]
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    simple_bbox = [
                        int(min(x_coords)),
                        int(min(y_coords)),
                        int(max(x_coords)),
                        int(max(y_coords))
                    ]
                    
                    text_blocks.append({
                        "text": text,
                        "bbox": simple_bbox,
                        "confidence": round(confidence * 100, 2)
                    })
            
            # Combine all text
            combined_text = "\n".join(all_text_lines)
            
            # Calculate average confidence
            avg_confidence = (total_confidence / len(results) * 100) if results else 0.0
            
            processing_time = time.time() - start_time
            
            result = {
                "text": combined_text,
                "confidence": round(avg_confidence, 2),
                "blocks_found": len(results),
                "processing_time": round(processing_time, 2)
            }
            
            if include_detailed_blocks:
                result["text_blocks"] = text_blocks
            
            logger.info(f"Extracted {len(results)} text blocks in {processing_time:.2f}s, "
                       f"avg confidence: {avg_confidence:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}", exc_info=True)
            raise
    
    def extract_text_from_pages(
        self,
        images: List[np.ndarray],
        include_detailed_blocks: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text from multiple pages
        
        Args:
            images: List of images as numpy arrays (BGR format from cv2)
            include_detailed_blocks: Include detailed text block information
            
        Returns:
            Dictionary with text data for all pages
        """
        try:
            start_time = time.time()
            
            pages_data = []
            all_text_parts = []
            errors = []
            warnings = []
            
            for page_num, image in enumerate(images, start=1):
                try:
                    logger.info(f"Processing page {page_num}/{len(images)}")
                    
                    # Extract text from this page
                    page_result = self.extract_text_from_image(
                        image,
                        include_detailed_blocks=include_detailed_blocks
                    )
                    
                    # Build page data
                    page_data = {
                        "page_number": page_num,
                        "text": page_result["text"],
                        "confidence": page_result["confidence"]
                    }
                    
                    if include_detailed_blocks and "text_blocks" in page_result:
                        page_data["text_blocks"] = page_result["text_blocks"]
                    
                    pages_data.append(page_data)
                    all_text_parts.append(page_result["text"])
                    
                    # Warnings for low confidence
                    if page_result["confidence"] < 70:
                        warnings.append(
                            f"Page {page_num}: Low OCR confidence ({page_result['confidence']:.1f}%). "
                            "Consider improving image quality."
                        )
                    
                    # Warnings for no text found
                    if page_result["blocks_found"] == 0:
                        warnings.append(f"Page {page_num}: No text detected")
                    
                except Exception as e:
                    error_msg = f"Page {page_num}: Failed to extract text - {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    
                    # Add empty page data
                    pages_data.append({
                        "page_number": page_num,
                        "text": "",
                        "confidence": 0.0,
                        "error": str(e)
                    })
            
            # Combine all text
            combined_text = "\n\n--- Page Break ---\n\n".join(all_text_parts)
            
            total_time = time.time() - start_time
            
            return {
                "success": len(errors) == 0,
                "total_pages": len(images),
                "pages": pages_data,
                "combined_text": combined_text,
                "ocr_method": "easyocr",
                "processing_time_seconds": round(total_time, 2),
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Multi-page text extraction failed: {e}", exc_info=True)
            raise


# Global instance
text_extraction_service = TextExtractionService()
