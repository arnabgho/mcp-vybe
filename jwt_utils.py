"""JWT token utilities for authentication."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import logging

# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = float(os.getenv("JWT_EXPIRATION_HOURS", "1"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "30"))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.
    
    Args:
        data: Dictionary containing the claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token.
    
    Args:
        data: Dictionary containing the claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token as string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
            return None
        
        # Check expiration (jose handles this but we can add custom logic)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.debug("Token has expired")
            return None
        
        return payload
        
    except JWTError as e:
        logger.debug(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Use a refresh token to create a new access token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access token if refresh token is valid, None otherwise
    """
    # Verify the refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        return None
    
    # Create new access token with same claims (minus token-specific fields)
    new_claims = {
        k: v for k, v in payload.items()
        if k not in ["exp", "iat", "type"]
    }
    
    return create_access_token(new_claims)


def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """Get information about a token without full verification.
    
    Args:
        token: JWT token to inspect
        
    Returns:
        Token information including expiration time
    """
    try:
        # Decode without verification to get claims
        unverified = jwt.get_unverified_claims(token)
        
        # Also verify it properly
        verified = verify_token(token, token_type=unverified.get("type", "access"))
        
        if verified:
            exp_timestamp = verified.get("exp")
            iat_timestamp = verified.get("iat")
            
            info = {
                "valid": True,
                "type": verified.get("type"),
                "subject": verified.get("sub"),
                "provider": verified.get("provider"),
                "issued_at": datetime.fromtimestamp(iat_timestamp).isoformat() if iat_timestamp else None,
                "expires_at": datetime.fromtimestamp(exp_timestamp).isoformat() if exp_timestamp else None,
                "expires_in_seconds": exp_timestamp - datetime.utcnow().timestamp() if exp_timestamp else None
            }
            return info
        else:
            return {"valid": False, "error": "Token verification failed"}
            
    except Exception as e:
        return {"valid": False, "error": str(e)}