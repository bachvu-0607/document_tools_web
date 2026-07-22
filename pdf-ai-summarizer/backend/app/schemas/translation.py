from pydantic import BaseModel

class TranslationRequest(BaseModel):
    document_id: str
    document_name: str
    target_language: str
    extraction_mode: str = "text"

class TranslationResponse(BaseModel):
    document_id: str
    translated_text: str
