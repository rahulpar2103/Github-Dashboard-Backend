from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.userSchema import UserRegisterRequest, UserRegisterResponse, Token
from app.dependencies.db import get_db
from sqlalchemy.orm import Session
from app.services.authService import authService

router=APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/register", response_model=UserRegisterResponse)
def register(user: UserRegisterRequest, db: Session = Depends(get_db)) -> dict:
    return authService.register(user, db)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return authService.login(form_data.username, form_data.password, db)