from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    github_id = Column(String, unique=True, index=True, nullable=True)
    github_access_token = Column(String, nullable=True)
    is_github_user = Column(Boolean, default=False, nullable=False)
    