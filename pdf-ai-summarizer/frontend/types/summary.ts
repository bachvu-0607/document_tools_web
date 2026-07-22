export type SummaryRequest = {
  document_id: string;
  document_name: string;
  summary_type: string;
  language: string;
  max_length: number;
  audience: string;
  focus: string;
  tone: string;
  custom_note: string;
  extraction_mode: string;
};

export type SummaryResponse = {
  document_id: string;
  summary: string;
};
