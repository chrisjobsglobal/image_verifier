"""Image processing utility functions"""

import io
from typing import Tuple, Optional
import cv2
import numpy as np
from PIL import Image


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Load an image from bytes into OpenCV format.
    
    Args:
        image_bytes: Image file bytes
        
    Returns:
        Image as numpy array in BGR format
        
    Raises:
        ValueError: If image cannot be loaded
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
        return image
    except Exception as e:
        raise ValueError(f"Error loading image: {str(e)}")


def load_image_from_pil(pil_image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to OpenCV format.
    
    Args:
        pil_image: PIL Image object
        
    Returns:
        Image as numpy array in BGR format
    """
    # Convert PIL Image to numpy array
    rgb_image = np.array(pil_image.convert('RGB'))
    # Convert RGB to BGR for OpenCV
    bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
    return bgr_image


def image_to_pil(cv_image: np.ndarray) -> Image.Image:
    """
    Convert OpenCV image to PIL Image.
    
    Args:
        cv_image: Image as numpy array in BGR format
        
    Returns:
        PIL Image object
    """
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_image)


def get_image_dimensions(image: np.ndarray) -> Tuple[int, int]:
    """
    Get image width and height.
    
    Args:
        image: Image as numpy array
        
    Returns:
        Tuple of (width, height)
    """
    height, width = image.shape[:2]
    return width, height


def resize_image(image: np.ndarray, max_width: int = 1920, max_height: int = 1080) -> np.ndarray:
    """
    Resize image to fit within max dimensions while maintaining aspect ratio.
    
    Args:
        image: Image as numpy array
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    # Calculate scaling factor
    scale = min(max_width / width, max_height / height)
    
    # Only resize if image is larger than max dimensions
    if scale < 1:
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale.
    
    Args:
        image: Image as numpy array in BGR format
        
    Returns:
        Grayscale image
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotate image by specified angle.
    
    Args:
        image: Image as numpy array
        angle: Rotation angle in degrees (positive = counter-clockwise)
        
    Returns:
        Rotated image
    """
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    
    # Get rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Perform rotation
    rotated = cv2.warpAffine(image, rotation_matrix, (width, height), 
                             flags=cv2.INTER_LINEAR, 
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=(255, 255, 255))
    
    return rotated


def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """
    Crop image to specified rectangle.
    
    Args:
        image: Image as numpy array
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Width of crop area
        height: Height of crop area
        
    Returns:
        Cropped image
    """
    return image[y:y+height, x:x+width]


def normalize_brightness(image: np.ndarray) -> np.ndarray:
    """
    Normalize image brightness using histogram equalization.
    
    Args:
        image: Image as numpy array
        
    Returns:
        Brightness-normalized image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    # Split into channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_equalized = clahe.apply(l)
    
    # Merge channels
    lab_equalized = cv2.merge([l_equalized, a, b])
    
    # Convert back to BGR
    normalized = cv2.cvtColor(lab_equalized, cv2.COLOR_LAB2BGR)
    
    return normalized


def enhance_image_quality(image: np.ndarray) -> np.ndarray:
    """
    Apply general image quality enhancements.
    
    Args:
        image: Image as numpy array
        
    Returns:
        Enhanced image
    """
    # Denoise
    denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    
    # Sharpen
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    return sharpened


def calculate_aspect_ratio(width: int, height: int) -> float:
    """
    Calculate aspect ratio.
    
    Args:
        width: Image width
        height: Image height
        
    Returns:
        Aspect ratio (width/height)
    """
    return width / height if height > 0 else 0.0


def is_color_image(image: np.ndarray) -> bool:
    """
    Check if image is color or grayscale.
    
    Args:
        image: Image as numpy array
        
    Returns:
        True if color, False if grayscale
    """
    return len(image.shape) == 3 and image.shape[2] == 3


def get_file_size(image_bytes: bytes) -> int:
    """
    Get file size in bytes.
    
    Args:
        image_bytes: Image file bytes
        
    Returns:
        File size in bytes
    """
    return len(image_bytes)


def validate_image_format(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate image format using PIL.
    
    Args:
        image_bytes: Image file bytes
        
    Returns:
        Tuple of (is_valid, format_name)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return True, image.format
    except Exception:
        return False, None
