from pydantic import BaseModel

class SummaryRequest(BaseModel):
    document_id: str
    document_name: str
    summary_type: str
    language: str
    max_length: int
    audience: str
    focus: str
    tone: str
    custom_note: str = ""
    extraction_mode: str = "text"

class SummaryResponse(BaseModel):
    document_id: str
    summary: str

class PdfExportRequest(BaseModel):
    document_id: str