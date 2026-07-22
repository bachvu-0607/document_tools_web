from fastapi import APIRouter

from app.schemas.translation import TranslationRequest, TranslationResponse
from app.services.translation_service import translate_document

router = APIRouter(tags=["translations"])

@router.post("/translations", response_model=TranslationResponse)
def send_translation_request(request: TranslationRequest) -> TranslationResponse:
    return translate_document(request=request)
