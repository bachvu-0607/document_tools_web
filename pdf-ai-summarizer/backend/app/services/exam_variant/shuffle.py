from app.services.exam_variant.models import Question, Paragraph, Part
import random
CHOICE_LETTERS = "ABCD"

def shuffle_question(num_options: int, seed: int) -> list[int]:
    order = list(range(num_options))
    random.Random(seed).shuffle(order)
    return order

def new_correct_label(question: Question, permutation: list[int]) -> str:
    correct_indices = [i for i, opt in enumerate(question.options) if opt.is_correct]
    if not correct_indices:
        raise ValueError(
            f"Cau {question.number}: khong doc duoc dap an nao (co the dap an nam trong bang, "
            "chua ho tro doc bang - xem canh bao 'file co N bang' trong log)."
        )
    new_position = permutation.index(correct_indices[0])
    return CHOICE_LETTERS[new_position]

def build_variant_plan(parts: list[Part], variant_index: int) -> dict[int, list[int]]:
    plan = {}
    for part in parts:
        for question in part.questions:
            num_options = len(question.options)
            if num_options <= 2:
                # Cau dang True/False (2 dap an) - xao khong co nhieu y nghia
                # chong gian lan (chi co 2 hoan vi, giu nguyen/dao nguoc), va
                # nguoi dung yeu cau giu nguyen thu tu goc cho cac cau nay.
                plan[question.number] = list(range(num_options))
                continue
            seed = variant_index * 1000 + question.number
            plan[question.number] = shuffle_question(num_options, seed)
    return plan

def build_answer_key(parts: list[Part], plan: dict[int, list[int]]) -> dict[int, str]:
    answer_key = {}
    for part in parts:
        for question in part.questions:
            answer_key[question.number] = new_correct_label(question, plan[question.number])
    return answer_key