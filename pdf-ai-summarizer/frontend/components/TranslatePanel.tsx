"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CheckIcon, CopyIcon, SparklesIcon } from "@/components/ui/icons";
import { translateDocument } from "@/lib/api";
import type { TranslationResponse } from "@/types/translation";

type RequestState = "idle" | "uploading" | "previewing" | "summarizing";

const languages = [
  { label: "Tiếng Việt", value: "Tieng Viet" },
  { label: "English", value: "English" },
  { label: "日本語 (Nhật)", value: "Japanese" },
  { label: "한국어 (Hàn)", value: "Korean" },
  { label: "中文 (Trung)", value: "Chinese" },
  { label: "Français (Pháp)", value: "French" },
];

const extractionModes = [
  { label: "Chỉ text", value: "text" },
  { label: "Text + mô tả ảnh", value: "text_images" },
  { label: "Toàn trang dạng ảnh", value: "full_page_images" },
];

type TranslatePanelProps = {
  activeDocumentId: string;
  documentName: string;
  requestState: RequestState;
};

export function TranslatePanel({
  activeDocumentId,
  documentName,
  requestState,
}: TranslatePanelProps) {
  const [targetLanguage, setTargetLanguage] = useState("English");
  const [extractionMode, setExtractionMode] = useState("text");
  const [translating, setTranslating] = useState(false);
  const [translateError, setTranslateError] = useState("");
  const [result, setResult] = useState<TranslationResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const canTranslate = Boolean(activeDocumentId) && requestState === "idle";

  async function handleTranslate() {
    if (!activeDocumentId) return;
    setTranslating(true);
    setTranslateError("");

    try {
      const response = await translateDocument({
        document_id: activeDocumentId,
        document_name: documentName,
        target_language: targetLanguage,
        extraction_mode: extractionMode,
      });
      setResult(response);
    } catch (error) {
      setTranslateError(
        error instanceof Error ? error.message : "Không dịch được",
      );
    } finally {
      setTranslating(false);
    }
  }

  async function handleCopy() {
    if (!result?.translated_text) return;
    await navigator.clipboard.writeText(result.translated_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-300">
          <SparklesIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Dịch tài liệu</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            {activeDocumentId || "Chưa có document id"}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Dịch sang ngôn ngữ
            <select
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setTargetLanguage(event.target.value)}
              value={targetLanguage}
            >
              {languages.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Chế độ đọc PDF
            <select
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setExtractionMode(event.target.value)}
              value={extractionMode}
            >
              {extractionModes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <p className="-mt-2 text-xs text-zinc-500 dark:text-zinc-400">
          Dịch luôn cần gọi AI (đã tính phí). "Text + mô tả ảnh" và "Toàn trang dạng ảnh" tốn thêm chi phí và thời gian so với "Chỉ text".
        </p>

        <Button
          variant="accent"
          className="min-h-11 font-semibold"
          disabled={!canTranslate}
          loading={translating}
          onClick={handleTranslate}
          type="button"
        >
          <SparklesIcon className="h-4 w-4" />
          {translating ? "Đang dịch" : "Dịch tài liệu"}
        </Button>

        {translateError ? (
          <p className="text-sm text-red-600 dark:text-red-400">{translateError}</p>
        ) : null}

        <div className="relative">
          <textarea
            className="min-h-96 w-full resize-y rounded-xl border border-zinc-300 bg-zinc-50 p-4 text-sm leading-6 outline-none focus:border-zinc-400 dark:border-zinc-800 dark:bg-zinc-950 dark:focus:border-zinc-600"
            placeholder="Bản dịch sẽ hiện ở đây."
            readOnly
            value={result?.translated_text ?? ""}
          />
          {result?.translated_text ? (
            <button
              className="absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-600 shadow-sm transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
              onClick={handleCopy}
              type="button"
            >
              {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <CopyIcon className="h-3.5 w-3.5" />}
              {copied ? "Đã chép" : "Sao chép"}
            </button>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
