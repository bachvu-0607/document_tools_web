from fastapi import APIRouter, Depends, HTTPException, Response
from pathlib import Path
from urllib.parse import quote
from app.core.database import get_latest_summary
from app.schemas.auth import UserInfo
from app.schemas.summary import SummaryRequest, SummaryResponse, PdfExportRequest
from app.services.auth_service import get_current_user
from app.services.summary_service import create_summary
from app.services.pdf_export_service import create_summary_pdf
router = APIRouter(tags= ["summaries"])

@router.post("/summaries", response_model=SummaryResponse)
async def send_summary_request(
    request: SummaryRequest, current_user: UserInfo = Depends(get_current_user),
) -> SummaryResponse:
    return await create_summary(request=request, user_id=current_user.id)

@router.post("/summaries/export-pdf")
async def send_pdf_export_request(
    request: PdfExportRequest, current_user: UserInfo = Depends(get_current_user),
) -> Response:
    record = await get_latest_summary(request.document_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Chua co ban tom tat cho document nay")

    pdf_bytes = create_summary_pdf(record["document_name"], record["summary_text"])
    safe_name = Path(record["document_name"]).stem
    output_filename = f"{safe_name}-tom-tat.pdf"
    # Header HTTP chi cho phep ky tu Latin-1 - ten file co dau tieng Viet (vd "Đa
    # luồng") lam vo header neu dat truc tiep vao filename=. Dung ca 2 dang:
    # ascii_fallback (filename=, trinh duyet cu doc duoc nhung mat dau) va
    # filename*=UTF-8'' (RFC 5987, trinh duyet hien dai uu tien dung, giu nguyen dau).
    ascii_fallback = output_filename.encode("ascii", "ignore").decode("ascii") or "tom-tat.pdf"
    encoded_filename = quote(output_filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_fallback}"; '
                f"filename*=UTF-8''{encoded_filename}"
            )
        },
    )