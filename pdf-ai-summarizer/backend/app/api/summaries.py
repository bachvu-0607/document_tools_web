from fastapi import APIRouter, HTTPException, Response
from pathlib import Path
from app.core.database import get_latest_summary
from app.schemas.summary import SummaryRequest, SummaryResponse, PdfExportRequest
from app.services.summary_service import create_summary
from app.services.pdf_export_service import create_summary_pdf
router = APIRouter(tags= ["summaries"])

@router.post("/summaries", response_model=SummaryResponse)
async def send_summary_request(request: SummaryRequest) -> SummaryResponse:
    return await create_summary(request=request)

@router.post("/summaries/export-pdf")
async def send_pdf_export_request(request: PdfExportRequest) -> Response:
    record = await get_latest_summary(request.document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Chua co ban tom tat cho document nay")

    pdf_bytes = create_summary_pdf(record["document_name"], record["summary_text"])
    safe_name = Path(record["document_name"]).stem
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}-tom-tat.pdf"'
        },
    )