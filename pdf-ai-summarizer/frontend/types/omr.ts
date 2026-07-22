export type OmrSheetResponse = {
  id: string;
  label: string;
  original_filename: string;
  content_type: string;
  uploaded_at: string;
};

export type ZoneRect = {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
};

export type AnswerBlock = {
  zone: ZoneRect;
  num_questions: number;
  num_columns: number;
};

export type OmrTemplateCreateRequest = {
  name: string;
  reference_sheet_id: string;
  sbd_zone: ZoneRect;
  sbd_digits: number;
  made_zone: ZoneRect;
  made_digits: number;
  answer_blocks: AnswerBlock[];
  num_choices: number;
};

export type OmrTemplateResponse = OmrTemplateCreateRequest & {
  id: string;
  created_at: string;
};

export type OmrDetectionResponse = {
  sheet_id: string;
  template_id: string;
  sbd: string;
  sbd_ambiguous_digits: number[];
  made: string;
  made_ambiguous_digits: number[];
  answers: string[];
  ambiguous_questions: number[];
  detected_at: string;
  aligned: boolean;
};

export type OmrDetectionOverrideRequest = {
  sbd: string;
  made: string;
  answers: string[];
};

export type OmrAnswerKeyCreateRequest = {
  name: string;
  template_id: string;
  source_sheet_id: string;
  sbd: string;
  made: string;
  answers: string[];
};

export type OmrAnswerKeyResponse = OmrAnswerKeyCreateRequest & {
  id: string;
  created_at: string;
};

export type OmrGradeQuestionResult = {
  question: number;
  correct_answer: string;
  detected_answer: string;
  status: "correct" | "wrong" | "blank" | "ambiguous";
};

export type OmrGradeSheetResult = {
  sheet_id: string;
  sheet_label: string;
  sbd: string;
  made: string;
  correct_count: number;
  wrong_count: number;
  blank_count: number;
  ambiguous_count: number;
  score_10: number;
  questions: OmrGradeQuestionResult[];
  aligned: boolean;
};

export type OmrGradeBatchResponse = {
  answer_key_id: string;
  results: OmrGradeSheetResult[];
};

export type OmrGradedResultSaveRequest = {
  class_name: string;
  answer_key_id: string;
  sheet_ids: string[];
};

export type OmrGradedResultResponse = {
  id: string;
  class_name: string;
  sheet_id: string;
  sheet_label: string;
  answer_key_id: string;
  answer_key_name: string;
  sbd: string;
  made: string;
  correct_count: number;
  wrong_count: number;
  blank_count: number;
  ambiguous_count: number;
  score_10: number;
  aligned: boolean;
  saved_at: string;
};
