"use client";

import { useState } from "react";
import type { ChangeEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DownloadIcon, UploadIcon, WrenchIcon } from "@/components/ui/icons";
import {
  compressPdf,
  convertDocumentToExcel,
  convertDocumentToExcelByTemplate,
  exportPageImagesZip,
  mergePdfs,
  uploadDocument,
} from "@/lib/api";

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

type MergeFile = {
  name: string;
  documentId: string;
};

type PdfToolsPanelProps = {
  activeDocumentId: string;
};

export function PdfToolsPanel({ activeDocumentId }: PdfToolsPanelProps) {
  const [exportingImages, setExportingImages] = useState(false);
  const [compressing, setCompressing] = useState(false);
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingExcelTemplate, setExportingExcelTemplate] = useState(false);
  const [toolsError, setToolsError] = useState("");

  const [mergeFiles, setMergeFiles] = useState<MergeFile[]>([]);
  const [uploadingForMerge, setUploadingForMerge] = useState(false);
  const [merging, setMerging] = useState(false);

  async function handleExportImages() {
    if (!activeDocumentId) return;
    setExportingImages(true);
    setToolsError("");
    try {
      const blob = await exportPageImagesZip(activeDocumentId);
      triggerBlobDownload(blob, "cac-trang-pdf.zip");
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Không xuất được ảnh");
    } finally {
      setExportingImages(false);
    }
  }

  async function handleCompress() {
    if (!activeDocumentId) return;
    setCompressing(true);
    setToolsError("");
    try {
      const blob = await compressPdf(activeDocumentId);
      triggerBlobDownload(blob, "nen-file.pdf");
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Không nén được file");
    } finally {
      setCompressing(false);
    }
  }

  async function handleExportExcel() {
    if (!activeDocumentId) return;
    setExportingExcel(true);
    setToolsError("");
    try {
      const blob = await convertDocumentToExcel(activeDocumentId);
      triggerBlobDownload(blob, "bao-cao-tai-chinh.xlsx");
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Không xuất được Excel");
    } finally {
      setExportingExcel(false);
    }
  }

  async function handleExportExcelTemplate() {
    if (!activeDocumentId) return;
    setExportingExcelTemplate(true);
    setToolsError("");
    try {
      const blob = await convertDocumentToExcelByTemplate(activeDocumentId);
      triggerBlobDownload(blob, "bctc-theo-mau.xlsx");
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Không xuất được Excel theo mẫu");
    } finally {
      setExportingExcelTemplate(false);
    }
  }

  async function handleAddFilesForMerge(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) return;

    setUploadingForMerge(true);
    setToolsError("");

    try {
      const uploaded: MergeFile[] = [];
      for (const file of files) {
        const result = await uploadDocument(file);
        uploaded.push({ name: result.original_filename, documentId: result.id });
      }
      setMergeFiles((prev) => [...prev, ...uploaded]);
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Không upload được file");
    } finally {
      setUploadingForMerge(false);
      event.target.value = "";
    }
  }

  function handleRemoveMergeFile(documentId: string) {
    setMergeFiles((prev) => prev.filter((file) => file.documentId !== documentId));
  }

  async function handleMerge() {
    if (mergeFiles.length < 2) return;
    setMerging(true);
    setToolsError("");
    try {
      const blob = await mergePdfs(mergeFiles.map((file) => file.documentId));
      triggerBlobDownload(blob, "gop-file.pdf");
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Không gộp được file");
    } finally {
      setMerging(false);
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-300">
          <WrenchIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Công cụ PDF</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            Các tiện ích nhỏ, không dùng AI, miễn phí
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-5">
        <div className="grid gap-2">
          <p className="text-sm font-medium">Xuất ảnh từng trang</p>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Tải xuống mỗi trang của tài liệu đang mở dưới dạng 1 file PNG, đóng gói trong 1 file ZIP.
          </p>
          <Button
            variant="secondary"
            disabled={!activeDocumentId}
            loading={exportingImages}
            onClick={handleExportImages}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {exportingImages ? "Đang xuất" : "Tải ảnh từng trang (.zip)"}
          </Button>
        </div>

        <div className="grid gap-2 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <p className="text-sm font-medium">Nén file PDF</p>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Nén tài liệu đang mở. Hiệu quả với PDF nhiều chữ; PDF nhiều ảnh sẽ giảm rất ít vì ảnh đã được nén sẵn.
          </p>
          <Button
            variant="secondary"
            disabled={!activeDocumentId}
            loading={compressing}
            onClick={handleCompress}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {compressing ? "Đang nén" : "Nén & tải PDF"}
          </Button>
        </div>

        <div className="grid gap-2 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <p className="text-sm font-medium">Xuất bảng biểu ra Excel</p>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Dò tìm các bảng số liệu trong tài liệu đang mở (phù hợp với báo cáo tài chính dạng bảng) và đổ ra file Excel. Dữ liệu có thể cần chỉnh lại thủ công sau khi xuất.
          </p>
          <Button
            variant="secondary"
            disabled={!activeDocumentId}
            loading={exportingExcel}
            onClick={handleExportExcel}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {exportingExcel ? "Đang xuất" : "Xuất Excel (.xlsx)"}
          </Button>

          <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
            Hoặc: nếu tài liệu đúng mẫu báo cáo tài chính chuẩn NHNN (B02a/B03a/B04a/B05a), thử cách đối chiếu theo mẫu — có tiêu đề, tên cột, in đậm dòng tổng, gọn và đúng thứ tự hơn. Riêng B05a (thuyết minh) không so khớp theo tên dòng mà xuất nguyên văn từng trang, có bảng thì lấy bảng, không có bảng thì lấy văn bản.
          </p>
          <Button
            variant="secondary"
            disabled={!activeDocumentId}
            loading={exportingExcelTemplate}
            onClick={handleExportExcelTemplate}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {exportingExcelTemplate ? "Đang xuất" : "Xuất Excel theo mẫu chuẩn"}
          </Button>
        </div>

        <div className="grid gap-2 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <p className="text-sm font-medium">Gộp nhiều PDF thành 1</p>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Chọn từ 2 file PDF trở lên — thứ tự trong danh sách là thứ tự gộp.
          </p>

          <label className="grid gap-2 text-sm font-medium">
            <span className="block w-fit cursor-pointer rounded-md border-0 bg-zinc-950 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-950 dark:hover:bg-zinc-300">
              <UploadIcon className="mr-1.5 inline h-4 w-4 align-text-bottom" />
              {uploadingForMerge ? "Đang upload..." : "Chọn file PDF"}
            </span>
            <input
              accept="application/pdf,.pdf"
              className="hidden"
              disabled={uploadingForMerge}
              multiple
              onChange={handleAddFilesForMerge}
              type="file"
            />
          </label>

          {mergeFiles.length > 0 ? (
            <ul className="grid gap-1.5 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm dark:border-zinc-800 dark:bg-zinc-950">
              {mergeFiles.map((file, index) => (
                <li key={file.documentId} className="flex items-center justify-between gap-2">
                  <span className="truncate">
                    {index + 1}. {file.name}
                  </span>
                  <button
                    className="shrink-0 text-xs text-red-600 hover:underline dark:text-red-400"
                    onClick={() => handleRemoveMergeFile(file.documentId)}
                    type="button"
                  >
                    Xoá
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          <Button
            variant="secondary"
            disabled={mergeFiles.length < 2}
            loading={merging}
            onClick={handleMerge}
            type="button"
          >
            <DownloadIcon className="h-4 w-4" />
            {merging ? "Đang gộp" : `Gộp & tải PDF (${mergeFiles.length} file)`}
          </Button>
        </div>

        {toolsError ? (
          <p className="text-sm text-red-600 dark:text-red-400">{toolsError}</p>
        ) : null}
      </div>
    </Card>
  );
}
