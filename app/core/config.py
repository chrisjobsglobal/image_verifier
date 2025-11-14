"""Application Configuration and Settings"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = "Image Verifier API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API Settings
    api_prefix: str = "/api/v1"
    
    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # File Upload Settings
    max_upload_size: int = 10 * 1024 * 1024  # 10MB in bytes
    allowed_image_types: list[str] = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    upload_directory: str = "uploads"
    
    # Image Processing Settings
    min_image_width: int = 1920  # Full HD minimum
    min_image_height: int = 1080
    max_image_width: int = 8000
    max_image_height: int = 8000
    
    # Photo Quality Thresholds
    min_face_percentage: float = 70.0
    max_face_percentage: float = 80.0
    max_tilt_angle_degrees: float = 10.0
    blur_threshold: float = 100.0  # Laplacian variance threshold
    min_brightness: int = 50
    max_brightness: int = 200
    min_contrast: float = 40.0
    
    # Passport Document Settings (for photos of passport documents)
    min_document_percentage: float = 30.0  # Minimum 30% for photographed documents
    max_document_percentage: float = 95.0  # Maximum 95% (allow some margin)
    max_document_tilt_degrees: float = 10.0
    
    # Tesseract OCR Path (Windows default, adjust if needed)
    tesseract_cmd: Optional[str] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # MediaPipe Settings
    mediapipe_model_complexity: int = 1
    mediapipe_min_detection_confidence: float = 0.5
    mediapipe_min_tracking_confidence: float = 0.5
    
    # Face Recognition Settings
    face_recognition_tolerance: float = 0.6
    face_recognition_model: str = "hog"  # "hog" or "cnn"
    
    # Security Settings
    api_key: Optional[str] = None
    api_key_name: str = "X-API-Key"
    
    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    
    # Database (optional, for audit trails)
    database_url: Optional[str] = None
    
    # External API Keys (optional)
    idanalyzer_api_key: Optional[str] = None
    biogaze_api_key: Optional[str] = None


# Create global settings instance
settings = Settings()
