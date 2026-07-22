"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { UploadIcon, WrenchIcon } from "@/components/ui/icons";
import { OmrCameraCapture } from "@/components/OmrCameraCapture";
import { deleteOmrSheet, getOmrSheetFileUrl, listOmrSheets, uploadOmrSheet } from "@/lib/api";
import type { OmrSheetResponse } from "@/types/omr";

type OmrUploadPanelProps = {
  onGoToTemplate: (sheetId: string) => void;
  onGoToAnswerKey: (sheetId: string) => void;
  onGoToGrade: (sheetIds: string[]) => void;
};

export function OmrUploadPanel({ onGoToTemplate, onGoToAnswerKey, onGoToGrade }: OmrUploadPanelProps) {
  const [sheets, setSheets] = useState<OmrSheetResponse[]>([]);
  const [loadingSheets, setLoadingSheets] = useState(false);
  const [listError, setListError] = useState("");

  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  async function refreshSheets() {
    setLoadingSheets(true);
    setListError("");
    try {
      const result = await listOmrSheets();
      setSheets(result);
    } catch (error) {
      setListError(error instanceof Error ? error.message : "Không tải được danh sách phiếu");
    } finally {
      setLoadingSheets(false);
    }
  }

  useEffect(() => {
    void refreshSheets();
  }, []);

  async function handleUpload() {
    if (files.length === 0) return;
    setUploading(true);
    setUploadError("");
    try {
      for (const file of files) {
        // Khong dat ten rieng - backend tu dung ten file goc lam nhan, du
        // nhanh cho upload hang loat (ca lop 1 luot) ma khong phai go tay.
        await uploadOmrSheet(file, "");
      }
      setFiles([]);
      await refreshSheets();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Không tải lên được phiếu");
    } finally {
      setUploading(false);
    }
  }

  function toggleSelect(sheetId: string) {
    setSelectedIds((prev) =>
      prev.includes(sheetId) ? prev.filter((id) => id !== sheetId) : [...prev, sheetId],
    );
  }

  async function handleDeleteSelected() {
    if (selectedIds.length === 0) return;
    const confirmed = window.confirm(
      `Xoá ${selectedIds.length} phiếu đã chọn? Không thể hoàn tác.`,
    );
    if (!confirmed) return;

    setDeleting(true);
    setDeleteError("");
    const failed: string[] = [];
    for (const id of selectedIds) {
      try {
        await deleteOmrSheet(id);
      } catch (error) {
        failed.push(error instanceof Error ? error.message : `Không xoá được phiếu ${id}`);
      }
    }
    setSelectedIds([]);
    await refreshSheets();
    setDeleting(false);
    if (failed.length > 0) {
      setDeleteError(failed.join(" | "));
    }
  }

  const exactlyOneSelected = selectedIds.length === 1;
  const atLeastOneSelected = selectedIds.length >= 1;

  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300">
          <WrenchIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Upload bài làm</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            Chọn 1 hoặc nhiều ảnh phiếu (cả lớp cùng lúc cũng được)
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="flex flex-wrap gap-3">
          <label className="grid gap-2 text-sm font-medium">
            <span className="block w-fit cursor-pointer rounded-md border-0 bg-zinc-950 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-950 dark:hover:bg-zinc-300">
              <UploadIcon className="mr-1.5 inline h-4 w-4 align-text-bottom" />
              Chọn ảnh phiếu
            </span>
            <input
              accept="image/jpeg,image/png"
              className="hidden"
              multiple
              onChange={(event) =>
                setFiles(Array.from(event.target.files ?? []).filter((f) => f.type.startsWith("image/")))
              }
              type="file"
            />
          </label>

          <label className="grid gap-2 text-sm font-medium">
            <span className="block w-fit cursor-pointer rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:bg-zinc-800">
              <UploadIcon className="mr-1.5 inline h-4 w-4 align-text-bottom" />
              Chọn cả thư mục
            </span>
            <input
              // @ts-expect-error -- webkitdirectory khong nam trong type chuan cua React nhung duoc trinh duyet ho tro
              webkitdirectory=""
              accept="image/jpeg,image/png"
              className="hidden"
              multiple
              onChange={(event) =>
                setFiles(Array.from(event.target.files ?? []).filter((f) => f.type.startsWith("image/")))
              }
              type="file"
            />
          </label>
        </div>

        {files.length > 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Đã chọn {files.length} ảnh — giữ nguyên tên file gốc làm tên gợi nhớ.</p>
        ) : null}

        <Button disabled={files.length === 0} loading={uploading} onClick={handleUpload} type="button">
          <UploadIcon className="h-4 w-4" />
          {uploading ? "Đang tải lên" : `Tải lên${files.length > 0 ? ` (${files.length})` : ""}`}
        </Button>

        {uploadError ? <p className="text-sm text-red-600 dark:text-red-400">{uploadError}</p> : null}

        <div className="grid gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
          <p className="text-sm font-medium">Hoặc chụp trực tiếp bằng camera</p>
          <OmrCameraCapture onCaptured={() => void refreshSheets()} />
        </div>

        <div className="mt-2 grid gap-3 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Phiếu đã tải lên — bấm để chọn</p>
            <Button
              className="!min-h-8 !px-3 !text-xs"
              loading={loadingSheets}
              onClick={() => void refreshSheets()}
              type="button"
              variant="secondary"
            >
              Làm mới
            </Button>
          </div>

          {listError ? <p className="text-sm text-red-600 dark:text-red-400">{listError}</p> : null}
          {deleteError ? <p className="text-sm text-red-600 dark:text-red-400">{deleteError}</p> : null}

          {sheets.length === 0 && !loadingSheets ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Chưa có phiếu nào.</p>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {sheets.map((sheet) => {
                const checked = selectedIds.includes(sheet.id);
                return (
                  <button
                    className={`grid gap-2 rounded-xl border-2 p-2 text-left transition ${
                      checked
                        ? "border-indigo-500 bg-indigo-500/10"
                        : "border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950"
                    }`}
                    key={sheet.id}
                    onClick={() => toggleSelect(sheet.id)}
                    type="button"
                  >
                    <div className="relative">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        alt={sheet.label}
                        className="aspect-[3/4] w-full rounded-lg object-cover"
                        src={getOmrSheetFileUrl(sheet.id)}
                      />
                      {checked ? (
                        <span className="absolute right-1.5 top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                          ✓
                        </span>
                      ) : null}
                    </div>
                    <p className="truncate text-xs font-medium" title={sheet.label}>
                      {sheet.label}
                    </p>
                  </button>
                );
              })}
            </div>
          )}

          {atLeastOneSelected ? (
            <div className="sticky bottom-0 flex flex-wrap gap-2 rounded-xl border border-zinc-200 bg-white/95 p-3 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/95">
              <Button
                disabled={!exactlyOneSelected}
                onClick={() => onGoToTemplate(selectedIds[0])}
                type="button"
                variant="secondary"
              >
                Đọc phiếu mẫu →
              </Button>
              <Button
                disabled={!exactlyOneSelected}
                onClick={() => onGoToAnswerKey(selectedIds[0])}
                type="button"
                variant="secondary"
              >
                Tạo đáp án →
              </Button>
              <Button onClick={() => onGoToGrade(selectedIds)} type="button" variant="accent">
                Chấm bài ({selectedIds.length}) →
              </Button>
              <Button
                className="!border-red-300 !text-red-600 hover:!bg-red-50 dark:!border-red-800 dark:!text-red-400 dark:hover:!bg-red-950"
                loading={deleting}
                onClick={() => void handleDeleteSelected()}
                type="button"
                variant="secondary"
              >
                Xoá ({selectedIds.length})
              </Button>
              {!exactlyOneSelected ? (
                <p className="w-full text-xs text-zinc-500 dark:text-zinc-400">
                  "Đọc phiếu mẫu" và "Tạo đáp án" chỉ dùng được khi chọn đúng 1 ảnh.
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
