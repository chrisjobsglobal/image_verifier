"""Main FastAPI Application"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys
import os

from app.core.config import settings
from app.api.endpoints import photo, passport, debug
from app.models.response import HealthCheckResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("Initializing services...")
    
    # Verify services are available
    try:
        import cv2
        logger.info(f"OpenCV version: {cv2.__version__}")
    except ImportError:
        logger.warning("OpenCV not available")
    
    try:
        import mediapipe as mp
        logger.info(f"MediaPipe version: {mp.__version__}")
    except ImportError:
        logger.warning("MediaPipe not available")
    
    try:
        import face_recognition
        logger.info("face_recognition library loaded")
    except ImportError:
        logger.warning("face_recognition not available")
    
    try:
        from passporteye import read_mrz
        logger.info("PassportEye library loaded")
    except ImportError:
        logger.warning("PassportEye not available")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Image Verification API for passport photos and documents.
    
    This API provides comprehensive verification services for:
    - Personal photos (ICAO 9303 compliance for passports/IDs)
    - Passport documents (quality and MRZ reading)
    
    ## Features
    
    ### Photo Verification
    - Face detection and positioning analysis
    - Image quality assessment (blur, brightness, contrast)
    - ICAO 9303 compliance validation
    - Background and lighting checks
    - Accessories detection (glasses, head coverings)
    
    ### Passport Verification
    - Document positioning and quality checks
    - MRZ (Machine Readable Zone) extraction
    - Data validation and expiration checks
    - ICAO compliance verification
    
    ## Authentication
    
    API key authentication can be enabled via the `X-API-Key` header.
    Set `API_KEY` in your environment to enable authentication.
    """,
    debug=settings.debug,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": {"errors": errors}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": {"message": str(exc) if settings.debug else "An unexpected error occurred"}
        }
    )


# Include routers
app.include_router(passport.router, prefix="/api/v1/passport")
app.include_router(photo.router, prefix="/api/v1/photo")
app.include_router(debug.router, prefix="/api/v1/debug")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted at /static from {static_dir}")


# Root endpoint
@app.get(
    "/",
    summary="Root",
    description="API root endpoint with basic information"
)
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "documentation": "/docs",
        "api_prefix": settings.api_prefix,
        "endpoints": {
            "photo_verification": f"{settings.api_prefix}/photo/verify",
            "passport_verification": f"{settings.api_prefix}/passport/verify",
            "health_check": "/health"
        }
    }


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check API health and service availability"
)
async def health_check():
    """
    Health check endpoint to verify service availability.
    
    Returns:
        Health status with service availability information
    """
    services_status = {}
    
    # Check OpenCV
    try:
        import cv2
        services_status["opencv"] = "available"
    except ImportError:
        services_status["opencv"] = "unavailable"
    
    # Check MediaPipe
    try:
        import mediapipe
        services_status["mediapipe"] = "available"
    except ImportError:
        services_status["mediapipe"] = "unavailable"
    
    # Check face_recognition
    try:
        import face_recognition
        services_status["face_recognition"] = "available"
    except ImportError:
        services_status["face_recognition"] = "unavailable"
    
    # Check PassportEye
    try:
        from passporteye import read_mrz
        services_status["passporteye"] = "available"
    except ImportError:
        services_status["passporteye"] = "unavailable"
    
    # Check Tesseract
    try:
        import pytesseract
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        # Try to get version
        version = pytesseract.get_tesseract_version()
        services_status["tesseract"] = f"available (v{version})"
    except Exception:
        services_status["tesseract"] = "unavailable"
    
    # Determine overall health
    critical_services = ["opencv", "mediapipe", "face_recognition"]
    all_critical_available = all(
        services_status.get(svc) == "available" 
        for svc in critical_services
    )
    
    overall_status = "healthy" if all_critical_available else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        services=services_status
    )


# API information endpoint
@app.get(
    f"{settings.api_prefix}/info",
    summary="API Information",
    description="Get detailed API configuration and limits"
)
async def api_info():
    """Get API configuration information"""
    return {
        "version": settings.app_version,
        "api_prefix": settings.api_prefix,
        "limits": {
            "max_upload_size_mb": settings.max_upload_size / 1024 / 1024,
            "allowed_image_types": settings.allowed_image_types,
            "min_resolution": f"{settings.min_image_width}x{settings.min_image_height}",
            "max_resolution": f"{settings.max_image_width}x{settings.max_image_height}"
        },
        "thresholds": {
            "face_percentage": f"{settings.min_face_percentage}-{settings.max_face_percentage}%",
            "max_tilt_angle": f"{settings.max_tilt_angle_degrees}°",
            "blur_threshold": settings.blur_threshold,
            "min_contrast": settings.min_contrast
        },
        "features": {
            "photo_verification": True,
            "passport_verification": True,
            "mrz_reading": True,
            "icao_validation": True,
            "face_detection": True
        },
        "authentication": {
            "enabled": bool(settings.api_key),
            "method": "API Key (Header: X-API-Key)" if settings.api_key else "None"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=27000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
