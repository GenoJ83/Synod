from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        # Verify the Firebase ID token
        decoded_token = id_token.verify_firebase_token(
            token, 
            google_requests.Request(), 
            audience=FIREBASE_PROJECT_ID
        )
        
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: missing email")
            
        # Check if user exists in local DB, if not, create them (sync)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name=decoded_token.get("name", email.split('@')[0]),
                # No shadow password - Firebase handles auth
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        return user
        
    except ValueError as e:
        # Token is invalid or expired
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
