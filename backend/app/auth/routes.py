"""
Authentication Routes for OAuth and JWT
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import httpx

from .oauth import oauth
from .jwt_handler import create_access_token, verify_access_token

load_dotenv()

router = APIRouter(prefix="/auth", tags=["authentication"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# --- Google OAuth ---

@router.get("/google/login")
async def google_login(request: Request):
    """Redirect to Google OAuth authorization page"""
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback and create JWT token"""
    try:
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Create user data
        user_data = {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "provider": "google"
        }
        
        # Create JWT token
        jwt_token = create_access_token(user_data)
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}"
        )
    
    except Exception as e:
        print(f"Google OAuth error: {str(e)}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=oauth_failed"
        )


# --- GitHub OAuth ---

@router.get("/github/login")
async def github_login(request: Request):
    """Redirect to GitHub OAuth authorization page"""
    redirect_uri = f"{BACKEND_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request):
    """Handle GitHub OAuth callback and create JWT token"""
    try:
        # Get access token from GitHub
        token = await oauth.github.authorize_access_token(request)
        
        # GitHub doesn't return user info in the token, we need to fetch it
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token['access_token']}"}
            
            # Get user profile
            user_response = await client.get(
                "https://api.github.com/user",
                headers=headers
            )
            user_info = user_response.json()
            
            # Get user email (might be private)
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers=headers
            )
            emails = email_response.json()
            
            # Find primary email
            primary_email = next(
                (email["email"] for email in emails if email["primary"]),
                emails[0]["email"] if emails else user_info.get("email")
            )
        
        # Create user data
        user_data = {
            "email": primary_email,
            "name": user_info.get("name") or user_info.get("login"),
            "picture": user_info.get("avatar_url"),
            "provider": "github"
        }
        
        # Create JWT token
        jwt_token = create_access_token(user_data)
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}"
        )
    
    except Exception as e:
        print(f"GitHub OAuth error: {str(e)}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=oauth_failed"
        )


# --- Token Verification ---

class TokenVerifyRequest(BaseModel):
    token: str


@router.post("/verify")
async def verify_token(request: TokenVerifyRequest):
    """Verify a JWT token and return user data"""
    payload = verify_access_token(request.token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "user": {
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "provider": payload.get("provider")
        }
    }
