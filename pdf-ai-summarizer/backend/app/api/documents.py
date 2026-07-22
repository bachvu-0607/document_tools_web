from fastapi import APIRouter, Depends, File, Response, UploadFile

from app.schemas.auth import UserInfo
from app.schemas.document import DocumentUploadResponse
from app.schemas.document import DocumentTextPreviewResponse
from app.schemas.document import DocxAiConvertRequest
from app.schemas.document import MergePdfRequest
from app.services.auth_service import get_current_user
from app.services.file_storage import save_upload_file
from app.services.pdf_reader import get_pdf_text_preview
from app.services.docx_export_service import (
    convert_pdf_to_docx_ai,
    convert_pdf_to_docx_mechanical,
)
from app.services.pdf_tools_service import (
    compress_pdf,
    export_page_images_zip,
    merge_pdfs,
)
from app.services.financial_extract_service import (
    export_pdf_by_template_to_excel,
    export_pdf_tables_to_excel,
)

router = APIRouter(tags=["documents"])

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...), current_user: UserInfo = Depends(get_current_user),
) -> DocumentUploadResponse:
    return await save_upload_file(file)

@router.get("/documents/{document_id}/text-preview", response_model=DocumentTextPreviewResponse)
def read_document_text_preview(
    document_id: str, current_user: UserInfo = Depends(get_current_user),
) -> DocumentTextPreviewResponse:
    return get_pdf_text_preview(document_id)

@router.post("/documents/{document_id}/convert-docx")
def convert_document_to_docx(
    document_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    docx_bytes = convert_pdf_to_docx_mechanical(document_id)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="chuyen-doi.docx"'},
    )

@router.post("/documents/{document_id}/convert-docx-ai")
def convert_document_to_docx_ai(
    document_id: str, request: DocxAiConvertRequest, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    docx_bytes = convert_pdf_to_docx_ai(document_id, request.extraction_mode)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="chuyen-doi-ai.docx"'},
    )

@router.post("/documents/{document_id}/convert-excel")
def convert_document_to_excel(
    document_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    excel_bytes = export_pdf_tables_to_excel(document_id=document_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="chuyen-doi-bctc.xlsx"'},
    )

@router.post("/documents/{document_id}/convert-excel-template")
def convert_document_to_excel_template(
    document_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    excel_bytes = export_pdf_by_template_to_excel(document_id=document_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="bctc-theo-mau.xlsx"'},
    )

@router.post("/documents/{document_id}/export-images")
def export_document_page_images(
    document_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    zip_bytes = export_page_images_zip(document_id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="cac-trang-pdf.zip"'},
    )

@router.post("/documents/merge")
def merge_documents(
    request: MergePdfRequest, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    merged_bytes = merge_pdfs(request.document_ids)
    return Response(
        content=merged_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="gop-file.pdf"'},
    )

@router.post("/documents/{document_id}/compress")
def compress_document(
    document_id: str, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    compressed_bytes = compress_pdf(document_id)
    return Response(
        content=compressed_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="nen-file.pdf"'},
    )
