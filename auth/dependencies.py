from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
import os



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        return payload  # { "sub": "admin", "role": "admin" }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

def get_admin_user(token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only for Admin!")
    return user