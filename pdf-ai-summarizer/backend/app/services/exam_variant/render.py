from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from app.services.exam_variant.models import Question
from app.services.exam_variant.parse import parse_exam_document

XML_SPACE_ATTR = qn("xml:space")


def _set_run_plain_text(run_element, text: str) -> None:
    """Xoa het noi dung hien co cua 1 <w:r> (w:t/w:tab/w:br...), GIU NGUYEN
    <w:rPr> (dinh dang: bold, underline, font, size...), roi ghi lai noi dung
    moi. `text` co the chua "\\n" (dai dien cho <w:br/> - xuong dong mem that
    su trong run goc, vi run.text tu dong quy doi <w:br/> thanh "\\n") - PHAI
    tach ra ghi lai bang <w:br/> that, KHONG duoc nhet thang ky tu "\\n" vao
    1 the <w:t> (Word khong coi do la xuong dong, chi la ky tu vo hinh, khien
    cac dong dinh lien/chay tran vao nhau)."""
    for child in list(run_element):
        if child.tag != qn("w:rPr"):
            run_element.remove(child)
    for i, line in enumerate(text.split("\n")):
        if i > 0:
            run_element.append(run_element.makeelement(qn("w:br"), {}))
        if line:
            t_el = run_element.makeelement(qn("w:t"), {})
            t_el.set(XML_SPACE_ATTR, "preserve")
            t_el.text = line
            run_element.append(t_el)


def _force_black(run_element) -> None:
    """Xoa mau chu cu (co the la do - dau hieu dap an dung) khoi 1 run da
    copy, luon dat lai thanh den - de dap an dung khong bi lo mau khi noi
    dung cua no doi sang vi tri/nhan khac."""
    r_pr = run_element.find(qn("w:rPr"))
    if r_pr is None:
        r_pr = run_element.makeelement(qn("w:rPr"), {})
        run_element.insert(0, r_pr)
    color_el = r_pr.find(qn("w:color"))
    if color_el is None:
        color_el = r_pr.makeelement(qn("w:color"), {})
        r_pr.append(color_el)
    for attr in list(color_el.attrib):
        del color_el.attrib[attr]
    color_el.set(qn("w:val"), "000000")


def _extract_content_runs(paragraph: Paragraph, start: int, end: int) -> list:
    """Tra ve list <w:r> XML element (da deepcopy) ung voi dung khoang
    [start, end) trong paragraph.text - GIU NGUYEN dinh dang goc cua tung
    run (bold, underline, font...), vi dinh dang la thuoc tinh CAP RUN nen
    khong the tach nho hon - chi lay dung phan text can neu 1 run chi giao
    1 phan voi khoang nay. Mau chu bi ep ve den (xem _force_black)."""
    result = []
    offset = 0
    for run in paragraph.runs:
        run_text = run.text
        run_start, run_end = offset, offset + len(run_text)
        if run_start < end and run_end > start:
            local_start = max(start, run_start) - run_start
            local_end = min(end, run_end) - run_start
            sub_text = run_text[local_start:local_end]
            if sub_text:
                new_r = deepcopy(run._r)
                _set_run_plain_text(new_r, sub_text)
                _force_black(new_r)
                result.append(new_r)
        offset = run_end
    return result


def _replace_span(paragraph: Paragraph, start: int, end: int, new_elements: list) -> None:
    """Thay doan [start, end) trong paragraph.text bang new_elements (list
    <w:r> da chuan bi san tu _extract_content_runs). Run nao NGOAI khoang nay
    giu nguyen, KHONG dong toi (khong mat dinh dang). Run nao bi khoang nay
    cat ngang giua chung thi tach lam 2 - phan con lai ngoai khoang giu
    nguyen dinh dang cu cua chinh no."""
    offset = 0
    inserted = False
    for run in list(paragraph.runs):
        run_text = run.text
        run_start, run_end = offset, offset + len(run_text)
        r_el = run._r

        if run_end <= start or run_start >= end:
            offset = run_end
            continue

        local_start = max(start, run_start) - run_start
        local_end = min(end, run_end) - run_start
        before_text = run_text[:local_start]
        after_text = run_text[local_end:]

        parent = r_el.getparent()
        insert_index = list(parent).index(r_el)

        if before_text:
            before_r = deepcopy(r_el)
            _set_run_plain_text(before_r, before_text)
            parent.insert(insert_index, before_r)
            insert_index += 1

        if not inserted:
            for el in new_elements:
                parent.insert(insert_index, el)
                insert_index += 1
            inserted = True

        if after_text:
            after_r = deepcopy(r_el)
            _set_run_plain_text(after_r, after_text)
            parent.insert(insert_index, after_r)
            insert_index += 1

        parent.remove(r_el)
        offset = run_end


def _render_question(question: Question, permutation: list[int]) -> None:
    seen_paragraphs: list[Paragraph] = []
    for opt in question.options:
        if opt.paragraph not in seen_paragraphs:
            seen_paragraphs.append(opt.paragraph)

    # Buoc 1 - DOC HET truoc: trich xuat toan bo noi dung nguon TRUOC KHI sua
    # bat ky paragraph nao. Bat buoc phai tach rieng buoc doc va buoc ghi, vi
    # nhieu dap an co the CUNG 1 paragraph (vd cau chi co 1 dong voi 4 dap an
    # tren cung dong) - neu vua doc vua ghi xen ke, den luot doc 1 dap an co
    # vi tri nguon trung/gan vi tri 1 dap an DA ghi truoc do trong CUNG vong
    # lap se doc phai du lieu da bi ghi de, khong con la noi dung goc.
    extracted = [
        _extract_content_runs(question.options[permutation[i]].paragraph, question.options[permutation[i]].start, question.options[permutation[i]].end)
        for i in range(len(question.options))
    ]

    # Buoc 2 - GHI: dung dung noi dung da trich xuat san o buoc 1, khong doc
    # lai tu paragraph nua.
    for paragraph in seen_paragraphs:
        slot_indices = [i for i, opt in enumerate(question.options) if opt.paragraph is paragraph]
        ordered = sorted(slot_indices, key=lambda i: question.options[i].start)

        replacements = [(question.options[i].start, question.options[i].end, extracted[i]) for i in ordered]

        # (Da thu "noi rong khoang cach theo khoang lon nhat trong cung cau"
        # o day nhung phan tac dung - dong bi day dai qua kho trang, khien
        # dap an cuoi bi xuong dong, con te hon truoc. Bo han, giu nguyen so
        # tab/khoang trang GOC tai tung vi tri - chap nhan lech nhe con hon
        # vo layout.)

        # Ap dung thay the theo thu tu CUOI dong VE DAU - sua 1 doan se
        # khong lam lech vi tri cac doan khac CHUA xu ly (nam truoc no trong
        # cung paragraph).
        for start, end, elements in sorted(replacements, key=lambda r: r[0], reverse=True):
            _replace_span(paragraph, start, end, elements)

        # Ep den TOAN BO run trong doan nay sau khi ghep xong - vi phan
        # "before/after" khi tach run (trong _replace_span) giu nguyen dinh
        # dang GOC, nen neu nhan ("C. ") va noi dung von la 1 run DUY NHAT
        # to do (dap an dung goc), phan nhan van con do sot lai du noi dung
        # da doi. Doan nao co option la chac chan thuoc vung dap an, khong
        # so anh huong nham sang cho khac.
        for run in paragraph.runs:
            _force_black(run._r)


def render_variant(original_path: Path, plan: dict[int, list[int]], output_path: Path) -> None:
    document = Document(str(original_path))
    parts = parse_exam_document(document)

    for part in parts:
        for question in part.questions:
            permutation = plan[question.number]
            _render_question(question, permutation)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_path))
