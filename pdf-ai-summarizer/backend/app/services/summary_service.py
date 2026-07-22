import datetime
from pathlib import Path
from fastapi import HTTPException
from app.core.config import settings
from app.core.database import save_summary_record
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.pdf_reader import get_pdf_text
from app.services.openai_service import generate_summary_from_prompt
from app.prompts.instructions import (
    AUDIENCE_INSTRUCTIONS,
    FOCUS_INSTRUCTIONS,
    SUMMARY_TYPE_INSTRUCTIONS,
    TONE_INSTRUCTIONS,
)

async def create_summary(request: SummaryRequest) -> SummaryResponse:
    text = get_pdf_text(request.document_id, request.extraction_mode)
    prompt: str = build_prompt_from_request(request= request, text=text)
    summary: str = generate_summary_from_prompt(prompt=prompt)

    await save_summary_record(
        document_id=request.document_id,
        document_name=request.document_name,
        summary_text=summary,
        at_time=datetime.datetime.now().isoformat(),
    )

    return SummaryResponse(document_id=request.document_id, summary=summary)

def build_prompt_from_request(request: SummaryRequest, text: str) -> str:
    summary_type_instruction = SUMMARY_TYPE_INSTRUCTIONS.get(
        request.summary_type, request.summary_type
    )
    audience_instruction = AUDIENCE_INSTRUCTIONS.get(request.audience, request.audience)
    focus_instruction = FOCUS_INSTRUCTIONS.get(request.focus, request.focus)
    tone_instruction = TONE_INSTRUCTIONS.get(request.tone, request.tone)

    custom_note_section = ""
    if request.custom_note.strip():
        custom_note_section = f"""
            Ghi chu them tu nguoi dung (uu tien lam theo yeu cau nay):
            {request.custom_note.strip()}
            """

    return f"""
            Ban la mot tro ly tom tat van ban.
            Hay tra loi bang dinh dang Markdown, dung "## " cho tieu de muc va "- " cho gach dau dong.

            Yeu cau tom tat:
            - Kieu tom tat: {summary_type_instruction}
            - Ngon ngu: {request.language}
            - Do dai toi da: {request.max_length}
            - Doi tuong doc: {audience_instruction}
            - Trong tam: {focus_instruction}
            - Van phong: {tone_instruction}
            {custom_note_section}
            Noi dung can tom tat:
            {text}
            """