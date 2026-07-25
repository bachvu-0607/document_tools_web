from dataclasses import dataclass, field

from docx.text.paragraph import Paragraph


@dataclass
class Option:
    label: str
    text: str
    paragraph: Paragraph
    is_correct: bool
    # Vi tri (start, end) cua `text` trong paragraph.text GOC luc parse - dung
    # de render CHI thay dung phan noi dung nay, giu nguyen 100% phan con lai
    # (nhan, tab, khoang trang canh cot, xuong dong...) thay vi xoa ca dong
    # roi tu noi lai (de bi lech canh le so voi ban goc).
    start: int
    end: int


@dataclass
class Question:
    number: int
    paragraphs: list[Paragraph] = field(default_factory=list)
    options: list[Option] = field(default_factory=list)


@dataclass
class Part:
    title: str
    questions: list[Question] = field(default_factory=list)
