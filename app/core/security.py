"""Security utilities and API key validation"""

from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings


# API Key header security
api_key_header = APIKeyHeader(name=settings.api_key_name, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from request header
        
    Returns:
        Valid API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # If API key is not configured, skip validation
    if not settings.api_key:
        return "no-auth-configured"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key
