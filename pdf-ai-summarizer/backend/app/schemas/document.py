from pydantic import BaseModel

class DocumentUploadResponse(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: str

class DocumentTextPreviewResponse(BaseModel):
    id: str
    page_count: int
    text_length: int
    preview: str

class DocxAiConvertRequest(BaseModel):
    extraction_mode: str = "text"

class MergePdfRequest(BaseModel):
    document_ids: list[str]