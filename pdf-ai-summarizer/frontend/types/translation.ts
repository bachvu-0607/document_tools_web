export type TranslationRequest = {
  document_id: string;
  document_name: string;
  target_language: string;
  extraction_mode: string;
};

export type TranslationResponse = {
  document_id: string;
  translated_text: string;
};
