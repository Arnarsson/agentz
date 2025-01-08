"""
Authentication router for token verification and user management.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth import decode_jwt_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.get("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify and decode a JWT token.
    
    Args:
        credentials: The HTTP Authorization header containing the JWT token
        
    Returns:
        dict: The decoded token data if valid
    """
    token = credentials.credentials
    is_valid, result = decode_jwt_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail=result.get("error", "Invalid token")
        )
    
    return {
        "message": "Token is valid",
        "user_id": result.get("sub"),
        "session_id": result.get("sid"),
        "issued_at": result.get("iat"),
        "expires_at": result.get("exp"),
        "token_data": result
    } 