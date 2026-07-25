import datetime
import json
from uuid import uuid4

import cv2
import numpy as np
from fastapi import HTTPException

from app.core.omr_database import (
    delete_template_record,
    find_template_usages,
    get_sheet,
    get_template,
    list_templates,
    save_template_record,
)
from app.schemas.omr import AnswerBlock, OmrTemplateCreateRequest, OmrTemplateResponse, ZoneRect
from app.services.omr.omr_align_service import align_image, decode_image_exif_aware, detect_all_markers_normalized
from app.services.omr.omr_storage import get_omr_sheet_file

MAX_ANSWER_BLOCKS = 3


def _validate_zone(zone: ZoneRect, field_name: str) -> None:
    if not (0 <= zone.x0 < zone.x1 <= 1 and 0 <= zone.y0 < zone.y1 <= 1):
        raise HTTPException(status_code=400, detail=f"Khung {field_name} khong hop le")


def _validate_answer_blocks(blocks: list[AnswerBlock]) -> None:
    if not (1 <= len(blocks) <= MAX_ANSWER_BLOCKS):
        raise HTTPException(
            status_code=400,
            detail=f"Vung cau hoi phai co tu 1 den {MAX_ANSWER_BLOCKS} khoi",
        )
    for index, block in enumerate(blocks, start=1):
        _validate_zone(block.zone, f"cau hoi - khoi {index}")
        if block.num_questions < 1:
            raise HTTPException(status_code=400, detail=f"Khoi {index}: so cau phai >= 1")
        if block.num_columns < 1 or block.num_questions % block.num_columns != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Khoi {index}: so cau phai chia het cho so cot",
            )


def _row_to_response(row, user_id: str) -> OmrTemplateResponse:
    return OmrTemplateResponse(
        id=row["id"],
        name=row["name"],
        reference_sheet_id=row["reference_sheet_id"],
        sbd_zone=ZoneRect.model_validate_json(row["sbd_zone"]),
        sbd_digits=row["sbd_digits"],
        made_zone=ZoneRect.model_validate_json(row["made_zone"]),
        made_digits=row["made_digits"],
        answer_blocks=[AnswerBlock.model_validate(item) for item in json.loads(row["answer_blocks"])],
        num_choices=row["num_choices"],
        created_at=row["created_at"],
        is_owner=row["user_id"] == user_id,
    )


async def _capture_marker_layout(sheet_id: str, user_id: str) -> str:
    # Chup lai "ban do" toan bo dau moc (o vuong den) tren anh mau, luu theo
    # toa do % - dung sau nay de nan tinh chinh cho tung anh phieu hoc sinh
    # (xem align_image_with_template). That bai o day KHONG chan viec tao mau
    # (tra ve rong "[]"), chi la mau do se tu dong dung lai cach nan tho 4 goc
    # cu thay vi duoc tinh chinh - khong nghiem trong bang loi tao mau.
    try:
        file_bytes, _ = await get_omr_sheet_file(sheet_id, user_id)
        color = decode_image_exif_aware(file_bytes)
        if color is None:
            return json.dumps([])
        aligned, was_aligned = align_image(color)
        if not was_aligned:
            return json.dumps([])
        return json.dumps(detect_all_markers_normalized(aligned))
    except Exception:
        return json.dumps([])


async def create_omr_template(request: OmrTemplateCreateRequest, user_id: str) -> OmrTemplateResponse:
    # Van bat buoc anh mau phai la anh CUA CHINH MINH thi moi tao template
    # duoc (get_sheet loc nghiem theo user_id) - dung chung chi ap dung SAU
    # khi template da tao xong, khong ai tao duoc template tu anh nguoi khac.
    if await get_sheet(request.reference_sheet_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Reference sheet not found")

    _validate_zone(request.sbd_zone, "SBD")
    _validate_zone(request.made_zone, "Ma de")
    _validate_answer_blocks(request.answer_blocks)

    if request.sbd_digits < 1:
        raise HTTPException(status_code=400, detail="So chu so SBD phai >= 1")
    if request.made_digits < 1:
        raise HTTPException(status_code=400, detail="So chu so Ma de phai >= 1")
    if request.num_choices < 2:
        raise HTTPException(status_code=400, detail="So lua chon/cau khong hop le")

    template_id = str(uuid4())
    created_at = datetime.datetime.now().isoformat()
    marker_layout = await _capture_marker_layout(request.reference_sheet_id, user_id)

    await save_template_record(
        template_id=template_id,
        user_id=user_id,
        name=request.name.strip() or "Mau phieu chua dat ten",
        reference_sheet_id=request.reference_sheet_id,
        sbd_zone=request.sbd_zone.model_dump_json(),
        sbd_digits=request.sbd_digits,
        made_zone=request.made_zone.model_dump_json(),
        made_digits=request.made_digits,
        answer_blocks=json.dumps([block.model_dump() for block in request.answer_blocks]),
        num_choices=request.num_choices,
        created_at=created_at,
        marker_layout=marker_layout,
    )

    row = await get_template(template_id)
    return _row_to_response(row, user_id)


async def list_omr_templates(user_id: str) -> list[OmrTemplateResponse]:
    # Mau phieu dung chung ca nhom - tra ve CUA MOI NGUOI, khong chi cua
    # user_id nay (user_id chi dung de tinh is_owner cho tung dong).
    rows = await list_templates()
    return [_row_to_response(row, user_id) for row in rows]


async def get_omr_template(template_id: str, user_id: str) -> OmrTemplateResponse:
    row = await get_template(template_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return _row_to_response(row, user_id)


async def delete_omr_template(template_id: str, user_id: str) -> None:
    row = await get_template(template_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Chi nguoi tao mau nay moi xoa duoc")

    usages = await find_template_usages(template_id)
    if usages:
        raise HTTPException(
            status_code=400,
            detail=f"Khong the xoa - mau nay dang duoc dung boi dap an: {', '.join(usages)}",
        )

    await delete_template_record(template_id)
