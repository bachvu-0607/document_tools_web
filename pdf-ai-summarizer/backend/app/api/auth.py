from fastapi import APIRouter, Depends

from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import get_current_user, login

router = APIRouter(tags=["auth"])

@router.post("/auth/login", response_model=LoginResponse)
async def login_endpoint(request: LoginRequest) -> LoginResponse:
    return await login(request)

@router.get("/auth/me", response_model=UserInfo)
async def get_me_endpoint(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    return current_user
