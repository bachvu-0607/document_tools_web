from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.schemas.document import DocumentUploadResponse

async def save_upload_file(file: UploadFile) -> DocumentUploadResponse:
    original_filename = file.filename or ""
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail= "Only PDF file allowed")
    
    file_bytes = await file.read()
    max_byte = settings.max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_byte:
        raise HTTPException(status_code=400, detail="File is too large")
    
    document_id = str(uuid4())
    stored_filename = f"{document_id}.pdf"
    
    upload_dir = Path(settings.upload_dir)
    # tao thu muc neu chua co, neu chua co thu muc cha thi tao luon, neu thu muc da ton tai thi bo qua
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir/ stored_filename
    stored_path.write_bytes(file_bytes)

    return DocumentUploadResponse(
        id=document_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=len(file_bytes),
        content_type=file.content_type or "application/pdf",
    )