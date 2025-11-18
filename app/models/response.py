"""Pydantic response models"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Validation error detail"""
    message: str
    field: Optional[str] = None
    code: Optional[str] = None


class ImageMetrics(BaseModel):
    """Image quality metrics"""
    width: int
    height: int
    resolution: str
    blur_score: Optional[float] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    sharpness: Optional[float] = None
    noise_level: Optional[float] = None


class FaceMetrics(BaseModel):
    """Face analysis metrics"""
    face_detected: bool
    face_percentage: Optional[float] = None
    is_centered: Optional[bool] = None
    center_offset_percentage: Optional[float] = None
    head_tilt_degrees: Optional[float] = None
    eyes_visible: Optional[bool] = None
    eyes_open: Optional[bool] = None
    mouth_closed: Optional[bool] = None
    looking_at_camera: Optional[bool] = None
    glasses_detected: Optional[bool] = None
    face_location: Optional[Dict[str, int]] = None


class MRZData(BaseModel):
    """MRZ (Machine Readable Zone) data"""
    type: Optional[str] = None
    country: Optional[str] = None
    surname: Optional[str] = None
    names: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    expiration_date: Optional[str] = None
    personal_number: Optional[str] = None
    raw_mrz_text: Optional[str] = None


class VerificationResponse(BaseModel):
    """Base verification response model"""
    
    success: bool = Field(description="Whether the verification process completed successfully")
    is_valid: bool = Field(description="Whether the image meets all validation criteria")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
        }


class PhotoVerificationResponse(VerificationResponse):
    """Response model for personal photo verification"""
    
    compliance_score: float = Field(
        description="ICAO compliance score (0-100)",
        ge=0,
        le=100
    )
    
    face_metrics: Optional[FaceMetrics] = Field(
        default=None,
        description="Detailed face analysis metrics"
    )
    
    image_metrics: Optional[ImageMetrics] = Field(
        default=None,
        description="Image quality metrics"
    )
    
    icao_requirements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed ICAO requirement checks"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations to improve photo quality"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "is_valid": True,
                "compliance_score": 95.0,
                "errors": [],
                "warnings": ["Face is slightly off-center"],
                "recommendations": ["Ensure face is centered in frame"],
                "face_metrics": {
                    "face_detected": True,
                    "face_percentage": 75.0,
                    "is_centered": True,
                    "head_tilt_degrees": 2.5,
                    "eyes_open": True,
                    "looking_at_camera": True
                }
            }
        }


class PassportVerificationResponse(VerificationResponse):
    """Response model for passport document verification"""
    
    document_detected: bool = Field(
        description="Whether a passport document was detected"
    )
    
    mrz_found: bool = Field(
        default=False,
        description="Whether MRZ was successfully detected and read"
    )
    
    ocr_method: Optional[str] = Field(
        default=None,
        description="OCR method used: 'paddleocr' (AI), 'easyocr', 'passporteye' (traditional), or 'none'"
    )
    
    mrz_confidence: Optional[float] = Field(
        default=None,
        description="MRZ OCR confidence percentage (0-100)"
    )
    
    mrz_data: Optional[MRZData] = Field(
        default=None,
        description="Extracted MRZ data"
    )
    
    document_metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Document positioning and quality metrics"
    )
    
    image_metrics: Optional[ImageMetrics] = Field(
        default=None,
        description="Image quality metrics"
    )
    
    passport_valid: Optional[bool] = Field(
        default=None,
        description="Whether passport is currently valid (not expired)"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations to improve document capture"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "is_valid": True,
                "document_detected": True,
                "mrz_found": True,
                "errors": [],
                "warnings": [],
                "recommendations": [],
                "mrz_confidence": 98.5,
                "mrz_data": {
                    "type": "P",
                    "country": "USA",
                    "surname": "SMITH",
                    "names": "JOHN",
                    "passport_number": "123456789",
                    "nationality": "USA",
                    "date_of_birth": "850115",
                    "sex": "M",
                    "expiration_date": "300115"
                },
                "passport_valid": True
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of individual services"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "services": {
                    "image_processing": "available",
                    "face_detection": "available",
                    "mrz_reader": "available"
                }
            }
        }


class PageTextData(BaseModel):
    """Text data extracted from a single page"""
    page_number: int = Field(description="Page number (1-indexed)")
    text: str = Field(description="Extracted text from the page")
    confidence: Optional[float] = Field(default=None, description="OCR confidence score (0-100)")
    text_blocks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Detailed text blocks with coordinates"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "page_number": 1,
                "text": "PASSPORT\nUnited States of America\nSurname: SMITH\nGiven Names: JOHN DAVID",
                "confidence": 95.5,
                "text_blocks": [
                    {"text": "PASSPORT", "bbox": [100, 50, 200, 80], "confidence": 98.2},
                    {"text": "United States of America", "bbox": [80, 100, 220, 120], "confidence": 96.5}
                ]
            }
        }


class PassportTextExtractionResponse(VerificationResponse):
    """Response model for passport text extraction"""
    
    total_pages: int = Field(description="Total number of pages processed")
    pages: List[PageTextData] = Field(
        description="Text data extracted from each page"
    )
    combined_text: str = Field(
        description="All text combined from all pages"
    )
    ocr_method: str = Field(
        description="OCR method used: 'easyocr', 'paddleocr', or 'tesseract'"
    )
    processing_time_seconds: Optional[float] = Field(
        default=None,
        description="Total processing time in seconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "is_valid": True,
                "total_pages": 2,
                "errors": [],
                "warnings": [],
                "ocr_method": "easyocr",
                "combined_text": "PASSPORT United States of America...",
                "pages": [
                    {
                        "page_number": 1,
                        "text": "PASSPORT\nUnited States of America",
                        "confidence": 95.5
                    },
                    {
                        "page_number": 2,
                        "text": "Visa pages",
                        "confidence": 92.3
                    }
                ],
                "processing_time_seconds": 3.45
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    
    success: bool = False
    error: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid image format",
                "error_code": "INVALID_FORMAT",
                "details": {
                    "supported_formats": ["image/jpeg", "image/png"]
                }
            }
        }
