from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import logging

logger = logging.getLogger(__name__)

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    
    try:
        decoded_token = id_token.verify_firebase_token(
            token, 
            google_requests.Request(), 
            audience=FIREBASE_PROJECT_ID
        )
        
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: missing email")
            
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                full_name=decoded_token.get("name", email.split('@')[0]),
                is_active=True,
                last_analysis_date="",
                daily_analysis_count=0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        return user
        
    except ValueError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")
