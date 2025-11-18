"""
OCR Text Extraction Endpoints
Extract text from various document types (passports, IDs, certificates, etc.)
"""

import logging
import numpy as np
from typing import Optional, Any
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Body
from app.models.response import ErrorResponse
from app.core.security import verify_api_key
from app.core.config import settings
from app.utils.image_utils import (
    download_image_from_url,
    get_file_size,
    validate_image_format,
    load_images_from_bytes
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR & Text Extraction"])


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types.
    
    Args:
        obj: Object that may contain numpy types
        
    Returns:
        Object with numpy types converted to Python types
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


@router.post(
    "/extract-text/upload",
    response_model=dict,
    summary="Extract Text from Document Pages (File Upload)",
    description="Extract all text from document pages (single/multi-page PDF or image). Works with passports, IDs, certificates, and other documents.",
    responses={
        200: {"description": "Text extraction completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def extract_text_from_document_upload(
    file: UploadFile = File(..., description="Document file (JPEG, PNG, or multi-page PDF)"),
    include_detailed_blocks: bool = Form(default=False, description="Include detailed text blocks with coordinates"),
    max_pages: int = Form(default=50, description="Maximum number of pages to process from PDF (default 50)"),
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Extract all text from document pages using OCR.
    
    This endpoint extracts readable text from various document types:
    - Passports (bio page, visa stamps, endorsements)
    - National IDs and driver's licenses
    - Birth certificates and marriage certificates
    - Academic transcripts and diplomas
    - Employment letters and contracts
    - Any document with printed or typed text
    
    Features:
    - Supports single images (JPEG, PNG) - treated as page 1
    - Supports multi-page PDFs - all pages will be processed up to max_pages
    - Uses EasyOCR for text detection and recognition
    - Returns text organized by page number
    - Optionally includes text block positions and confidence scores
    
    Args:
        file: Document file (required)
        include_detailed_blocks: Include text block coordinates and confidence
        max_pages: Maximum pages to process (default 50, prevents processing huge PDFs)
        
    Returns:
        Dictionary with extracted text from all pages
    """
    try:
        from app.services.text_extractor import text_extraction_service
        
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
                detail=f"Invalid file format. Supported: JPEG, PNG, PDF. Detected: {image_format}"
            )
        
        logger.info(f"Processing {image_format} file for text extraction (size: {file_size / 1024:.1f}KB)")
        
        # Load image(s) from file
        images = load_images_from_bytes(content, max_pages=max_pages)
        
        if not images or len(images) == 0:
            raise HTTPException(
                status_code=400,
                detail="Failed to load image from file"
            )
        
        logger.info(f"Loaded {len(images)} page(s) from file")
        
        # Extract text from all pages
        result = text_extraction_service.extract_text_from_pages(
            images,
            include_detailed_blocks=include_detailed_blocks
        )
        
        # Build response
        response = {
            "success": result["success"],
            "is_valid": result["success"],
            "total_pages": result["total_pages"],
            "pages": result["pages"],
            "combined_text": result["combined_text"],
            "ocr_method": result["ocr_method"],
            "processing_time_seconds": result["processing_time_seconds"],
            "errors": result["errors"],
            "warnings": result["warnings"]
        }
        
        # Convert numpy types if any
        response = convert_numpy_types(response)
        
        logger.info(f"Text extraction completed: {len(result['pages'])} pages, "
                   f"{len(result['combined_text'])} characters total")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(e)}"
        )


@router.post(
    "/extract-text/url",
    response_model=dict,
    summary="Extract Text from Document Pages (URL)",
    description="Extract all text from document pages by providing a URL. Works with passports, IDs, certificates, and other documents.",
    responses={
        200: {"description": "Text extraction completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def extract_text_from_document_url(
    request: dict = Body(..., example={
        "image_url": "https://example.com/document.pdf",
        "include_detailed_blocks": False,
        "max_pages": 50
    }),
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Extract all text from document pages by providing a URL.
    
    This endpoint downloads and processes documents from a URL:
    - Supports single images (JPEG, PNG) - treated as page 1
    - Supports multi-page PDFs - processes up to max_pages (default 50)
    - Uses EasyOCR for text detection and recognition
    - Returns text organized by page number
    - Works with various document types (passports, IDs, certificates, etc.)
    
    Args:
        request: JSON body with image_url, optional include_detailed_blocks and max_pages
        
    Returns:
        Dictionary with extracted text from all pages
    """
    try:
        from app.services.text_extractor import text_extraction_service
        
        # Extract parameters
        image_url = request.get("image_url")
        include_detailed_blocks = request.get("include_detailed_blocks", False)
        max_pages = request.get("max_pages", 50)
        
        if not image_url:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: image_url"
            )
        
        logger.info(f"Downloading document from URL: {image_url}")
        
        # Download image
        content = await download_image_from_url(image_url)
        
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
                detail=f"Invalid file format. Supported: JPEG, PNG, PDF. Detected: {image_format}"
            )
        
        logger.info(f"Processing {image_format} file for text extraction (size: {file_size / 1024:.1f}KB)")
        
        # Load image(s) from file
        images = load_images_from_bytes(content, max_pages=max_pages)
        
        if not images or len(images) == 0:
            raise HTTPException(
                status_code=400,
                detail="Failed to load image from URL"
            )
        
        logger.info(f"Loaded {len(images)} page(s) from URL")
        
        # Extract text from all pages
        result = text_extraction_service.extract_text_from_pages(
            images,
            include_detailed_blocks=include_detailed_blocks
        )
        
        # Build response
        response = {
            "success": result["success"],
            "is_valid": result["success"],
            "total_pages": result["total_pages"],
            "pages": result["pages"],
            "combined_text": result["combined_text"],
            "ocr_method": result["ocr_method"],
            "processing_time_seconds": result["processing_time_seconds"],
            "errors": result["errors"],
            "warnings": result["warnings"]
        }
        
        # Convert numpy types if any
        response = convert_numpy_types(response)
        
        logger.info(f"Text extraction completed: {len(result['pages'])} pages, "
                   f"{len(result['combined_text'])} characters total")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(e)}"
        )
