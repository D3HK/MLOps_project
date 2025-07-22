from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import os
from src.database.database import get_db
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    try:
        expires_delta = timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        expires = datetime.now(timezone.utc) + expires_delta
        
        data.update({"exp": expires})
        
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY not set in environment variables")
            
        algorithm = os.getenv("ALGORITHM", "HS256")
        
        return jwt.encode(data, secret_key, algorithm=algorithm)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token creation failed: {str(e)}"
        )

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        return dict(user) if user else None
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        db.close()