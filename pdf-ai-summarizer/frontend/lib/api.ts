import type { HealthResponse } from "@/types/health";
import type {
  DocumentTextPreviewResponse,
  DocumentUploadResponse,
} from "@/types/document";
import type { SummaryRequest, SummaryResponse } from "@/types/summary";
import type { TranslationRequest, TranslationResponse } from "@/types/translation";
import type {
  OmrAnswerKeyCreateRequest,
  OmrAnswerKeyResponse,
  OmrDetectionOverrideRequest,
  OmrDetectionResponse,
  OmrGradeBatchResponse,
  OmrGradedResultResponse,
  OmrGradedResultSaveRequest,
  OmrSheetResponse,
  OmrTemplateCreateRequest,
  OmrTemplateResponse,
} from "@/types/omr";
import type { LoginRequest, LoginResponse, UserInfo } from "@/types/auth";
import { authHeader, clearToken, getToken } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function readErrorMessage(response: Response): Promise<string> {
  if (response.status === 401) {
    // Token thieu/het han/khong hop le - xoa token cu va bao cho AuthGate
    // biet de quay lai man hinh dang nhap, thay vi de nguoi dung thay loi
    // kho hieu o tung cho rieng le.
    clearToken();
    window.dispatchEvent(new Event("auth:unauthorized"));
  }

  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // Neu response khong phai JSON thi dung status text ben duoi.
  }

  return response.statusText || `Request failed with status ${response.status}`;
}

// Goi backend health check va tra ve JSON neu backend phan hoi thanh cong.
// Khong can dang nhap - chi de kiem tra server co song khong.
export async function getBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function login(request: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    // Khong dung readErrorMessage o day - login that bai (sai mat khau) khong
    // phai la "chua dang nhap", khong nen xoa token/bat AuthGate dang co (neu
    // co) doi trang thai gi ca.
    const data = (await response.json().catch(() => ({}))) as { detail?: unknown };
    throw new Error(typeof data.detail === "string" ? data.detail : "Dang nhap that bai");
  }

  return response.json() as Promise<LoginResponse>;
}

export async function getMe(): Promise<UserInfo> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { ...authHeader() },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<UserInfo>;
}

export async function uploadDocument(
  file: File,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: "POST",
    headers: { ...authHeader() },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<DocumentUploadResponse>;
}

export async function getDocumentTextPreview(
  documentId: string,
): Promise<DocumentTextPreviewResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/text-preview`,
    {
      headers: { ...authHeader() },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<DocumentTextPreviewResponse>;
}

export async function createSummary(
  request: SummaryRequest,
): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/summaries`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<SummaryResponse>;
}

export async function exportSummaryPdf(documentId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/summaries/export-pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ document_id: documentId }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function convertPdfToDocx(documentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/convert-docx`,
    { method: "POST", headers: { ...authHeader() } },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function convertPdfToDocxAi(
  documentId: string,
  extractionMode: string,
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/convert-docx-ai`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeader(),
      },
      body: JSON.stringify({ extraction_mode: extractionMode }),
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function translateDocument(
  request: TranslationRequest,
): Promise<TranslationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/translations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<TranslationResponse>;
}

export async function exportPageImagesZip(documentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/export-images`,
    { method: "POST", headers: { ...authHeader() } },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function mergePdfs(documentIds: string[]): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/documents/merge`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ document_ids: documentIds }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function compressPdf(documentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/compress`,
    { method: "POST", headers: { ...authHeader() } },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function convertDocumentToExcel(documentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/convert-excel`,
    { method: "POST", headers: { ...authHeader() } },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function convertDocumentToExcelByTemplate(documentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${documentId}/convert-excel-template`,
    { method: "POST", headers: { ...authHeader() } },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function convertImage(
  file: File,
  targetFormat: string,
  quality: number,
): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_format", targetFormat);
  formData.append("quality", String(quality));

  const response = await fetch(`${API_BASE_URL}/api/images/convert`, {
    method: "POST",
    headers: { ...authHeader() },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function uploadOmrSheet(
  file: File,
  label: string,
): Promise<OmrSheetResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("label", label);

  const response = await fetch(`${API_BASE_URL}/api/omr/sheets/upload`, {
    method: "POST",
    headers: { ...authHeader() },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrSheetResponse>;
}

export async function listOmrSheets(): Promise<OmrSheetResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/omr/sheets`, {
    headers: { ...authHeader() },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrSheetResponse[]>;
}

export async function deleteOmrSheet(sheetId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/omr/sheets/${sheetId}`, {
    method: "DELETE",
    headers: { ...authHeader() },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

// Dung lam src cua the <img> - trinh duyet tu goi GET, khong the dinh kem
// header Authorization qua the nay duoc (chi fetch() trong JS moi gan header
// duoc). Backend cho phep truyen token qua query string (?token=...) rieng
// cho 3 endpoint anh nay (xem get_current_user_flexible ben backend).
export function getOmrSheetFileUrl(sheetId: string): string {
  return `${API_BASE_URL}/api/omr/sheets/${sheetId}/file?token=${getToken() ?? ""}`;
}

export function getOmrSheetAlignedUrl(sheetId: string): string {
  return `${API_BASE_URL}/api/omr/sheets/${sheetId}/aligned?token=${getToken() ?? ""}`;
}

export async function createOmrTemplate(
  request: OmrTemplateCreateRequest,
): Promise<OmrTemplateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/omr/templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrTemplateResponse>;
}

export async function deleteOmrTemplate(templateId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/omr/templates/${templateId}`, {
    method: "DELETE",
    headers: { ...authHeader() },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function listOmrTemplates(): Promise<OmrTemplateResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/omr/templates`, {
    headers: { ...authHeader() },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrTemplateResponse[]>;
}

export async function detectOmrSheet(
  templateId: string,
  sheetId: string,
): Promise<OmrDetectionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/omr/templates/${templateId}/detect?sheet_id=${sheetId}`,
    { method: "POST", headers: { ...authHeader() } },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrDetectionResponse>;
}

export function getOmrSheetPreviewUrl(sheetId: string, templateId: string): string {
  return `${API_BASE_URL}/api/omr/sheets/${sheetId}/preview?template_id=${templateId}&token=${getToken() ?? ""}`;
}

export async function overrideOmrDetection(
  sheetId: string,
  templateId: string,
  request: OmrDetectionOverrideRequest,
): Promise<OmrDetectionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/omr/detections/${sheetId}?template_id=${templateId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrDetectionResponse>;
}

export async function createOmrAnswerKey(
  request: OmrAnswerKeyCreateRequest,
): Promise<OmrAnswerKeyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/omr/answer-keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrAnswerKeyResponse>;
}

export async function listOmrAnswerKeys(): Promise<OmrAnswerKeyResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/omr/answer-keys`, {
    headers: { ...authHeader() },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrAnswerKeyResponse[]>;
}

export async function deleteOmrAnswerKey(answerKeyId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/omr/answer-keys/${answerKeyId}`, {
    method: "DELETE",
    headers: { ...authHeader() },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function gradeOmrSheetsBatch(
  answerKeyId: string,
  sheetIds: string[],
): Promise<OmrGradeBatchResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/omr/answer-keys/${answerKeyId}/grade-batch`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ sheet_ids: sheetIds }),
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrGradeBatchResponse>;
}

export async function saveOmrGradedResults(
  request: OmrGradedResultSaveRequest,
): Promise<OmrGradedResultResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/omr/results`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrGradedResultResponse[]>;
}

export async function listOmrGradedResults(): Promise<OmrGradedResultResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/omr/results`, {
    headers: { ...authHeader() },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<OmrGradedResultResponse[]>;
}

export async function deleteOmrGradedResult(resultId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/omr/results/${resultId}`, {
    method: "DELETE",
    headers: { ...authHeader() },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function exportOmrResultsExcel(resultIds: string[]): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/omr/results/export-excel`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ result_ids: resultIds }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function generateExamVariants(
  file: File,
  startCode: number,
  count: number,
): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("start_code", String(startCode));
  formData.append("count", String(count));

  const response = await fetch(`${API_BASE_URL}/api/exam-variants/generate`, {
    method: "POST",
    headers: { ...authHeader() },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function checkOmrAlignment(blob: Blob): Promise<boolean> {
  const formData = new FormData();
  formData.append("file", blob, "check.jpg");

  const response = await fetch(`${API_BASE_URL}/api/omr/align-check`, {
    method: "POST",
    headers: { ...authHeader() },
    body: formData,
  });

  if (!response.ok) {
    return false;
  }

  const data = (await response.json()) as { found: boolean };
  return data.found;
}
