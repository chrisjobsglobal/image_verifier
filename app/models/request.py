"""Pydantic request models"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class VerificationRequest(BaseModel):
    """Base verification request model"""
    
    image_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL of the image to verify (alternative to file upload)"
    )
    
    include_detailed_metrics: bool = Field(
        default=False,
        description="Include detailed technical metrics in response"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/photo.jpg",
                "include_detailed_metrics": False
            }
        }


class PhotoVerificationRequest(VerificationRequest):
    """Request model for personal photo verification"""
    
    check_age_requirement: bool = Field(
        default=True,
        description="Warn if photo appears to be older than 6 months (requires metadata)"
    )
    
    strict_mode: bool = Field(
        default=False,
        description="Enable strict ICAO compliance mode (no warnings, only hard failures)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/photo.jpg",
                "include_detailed_metrics": True,
                "check_age_requirement": True,
                "strict_mode": False
            }
        }


class PassportVerificationRequest(VerificationRequest):
    """Request model for passport document verification"""
    
    read_mrz: bool = Field(
        default=True,
        description="Attempt to read and validate MRZ data"
    )
    
    validate_expiration: bool = Field(
        default=True,
        description="Check if passport is expired"
    )
    
    extract_data: bool = Field(
        default=True,
        description="Extract all available passport data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/passport.jpg",
                "include_detailed_metrics": False,
                "read_mrz": True,
                "validate_expiration": True,
                "extract_data": True
            }
        }
