import datetime
import io
from uuid import uuid4

from fastapi import HTTPException
from openpyxl import Workbook
from openpyxl.styles import Font

from app.core.omr_database import (
    delete_graded_result_record,
    get_graded_result,
    get_graded_result_by_sheet_and_key,
    list_graded_results,
    save_graded_result_record,
)
from app.schemas.omr import OmrGradedResultResponse, OmrGradedResultSaveRequest
from app.services.omr.omr_answer_key_service import get_omr_answer_key
from app.services.omr.omr_grade_service import grade_sheet


def _row_to_response(row) -> OmrGradedResultResponse:
    return OmrGradedResultResponse(
        id=row["id"],
        class_name=row["class_name"],
        sheet_id=row["sheet_id"],
        sheet_label=row["sheet_label"],
        answer_key_id=row["answer_key_id"],
        answer_key_name=row["answer_key_name"],
        sbd=row["sbd"],
        made=row["made"],
        correct_count=row["correct_count"],
        wrong_count=row["wrong_count"],
        blank_count=row["blank_count"],
        ambiguous_count=row["ambiguous_count"],
        score_10=row["score_10"],
        aligned=bool(row["aligned"]),
        saved_at=row["saved_at"],
    )


async def save_graded_results(request: OmrGradedResultSaveRequest, user_id: str) -> list[OmrGradedResultResponse]:
    class_name = request.class_name.strip()
    if not class_name:
        raise HTTPException(status_code=400, detail="Ten lop khong duoc de trong")
    if not request.sheet_ids:
        raise HTTPException(status_code=400, detail="Chua co phieu nao de luu")

    answer_key = await get_omr_answer_key(request.answer_key_id, user_id)
    saved_at = datetime.datetime.now().isoformat()

    responses: list[OmrGradedResultResponse] = []
    for sheet_id in request.sheet_ids:
        # Tinh lai diem tu server (khong tin so lieu tu client) - dam bao ban
        # luu luon la ban moi nhat, khop voi du lieu detection hien co.
        grade = await grade_sheet(answer_key, sheet_id, user_id)
        await save_graded_result_record(
            result_id=str(uuid4()),
            user_id=user_id,
            class_name=class_name,
            sheet_id=grade.sheet_id,
            sheet_label=grade.sheet_label,
            answer_key_id=answer_key.id,
            answer_key_name=answer_key.name,
            sbd=grade.sbd,
            made=grade.made,
            correct_count=grade.correct_count,
            wrong_count=grade.wrong_count,
            blank_count=grade.blank_count,
            ambiguous_count=grade.ambiguous_count,
            score_10=grade.score_10,
            aligned=grade.aligned,
            saved_at=saved_at,
        )
        row = await get_graded_result_by_sheet_and_key(sheet_id, answer_key.id, user_id)
        if row is not None:
            responses.append(_row_to_response(row))

    return responses


async def list_omr_graded_results(user_id: str) -> list[OmrGradedResultResponse]:
    rows = await list_graded_results(user_id)
    return [_row_to_response(row) for row in rows]


async def delete_omr_graded_result(result_id: str, user_id: str) -> None:
    if await get_graded_result(result_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Result not found")
    await delete_graded_result_record(result_id)


EXCEL_HEADERS = [
    "STT", "Lớp", "SBD", "Mã đề", "Tên phiếu", "Điểm",
    "Đúng", "Sai", "Bỏ trống", "Lưu lúc",
]


async def export_graded_results_excel(result_ids: list[str], user_id: str) -> bytes:
    if not result_ids:
        raise HTTPException(status_code=400, detail="Chua chon ket qua nao de xuat")

    rows = []
    for result_id in result_ids:
        row = await get_graded_result(result_id, user_id)
        if row is not None:
            rows.append(row)
    if not rows:
        raise HTTPException(status_code=404, detail="Khong tim thay ket qua nao trong so da chon")

    # Sap theo lop roi SBD cho de doi chieu, giong thu tu hien thi ngoai UI.
    rows.sort(key=lambda r: (r["class_name"], r["sbd"]))

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Bang diem"
    sheet.append(EXCEL_HEADERS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for index, row in enumerate(rows, start=1):
        sheet.append([
            index,
            row["class_name"],
            row["sbd"],
            row["made"],
            row["sheet_label"],
            row["score_10"],
            row["correct_count"],
            row["wrong_count"],
            row["blank_count"],
            row["saved_at"],
        ])

    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 10), 40)

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
