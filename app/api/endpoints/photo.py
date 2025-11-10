"""Photo verification API endpoint"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import Optional
import logging

from app.models.response import PhotoVerificationResponse, ErrorResponse, FaceMetrics, ImageMetrics
from app.services.icao_validator import icao_validator_service
from app.utils.image_utils import load_image_from_bytes, validate_image_format, get_file_size
from app.core.config import settings
from app.core.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/photo", tags=["Photo Verification"])


@router.post(
    "/verify",
    response_model=PhotoVerificationResponse,
    summary="Verify Personal Photo",
    description="Verify a personal photo for ICAO 9303 compliance",
    responses={
        200: {"description": "Verification completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def verify_photo(
    file: UploadFile = File(..., description="Photo file to verify (JPEG or PNG)"),
    include_detailed_metrics: bool = Form(default=False, description="Include detailed technical metrics"),
    strict_mode: bool = Form(default=False, description="Enable strict compliance mode"),
    api_key: str = Depends(verify_api_key)
) -> PhotoVerificationResponse:
    """
    Verify a personal photo for passport/ID compliance.
    
    This endpoint performs comprehensive validation including:
    - Face detection and positioning
    - Image quality assessment (blur, brightness, contrast)
    - ICAO 9303 compliance checks
    - Background validation
    - Lighting and shadow detection
    - Accessories (glasses) detection
    
    Args:
        file: Image file (JPEG or PNG)
        include_detailed_metrics: Return detailed technical metrics
        strict_mode: Treat warnings as errors
        
    Returns:
        PhotoVerificationResponse with validation results
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
        
        # Validate file format
        is_valid_format, image_format = validate_image_format(content)
        if not is_valid_format:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format. Supported formats: {', '.join(settings.allowed_image_types)}"
            )
        
        # Validate content type
        if file.content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {file.content_type}. Allowed types: {', '.join(settings.allowed_image_types)}"
            )
        
        # Load image
        try:
            image = load_image_from_bytes(content)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # Perform ICAO compliance validation
        validation_results = icao_validator_service.validate_photo_compliance(image)
        
        # Build response
        response = PhotoVerificationResponse(
            success=True,
            is_valid=validation_results["is_compliant"],
            compliance_score=validation_results["compliance_score"],
            errors=validation_results["errors"],
            warnings=validation_results["warnings"] if not strict_mode else [],
            recommendations=_generate_recommendations(validation_results)
        )
        
        # Add warnings as errors in strict mode
        if strict_mode and validation_results["warnings"]:
            response.is_valid = False
            response.errors.extend(validation_results["warnings"])
        
        # Add detailed metrics if requested
        if include_detailed_metrics:
            # Extract face metrics
            face_analysis = validation_results["validations"].get("face_analysis", {})
            if face_analysis.get("face_detected"):
                face_data = face_analysis.get("metrics", {})
                response.face_metrics = FaceMetrics(
                    face_detected=True,
                    face_percentage=face_data.get("face_percentage"),
                    is_centered=face_data.get("is_centered"),
                    center_offset_percentage=face_data.get("center_offset_percentage"),
                    head_tilt_degrees=face_data.get("head_tilt_degrees"),
                    eyes_visible=face_data.get("eyes", {}).get("both_eyes_visible"),
                    eyes_open=not face_data.get("eyes", {}).get("eyes_closed", True),
                    mouth_closed=not face_data.get("mouth_open", False),
                    looking_at_camera=face_data.get("gaze", {}).get("looking_at_camera"),
                    glasses_detected=face_data.get("glasses_detected"),
                    face_location=face_data.get("face_location")
                )
            else:
                response.face_metrics = FaceMetrics(face_detected=False)
            
            # Extract image metrics
            image_quality = validation_results["validations"].get("image_quality", {})
            if image_quality:
                quality_metrics = image_quality.get("metrics", {})
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
            
            # Add ICAO requirement details
            response.icao_requirements = validation_results.get("validations", {})
        
        logger.info(
            f"Photo verification completed: valid={response.is_valid}, "
            f"score={response.compliance_score}, errors={len(response.errors)}"
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Photo verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during photo verification: {str(e)}"
        )


def _generate_recommendations(validation_results: dict) -> list:
    """Generate actionable recommendations based on validation results"""
    recommendations = []
    
    errors = validation_results.get("errors", [])
    warnings = validation_results.get("warnings", [])
    
    # Recommendations based on common errors
    if any("blur" in err.lower() for err in errors):
        recommendations.append("Use a camera with better focus or ensure the subject is still")
    
    if any("dark" in err.lower() or "bright" in err.lower() for err in errors):
        recommendations.append("Adjust lighting to ensure proper exposure")
    
    if any("face" in err.lower() and ("small" in err.lower() or "large" in err.lower()) for err in errors):
        recommendations.append("Adjust distance from camera so face occupies 70-80% of frame")
    
    if any("tilt" in err.lower() for err in errors):
        recommendations.append("Ensure head is straight and not tilted")
    
    if any("background" in err.lower() for err in errors):
        recommendations.append("Use a plain, light-colored (white or light gray) background")
    
    if any("shadow" in err.lower() for err in errors):
        recommendations.append("Use diffused, uniform lighting to eliminate shadows")
    
    if any("eyes" in err.lower() for err in errors):
        recommendations.append("Ensure both eyes are clearly visible and open")
    
    if any("glasses" in warn.lower() for warn in warnings):
        recommendations.append("If wearing glasses, ensure no reflections and eyes are fully visible")
    
    if any("centered" in warn.lower() for warn in warnings):
        recommendations.append("Center face in the frame")
    
    # Generic recommendation if no specific errors
    if not recommendations and not validation_results.get("is_compliant"):
        recommendations.append("Review ICAO 9303 photo guidelines for passport photos")
    
    return recommendations


@router.get(
    "/requirements",
    summary="Get Photo Requirements",
    description="Get detailed ICAO 9303 photo requirements"
)
async def get_photo_requirements():
    """
    Get detailed photo requirements for ICAO 9303 compliance.
    
    Returns:
        Dictionary with photo requirements and guidelines
    """
    return {
        "dimensions": {
            "minimum_resolution": f"{settings.min_image_width}x{settings.min_image_height}",
            "recommended_resolution": "1920x1080 (Full HD) or higher",
            "face_coverage": f"{settings.min_face_percentage}-{settings.max_face_percentage}% of image"
        },
        "quality": {
            "focus": "Sharp focus, no blurred areas",
            "brightness": "Well-lit with natural skin tones",
            "contrast": "Good contrast, not washed out",
            "color": "Color photo with neutral tones"
        },
        "face_requirements": {
            "expression": "Neutral expression, mouth closed",
            "eyes": "Open and clearly visible, looking at camera",
            "head_position": "Facing camera, not tilted",
            "max_tilt_angle": f"{settings.max_tilt_angle_degrees} degrees"
        },
        "background": {
            "color": "Plain light-colored (white or light gray)",
            "uniformity": "Uniform, no patterns or objects",
            "shadows": "No shadows on face or background"
        },
        "accessories": {
            "glasses": "Allowed if eyes visible, no reflections, no tinted lenses",
            "head_covering": "Not permitted except for religious reasons",
            "other": "No hats, toys, or other objects visible"
        },
        "lighting": {
            "type": "Uniform, diffused lighting",
            "shadows": "No shadows across face",
            "flash": "Avoid flash reflections"
        },
        "age": {
            "photo_age": "No more than 6 months old"
        }
    }
