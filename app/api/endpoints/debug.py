"""Debug endpoints for troubleshooting"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
import logging
import cv2
import os
import uuid
from datetime import datetime

from app.utils.image_utils import download_image_from_url, load_image_from_bytes
from app.core.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Debug"])


class DebugImageRequest(BaseModel):
    """Request for debugging image conversion"""
    image_url: str


@router.post(
    "/pdf-to-image",
    summary="Debug: Convert PDF to Image and Save",
    description="Downloads PDF, converts to image, saves to public folder, and returns URL for inspection"
)
async def debug_pdf_to_image(
    request: DebugImageRequest = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Debug endpoint to convert PDF to image and save for visual inspection.
    
    Useful for troubleshooting why PDF conversion might not be working as expected.
    
    Args:
        request: JSON body with image_url
        
    Returns:
        Image URL, dimensions, and file path
    """
    try:
        # Download from URL
        logger.info(f"Downloading from URL: {request.image_url}")
        content = await download_image_from_url(str(request.image_url))
        
        # Load image (this will convert PDF if needed)
        logger.info("Converting to image...")
        image = load_image_from_bytes(content)
        
        # Get image info
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        
        logger.info(f"Image loaded: {width}x{height}, channels={channels}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"debug_{timestamp}_{unique_id}.jpg"
        
        # Save to public/debug folder
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "public", "debug")
        os.makedirs(public_dir, exist_ok=True)
        
        filepath = os.path.join(public_dir, filename)
        
        # Save image
        success = cv2.imwrite(filepath, image)
        
        if not success:
            raise ValueError("Failed to save image")
        
        logger.info(f"Image saved to: {filepath}")
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Return info
        return {
            "success": True,
            "message": "Image converted and saved successfully",
            "image_url": f"/static/debug/{filename}",
            "full_url": f"http://104.167.8.60:27000/static/debug/{filename}",
            "image_info": {
                "width": width,
                "height": height,
                "channels": channels,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2)
            },
            "file_path": filepath,
            "was_pdf": content[:4] == b'%PDF'
        }
    
    except Exception as e:
        logger.error(f"Debug conversion error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during conversion: {str(e)}"
        )


@router.get(
    "/list-debug-images",
    summary="List Saved Debug Images",
    description="List all debug images saved in public folder"
)
async def list_debug_images(api_key: str = Depends(verify_api_key)):
    """List all debug images"""
    try:
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "public", "debug")
        
        if not os.path.exists(public_dir):
            return {
                "success": True,
                "images": [],
                "message": "Debug directory does not exist yet"
            }
        
        files = []
        for filename in os.listdir(public_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(public_dir, filename)
                file_size = os.path.getsize(filepath)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                files.append({
                    "filename": filename,
                    "url": f"/static/debug/{filename}",
                    "full_url": f"http://104.167.8.60:27000/static/debug/{filename}",
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "modified": file_time.isoformat()
                })
        
        # Sort by modified time, newest first
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "success": True,
            "count": len(files),
            "images": files
        }
    
    except Exception as e:
        logger.error(f"Error listing debug images: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing images: {str(e)}"
        )


@router.delete(
    "/clear-debug-images",
    summary="Clear All Debug Images",
    description="Delete all debug images from public folder"
)
async def clear_debug_images(api_key: str = Depends(verify_api_key)):
    """Clear all debug images"""
    try:
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "public", "debug")
        
        if not os.path.exists(public_dir):
            return {
                "success": True,
                "deleted": 0,
                "message": "Debug directory does not exist"
            }
        
        deleted = 0
        for filename in os.listdir(public_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(public_dir, filename)
                os.remove(filepath)
                deleted += 1
        
        return {
            "success": True,
            "deleted": deleted,
            "message": f"Deleted {deleted} debug images"
        }
    
    except Exception as e:
        logger.error(f"Error clearing debug images: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing images: {str(e)}"
        )
