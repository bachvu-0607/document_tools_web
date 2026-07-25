import io
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from app.services.exam_variant.convert import convert_doc_to_docx
from app.services.exam_variant.parse import parse_exam, validate_exam
from app.services.exam_variant.render import render_variant
from app.services.exam_variant.shuffle import build_answer_key, build_variant_plan


def answer_key_to_list(answer_key: dict[int, str]) -> list[str]:
    max_question = max(answer_key)
    return [answer_key[q] for q in range(1, max_question + 1)]


def build_answer_key_excel(results: dict[int, list[str]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Dap an"

    num_questions = max((len(answers) for answers in results.values()), default=0)
    headers = ["Ma de"] + [f"Cau {i}" for i in range(1, num_questions + 1)]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for code in sorted(results):
        sheet.append([code, *results[code]])

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def generate_variants(source_path: Path, start_code: int, count: int, out_dir: Path) -> dict[int, list[str]]:
    docx_path = convert_doc_to_docx(source_path)
    # Chi dung parts nay de TINH plan (so luong dap an + dap an dung) - KHONG
    # dung paragraph cua lan parse nay de sua file, vi render_variant tu mo
    # lai document rieng cho tung ma de (xem giai thich trong render.py).
    parts = parse_exam(docx_path)

    issues = validate_exam(parts)
    if issues:
        raise ValueError("De doc bi loi, kiem tra lai file goc:\n" + "\n".join(issues))

    results: dict[int, list[str]] = {}
    for i in range(count):
        code = start_code + i
        plan = build_variant_plan(parts, variant_index=code)
        answer_key = build_answer_key(parts, plan)

        output_path = out_dir / f"made_{code}.docx"
        render_variant(docx_path, plan, output_path)

        results[code] = answer_key_to_list(answer_key)

    return results
