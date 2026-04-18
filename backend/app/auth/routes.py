"""
Authentication Routes for Firebase Auth
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import secrets

from .oauth import oauth
from .jwt_handler import create_access_token, verify_access_token

load_dotenv()

router = APIRouter(prefix="/auth", tags=["authentication"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")


# --- Firebase Auth ---

class FirebaseAuthRequest(BaseModel):
    token: str


@router.post("/firebase")
async def firebase_auth(request: FirebaseAuthRequest):
    """Verify Firebase ID token and sync user to database."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    
    try:
        decoded_token = id_token.verify_firebase_token(
            request.token,
            google_requests.Request(),
            audience=FIREBASE_PROJECT_ID
        )
        
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: missing email")
        
        from ..database import SessionLocal
        from ..models import User
        from .security import get_password_hash
        
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.email == email).first()
            if not db_user:
                db_user = User(
                    email=email,
                    full_name=decoded_token.get("name", email.split('@')[0]),
                    hashed_password=get_password_hash(secrets.token_urlsafe(16)),
                    is_active=True
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
        finally:
            db.close()
        
        user_data = {
            "email": email,
            "name": decoded_token.get("name", email.split('@')[0]),
            "picture": decoded_token.get("picture"),
            "provider": "firebase"
        }
        
        jwt_token = create_access_token(user_data)
        return {"token": jwt_token, "user": user_data}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth error: {str(e)}")


# --- Google OAuth ---

@router.get("/google/login")
async def google_login(request: Request):
    """Redirect to Google OAuth authorization page"""
    try:
        redirect_uri = f"{BACKEND_URL}/auth/google/callback"
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f"Google login redirect error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_init_failed&details={str(e)}")


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

        # --- PERSIST GOOGLE USER TO DB ---
        from ..database import SessionLocal
        from ..models import User
        
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not db_user:
                # Create new user for Google login
                # We use a dummy password since they login via Google
                dummy_password = get_password_hash(secrets.token_urlsafe(16))
                new_user = User(
                    email=user_data["email"],
                    hashed_password=dummy_password,
                    full_name=user_data["name"]
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                print(f"Created new Google user in DB: {new_user.email}")
            else:
                print(f"Google user already exists in DB: {db_user.email}")
        except Exception as db_e:
            print(f"Database error during Google login: {db_e}")
        finally:
            db.close()
        # ---------------------------------
        
        # Create JWT token
        jwt_token = create_access_token(user_data)
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}"
        )
    
    except Exception as e:
        import traceback
        print(f"Google OAuth error: {str(e)}")
        traceback.print_exc()
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=oauth_failed&details={str(e)}"
        )


# --- GitHub OAuth ---

@router.get("/github/login")
async def github_login(request: Request):
    """Redirect to GitHub OAuth authorization page"""
    try:
        redirect_uri = f"{BACKEND_URL}/auth/github/callback"
        return await oauth.github.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f"GitHub login redirect error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_init_failed&details={str(e)}")


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
from sqlalchemy.orm import Session
from fastapi import Depends, status
from ..database import get_db
from ..models import User
from ..auth.security import get_password_hash, verify_password

# --- Standard Auth (Email/Password) ---

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-login after register
    user_data = {
        "email": new_user.email,
        "name": new_user.full_name,
        "provider": "email"
    }
    token = create_access_token(user_data)
    return {"token": token, "user": user_data}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_data = {
        "email": db_user.email,
        "name": db_user.full_name,
        "provider": "email"
    }
    token = create_access_token(user_data)
    return {"token": token, "user": user_data}
