import io
import zipfile
import fitz
from fastapi import HTTPException

from app.core.config import settings
from app.services.pdf_reader import render_page_to_image
from app.services.path_service import _resolve_pdf_path

def export_page_images_zip(document_id: str) -> bytes:
    pdf_path = _resolve_pdf_path(document_id)

    zip_buffer = io.BytesIO()
    try:
        with fitz.open(str(pdf_path)) as pdf:
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for page_index, page in enumerate(pdf):
                    image_bytes = render_page_to_image(page)
                    zip_file.writestr(f"trang-{page_index + 1}.png", image_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Cannot export page images") from exc

    return zip_buffer.getvalue()

def merge_pdfs(document_ids: list[str]) -> bytes:
    if len(document_ids) < 2:
        raise HTTPException(status_code=400, detail="Can it nhat 2 file de gop")

    try:
        merged = fitz.open()
        for document_id in document_ids:
            pdf_path = _resolve_pdf_path(document_id)
            with fitz.open(str(pdf_path)) as source:
                merged.insert_pdf(source)

        merged_bytes = merged.tobytes()
        merged.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Cannot merge PDF files") from exc

    return merged_bytes

def compress_pdf(document_id: str) -> bytes:
    pdf_path = _resolve_pdf_path(document_id)

    try:
        with fitz.open(str(pdf_path)) as pdf:
            compressed_bytes = pdf.tobytes(garbage=4, deflate=True)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Cannot compress PDF file") from exc

    return compressed_bytes
