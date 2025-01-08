from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.auth.clerk_middleware import clerk_auth, TokenPayload, UserMetadata
import jwt
from typing import Optional


router = APIRouter()


class UserResponse(BaseModel):
    """Response model for user information"""
    user_id: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    image_url: Optional[str] = None
    message: str


class TokenDebugResponse(BaseModel):
    """Response model for token debugging"""
    token: str
    decoded_payload: dict
    is_valid: bool
    validation_message: str
    user_info: Optional[UserMetadata] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, token: TokenPayload = Depends(clerk_auth)):
    """
    Get current authenticated user information.
    This is a protected endpoint that requires a valid Clerk JWT token.
    """
    return UserResponse(
        user_id=request.state.user_id,
        email=request.state.user.primary_email_address if request.state.user else None,
        first_name=request.state.user.first_name if request.state.user else None,
        last_name=request.state.user.last_name if request.state.user else None,
        username=request.state.user.username if request.state.user else None,
        image_url=request.state.user.image_url if request.state.user else None,
        message="Successfully authenticated"
    )


@router.get("/debug-token")
async def debug_token(request: Request):
    """
    Debug endpoint to validate JWT token structure.
    Send your token in the Authorization header as 'Bearer <token>'.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No Bearer token provided")
    
    token = auth_header.split(" ")[1]
    try:
        # First, try to decode without verification to check structure
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        
        # Now try to verify with our public key
        public_key = f"""-----BEGIN PUBLIC KEY-----
{clerk_auth.public_key}
-----END PUBLIC KEY-----"""
        
        verified_payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=clerk_auth.audience,
            options={"verify_exp": True}
        )
        
        # Try to parse user info if available
        user_info = None
        if "user" in verified_payload:
            try:
                user_info = UserMetadata(**verified_payload["user"])
            except Exception as e:
                print(f"Failed to parse user info: {e}")
        
        return TokenDebugResponse(
            token=token,
            decoded_payload=verified_payload,
            is_valid=True,
            validation_message="Token is valid and properly verified",
            user_info=user_info
        )
    except jwt.InvalidTokenError as e:
        return TokenDebugResponse(
            token=token,
            decoded_payload=unverified_payload if 'unverified_payload' in locals() else {},
            is_valid=False,
            validation_message=f"Token validation failed: {str(e)}",
            user_info=None
        )
    except Exception as e:
        return TokenDebugResponse(
            token=token,
            decoded_payload={},
            is_valid=False,
            validation_message=f"Error processing token: {str(e)}",
            user_info=None
        )


@router.get("/protected-resource")
async def protected_resource(request: Request, token: TokenPayload = Depends(clerk_auth)):
    """
    Example of a protected resource.
    This endpoint requires authentication via Clerk.
    """
    return {
        "message": "This is a protected resource",
        "user_id": token.sub,
        "email": token.user.primary_email_address if token.user else None,
        "username": token.user.username if token.user else None
    } 