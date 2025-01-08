from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
from pydantic import BaseModel, EmailStr
from app.core.config import settings
from datetime import datetime


class ClerkAuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)


class UserMetadata(BaseModel):
    """Model for user metadata from Clerk token"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    image_url: Optional[str] = None
    email_verified: Optional[bool] = None
    phone_number_verified: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    external_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None
    primary_email_address: Optional[EmailStr] = None
    primary_phone_number: Optional[str] = None
    primary_web3_wallet: Optional[str] = None
    unsafe_metadata: Optional[dict] = None
    public_metadata: Optional[dict] = None


class TokenPayload(BaseModel):
    """Model for Clerk JWT token payload"""
    sub: str  # User ID
    exp: int  # Expiration time
    azp: Optional[str] = None  # Authorized party
    iss: Optional[str] = None  # Issuer
    aud: Optional[list[str]] = None  # Audience
    iat: Optional[int] = None  # Issued at
    nbf: Optional[int] = None  # Not before
    jti: Optional[str] = None  # JWT ID
    sid: Optional[str] = None  # Session ID
    user: Optional[UserMetadata] = None  # User metadata
    source_platform: Optional[str] = None
    session: Optional[dict] = None


class ClerkAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.public_key = settings.CLERK_JWT_VERIFICATION_KEY

    async def __call__(self, request: Request) -> TokenPayload:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise ClerkAuthError("No credentials provided")
        
        if credentials.scheme.lower() != "bearer":
            raise ClerkAuthError("Invalid authentication scheme")
        
        try:
            # The public key is already in PEM format from settings
            payload = jwt.decode(
                credentials.credentials,
                self.public_key,
                algorithms=[ALGORITHMS.RS256],
                options={"verify_exp": True}
            )
            token_data = TokenPayload(**payload)
            
            # Store full user data in request state for easy access
            request.state.user_id = token_data.sub
            request.state.user = token_data.user
            request.state.session_id = token_data.sid
            
            return token_data
        except JWTError as e:
            raise ClerkAuthError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise ClerkAuthError(f"Failed to process token: {str(e)}")


# Create a reusable instance
clerk_auth = ClerkAuth() 