"""Debug endpoints for troubleshooting"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
import logging
import cv2
import numpy as np
import os
import uuid
from datetime import datetime

from app.utils.image_utils import download_image_from_url, load_image_from_bytes
from app.core.security import verify_api_key
from app.services.icao_validator import ICAOValidatorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Debug"])

# Initialize services
icao_validator = ICAOValidatorService()


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


@router.post(
    "/analyze-tilt",
    summary="Debug: Analyze Document Tilt Detection",
    description="Analyzes tilt detection using ONLY outermost border pixels"
)
async def debug_analyze_tilt(
    request: DebugImageRequest = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Debug endpoint to analyze tilt detection focusing on border pixels only.
    Saves image with border strips highlighted and detected lines overlaid.
    """
    try:
        # Download and load image
        logger.info(f"Downloading from URL: {request.image_url}")
        content = await download_image_from_url(str(request.image_url))
        image = load_image_from_bytes(content)
        
        # Detect document region
        document_region = icao_validator._detect_document_edges(image)
        x, y, w, h = document_region
        
        # Extract document
        doc_img = image[y:y+h, x:x+w].copy()
        gray = cv2.cvtColor(doc_img, cv2.COLOR_BGR2GRAY)
        
        # Visualization
        viz_img = doc_img.copy()
        
        # Border width for analysis
        border_width = 5
        
        # Highlight the border strips being analyzed
        # Top strip - red
        cv2.rectangle(viz_img, (0, 0), (w, border_width), (0, 0, 255), 2)
        # Bottom strip - red
        cv2.rectangle(viz_img, (0, h - border_width), (w, h), (0, 0, 255), 2)
        # Left strip - blue
        cv2.rectangle(viz_img, (0, 0), (border_width, h), (255, 0, 0), 2)
        # Right strip - blue
        cv2.rectangle(viz_img, (w - border_width, 0), (w, h), (255, 0, 0), 2)
        
        # Extract border strips
        top_strip = gray[:border_width, :]
        bottom_strip = gray[-border_width:, :]
        left_strip = gray[:, :border_width]
        right_strip = gray[:, -border_width:]
        
        all_angles = []
        horizontal_angles = []
        vertical_angles = []
        
        # Analyze top and bottom borders
        for idx, strip in enumerate([top_strip, bottom_strip]):
            edges = cv2.Canny(strip, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20,
                                   minLineLength=50, maxLineGap=10)
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Draw on viz (offset y for top/bottom)
                    if idx == 0:  # top
                        cv2.line(viz_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    else:  # bottom
                        cv2.line(viz_img, (x1, h - border_width + y1), (x2, h - border_width + y2), (0, 255, 0), 2)
                    
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    all_angles.append(angle)
                    horizontal_angles.append(angle)
        
        # Analyze left and right borders
        for idx, strip in enumerate([left_strip, right_strip]):
            edges = cv2.Canny(strip, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20,
                                   minLineLength=50, maxLineGap=10)
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Draw on viz (offset x for left/right)
                    if idx == 0:  # left
                        cv2.line(viz_img, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    else:  # right
                        cv2.line(viz_img, (w - border_width + x1, y1), (w - border_width + x2, y2), (0, 255, 255), 2)
                    
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    vertical_angles.append(angle)
        
        # Calculate tilt angle
        calculated_angle = icao_validator._calculate_document_angle(image, document_region)
        
        # Normalize angles for display
        normalized_angles = []
        for angle in all_angles:
            while angle > 90:
                angle -= 180
            while angle < -90:
                angle += 180
            if abs(angle) < 60:
                normalized_angles.append(angle)
        
        # Save visualization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"tilt_border_analysis_{timestamp}_{unique_id}.jpg"
        
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "public", "debug")
        os.makedirs(public_dir, exist_ok=True)
        filepath = os.path.join(public_dir, filename)
        
        cv2.imwrite(filepath, viz_img)
        
        return {
            "success": True,
            "calculated_tilt_angle": calculated_angle,
            "border_width_pixels": border_width,
            "horizontal_lines_found": len(horizontal_angles),
            "vertical_lines_found": len(vertical_angles),
            "horizontal_angles": [round(a, 2) for a in horizontal_angles][:10],
            "vertical_angles": [round(a, 2) for a in vertical_angles][:10],
            "normalized_angles": [round(a, 2) for a in normalized_angles][:20],
            "median_angle": round(np.median(normalized_angles), 2) if normalized_angles else 0.0,
            "document_region": {
                "x": x, "y": y, "width": w, "height": h
            },
            "visualization_url": f"/static/debug/{filename}",
            "full_url": f"http://104.167.8.60:27000/static/debug/{filename}",
            "legend": {
                "red_boxes": "Top/Bottom border strips (5px high)",
                "blue_boxes": "Left/Right border strips (5px wide)",
                "green_lines": "Lines detected in horizontal borders",
                "cyan_lines": "Lines detected in vertical borders"
            }
        }
        
    except Exception as e:
        logger.error(f"Debug tilt analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during tilt analysis: {str(e)}"
        )


@router.post(
    "/extract-face",
    summary="Debug: Extract Detected Face from Image",
    description="Detects face in image, extracts it, and saves to public folder for inspection"
)
async def debug_extract_face(
    request: DebugImageRequest = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Debug endpoint to extract and save the detected face from an image.
    Useful for troubleshooting face detection and seeing what area is being analyzed.
    """
    try:
        # Download and load image
        logger.info(f"Downloading from URL: {request.image_url}")
        content = await download_image_from_url(str(request.image_url))
        image = load_image_from_bytes(content)
        
        # Get face detection service
        from app.services.face_detection import FaceDetectionService
        face_service = FaceDetectionService()
        
        # Detect face
        logger.info("Detecting face...")
        face_results = face_service.analyze_face(image)
        
        # Check if face was detected (convert numpy.bool_ to Python bool)
        face_detected = bool(face_results.get("face_detected", False))
        
        if not face_detected:
            return {
                "success": False,
                "error": "No face detected in image"
            }
        
        # Get face location from metrics
        face_location_dict = face_results.get("metrics", {}).get("face_location")
        if not face_location_dict:
            return {
                "success": False,
                "error": "Face detected but location not available"
            }
        
        # Extract face location coordinates
        top = face_location_dict["top"]
        right = face_location_dict["right"]
        bottom = face_location_dict["bottom"]
        left = face_location_dict["left"]
        face_height = bottom - top
        face_width = right - left
        
        # Add padding around face (20% on each side)
        padding_h = int(face_height * 0.2)
        padding_w = int(face_width * 0.2)
        
        img_height, img_width = image.shape[:2]
        
        # Calculate padded coordinates (with bounds checking)
        top_padded = max(0, top - padding_h)
        bottom_padded = min(img_height, bottom + padding_h)
        left_padded = max(0, left - padding_w)
        right_padded = min(img_width, right + padding_w)
        
        # Extract face region with padding
        face_img = image[top_padded:bottom_padded, left_padded:right_padded]
        
        # Create visualization showing face box on original image
        viz_img = image.copy()
        
        # Draw face bounding box (red)
        cv2.rectangle(viz_img, (left, top), (right, bottom), (0, 0, 255), 3)
        
        # Draw padded extraction box (green)
        cv2.rectangle(viz_img, (left_padded, top_padded), (right_padded, bottom_padded), (0, 255, 0), 2)
        
        # Add text with face percentage (from metrics)
        face_percentage = face_results.get("metrics", {}).get("face_percentage", 0)
        text = f"Face: {face_percentage:.1f}%"
        cv2.putText(viz_img, text, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.9, (0, 0, 255), 2)
        
        # Save extracted face
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        face_filename = f"extracted_face_{timestamp}_{unique_id}.jpg"
        viz_filename = f"face_detection_{timestamp}_{unique_id}.jpg"
        
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "public", "debug")
        os.makedirs(public_dir, exist_ok=True)
        
        face_filepath = os.path.join(public_dir, face_filename)
        viz_filepath = os.path.join(public_dir, viz_filename)
        
        # Save both images
        cv2.imwrite(face_filepath, face_img)
        cv2.imwrite(viz_filepath, viz_img)
        
        # Get file sizes
        face_size = os.path.getsize(face_filepath)
        viz_size = os.path.getsize(viz_filepath)
        
        return {
            "success": True,
            "face_detected": True,
            "face_metrics": {
                "face_percentage": float(face_percentage),
                "face_size": {
                    "width": int(face_width),
                    "height": int(face_height)
                },
                "extracted_size": {
                    "width": int(right_padded - left_padded),
                    "height": int(bottom_padded - top_padded)
                },
                "face_location": {
                    "top": int(top),
                    "right": int(right),
                    "bottom": int(bottom),
                    "left": int(left)
                }
            },
            "original_image_size": {
                "width": int(img_width),
                "height": int(img_height)
            },
            "extracted_face": {
                "url": f"/static/debug/{face_filename}",
                "full_url": f"http://104.167.8.60:27000/static/debug/{face_filename}",
                "file_size_kb": round(face_size / 1024, 2)
            },
            "visualization": {
                "url": f"/static/debug/{viz_filename}",
                "full_url": f"http://104.167.8.60:27000/static/debug/{viz_filename}",
                "file_size_kb": round(viz_size / 1024, 2)
            },
            "legend": {
                "red_box": "Detected face boundary",
                "green_box": "Extracted region (face + 20% padding)",
                "extracted_face": "Cropped face image saved separately"
            }
        }
        
    except Exception as e:
        logger.error(f"Debug face extraction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during face extraction: {str(e)}"
        )
