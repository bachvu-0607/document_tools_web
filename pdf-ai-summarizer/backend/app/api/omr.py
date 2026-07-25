from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.schemas.auth import UserInfo
from app.schemas.omr import (
    OmrAlignCheckResponse,
    OmrAnswerKeyCreateRequest,
    OmrAnswerKeyResponse,
    OmrDetectionOverrideRequest,
    OmrDetectionResponse,
    OmrGradeBatchRequest,
    OmrGradeBatchResponse,
    OmrGradedResultResponse,
    OmrGradedResultSaveRequest,
    OmrResultsExportRequest,
    OmrSheetResponse,
    OmrTemplateCreateRequest,
    OmrTemplateResponse,
)
from app.services.auth_service import get_current_user, get_current_user_flexible
from app.services.omr.omr_align_service import check_alignment_bytes
from app.services.omr.omr_answer_key_service import (
    create_answer_key,
    delete_omr_answer_key,
    get_omr_answer_key,
    list_omr_answer_keys,
)
from app.services.omr.omr_detect_service import (
    get_saved_detection,
    override_detection,
    render_preview_image,
    run_detection,
)
from app.services.omr.omr_grade_service import grade_sheets_batch
from app.services.omr.omr_results_service import (
    delete_omr_graded_result,
    export_graded_results_excel,
    list_omr_graded_results,
    save_graded_results,
)
from app.services.omr.omr_storage import (
    delete_omr_sheet,
    get_omr_sheet_aligned_bytes,
    get_omr_sheet_file,
    list_omr_sheets,
    save_omr_sheet,
)
from app.services.omr.omr_template_service import (
    create_omr_template,
    delete_omr_template,
    get_omr_template,
    list_omr_templates,
)

router = APIRouter(tags=["omr"])

@router.post("/omr/sheets/upload", response_model=OmrSheetResponse)
async def upload_omr_sheet(
    file: UploadFile = File(...),
    label: str = Form(""),
    current_user: UserInfo = Depends(get_current_user),
) -> OmrSheetResponse:
    return await save_omr_sheet(file, label, current_user.id)

@router.post("/omr/align-check", response_model=OmrAlignCheckResponse)
async def check_omr_align_endpoint(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user),
) -> OmrAlignCheckResponse:
    # Dung cho tinh nang camera truc tiep - kiem tra nhe (khong luu gi) xem 1
    # khung hinh tam co du 4 dau goc den khong, de bao cho nguoi dung biet da
    # canh may khop giay chua truoc khi tu dong chup that. Van bat buoc dang
    # nhap de tranh nguoi la spam xu ly anh (ton CPU) mien phi.
    contents = await file.read()
    return OmrAlignCheckResponse(found=check_alignment_bytes(contents))

@router.get("/omr/sheets", response_model=list[OmrSheetResponse])
async def get_omr_sheets(current_user: UserInfo = Depends(get_current_user)) -> list[OmrSheetResponse]:
    return await list_omr_sheets(current_user.id)

@router.get("/omr/sheets/{sheet_id}/file")
async def get_omr_sheet_file_endpoint(
    sheet_id: str, current_user: UserInfo = Depends(get_current_user_flexible),
) -> Response:
    file_bytes, content_type = await get_omr_sheet_file(sheet_id, current_user.id)
    return Response(content=file_bytes, media_type=content_type)

@router.delete("/omr/sheets/{sheet_id}")
async def delete_omr_sheet_endpoint(
    sheet_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    await delete_omr_sheet(sheet_id, current_user.id)
    return Response(status_code=204)

@router.get("/omr/sheets/{sheet_id}/aligned")
async def get_omr_sheet_aligned_endpoint(
    sheet_id: str, current_user: UserInfo = Depends(get_current_user_flexible),
) -> Response:
    image_bytes, was_aligned = await get_omr_sheet_aligned_bytes(sheet_id, current_user.id)
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"X-Omr-Aligned": "true" if was_aligned else "false"},
    )

@router.post("/omr/templates", response_model=OmrTemplateResponse)
async def create_omr_template_endpoint(
    request: OmrTemplateCreateRequest, current_user: UserInfo = Depends(get_current_user),
) -> OmrTemplateResponse:
    return await create_omr_template(request, current_user.id)

@router.get("/omr/templates", response_model=list[OmrTemplateResponse])
async def get_omr_templates(current_user: UserInfo = Depends(get_current_user)) -> list[OmrTemplateResponse]:
    return await list_omr_templates(current_user.id)

@router.get("/omr/templates/{template_id}", response_model=OmrTemplateResponse)
async def get_omr_template_endpoint(
    template_id: str, current_user: UserInfo = Depends(get_current_user),
) -> OmrTemplateResponse:
    return await get_omr_template(template_id, current_user.id)

@router.delete("/omr/templates/{template_id}")
async def delete_omr_template_endpoint(
    template_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    await delete_omr_template(template_id, current_user.id)
    return Response(status_code=204)

@router.post("/omr/templates/{template_id}/detect", response_model=OmrDetectionResponse)
async def detect_omr_sheet_endpoint(
    template_id: str, sheet_id: str, current_user: UserInfo = Depends(get_current_user),
) -> OmrDetectionResponse:
    return await run_detection(template_id, sheet_id, current_user.id)

@router.get("/omr/detections/{sheet_id}", response_model=OmrDetectionResponse)
async def get_omr_detection_endpoint(
    sheet_id: str, current_user: UserInfo = Depends(get_current_user),
) -> OmrDetectionResponse:
    return await get_saved_detection(sheet_id, current_user.id)

@router.get("/omr/sheets/{sheet_id}/preview")
async def get_omr_sheet_preview_endpoint(
    sheet_id: str, template_id: str, current_user: UserInfo = Depends(get_current_user_flexible),
) -> Response:
    image_bytes = await render_preview_image(template_id, sheet_id, current_user.id)
    return Response(content=image_bytes, media_type="image/png")

@router.put("/omr/detections/{sheet_id}", response_model=OmrDetectionResponse)
async def override_omr_detection_endpoint(
    sheet_id: str,
    template_id: str,
    request: OmrDetectionOverrideRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> OmrDetectionResponse:
    return await override_detection(
        sheet_id, template_id, request.sbd, request.made, request.answers, current_user.id,
    )

@router.post("/omr/answer-keys", response_model=OmrAnswerKeyResponse)
async def create_omr_answer_key_endpoint(
    request: OmrAnswerKeyCreateRequest, current_user: UserInfo = Depends(get_current_user),
) -> OmrAnswerKeyResponse:
    return await create_answer_key(request, current_user.id)

@router.get("/omr/answer-keys", response_model=list[OmrAnswerKeyResponse])
async def get_omr_answer_keys_endpoint(
    current_user: UserInfo = Depends(get_current_user),
) -> list[OmrAnswerKeyResponse]:
    return await list_omr_answer_keys(current_user.id)

@router.get("/omr/answer-keys/{answer_key_id}", response_model=OmrAnswerKeyResponse)
async def get_omr_answer_key_endpoint(
    answer_key_id: str, current_user: UserInfo = Depends(get_current_user),
) -> OmrAnswerKeyResponse:
    return await get_omr_answer_key(answer_key_id, current_user.id)

@router.delete("/omr/answer-keys/{answer_key_id}")
async def delete_omr_answer_key_endpoint(
    answer_key_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    await delete_omr_answer_key(answer_key_id, current_user.id)
    return Response(status_code=204)

@router.post("/omr/answer-keys/{answer_key_id}/grade-batch", response_model=OmrGradeBatchResponse)
async def grade_omr_batch_endpoint(
    answer_key_id: str,
    request: OmrGradeBatchRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> OmrGradeBatchResponse:
    return await grade_sheets_batch(answer_key_id, request.sheet_ids, current_user.id)

@router.post("/omr/results", response_model=list[OmrGradedResultResponse])
async def save_omr_results_endpoint(
    request: OmrGradedResultSaveRequest, current_user: UserInfo = Depends(get_current_user),
) -> list[OmrGradedResultResponse]:
    return await save_graded_results(request, current_user.id)

@router.get("/omr/results", response_model=list[OmrGradedResultResponse])
async def get_omr_results_endpoint(
    current_user: UserInfo = Depends(get_current_user),
) -> list[OmrGradedResultResponse]:
    return await list_omr_graded_results(current_user.id)

@router.delete("/omr/results/{result_id}")
async def delete_omr_result_endpoint(
    result_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    await delete_omr_graded_result(result_id, current_user.id)
    return Response(status_code=204)

@router.post("/omr/results/export-excel")
async def export_omr_results_endpoint(
    request: OmrResultsExportRequest, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    excel_bytes = await export_graded_results_excel(request.result_ids, current_user.id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="bang-diem.xlsx"'},
    )
