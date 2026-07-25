from pathlib import Path
from fastapi import HTTPException

from app.core.config import settings


def resolve_stored_file(directory: str, filename: str, not_found_detail: str) -> Path:
    path = Path(directory) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=not_found_detail)
    return path

def _resolve_pdf_path(document_id: str) -> Path:
    return resolve_stored_file(settings.upload_dir, f"{document_id}.pdf", "Document not found")