"""Passport document verification API endpoint"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body, Form
from typing import Optional, Union
import logging

from app.models.request import PassportVerificationRequest
from app.models.response import PassportVerificationResponse, ErrorResponse, MRZData, ImageMetrics
from app.services.icao_validator import icao_validator_service
from app.services.mrz_reader_enhanced import enhanced_mrz_reader_service as mrz_reader_service
from app.utils.image_utils import load_image_from_bytes, validate_image_format, get_file_size, download_image_from_url
from app.core.config import settings
from app.core.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Passport Verification"])


@router.post(
    "/verify/upload",
    response_model=PassportVerificationResponse,
    summary="Verify Passport Document (File Upload)",
    description="Verify a passport document image by uploading a file (JPEG, PNG, or PDF)",
    responses={
        200: {"description": "Verification completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def verify_passport_upload(
    file: UploadFile = File(..., description="Passport document image file (JPEG, PNG, or PDF)"),
    read_mrz: bool = Form(default=True, description="Attempt to read and validate MRZ"),
    validate_expiration: bool = Form(default=True, description="Check if passport is expired"),
    include_detailed_metrics: bool = Form(default=False, description="Include detailed technical metrics"),
    api_key: str = Depends(verify_api_key)
) -> PassportVerificationResponse:
    """
    Verify a passport document image by uploading a file.
    
    This endpoint performs comprehensive validation including:
    - Document detection and positioning
    - Image quality assessment
    - MRZ (Machine Readable Zone) reading and validation
    - ICAO 9303 compliance checks
    - Lighting and reflection detection
    - Expiration date validation
    
    Supports: JPEG, PNG, and PDF files (PDF first page will be extracted)
    
    Args:
        file: Passport image file (required)
        read_mrz: Attempt to extract MRZ data
        validate_expiration: Check passport expiration
        include_detailed_metrics: Return detailed technical metrics
        
    Returns:
        PassportVerificationResponse with validation results
    """
    try:
        # Read file content
        content = await file.read()
        content_type = file.content_type
        
        # Validate file size
        file_size = get_file_size(content)
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024:.1f}MB"
            )
        
        # Validate file format
        is_valid_format, image_format = validate_image_format(content)
        if not is_valid_format:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format. Supported formats: {', '.join(settings.allowed_image_types)}"
            )
        
        # Validate content type
        if content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {content_type}. Allowed types: {', '.join(settings.allowed_image_types)}"
            )
        
        # Load image
        try:
            image = load_image_from_bytes(content)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # Process verification
        return await _process_passport_verification(
            image, read_mrz, validate_expiration, include_detailed_metrics
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Passport verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during passport verification: {str(e)}"
        )


@router.post(
    "/verify/url",
    response_model=PassportVerificationResponse,
    summary="Verify Passport Document (URL)",
    description="Verify a passport document image by providing a URL to the image",
    responses={
        200: {"description": "Verification completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def verify_passport_url(
    request: PassportVerificationRequest = Body(...),
    api_key: str = Depends(verify_api_key)
) -> PassportVerificationResponse:
    """
    Verify a passport document image from a URL.
    
    This endpoint performs comprehensive validation including:
    - Document detection and positioning
    - Image quality assessment
    - MRZ (Machine Readable Zone) reading and validation
    - ICAO 9303 compliance checks
    - Lighting and reflection detection
    - Expiration date validation
    
    Supports: JPEG, PNG, and PDF files (PDF first page will be extracted)
    
    Args:
        request: JSON body with image_url and options
        
    Returns:
        PassportVerificationResponse with validation results
    """
    try:
        # Download from URL (convert Pydantic HttpUrl to string)
        content = await download_image_from_url(str(request.image_url))
        
        # Validate file size
        file_size = get_file_size(content)
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024:.1f}MB"
            )
        
        # Validate file format
        is_valid_format, image_format = validate_image_format(content)
        if not is_valid_format:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format. Supported formats: {', '.join(settings.allowed_image_types)}"
            )
        
        # Load image
        try:
            image = load_image_from_bytes(content)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # Process verification
        return await _process_passport_verification(
            image, 
            request.read_mrz, 
            request.validate_expiration, 
            request.include_detailed_metrics
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Passport verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during passport verification: {str(e)}"
        )


async def _process_passport_verification(
    image,
    read_mrz: bool = True,
    validate_expiration: bool = True,
    include_detailed_metrics: bool = False
) -> PassportVerificationResponse:
    """
    Shared processing logic for passport verification.
    
    Args:
        image: Loaded image (numpy array)
        read_mrz: Attempt to extract MRZ data
        validate_expiration: Check passport expiration
        include_detailed_metrics: Return detailed technical metrics
        
    Returns:
        PassportVerificationResponse with validation results
    """
    # Perform document validation
    validation_results = icao_validator_service.validate_passport_document(image)
    
    # Initialize response
    response = PassportVerificationResponse(
        success=True,
        is_valid=validation_results["is_compliant"],
        document_detected=True,  # If we got this far, document was processed
        errors=validation_results["errors"],
        warnings=validation_results["warnings"],
        recommendations=_generate_passport_recommendations(validation_results)
    )
    
    # Read MRZ if requested
    if read_mrz:
        mrz_results = mrz_reader_service.read_passport_mrz(image)
        response.mrz_found = mrz_results["mrz_found"]
        response.ocr_method = mrz_results.get("ocr_method", "none")
        
        logger.info(f"MRZ reading: found={response.mrz_found}, method={response.ocr_method}")
        
        if mrz_results["mrz_found"]:
            mrz_data = mrz_results["mrz_data"]
            response.mrz_data = MRZData(
                type=mrz_data.get("type"),
                country=mrz_data.get("country"),
                surname=mrz_data.get("surname"),
                names=mrz_data.get("names"),
                passport_number=mrz_data.get("passport_number"),
                nationality=mrz_data.get("nationality"),
                date_of_birth=mrz_data.get("date_of_birth"),
                sex=mrz_data.get("sex"),
                expiration_date=mrz_data.get("expiration_date"),
                personal_number=mrz_data.get("personal_number"),
                raw_mrz_text=mrz_data.get("raw_mrz_text")
            )
            
            # Validate expiration if requested
            if validate_expiration and mrz_data.get("expiration_date"):
                response.passport_valid = not mrz_reader_service._is_date_expired(
                    mrz_data["expiration_date"]
                )
                
                if not response.passport_valid:
                    response.warnings.append("Passport appears to be expired")
        else:
            response.errors.extend(mrz_results["errors"])
            response.warnings.extend(mrz_results["warnings"])
    
    # Add detailed metrics if requested
    if include_detailed_metrics:
        # Extract document metrics
        positioning = validation_results["validations"].get("positioning", {})
        quality = validation_results["validations"].get("quality", {})
        
        response.document_metrics = {
            "positioning": positioning,
            "quality_checks": quality
        }
        
        # Extract image metrics
        if quality:
            quality_metrics = quality.get("metrics", {})
            response.image_metrics = ImageMetrics(
                width=quality_metrics.get("width", 0),
                height=quality_metrics.get("height", 0),
                resolution=quality_metrics.get("resolution", ""),
                blur_score=quality_metrics.get("blur_score"),
                brightness=quality_metrics.get("brightness"),
                contrast=quality_metrics.get("contrast"),
                sharpness=quality_metrics.get("sharpness"),
                noise_level=quality_metrics.get("noise_level")
            )
    
    logger.info(
        f"Passport verification completed: valid={response.is_valid}, "
        f"mrz_found={response.mrz_found}, errors={len(response.errors)}"
    )
    
    return response


def _generate_passport_recommendations(validation_results: dict) -> list:
    """Generate actionable recommendations for passport document capture"""
    recommendations = []
    
    errors = validation_results.get("errors", [])
    warnings = validation_results.get("warnings", [])
    
    # Recommendations based on common errors
    if any("blur" in err.lower() for err in errors):
        recommendations.append("Ensure camera is stable and document is in focus")
    
    if any("tilt" in err.lower() or "angle" in err.lower() for err in errors):
        recommendations.append("Place document flat and capture from directly above")
    
    if any("document" in err.lower() and ("small" in err.lower() or "large" in err.lower()) for err in errors):
        recommendations.append("Adjust distance so document occupies 70-80% of frame with margins visible")
    
    if any("glare" in err.lower() or "reflection" in err.lower() for err in errors):
        recommendations.append("Avoid flash and ensure no light reflections on document surface")
    
    if any("dark" in err.lower() or "bright" in err.lower() for err in errors):
        recommendations.append("Use good, even lighting - not too dark or too bright")
    
    if any("mrz" in err.lower() for err in errors):
        recommendations.append("Ensure bottom of passport (MRZ area) is clearly visible and in focus")
    
    if any("contrast" in err.lower() or "background" in err.lower() for err in errors):
        recommendations.append("Place document on contrasting background (light document on dark surface or vice versa)")
    
    # Generic recommendation
    if not recommendations and not validation_results.get("is_compliant"):
        recommendations.append("Review image quality guidelines for passport document capture")
    
    return recommendations


@router.get(
    "/requirements",
    summary="Get Passport Document Requirements",
    description="Get detailed requirements for passport document capture"
)
async def get_passport_requirements():
    """
    Get detailed requirements for passport document capture.
    
    Returns:
        Dictionary with document capture requirements
    """
    return {
        "document_positioning": {
            "coverage": f"{settings.min_document_percentage}-{settings.max_document_percentage}% of image",
            "centering": "Document should be centered in frame",
            "margins": "20-30% margins around document",
            "tilt_tolerance": f"Maximum {settings.max_document_tilt_degrees} degrees tilt",
            "orientation": "Document should be flat and parallel to camera"
        },
        "image_quality": {
            "minimum_resolution": f"{settings.min_image_width}x{settings.min_image_height}",
            "recommended_resolution": "1920x1080 (Full HD) or higher with autofocus",
            "focus": "Sharp focus across entire document",
            "clarity": "All text must be clearly readable"
        },
        "lighting": {
            "brightness": "Good lighting - not too dark or too bright",
            "uniformity": "Even lighting across entire document",
            "flash": "Do not use flash",
            "reflections": "Avoid glare and reflections on document surface",
            "shadows": "No shadows on document"
        },
        "background": {
            "contrast": "Document must contrast with background",
            "avoid": "Do not capture light document on light background or dark on dark"
        },
        "pages": {
            "required": "Both first and second pages for two-page passports",
            "format": "Both pages in single image attachment"
        },
        "mrz": {
            "visibility": "Machine Readable Zone (bottom text lines) must be fully visible",
            "clarity": "MRZ must be sharp and clearly readable"
        },
        "obstructions": {
            "hands": "No hands or fingers covering document data",
            "objects": "No other objects in frame",
            "damage": "Document should be undamaged and complete"
        }
    }


@router.post(
    "/extract-mrz/upload",
    summary="Extract MRZ Data Only (File Upload)",
    description="Extract MRZ data from passport by uploading a file without full validation"
)
async def extract_mrz_upload(
    file: UploadFile = File(..., description="Passport document image file"),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract only MRZ data from passport image by uploading a file.
    
    This is a lightweight endpoint for quick MRZ extraction without full quality validation.
    
    Args:
        file: Passport image file (required)
        
    Returns:
        MRZ data if found
    """
    try:
        # Read file content
        content = await file.read()
        
        # Validate file size
        file_size = get_file_size(content)
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024:.1f}MB"
            )
        
        # Load image
        try:
            image = load_image_from_bytes(content)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # Read MRZ
        mrz_results = mrz_reader_service.read_passport_mrz(image)
        
        if not mrz_results["mrz_found"]:
            raise HTTPException(
                status_code=404,
                detail="No MRZ found in image"
            )
        
        return {
            "success": True,
            "mrz_found": True,
            "mrz_data": mrz_results["mrz_data"],
            "warnings": mrz_results.get("warnings", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MRZ extraction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during MRZ extraction: {str(e)}"
        )


@router.post(
    "/extract-mrz/url",
    summary="Extract MRZ Data Only (URL)",
    description="Extract MRZ data from passport URL without full validation"
)
async def extract_mrz_url(
    request: PassportVerificationRequest = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract only MRZ data from passport image URL.
    
    This is a lightweight endpoint for quick MRZ extraction without full quality validation.
    
    Args:
        request: JSON body with image_url
        
    Returns:
        MRZ data if found
    """
    try:
        # Download from URL (convert Pydantic HttpUrl to string)
        content = await download_image_from_url(str(request.image_url))
        
        # Validate file size
        file_size = get_file_size(content)
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024:.1f}MB"
            )
        
        # Load image
        try:
            image = load_image_from_bytes(content)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # Read MRZ
        mrz_results = mrz_reader_service.read_passport_mrz(image)
        
        if not mrz_results["mrz_found"]:
            raise HTTPException(
                status_code=404,
                detail="No MRZ found in image"
            )
        
        return {
            "success": True,
            "mrz_found": True,
            "mrz_data": mrz_results["mrz_data"],
            "warnings": mrz_results.get("warnings", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MRZ extraction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during MRZ extraction: {str(e)}"
        )
