from bcrypt import hashpw, checkpw, gensalt
import jwt
import time

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)  


def hash_password(password: str) -> str:
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password) -> bool:
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")
    return checkpw(plain_password.encode("utf-8"), hashed_password)

def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": time.time() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_jwt_token(token)