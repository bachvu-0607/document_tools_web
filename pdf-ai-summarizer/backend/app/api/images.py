from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.schemas.auth import UserInfo
from app.services.auth_service import get_current_user
from app.services.image_tools_service import convert_image

router = APIRouter(tags=["images"])

@router.post("/images/convert")
async def convert_image_endpoint(
    file: UploadFile = File(...),
    target_format: str = Form("same"),
    quality: int = Form(85),
    current_user: UserInfo = Depends(get_current_user),
) -> Response:
    contents = await file.read()
    original_ext = (file.filename or "").rsplit(".", 1)[-1] if file.filename else "png"

    converted_bytes, out_ext = convert_image(
        file_bytes=contents,
        original_ext=original_ext,
        target_format=target_format,
        quality=quality,
    )

    media_type = "image/jpeg" if out_ext == "jpg" else f"image/{out_ext}"
    return Response(
        content=converted_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="anh-da-xu-ly.{out_ext}"'},
    )
