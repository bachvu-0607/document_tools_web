from pydantic import BaseModel

class OmrSheetResponse(BaseModel):
    id: str
    label: str
    original_filename: str
    content_type: str
    uploaded_at: str

class OmrAlignCheckResponse(BaseModel):
    found: bool

class ZoneRect(BaseModel):
    # Toa do khung, tinh theo ty le % (0..1) so voi kich thuoc anh hien thi -
    # khong phu thuoc do phan giai anh thuc te cua tung phieu hoc sinh.
    x0: float
    y0: float
    x1: float
    y1: float

class AnswerBlock(BaseModel):
    # 1 khoi cau hoi rieng (khung + luoi). Nhieu khoi noi tiep nhau theo DUNG
    # THU TU trong list se tao thanh day cau hoi lien tuc: khoi dau la cau 1..N1,
    # khoi ke la cau N1+1..N1+N2,... - de ho tro phieu co vung cau hoi bi chia
    # thanh nhieu khoi tach roi tren trang (khong gom vao 1 hinh chu nhat duoc).
    zone: ZoneRect
    num_questions: int
    num_columns: int

class OmrTemplateCreateRequest(BaseModel):
    name: str
    reference_sheet_id: str
    sbd_zone: ZoneRect
    sbd_digits: int
    made_zone: ZoneRect
    made_digits: int
    answer_blocks: list[AnswerBlock]
    num_choices: int

class OmrTemplateResponse(BaseModel):
    id: str
    name: str
    reference_sheet_id: str
    sbd_zone: ZoneRect
    sbd_digits: int
    made_zone: ZoneRect
    made_digits: int
    answer_blocks: list[AnswerBlock]
    num_choices: int
    created_at: str

class OmrDetectionResponse(BaseModel):
    sheet_id: str
    template_id: str
    sbd: str
    # Vi tri (tinh tu 0) cac chu so SBD bi to mo/to doi, can nguoi xem lai bang mat.
    sbd_ambiguous_digits: list[int]
    made: str
    made_ambiguous_digits: list[int]
    # 1 phan tu / cau, "" neu bo trong, nhieu ky tu (vd "BD") neu to nhieu o.
    answers: list[str]
    # So cau (tinh tu 1) bi to mo/to doi, can nguoi xem lai bang mat.
    ambiguous_questions: list[int]
    detected_at: str
    # False neu khong tim du 4 dau goc den de nan thang anh - ket qua van co
    # nhung do tin cay thap hon, nen bao cho nguoi dung biet de tu kiem tra lai.
    aligned: bool

class OmrDetectionOverrideRequest(BaseModel):
    # Nguoi dung tu sua lai ket qua doc (sau khi xem anh preview thay may doc
    # sai) - luu de danh gia/cham diem dung ban da sua, khong bi ghi de lai
    # boi lan detect tu dong sau nay.
    sbd: str
    made: str
    answers: list[str]

class OmrAnswerKeyCreateRequest(BaseModel):
    name: str
    template_id: str
    source_sheet_id: str
    sbd: str = ""
    made: str = ""
    answers: list[str]

class OmrAnswerKeyResponse(BaseModel):
    id: str
    name: str
    template_id: str
    source_sheet_id: str
    sbd: str
    made: str
    answers: list[str]
    created_at: str

class OmrGradeQuestionResult(BaseModel):
    question: int
    correct_answer: str
    detected_answer: str
    # "correct" | "wrong" | "blank" | "ambiguous"
    status: str

class OmrGradeSheetResult(BaseModel):
    sheet_id: str
    sheet_label: str
    sbd: str
    made: str
    correct_count: int
    wrong_count: int
    blank_count: int
    ambiguous_count: int
    score_10: float
    questions: list[OmrGradeQuestionResult]
    # False neu khong nan thang duoc anh phieu nay - diem so co the kem tin
    # cay, nen xem lai bang mat truoc khi cong nhan.
    aligned: bool

class OmrGradeBatchRequest(BaseModel):
    sheet_ids: list[str]

class OmrGradeBatchResponse(BaseModel):
    answer_key_id: str
    results: list[OmrGradeSheetResult]

class OmrGradedResultSaveRequest(BaseModel):
    # Nguoi cham xem qua ket qua tu dong, thay on thi bam "luu" de chot vao so
    # diem - luu lai class_name nguoi dung tu go (khong co bang lop rieng,
    # phieu tu do minh hoa lop nao tuy nguoi dung dat ten luc go).
    class_name: str
    answer_key_id: str
    sheet_ids: list[str]

class OmrGradedResultResponse(BaseModel):
    id: str
    class_name: str
    sheet_id: str
    sheet_label: str
    answer_key_id: str
    answer_key_name: str
    sbd: str
    made: str
    correct_count: int
    wrong_count: int
    blank_count: int
    ambiguous_count: int
    score_10: float
    aligned: bool
    saved_at: str
