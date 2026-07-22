import datetime
import json
from uuid import uuid4

from fastapi import HTTPException

from app.core.omr_database import (
    delete_answer_key_record,
    get_answer_key,
    list_answer_keys,
    save_answer_key_record,
)
from app.schemas.omr import OmrAnswerKeyCreateRequest, OmrAnswerKeyResponse
from app.services.omr_template_service import get_omr_template


def _row_to_response(row) -> OmrAnswerKeyResponse:
    return OmrAnswerKeyResponse(
        id=row["id"],
        name=row["name"],
        template_id=row["template_id"],
        source_sheet_id=row["source_sheet_id"],
        sbd=row["sbd"],
        made=row["made"],
        answers=json.loads(row["answers"]),
        created_at=row["created_at"],
    )


async def create_answer_key(request: OmrAnswerKeyCreateRequest) -> OmrAnswerKeyResponse:
    template = await get_omr_template(request.template_id)
    total_questions = sum(block.num_questions for block in template.answer_blocks)
    if len(request.answers) != total_questions:
        raise HTTPException(
            status_code=400,
            detail=f"So dap an ({len(request.answers)}) khong khop so cau cua mau ({total_questions})",
        )

    answer_key_id = str(uuid4())
    created_at = datetime.datetime.now().isoformat()

    await save_answer_key_record(
        answer_key_id=answer_key_id,
        name=request.name.strip() or "Dap an chua dat ten",
        template_id=request.template_id,
        source_sheet_id=request.source_sheet_id,
        sbd=request.sbd,
        made=request.made,
        answers=json.dumps(request.answers),
        created_at=created_at,
    )

    row = await get_answer_key(answer_key_id)
    return _row_to_response(row)


async def list_omr_answer_keys() -> list[OmrAnswerKeyResponse]:
    rows = await list_answer_keys()
    return [_row_to_response(row) for row in rows]


async def get_omr_answer_key(answer_key_id: str) -> OmrAnswerKeyResponse:
    row = await get_answer_key(answer_key_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Answer key not found")
    return _row_to_response(row)


async def delete_omr_answer_key(answer_key_id: str) -> None:
    if await get_answer_key(answer_key_id) is None:
        raise HTTPException(status_code=404, detail="Answer key not found")
    await delete_answer_key_record(answer_key_id)
