from fastapi import APIRouter, Depends

from app.schemas.auth import UserInfo
from app.schemas.translation import TranslationRequest, TranslationResponse
from app.services.auth_service import get_current_user
from app.services.translation_service import translate_document

router = APIRouter(tags=["translations"])

@router.post("/translations", response_model=TranslationResponse)
def send_translation_request(
    request: TranslationRequest, current_user: UserInfo = Depends(get_current_user),
) -> TranslationResponse:
    return translate_document(request=request)
