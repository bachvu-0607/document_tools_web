"use client";

import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent } from "react";

import { Banner } from "@/components/Banner";
import { ConnectionBadge } from "@/components/ConnectionBadge";
import type { ConnectionState } from "@/components/ConnectionBadge";
import { DocumentPanel } from "@/components/DocumentPanel";
import { DocxExportPanel } from "@/components/DocxExportPanel";
import { ImageToolsPanel } from "@/components/ImageToolsPanel";
import { OmrPanel } from "@/components/OmrPanel";
import { PdfToolsPanel } from "@/components/PdfToolsPanel";
import { SummaryPanel } from "@/components/SummaryPanel";
import { TranslatePanel } from "@/components/TranslatePanel";
import { SparklesIcon } from "@/components/ui/icons";
import {
  createSummary,
  getBackendHealth,
  getDocumentTextPreview,
  uploadDocument,
} from "@/lib/api";
import type {
  DocumentTextPreviewResponse,
  DocumentUploadResponse,
} from "@/types/document";
import type { HealthResponse } from "@/types/health";
import type { SummaryResponse } from "@/types/summary";

type RequestState = "idle" | "uploading" | "previewing" | "summarizing";

const summaryTypes = [
  { label: "Ngắn gọn", value: "short" },
  { label: "Chi tiết", value: "detailed" },
  { label: "Gạch đầu dòng", value: "bullet" },
  { label: "Ghi chú học tập", value: "study_notes" },
  { label: "Tóm tắt điều hành", value: "executive" },
  { label: "Hỏi - đáp", value: "qa" },
];

const languages = [
  { label: "Tiếng Việt", value: "vi" },
  { label: "English", value: "en" },
];

const audiences = [
  { label: "Sinh viên", value: "student" },
  { label: "Người mới", value: "beginner" },
  { label: "Lập trình viên", value: "developer" },
  { label: "Giáo viên / người dạy", value: "teacher" },
  { label: "Người đi làm / chuyên gia", value: "professional" },
  { label: "Nhà nghiên cứu / học thuật", value: "researcher" },
];

const focuses = [
  { label: "Ôn thi", value: "exam" },
  { label: "Khái niệm", value: "concepts" },
  { label: "Ví dụ / code", value: "examples" },
  { label: "Số liệu quan trọng", value: "key_data" },
  { label: "Kết luận & khuyến nghị", value: "conclusions" },
  { label: "Phương pháp luận", value: "methodology" },
  { label: "Ưu & nhược điểm", value: "pros_cons" },
];

const tones = [
  { label: "Trang trọng", value: "formal" },
  { label: "Thân thiện, dễ hiểu", value: "friendly" },
  { label: "Học thuật", value: "academic" },
];

const extractionModes = [
  { label: "Chỉ text", value: "text" },
  { label: "Text + mô tả ảnh", value: "text_images" },
  { label: "Toàn trang dạng ảnh", value: "full_page_images" },
];

type RightPanelTab = "summarize" | "translate" | "docx" | "tools" | "image-tools" | "omr";

const tabConfig: { id: RightPanelTab; label: string; activeClassName: string }[] = [
  { id: "summarize", label: "Tóm tắt", activeClassName: "bg-indigo-600 text-white shadow-sm" },
  { id: "translate", label: "Dịch tài liệu", activeClassName: "bg-sky-600 text-white shadow-sm" },
  { id: "docx", label: "Chuyển đổi Word", activeClassName: "bg-emerald-600 text-white shadow-sm" },
  { id: "tools", label: "Công cụ PDF", activeClassName: "bg-amber-600 text-white shadow-sm" },
  { id: "image-tools", label: "Công cụ ảnh", activeClassName: "bg-rose-600 text-white shadow-sm" },
  { id: "omr", label: "Chấm trắc nghiệm", activeClassName: "bg-violet-600 text-white shadow-sm" },
];

export default function HomePage() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("checking");
  const [requestState, setRequestState] = useState<RequestState>("idle");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedDocument, setUploadedDocument] =
    useState<DocumentUploadResponse | null>(null);
  const [textPreview, setTextPreview] =
    useState<DocumentTextPreviewResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [summaryType, setSummaryType] = useState("detailed");
  const [language, setLanguage] = useState("vi");
  const [maxLength, setMaxLength] = useState(800);
  const [audience, setAudience] = useState("student");
  const [focus, setFocus] = useState("concepts");
  const [tone, setTone] = useState("friendly");
  const [customNote, setCustomNote] = useState("");
  const [extractionMode, setExtractionMode] = useState("text");
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>("summarize");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function checkBackend() {
    setConnectionState("checking");
    setErrorMessage("");

    try {
      const result = await getBackendHealth();
      setHealth(result);
      setConnectionState(result.status === "ok" ? "connected" : "disconnected");
    } catch (error) {
      setHealth(null);
      setConnectionState("disconnected");
      setErrorMessage(
        error instanceof Error ? error.message : "Cannot connect to backend",
      );
    }
  }

  useEffect(() => {
    void checkBackend();
  }, []);

  const activeDocumentId = uploadedDocument?.id ?? "";
  const canSummarize = Boolean(activeDocumentId) && requestState === "idle";

  const activeFileLabel = useMemo(() => {
    if (uploadedDocument) {
      return uploadedDocument.original_filename;
    }

    return selectedFile?.name ?? "Chua co file";
  }, [selectedFile, uploadedDocument]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadedDocument(null);
    setTextPreview(null);
    setSummary(null);
    setMessage("");
    setErrorMessage("");
  }

  async function handleUpload() {
    if (!selectedFile) {
      setErrorMessage("Hay chon mot file PDF truoc.");
      return;
    }

    setRequestState("uploading");
    setErrorMessage("");
    setMessage("");
    setSummary(null);

    try {
      const uploaded = await uploadDocument(selectedFile);
      setUploadedDocument(uploaded);
      setMessage("Upload thanh cong.");

      setRequestState("previewing");
      const preview = await getDocumentTextPreview(uploaded.id);
      setTextPreview(preview);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Upload failed",
      );
    } finally {
      setRequestState("idle");
    }
  }

  async function handleRefreshPreview() {
    if (!uploadedDocument) {
      return;
    }

    setRequestState("previewing");
    setErrorMessage("");

    try {
      const preview = await getDocumentTextPreview(uploadedDocument.id);
      setTextPreview(preview);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Cannot read PDF preview",
      );
    } finally {
      setRequestState("idle");
    }
  }

  async function handleCreateSummary() {
    if (!uploadedDocument) {
      setErrorMessage("Can upload PDF truoc khi tom tat.");
      return;
    }

    setRequestState("summarizing");
    setErrorMessage("");
    setMessage("");

    try {
      const result = await createSummary({
        document_id: uploadedDocument.id,
        document_name: uploadedDocument.original_filename,
        summary_type: summaryType,
        language,
        max_length: maxLength,
        audience,
        focus,
        tone,
        custom_note: customNote,
        extraction_mode: extractionMode,
      });
      setSummary(result);
      setMessage("Da tao tom tat.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Cannot create summary",
      );
    } finally {
      setRequestState("idle");
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 text-zinc-950 dark:text-zinc-50 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-4 border-b border-zinc-300/70 pb-5 dark:border-zinc-800/70 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-emerald-500 text-white shadow-sm">
              <SparklesIcon className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Local PDF AI Summarizer
              </p>
              <h1 className="mt-1 bg-gradient-to-br from-zinc-950 to-zinc-600 bg-clip-text text-3xl font-semibold text-transparent dark:from-white dark:to-zinc-400 sm:text-4xl">
                Tóm tắt PDF
              </h1>
            </div>
          </div>

          <ConnectionBadge state={connectionState} health={health} onRefresh={checkBackend} />
        </header>

        {errorMessage ? <Banner variant="error">{errorMessage}</Banner> : null}
        {message ? <Banner variant="success">{message}</Banner> : null}

        <div className="grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <DocumentPanel
            activeFileLabel={activeFileLabel}
            selectedFile={selectedFile}
            uploadedDocument={uploadedDocument}
            textPreview={textPreview}
            requestState={requestState}
            onFileChange={handleFileChange}
            onUpload={handleUpload}
            onRefreshPreview={handleRefreshPreview}
          />

          <div className="grid gap-3">
            <div className="inline-flex w-fit flex-wrap gap-1 rounded-full border border-zinc-300/80 bg-white/90 p-1 shadow-sm backdrop-blur-sm dark:border-zinc-800/80 dark:bg-zinc-900/90">
              {tabConfig.map((tab) => (
                <button
                  key={tab.id}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                    rightPanelTab === tab.id
                      ? tab.activeClassName
                      : "text-zinc-600 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-100"
                  }`}
                  onClick={() => setRightPanelTab(tab.id)}
                  type="button"
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {rightPanelTab === "summarize" ? (
              <SummaryPanel
                activeDocumentId={activeDocumentId}
                summaryTypes={summaryTypes}
                languages={languages}
                audiences={audiences}
                focuses={focuses}
                tones={tones}
                extractionModes={extractionModes}
                summaryType={summaryType}
                language={language}
                maxLength={maxLength}
                audience={audience}
                focus={focus}
                tone={tone}
                customNote={customNote}
                extractionMode={extractionMode}
                onSummaryTypeChange={setSummaryType}
                onLanguageChange={setLanguage}
                onMaxLengthChange={setMaxLength}
                onAudienceChange={setAudience}
                onFocusChange={setFocus}
                onToneChange={setTone}
                onCustomNoteChange={setCustomNote}
                onExtractionModeChange={setExtractionMode}
                canSummarize={canSummarize}
                requestState={requestState}
                summary={summary}
                onCreateSummary={handleCreateSummary}
              />
            ) : null}

            {rightPanelTab === "translate" ? (
              <TranslatePanel
                activeDocumentId={activeDocumentId}
                documentName={uploadedDocument?.original_filename ?? ""}
                requestState={requestState}
              />
            ) : null}

            {rightPanelTab === "docx" ? (
              <DocxExportPanel
                activeDocumentId={activeDocumentId}
                requestState={requestState}
              />
            ) : null}

            {rightPanelTab === "tools" ? (
              <PdfToolsPanel activeDocumentId={activeDocumentId} />
            ) : null}

            {rightPanelTab === "image-tools" ? <ImageToolsPanel /> : null}

            {rightPanelTab === "omr" ? <OmrPanel /> : null}
          </div>
        </div>
      </div>
    </main>
  );
}
