from pathlib import Path
import fitz
from fastapi import HTTPException
from collections import Counter

from app.core.config import settings
from app.schemas.document import DocumentTextPreviewResponse
from app.services.openai_service import describe_image, transcribe_page_image
from app.services.path_service import _resolve_pdf_path

MAX_PAGES_FOR_FULL_IMAGE = 15


def get_pdf_text_preview(document_id: str) -> DocumentTextPreviewResponse:
    pdf_path = Path(settings.upload_dir)/ f"{document_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        with fitz.open(str(pdf_path)) as pdf:
            text_parts : list[str] = []
            for page in pdf:
                text_parts.append(page.get_text())
            full_text = "\n".join(text_parts).strip()

            return DocumentTextPreviewResponse(
                id= document_id,
                page_count= pdf.page_count,
                text_length=len(full_text),
                preview=full_text[:1000],
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Cannot read PDF file") from exc
    
def get_pdf_text(document_id: str, extraction_mode: str = "text") -> str:
    pdf_path = _resolve_pdf_path(document_id)
    try:
        with fitz.open(str(pdf_path)) as pdf:
            if extraction_mode == "full_page_images" and pdf.page_count > MAX_PAGES_FOR_FULL_IMAGE:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Che do 'Toan trang dang anh' chi ho tro PDF toi da "
                        f"{MAX_PAGES_FOR_FULL_IMAGE} trang (file nay co {pdf.page_count} trang)."
                    ),
                )

            text_parts : list[str] = []
            for page in pdf:
                text_parts.extend(extract_text_from_page(page, pdf, extraction_mode))
            full_text = "\n".join(text_parts).strip()

            return full_text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Cannot read PDF file") from exc

def safe_cells(row: list) -> list[str]:
    return [str(cell) if cell is not None else "" for cell in row]

def get_body_font_size(page) -> float:
    sizes: list[float] = []
    page_dict = page.get_text("dict")
    for block in page_dict["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sizes.append(span["size"])
    
    most_common_size, count = Counter(sizes).most_common(1)[0]
    return most_common_size

def extract_images_from_page(page, doc) -> list[tuple[float, bytes, str]]:
    images_out: list[tuple[float, bytes, str]] = []
    image_list = page.get_images(full=True)

    for img in image_list:
        xref = img[0]
        rects = page.get_image_rects(xref)
        if not rects:
            continue

        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        y_position = rects[0].y0

        images_out.append((y_position, image_bytes, image_ext))

    return images_out

def render_page_to_image(page, zoom: float = 2.0) -> bytes:
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix)
    return pixmap.tobytes("png")

def extract_text_from_page(page, doc, extraction_mode: str = "text") -> list[str]:
    #che do "toan trang dang anh": bo qua het logic ben duoi, doc thang tu anh trang
    if extraction_mode == "full_page_images":
        page_image = render_page_to_image(page)
        return [transcribe_page_image(page_image)]

    #table
    text_parts: list[tuple[float, str]] = []
    tables = page.find_tables().tables

    #anh (chi chay khi nguoi dung chon che do "text_images", vi ton tien/thoi gian)
    if extraction_mode == "text_images":
        images = extract_images_from_page(page, doc)
        for y, image_bytes, image_ext in images:
            description = describe_image(image_bytes, image_ext)
            text_parts.append((y, f"**[Mo ta hinh anh]:** {description}"))

    for table in tables:
        rows = table.extract()
        if not rows: continue
        header = "| " + " | ".join(safe_cells(rows[0])) + " |"
        separator = "| " + " | ".join(["---"] * len(safe_cells(rows[0]))) + " |"
        body_lines = ["| " + " | ".join(safe_cells(row)) + " |" for row in rows[1:]]
        row_str = "\n".join([header, separator, *body_lines])
        text_parts.append((table.bbox[1], row_str))
    
    #text
    body_size = get_body_font_size(page)
    page_dict = page.get_text("dict")
    
    for block in page_dict["blocks"]:
        block_text = ""
        lines_out: list[str] = []

        for line in block.get("lines", []):
            check_line_in_table = False
            for table in tables:
                if line["bbox"][1] >= table.bbox[1] and line["bbox"][3] <= table.bbox[3]: 
                    check_line_in_table = True
            if check_line_in_table:
                continue
            line_text = ""
            for span in line.get("spans", []):
                line_text += span["text"]
            if line.get("spans") and line.get("spans")[0]["size"] > body_size * 1.2:
                line_text = "## " + line_text
            lines_out.append(line_text)
        block_text = "\n".join(lines_out)
        text_parts.append((block["bbox"][1], block_text))

    text_parts.sort(key=lambda x: x[0])
    return [content for _, content in text_parts]