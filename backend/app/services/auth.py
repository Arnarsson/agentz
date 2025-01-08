"""
Authentication service for JWT token handling.
"""
from typing import Tuple, Dict, Any
import jwt
from loguru import logger

from app.core.config import settings

def decode_jwt_token(token: str) -> Tuple[bool, Dict[Any, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Tuple[bool, dict]: (is_valid, token_data/error_message)
    """
    try:
        # First decode without verification to get header info
        unverified_header = jwt.get_unverified_header(token)
        logger.debug(f"JWT Header: {unverified_header}")
        
        # Verify the token with Clerk's public key
        decoded = jwt.decode(
            token,
            settings.CLERK_JWT_VERIFICATION_KEY,
            algorithms=["RS256"],
            audience="http://localhost:3001",  # Match your frontend URL
            options={"verify_exp": True}
        )
        
        logger.info(f"Successfully verified token for user: {decoded.get('sub')}")
        return True, decoded
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return False, {"error": "Token has expired"}
        
    except jwt.InvalidAudienceError:
        logger.warning("Invalid token audience")
        return False, {"error": "Invalid token audience"}
        
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return False, {"error": f"Invalid token: {str(e)}"}
        
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return False, {"error": f"Error decoding token: {str(e)}"} 