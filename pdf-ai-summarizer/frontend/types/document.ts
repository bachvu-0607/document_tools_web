export type DocumentUploadResponse = {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  content_type: string;
};

export type DocumentTextPreviewResponse = {
  id: string;
  page_count: number;
  text_length: number;
  preview: string;
};
