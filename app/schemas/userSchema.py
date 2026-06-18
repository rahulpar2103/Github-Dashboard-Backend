from pydantic import BaseModel

class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str

class UserRegisterResponse(BaseModel):
    id: int
    username: str
    email: str

class UserLoginResponse(BaseModel):
    id: int
    username: str
    email: str
    access_token: str
    token_type: str

class Token(BaseModel):
    access_token: str
    token_type: str