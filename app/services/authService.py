from app.models.userModel import User
from app.schemas.userSchema import UserRegisterRequest
from app.core.security import hash_password, verify_password, create_jwt_token
from fastapi import HTTPException
from sqlalchemy.orm import Session

class AuthService:
    def register(self, user: UserRegisterRequest, db: Session):
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        new_user = User(
            username=user.username,
            password=hash_password(user.password),
            email=user.email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "username": new_user.username, "email": new_user.email}

    def login(self, username: str, password: str, db: Session):
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(password, existing_user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_jwt_token(
            data={"sub": str(existing_user.id)}
        )
        return {"access_token": access_token, "token_type": "bearer"}

authService = AuthService()