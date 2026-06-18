from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from app.schemas.userSchema import UserRegisterRequest, UserRegisterResponse, Token
from app.dependencies.db import get_db
from sqlalchemy.orm import Session
from app.services.authService import authService
from app.services.githubAuthService import github_auth_service

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


@router.get("/github/login")
async def github_login():
    url = await github_auth_service.build_authorize_url()
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    await github_auth_service.verify_state(state)
    github_token = await github_auth_service.exchange_code_for_token(code)
    github_user = await github_auth_service.fetch_github_user(github_token)
    user = github_auth_service.upsert_user(db, github_user, github_token)
    access_token = github_auth_service.issue_jwt(user)
    return {"access_token": access_token, "token_type": "bearer"}