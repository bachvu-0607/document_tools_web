from pathlib import Path
from fastapi import HTTPException

from app.core.config import settings

def _resolve_pdf_path(document_id: str) -> Path:
    pdf_path = Path(settings.upload_dir) / f"{document_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return pdf_path