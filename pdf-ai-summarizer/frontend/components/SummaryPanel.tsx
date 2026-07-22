"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CheckIcon, CopyIcon, DownloadIcon, SparklesIcon } from "@/components/ui/icons";
import { exportSummaryPdf } from "@/lib/api";
import type { SummaryResponse } from "@/types/summary";

type RequestState = "idle" | "uploading" | "previewing" | "summarizing";

type Option = { label: string; value: string };

const selectClassName =
  "min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600";

type SummaryPanelProps = {
  activeDocumentId: string;
  summaryTypes: Option[];
  languages: Option[];
  audiences: Option[];
  focuses: Option[];
  tones: Option[];
  extractionModes: Option[];
  summaryType: string;
  language: string;
  maxLength: number;
  audience: string;
  focus: string;
  tone: string;
  customNote: string;
  extractionMode: string;
  onSummaryTypeChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onMaxLengthChange: (value: number) => void;
  onAudienceChange: (value: string) => void;
  onFocusChange: (value: string) => void;
  onToneChange: (value: string) => void;
  onCustomNoteChange: (value: string) => void;
  onExtractionModeChange: (value: string) => void;
  canSummarize: boolean;
  requestState: RequestState;
  summary: SummaryResponse | null;
  onCreateSummary: () => void;
};

export function SummaryPanel({
  activeDocumentId,
  summaryTypes,
  languages,
  audiences,
  focuses,
  tones,
  extractionModes,
  summaryType,
  language,
  maxLength,
  audience,
  focus,
  tone,
  customNote,
  extractionMode,
  onSummaryTypeChange,
  onLanguageChange,
  onMaxLengthChange,
  onAudienceChange,
  onFocusChange,
  onToneChange,
  onCustomNoteChange,
  onExtractionModeChange,
  canSummarize,
  requestState,
  summary,
  onCreateSummary,
}: SummaryPanelProps) {
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  async function handleCopy() {
    if (!summary?.summary) {
      return;
    }

    await navigator.clipboard.writeText(summary.summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  async function handleDownloadPdf() {
    if (!activeDocumentId) {
      return;
    }

    setDownloading(true);
    setDownloadError("");

    try {
      const blob = await exportSummaryPdf(activeDocumentId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "tom-tat.pdf";
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setDownloadError(
        error instanceof Error ? error.message : "Không tải được PDF",
      );
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300">
          <SparklesIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Tóm tắt</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            {activeDocumentId || "Chưa có document id"}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Kiểu tóm tắt
            <select
              className={selectClassName}
              onChange={(event) => onSummaryTypeChange(event.target.value)}
              value={summaryType}
            >
              {summaryTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Ngôn ngữ
            <select
              className={selectClassName}
              onChange={(event) => onLanguageChange(event.target.value)}
              value={language}
            >
              {languages.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Độ dài tối đa
            <input
              className={selectClassName}
              min={100}
              onChange={(event) => onMaxLengthChange(Number(event.target.value))}
              step={100}
              type="number"
              value={maxLength}
            />
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Đối tượng đọc
            <select
              className={selectClassName}
              onChange={(event) => onAudienceChange(event.target.value)}
              value={audience}
            >
              {audiences.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Trọng tâm
            <select
              className={selectClassName}
              onChange={(event) => onFocusChange(event.target.value)}
              value={focus}
            >
              {focuses.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Văn phong
            <select
              className={selectClassName}
              onChange={(event) => onToneChange(event.target.value)}
              value={tone}
            >
              {tones.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="grid gap-2 text-sm font-medium">
          Chế độ đọc PDF
          <select
            className={selectClassName}
            onChange={(event) => onExtractionModeChange(event.target.value)}
            value={extractionMode}
          >
            {extractionModes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-xs font-normal text-zinc-500 dark:text-zinc-400">
            Tóm tắt luôn cần gọi AI (đã tính phí). "Text + mô tả ảnh" và "Toàn trang dạng ảnh" tốn thêm chi phí và thời gian so với "Chỉ text".
          </p>
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Ghi chú thêm (tùy chọn)
          <textarea
            className="min-h-20 resize-y rounded-lg border border-zinc-300 bg-zinc-50 p-3 text-sm leading-6 outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
            placeholder="Ví dụ: chỉ tóm tắt chương 2, bỏ qua phần phụ lục, nhấn mạnh công thức..."
            onChange={(event) => onCustomNoteChange(event.target.value)}
            value={customNote}
          />
        </label>

        <Button
          variant="accent"
          className="min-h-11 font-semibold"
          disabled={!canSummarize}
          loading={requestState === "summarizing"}
          onClick={onCreateSummary}
          type="button"
        >
          <SparklesIcon className="h-4 w-4" />
          {requestState === "summarizing" ? "Đang tóm tắt" : "Tóm tắt"}
        </Button>

        <div className="relative">
          <textarea
            className="min-h-96 w-full resize-y rounded-xl border border-zinc-300 bg-zinc-50 p-4 text-sm leading-6 outline-none focus:border-zinc-400 dark:border-zinc-800 dark:bg-zinc-950 dark:focus:border-zinc-600"
            placeholder="Kết quả tóm tắt sẽ hiện ở đây."
            readOnly
            value={summary?.summary ?? ""}
          />
          {summary?.summary ? (
            <div className="absolute right-3 top-3 flex items-center gap-2">
              <button
                className="inline-flex items-center gap-1.5 rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-600 shadow-sm transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
                disabled={downloading}
                onClick={handleDownloadPdf}
                type="button"
              >
                <DownloadIcon className="h-3.5 w-3.5" />
                {downloading ? "Đang tải" : "Tải PDF"}
              </button>
              <button
                className="inline-flex items-center gap-1.5 rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-600 shadow-sm transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
                onClick={handleCopy}
                type="button"
              >
                {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <CopyIcon className="h-3.5 w-3.5" />}
                {copied ? "Đã chép" : "Sao chép"}
              </button>
            </div>
          ) : null}
        </div>

        {downloadError ? (
          <p className="text-sm text-red-600 dark:text-red-400">{downloadError}</p>
        ) : null}
      </div>
    </Card>
  );
}
