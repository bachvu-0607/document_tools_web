"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DownloadIcon, ImageIcon, UploadIcon } from "@/components/ui/icons";
import { convertImage } from "@/lib/api";

const imageFormats = [
  { label: "Giữ nguyên định dạng", value: "same" },
  { label: "JPG", value: "jpeg" },
  { label: "PNG", value: "png" },
  { label: "WebP", value: "webp" },
];

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function ImageToolsPanel() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageFormat, setImageFormat] = useState("same");
  const [imageQuality, setImageQuality] = useState(85);
  const [converting, setConverting] = useState(false);
  const [error, setError] = useState("");

  async function handleConvertImage() {
    if (!imageFile) return;
    setConverting(true);
    setError("");
    try {
      const blob = await convertImage(imageFile, imageFormat, imageQuality);
      const ext =
        imageFormat === "same"
          ? imageFile.name.split(".").pop() || "img"
          : imageFormat === "jpeg"
            ? "jpg"
            : imageFormat;
      triggerBlobDownload(blob, `anh-da-xu-ly.${ext}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không xử lý được ảnh");
    } finally {
      setConverting(false);
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-50 text-rose-600 dark:bg-rose-950 dark:text-rose-300">
          <ImageIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Công cụ ảnh</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            Đổi định dạng / nén ảnh, không dùng AI, miễn phí
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          <span className="block w-fit cursor-pointer rounded-md border-0 bg-zinc-950 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-950 dark:hover:bg-zinc-300">
            <UploadIcon className="mr-1.5 inline h-4 w-4 align-text-bottom" />
            {imageFile ? imageFile.name : "Chọn ảnh"}
          </span>
          <input
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(event) => setImageFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Định dạng đầu ra
            <select
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setImageFormat(event.target.value)}
              value={imageFormat}
            >
              {imageFormats.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Chất lượng ({imageQuality})
            <input
              className="mt-2"
              max={100}
              min={10}
              onChange={(event) => setImageQuality(Number(event.target.value))}
              step={5}
              type="range"
              value={imageQuality}
            />
          </label>
        </div>

        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          Chất lượng chỉ ảnh hưởng tới JPG/WebP — không có tác dụng nếu xuất ra PNG (định dạng không mất dữ liệu).
        </p>

        <Button
          variant="secondary"
          disabled={!imageFile}
          loading={converting}
          onClick={handleConvertImage}
          type="button"
        >
          <DownloadIcon className="h-4 w-4" />
          {converting ? "Đang xử lý" : "Xử lý & tải ảnh"}
        </Button>

        {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
      </div>
    </Card>
  );
}
