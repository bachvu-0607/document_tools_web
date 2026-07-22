import datetime
import json
from uuid import uuid4

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


def _row_to_response(row) -> OmrTemplateResponse:
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
    )


async def create_omr_template(request: OmrTemplateCreateRequest, user_id: str) -> OmrTemplateResponse:
    # get_sheet da tu loc theo user_id - phieu cua nguoi khac se coi nhu
    # "khong ton tai" o day, khong the tao mau tro toi anh khong phai cua minh.
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
    )

    row = await get_template(template_id, user_id)
    return _row_to_response(row)


async def list_omr_templates(user_id: str) -> list[OmrTemplateResponse]:
    rows = await list_templates(user_id)
    return [_row_to_response(row) for row in rows]


async def get_omr_template(template_id: str, user_id: str) -> OmrTemplateResponse:
    row = await get_template(template_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return _row_to_response(row)


async def delete_omr_template(template_id: str, user_id: str) -> None:
    if await get_template(template_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Template not found")

    usages = await find_template_usages(template_id)
    if usages:
        raise HTTPException(
            status_code=400,
            detail=f"Khong the xoa - mau nay dang duoc dung boi dap an: {', '.join(usages)}",
        )

    await delete_template_record(template_id)
