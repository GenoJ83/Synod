"""
JWT Token Handler for authentication
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "fallback_secret_key_change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def create_access_token(user_data: Dict) -> str:
    """
    Create a JWT access token for the user
    
    Args:
        user_data: Dictionary containing user information (email, name, provider, etc.)
    
    Returns:
        Encoded JWT token string
    """
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": user_data.get("email"),  # Subject (user identifier)
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "provider": user_data.get("provider", "email"),
        "picture": user_data.get("picture"),
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT access token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None
