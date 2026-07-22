"use client";

import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent } from "react";

import { AuthGate } from "@/components/AuthGate";
import { Banner } from "@/components/Banner";
import { ConnectionBadge } from "@/components/ConnectionBadge";
import type { ConnectionState } from "@/components/ConnectionBadge";
import { DocumentPanel } from "@/components/DocumentPanel";
import { DocxExportPanel } from "@/components/DocxExportPanel";
import { ImageToolsPanel } from "@/components/ImageToolsPanel";
import { OmrPanel, OMR_TAB_LABELS, OMR_TAB_ORDER } from "@/components/OmrPanel";
import type { OmrSubTab } from "@/components/OmrPanel";
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
import type { UserInfo } from "@/types/auth";

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

type DocumentToolTab = "summarize" | "translate" | "docx" | "tools" | "image-tools";
type AppSection = "documents" | "omr";

const documentToolConfig: { id: DocumentToolTab; label: string }[] = [
  { id: "summarize", label: "Tóm tắt" },
  { id: "translate", label: "Dịch tài liệu" },
  { id: "docx", label: "Chuyển đổi Word" },
  { id: "tools", label: "Công cụ PDF" },
  { id: "image-tools", label: "Công cụ ảnh" },
];

export default function HomePage() {
  return (
    <AuthGate>
      {(user, onLogout) => <HomePageContent user={user} onLogout={onLogout} />}
    </AuthGate>
  );
}

type HomePageContentProps = {
  user: UserInfo;
  onLogout: () => void;
};

function HomePageContent({ user, onLogout }: HomePageContentProps) {
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
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  // Dieu huong tang ngoai (2 nhom lon: cong cu tai lieu vs cham trac nghiem)
  // + tang trong (tab con cua tung nhom) - ca 2 deu song o day va duoc sidebar
  // dieu khien, khong con thanh dai pill rieng trong tung panel nua.
  const [activeSection, setActiveSection] = useState<AppSection>("documents");
  const [documentTab, setDocumentTab] = useState<DocumentToolTab>("summarize");
  const [omrTab, setOmrTab] = useState<OmrSubTab>("upload");
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  function selectDocumentTab(tab: DocumentToolTab) {
    setActiveSection("documents");
    setDocumentTab(tab);
    setSidebarOpen(false);
  }

  function selectOmrTab(tab: OmrSubTab) {
    setActiveSection("omr");
    setOmrTab(tab);
    setSidebarOpen(false);
  }

  const sidebarContent = (
    <nav className="grid gap-1">
      <p className="px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-wide text-zinc-400 dark:text-zinc-500">
        Công cụ tài liệu
      </p>
      {documentToolConfig.map((tab) => {
        const active = activeSection === "documents" && documentTab === tab.id;
        return (
          <button
            className={`rounded-lg px-3 py-2 text-left text-sm font-medium transition ${
              active
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            }`}
            key={tab.id}
            onClick={() => selectDocumentTab(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        );
      })}

      <div className="my-2 border-t border-zinc-200 dark:border-zinc-800" />

      <p className="px-3 pb-1 pt-1 text-xs font-semibold uppercase tracking-wide text-zinc-400 dark:text-zinc-500">
        Chấm trắc nghiệm
      </p>
      <div className="grid gap-0.5 border-l-2 border-zinc-200 pl-2 dark:border-zinc-800">
        {OMR_TAB_ORDER.map((tab) => {
          const active = activeSection === "omr" && omrTab === tab;
          return (
            <button
              className={`rounded-lg px-3 py-1.5 text-left text-sm font-medium transition ${
                active
                  ? "bg-violet-600 text-white shadow-sm"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
              }`}
              key={tab}
              onClick={() => selectOmrTab(tab)}
              type="button"
            >
              {OMR_TAB_LABELS[tab]}
            </button>
          );
        })}
      </div>
    </nav>
  );

  return (
    <main className="min-h-screen text-zinc-950 dark:text-zinc-50">
      <div className="flex">
        {/* Sidebar - luon hien tren desktop, chuyen thanh drawer keo ra tren dien thoai */}
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 overflow-y-auto border-r border-zinc-200 bg-white/70 p-3 dark:border-zinc-800 dark:bg-zinc-950/70 lg:block">
          {sidebarContent}
        </aside>

        {sidebarOpen ? (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div className="absolute inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
            <aside className="absolute left-0 top-0 h-full w-64 overflow-y-auto bg-white p-3 shadow-xl dark:bg-zinc-950">
              {sidebarContent}
            </aside>
          </div>
        ) : null}

        <div className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
            <header className="flex flex-col gap-4 border-b border-zinc-300/70 pb-5 dark:border-zinc-800/70 lg:flex-row lg:items-end lg:justify-between">
              <div className="flex items-center gap-3">
                <button
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-300 text-lg dark:border-zinc-700 lg:hidden"
                  onClick={() => setSidebarOpen(true)}
                  type="button"
                >
                  ☰
                </button>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-emerald-500 text-white shadow-sm">
                  <SparklesIcon className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                    Local PDF AI Summarizer
                  </p>
                  <h1 className="mt-1 bg-gradient-to-br from-zinc-950 to-zinc-600 bg-clip-text text-3xl font-semibold text-transparent dark:from-white dark:to-zinc-400 sm:text-4xl">
                    {activeSection === "omr" ? "Chấm trắc nghiệm" : "Tóm tắt PDF"}
                  </h1>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <ConnectionBadge state={connectionState} health={health} onRefresh={checkBackend} />
                <div className="flex items-center gap-2 rounded-full border border-zinc-300/80 bg-white/90 py-1 pl-3 pr-1 text-sm shadow-sm dark:border-zinc-800/80 dark:bg-zinc-900/90">
                  <span className="text-zinc-600 dark:text-zinc-400">{user.display_name}</span>
                  <button
                    className="rounded-full px-2.5 py-1 text-xs font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
                    onClick={onLogout}
                    type="button"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </header>

            {errorMessage ? <Banner variant="error">{errorMessage}</Banner> : null}
            {message ? <Banner variant="success">{message}</Banner> : null}

            {activeSection === "documents" ? (
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
                  {documentTab === "summarize" ? (
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

                  {documentTab === "translate" ? (
                    <TranslatePanel
                      activeDocumentId={activeDocumentId}
                      documentName={uploadedDocument?.original_filename ?? ""}
                      requestState={requestState}
                    />
                  ) : null}

                  {documentTab === "docx" ? (
                    <DocxExportPanel
                      activeDocumentId={activeDocumentId}
                      requestState={requestState}
                    />
                  ) : null}

                  {documentTab === "tools" ? (
                    <PdfToolsPanel activeDocumentId={activeDocumentId} />
                  ) : null}

                  {documentTab === "image-tools" ? <ImageToolsPanel /> : null}
                </div>
              </div>
            ) : (
              // Cham trac nghiem la 1 module rieng, khong dung chung khung
              // "Tai lieu" ben trai - de no chiem toan bo chieu ngang thay vi
              // bi bo hep trong 1 cot nhu cac tool tren.
              <OmrPanel activeTab={omrTab} onTabChange={setOmrTab} />
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
