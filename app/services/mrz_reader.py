"""
MRZ Reader Service - Entry Point

This module uses the EasyOCR-based implementation for passport MRZ reading.
The actual implementation is in mrz_reader_easyocr.py
"""

# Import the EasyOCR-based implementation
from app.services.mrz_reader_easyocr import (
    EnhancedMRZReaderService,
    enhanced_mrz_reader_service
)

__all__ = ['EnhancedMRZReaderService', 'enhanced_mrz_reader_service']
