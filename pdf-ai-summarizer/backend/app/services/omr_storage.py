import datetime
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.omr_database import (
    delete_sheet_record,
    find_sheet_usages,
    get_sheet,
    list_sheets,
    save_sheet_record,
)
from app.schemas.omr import OmrSheetResponse
from app.services.omr_align_service import align_image

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
EXT_TO_CONTENT_TYPE = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _row_to_response(row) -> OmrSheetResponse:
    return OmrSheetResponse(
        id=row["id"],
        label=row["label"],
        original_filename=row["original_filename"],
        content_type=row["content_type"],
        uploaded_at=row["uploaded_at"],
    )


async def save_omr_sheet(file: UploadFile, label: str, user_id: str) -> OmrSheetResponse:
    original_filename = file.filename or ""
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Chi nhan file anh (jpg, jpeg, png)")

    file_bytes = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=400, detail="File is too large")

    sheet_id = str(uuid4())
    stored_filename = f"{sheet_id}.{ext}"

    upload_dir = Path(settings.omr_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / stored_filename).write_bytes(file_bytes)

    content_type = EXT_TO_CONTENT_TYPE[ext]
    uploaded_at = datetime.datetime.now().isoformat()
    display_label = label.strip() or original_filename

    await save_sheet_record(
        sheet_id=sheet_id,
        user_id=user_id,
        label=display_label,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        uploaded_at=uploaded_at,
    )

    return OmrSheetResponse(
        id=sheet_id,
        label=display_label,
        original_filename=original_filename,
        content_type=content_type,
        uploaded_at=uploaded_at,
    )


async def list_omr_sheets(user_id: str) -> list[OmrSheetResponse]:
    rows = await list_sheets(user_id)
    return [_row_to_response(row) for row in rows]


async def get_omr_sheet_file(sheet_id: str, user_id: str) -> tuple[bytes, str]:
    row = await get_sheet(sheet_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sheet not found")

    file_path = Path(settings.omr_upload_dir) / row["stored_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sheet not found")

    return file_path.read_bytes(), row["content_type"]


async def delete_omr_sheet(sheet_id: str, user_id: str) -> None:
    row = await get_sheet(sheet_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sheet not found")

    template_names, answer_key_names = await find_sheet_usages(sheet_id)
    if template_names or answer_key_names:
        parts = []
        if template_names:
            parts.append(f"mau: {', '.join(template_names)}")
        if answer_key_names:
            parts.append(f"dap an: {', '.join(answer_key_names)}")
        raise HTTPException(
            status_code=400,
            detail=f"Khong the xoa - phieu nay dang duoc dung lam anh goc cho {'; '.join(parts)}",
        )

    file_path = Path(settings.omr_upload_dir) / row["stored_filename"]
    file_path.unlink(missing_ok=True)
    await delete_sheet_record(sheet_id)


async def get_omr_sheet_aligned_bytes(sheet_id: str, user_id: str) -> tuple[bytes, bool]:
    # Anh da duoc nan thang theo 4 dau goc den (hoac giu nguyen neu khong tim
    # du 4 dau goc) - dung LAM CHUAN cho ca man hinh khoanh vung mau lan buoc
    # detect that, de 2 ben luon cung 1 he toa do %, khong bi lech nhau.
    file_bytes, _ = await get_omr_sheet_file(sheet_id, user_id)
    array = np.frombuffer(file_bytes, dtype=np.uint8)
    color = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if color is None:
        raise HTTPException(status_code=400, detail="Khong doc duoc anh phieu")

    aligned, was_aligned = align_image(color)
    success, buffer = cv2.imencode(".png", aligned)
    if not success:
        raise HTTPException(status_code=500, detail="Khong tao duoc anh da nan")
    return buffer.tobytes(), was_aligned
