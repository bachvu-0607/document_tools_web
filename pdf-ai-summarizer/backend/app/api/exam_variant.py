import io
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from app.core.config import settings
from app.schemas.auth import UserInfo
from app.services.auth_service import get_current_user
from app.services.exam_variant.generate import build_answer_key_excel, generate_variants

router = APIRouter(tags=["exam-variant"])


@router.post("/exam-variants/generate")
async def generate_exam_variants_endpoint(
    file: UploadFile = File(...),
    start_code: int = Form(...),
    count: int = Form(...),
    current_user: UserInfo = Depends(get_current_user),
) -> Response:
    job_id = str(uuid4())
    work_dir = Path(settings.exam_variant_dir) / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename or "de_goc.docx"
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "docx"
    source_path = work_dir / f"de_goc.{ext}"
    source_path.write_bytes(await file.read())

    out_dir = work_dir / "out"
    try:
        answer_keys = generate_variants(source_path, start_code, count, out_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for code in answer_keys:
            docx_path = out_dir / f"made_{code}.docx"
            zf.write(docx_path, arcname=f"made_{code}.docx")

        zf.writestr("dap_an.xlsx", build_answer_key_excel(answer_keys))

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ma_de.zip"},
    )
