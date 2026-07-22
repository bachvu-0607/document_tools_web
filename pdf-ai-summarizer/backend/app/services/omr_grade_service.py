from app.core.omr_database import get_sheet
from app.schemas.omr import (
    OmrAnswerKeyResponse,
    OmrGradeBatchResponse,
    OmrGradeQuestionResult,
    OmrGradeSheetResult,
)
from app.services.omr_answer_key_service import get_omr_answer_key
from app.services.omr_detect_service import get_or_run_detection


def _compare(correct_answers: list[str], detection_answers: list[str], ambiguous_questions: list[int]) -> list[OmrGradeQuestionResult]:
    questions: list[OmrGradeQuestionResult] = []
    for index, correct_answer in enumerate(correct_answers):
        question_number = index + 1
        detected_answer = detection_answers[index] if index < len(detection_answers) else ""

        if question_number in ambiguous_questions:
            status = "ambiguous"
        elif detected_answer == "":
            status = "blank"
        elif detected_answer == correct_answer:
            status = "correct"
        else:
            status = "wrong"

        questions.append(OmrGradeQuestionResult(
            question=question_number,
            correct_answer=correct_answer,
            detected_answer=detected_answer,
            status=status,
        ))
    return questions


async def grade_sheet(answer_key: OmrAnswerKeyResponse, sheet_id: str, user_id: str) -> OmrGradeSheetResult:
    sheet_row = await get_sheet(sheet_id, user_id)
    sheet_label = sheet_row["label"] if sheet_row else sheet_id

    detection = await get_or_run_detection(answer_key.template_id, sheet_id, user_id)
    questions = _compare(answer_key.answers, detection.answers, detection.ambiguous_questions)

    correct_count = sum(1 for q in questions if q.status == "correct")
    wrong_count = sum(1 for q in questions if q.status == "wrong")
    blank_count = sum(1 for q in questions if q.status == "blank")
    ambiguous_count = sum(1 for q in questions if q.status == "ambiguous")
    total = len(questions)
    score_10 = round(correct_count / total * 10, 2) if total > 0 else 0.0

    return OmrGradeSheetResult(
        sheet_id=sheet_id,
        sheet_label=sheet_label,
        sbd=detection.sbd,
        made=detection.made,
        correct_count=correct_count,
        wrong_count=wrong_count,
        blank_count=blank_count,
        ambiguous_count=ambiguous_count,
        score_10=score_10,
        questions=questions,
        aligned=detection.aligned,
    )


async def grade_sheets_batch(answer_key_id: str, sheet_ids: list[str], user_id: str) -> OmrGradeBatchResponse:
    answer_key = await get_omr_answer_key(answer_key_id, user_id)
    results = [await grade_sheet(answer_key, sheet_id, user_id) for sheet_id in sheet_ids]
    return OmrGradeBatchResponse(answer_key_id=answer_key_id, results=results)
