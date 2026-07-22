from app.schemas.translation import TranslationRequest, TranslationResponse
from app.services.pdf_reader import get_pdf_text
from app.services.openai_service import generate_summary_from_prompt


def translate_document(request: TranslationRequest) -> TranslationResponse:
    text = get_pdf_text(request.document_id, request.extraction_mode)
    prompt = build_translation_prompt(request=request, text=text)
    translated_text = generate_summary_from_prompt(prompt=prompt)

    return TranslationResponse(
        document_id=request.document_id,
        translated_text=translated_text,
    )


def build_translation_prompt(request: TranslationRequest, text: str) -> str:
    return f"""
            Ban la mot tro ly dich thuat chuyen nghiep.
            Hay dich toan bo noi dung ben duoi sang: {request.target_language}.

            Yeu cau:
            - Dich sat nghia, tu nhien, khong bo sot noi dung nao.
            - Giu nguyen cau truc: dung "## " cho tieu de muc neu co trong ban goc.
            - Giu nguyen bang bieu dang markdown table neu co trong ban goc.
            - Chi tra ve ban dich, khong them binh luan hay giai thich gi them.

            Noi dung can dich:
            {text}
            """
