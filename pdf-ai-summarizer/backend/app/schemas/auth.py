from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: str
    username: str
    display_name: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
