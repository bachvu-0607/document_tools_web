import datetime
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Header, HTTPException, Query

from app.core.auth_database import create_user_record, get_user_by_id, get_user_by_username
from app.core.config import settings
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str, username: str) -> str:
    expire_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.jwt_expire_minutes,
    )
    payload = {"sub": user_id, "username": username, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


async def create_user(username: str, password: str, display_name: str) -> UserInfo:
    username = username.strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="Thieu username hoac mat khau")
    if await get_user_by_username(username) is not None:
        raise HTTPException(status_code=400, detail="Username da ton tai")

    user_id = str(uuid4())
    await create_user_record(
        user_id=user_id,
        username=username,
        password_hash=hash_password(password),
        display_name=display_name.strip() or username,
        created_at=datetime.datetime.now().isoformat(),
    )
    return UserInfo(id=user_id, username=username, display_name=display_name.strip() or username)


async def login(request: LoginRequest) -> LoginResponse:
    row = await get_user_by_username(request.username.strip())
    # Cau tra loi giong het nhau du sai username hay sai mat khau - tranh lo
    # cho ke tan cong biet duoc username nao co that trong he thong.
    if row is None or not verify_password(request.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai ten dang nhap hoac mat khau")

    token = create_access_token(row["id"], row["username"])
    return LoginResponse(
        access_token=token,
        user=UserInfo(id=row["id"], username=row["username"], display_name=row["display_name"]),
    )


async def _resolve_user_from_token(token: str | None) -> UserInfo:
    if not token:
        raise HTTPException(status_code=401, detail="Chua dang nhap")

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Phien dang nhap da het han, dang nhap lai")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token khong hop le")

    row = await get_user_by_id(payload.get("sub", ""))
    if row is None:
        raise HTTPException(status_code=401, detail="Tai khoan khong ton tai")

    return UserInfo(id=row["id"], username=row["username"], display_name=row["display_name"])


async def get_current_user(authorization: str | None = Header(default=None)) -> UserInfo:
    # Dung lam FastAPI dependency (Depends(get_current_user)) o moi route can
    # dang nhap - doc token tu header "Authorization: Bearer <token>" (khong
    # dung cookie, xem giai thich JWT vs cookie da trao doi). Dung cho moi
    # route goi qua fetch() - noi code JS chu dong gan duoc header.
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Chua dang nhap")
    return await _resolve_user_from_token(authorization.removeprefix("Bearer ").strip())


async def get_current_user_flexible(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> UserInfo:
    # Bien the danh rieng cho cac endpoint tra ve ANH duoc nhung thang vao the
    # <img src=...> - trinh duyet tu tai anh do, KHONG the gan header
    # Authorization vao request do duoc (chi JS goi fetch() moi gan header
    # duoc). Nen cho phep gui token qua query string (?token=...) thay the -
    # van uu tien header truoc neu co (truong hop test bang curl/Postman).
    if authorization and authorization.startswith("Bearer "):
        return await _resolve_user_from_token(authorization.removeprefix("Bearer ").strip())
    return await _resolve_user_from_token(token)
