from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .jwt_handler import verify_token, get_user_id_from_token

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user ID from JWT token"""
    token = credentials.credentials
    return get_user_id_from_token(token)


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """Get user ID from token if provided (optional authentication)"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization[7:]  # Remove "Bearer " prefix
    try:
        return get_user_id_from_token(token)
    except HTTPException:
        return None


async def verify_extension_version(
    x_extension_version: Optional[str] = Header(None)
) -> str:
    """Verify Chrome extension version"""
    if not x_extension_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension version header required"
        )
    return x_extension_version 