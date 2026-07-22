"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DownloadIcon, FileIcon } from "@/components/ui/icons";
import { convertPdfToDocx, convertPdfToDocxAi } from "@/lib/api";

type RequestState = "idle" | "uploading" | "previewing" | "summarizing";

const docxExtractionModes = [
  { label: "Chỉ text", value: "text" },
  { label: "Text + mô tả ảnh", value: "text_images" },
  { label: "Toàn trang dạng ảnh", value: "full_page_images" },
];

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

type DocxExportPanelProps = {
  activeDocumentId: string;
  requestState: RequestState;
};

export function DocxExportPanel({
  activeDocumentId,
  requestState,
}: DocxExportPanelProps) {
  const [docxMode, setDocxMode] = useState("text");
  const [convertingMechanical, setConvertingMechanical] = useState(false);
  const [convertingAi, setConvertingAi] = useState(false);
  const [convertError, setConvertError] = useState("");

  const canConvert = Boolean(activeDocumentId) && requestState === "idle";

  async function handleConvertMechanical() {
    if (!activeDocumentId) return;
    setConvertingMechanical(true);
    setConvertError("");
    try {
      const blob = await convertPdfToDocx(activeDocumentId);
      triggerBlobDownload(blob, "chuyen-doi.docx");
    } catch (error) {
      setConvertError(error instanceof Error ? error.message : "Không chuyển đổi được");
    } finally {
      setConvertingMechanical(false);
    }
  }

  async function handleConvertAi() {
    if (!activeDocumentId) return;
    setConvertingAi(true);
    setConvertError("");
    try {
      const blob = await convertPdfToDocxAi(activeDocumentId, docxMode);
      triggerBlobDownload(blob, "chuyen-doi-ai.docx");
    } catch (error) {
      setConvertError(error instanceof Error ? error.message : "Không chuyển đổi được");
    } finally {
      setConvertingAi(false);
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-300">
          <FileIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Chuyển đổi Word</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            {activeDocumentId || "Chưa có document id"}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-5">
        <div className="grid gap-2">
          <p className="text-sm font-medium">Phương án 1 — miễn phí</p>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Giữ nguyên layout gốc, không dùng AI. Có thể gặp lỗi hiển thị (thiếu ảnh, khoảng cách sai lệch...) với một số PDF, đặc biệt PDF dạng slide.
          </p>
          <Button
            variant="secondary"
            disabled={!canConvert}
            loading={convertingMechanical}
            onClick={handleConvertMechanical}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {convertingMechanical ? "Đang chuyển đổi" : "Tải .docx (miễn phí)"}
          </Button>
        </div>

        <div className="grid gap-2 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <p className="text-sm font-medium">Phương án 2 — dùng AI</p>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            AI đọc và trình bày lại đầy đủ nội dung (giữ heading, bảng biểu thật) — không rút gọn. Có thể tốn thêm chi phí tuỳ chế độ đọc bên dưới, hợp với PDF dạng slide.
          </p>
          <select
            className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
            onChange={(event) => setDocxMode(event.target.value)}
            value={docxMode}
          >
            {docxExtractionModes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            "Chỉ text" không tốn phí AI. 2 chế độ còn lại tốn thêm chi phí và thời gian ("Toàn trang dạng ảnh" giới hạn tối đa 15 trang).
          </p>
          <Button
            variant="secondary"
            disabled={!canConvert}
            loading={convertingAi}
            onClick={handleConvertAi}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {convertingAi ? "Đang chuyển đổi" : "Tải .docx (AI)"}
          </Button>
        </div>

        {convertError ? (
          <p className="text-sm text-red-600 dark:text-red-400">{convertError}</p>
        ) : null}
      </div>
    </Card>
  );
}
