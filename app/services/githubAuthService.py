import secrets
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import create_jwt_token, hash_password
from app.models.userModel import User

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


class GithubAuthService:
    async def build_authorize_url(self) -> str:
        state = secrets.token_urlsafe(16)
        await redis_client.set(f"oauth:state:{state}", "1", ex=300)
        params = (
            f"client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_OAUTH_REDIRECT_URI}"
            f"&scope=repo"
            f"&state={state}"
        )
        return f"{GITHUB_AUTHORIZE_URL}?{params}"

    async def verify_state(self, state: str) -> None:
        key = f"oauth:state:{state}"
        exists = await redis_client.get(key)
        if not exists:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        await redis_client.delete(key)

    async def exchange_code_for_token(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
                },
            )
        data = resp.json()
        if "access_token" not in data:
            raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {data}")
        return data["access_token"]

    async def fetch_github_user(self, github_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GITHUB_USER_URL,
                headers={"Authorization": f"token {github_token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")
        return resp.json()

    def upsert_user(self, db: Session, github_user: dict, github_token: str) -> User:
        github_id = str(github_user["id"])
        user = db.query(User).filter(User.github_id == github_id).first()
        if user is None:
            # Generate a secure random password for GitHub OAuth users
            random_plain_password = secrets.token_urlsafe(32)
            user = User(
                github_id=github_id,
                username=github_user.get("login"),
                email=github_user.get("email") or f"{github_id}@users.noreply.github.com",
                password=hash_password(random_plain_password),
                is_github_user=True
            )
            db.add(user)
        user.github_access_token = github_token
        db.commit()
        db.refresh(user)
        return user

    def issue_jwt(self, user: User) -> str:
        return create_jwt_token(data={"sub": str(user.id), "username": user.username})


github_auth_service = GithubAuthService()
