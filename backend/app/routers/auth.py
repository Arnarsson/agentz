"""
Authentication router for token verification and user management.
"""
from fastapi import APIRouter, Depends
from app.core.auth.clerk_middleware import ClerkAuth, TokenPayload

router = APIRouter(prefix="/auth", tags=["auth"])
clerk_auth = ClerkAuth()

@router.get("/me")
async def get_current_user(token: TokenPayload = Depends(clerk_auth)):
    """
    Get the current authenticated user's information.
    
    Args:
        token: The decoded JWT token data from Clerk
        
    Returns:
        dict: The user's information
    """
    return {
        "user_id": token.sub,
        "session_id": token.sid,
        "issued_at": token.iat,
        "expires_at": token.exp,
        "user": token.user,
        "token_data": token.dict(exclude_none=True)
    }

@router.get("/verify-token")
async def verify_token(token: TokenPayload = Depends(clerk_auth)):
    """
    Verify and decode a JWT token.
    
    Args:
        token: The decoded JWT token data from Clerk
        
    Returns:
        dict: The decoded token data if valid
    """
    return {
        "message": "Token is valid",
        "user_id": token.sub,
        "session_id": token.sid,
        "issued_at": token.iat,
        "expires_at": token.exp,
        "token_data": token.dict(exclude_none=True)
    } 