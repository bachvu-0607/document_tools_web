"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DownloadIcon, UploadIcon } from "@/components/ui/icons";
import { generateExamVariants } from "@/lib/api";

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function ExamVariantPanel() {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [startCode, setStartCode] = useState(101);
  const [count, setCount] = useState(4);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    if (!sourceFile) return;
    setGenerating(true);
    setError("");
    try {
      const blob = await generateExamVariants(sourceFile, startCode, count);
      triggerBlobDownload(blob, "ma_de.zip");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tạo được mã đề");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <Card>
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-semibold">Tạo nhiều mã đề</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Tải lên đề gốc (đáp án đúng bôi đỏ) — hệ thống tự xáo thứ tự đáp án mỗi câu để sinh nhiều mã đề, kèm file đáp án tương ứng.
        </p>
      </div>

      <div className="mt-5 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          <span className="block w-fit cursor-pointer rounded-md border-0 bg-zinc-950 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-950 dark:hover:bg-zinc-300">
            <UploadIcon className="mr-1.5 inline h-4 w-4 align-text-bottom" />
            {sourceFile ? sourceFile.name : "Chọn file đề gốc (.doc, .docx)"}
          </span>
          <input
            accept=".doc,.docx"
            className="hidden"
            onChange={(event) => setSourceFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Mã đề bắt đầu
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              min={1}
              onChange={(event) => setStartCode(Number(event.target.value))}
              type="number"
              value={startCode}
            />
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Số lượng mã đề
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              min={1}
              onChange={(event) => setCount(Number(event.target.value))}
              type="number"
              value={count}
            />
          </label>
        </div>

        <Button
          variant="secondary"
          disabled={!sourceFile}
          loading={generating}
          onClick={handleGenerate}
          type="button"
        >
          <DownloadIcon className="h-4 w-4" />
          {generating ? "Đang tạo mã đề" : "Tạo & tải mã đề (.zip)"}
        </Button>

        {error ? (
          <p className="whitespace-pre-line text-sm text-red-600 dark:text-red-400">{error}</p>
        ) : null}
      </div>
    </Card>
  );
}
