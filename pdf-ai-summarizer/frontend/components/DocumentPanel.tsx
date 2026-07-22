"use client";

import type { ChangeEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FileIcon, UploadIcon } from "@/components/ui/icons";
import type {
  DocumentTextPreviewResponse,
  DocumentUploadResponse,
} from "@/types/document";

type RequestState = "idle" | "uploading" | "previewing" | "summarizing";

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

type DocumentPanelProps = {
  activeFileLabel: string;
  selectedFile: File | null;
  uploadedDocument: DocumentUploadResponse | null;
  textPreview: DocumentTextPreviewResponse | null;
  requestState: RequestState;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onUpload: () => void;
  onRefreshPreview: () => void;
};

export function DocumentPanel({
  activeFileLabel,
  selectedFile,
  uploadedDocument,
  textPreview,
  requestState,
  onFileChange,
  onUpload,
  onRefreshPreview,
}: DocumentPanelProps) {
  return (
    <Card>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          <FileIcon />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 className="text-xl font-semibold">Tai lieu</h2>
          <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">
            {activeFileLabel}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          File PDF
          <input
            accept="application/pdf,.pdf"
            className="block w-full cursor-pointer rounded-xl border border-dashed border-zinc-300 bg-zinc-50 px-3 py-3 text-sm text-zinc-600 file:mr-3 file:cursor-pointer file:rounded-md file:border-0 file:bg-zinc-950 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300 dark:file:bg-zinc-100 dark:file:text-zinc-950 dark:hover:border-zinc-600"
            onChange={onFileChange}
            type="file"
          />
        </label>

        <div className="flex flex-wrap gap-3">
          <Button
            disabled={!selectedFile || requestState !== "idle"}
            loading={requestState === "uploading"}
            onClick={onUpload}
            type="button"
          >
            <UploadIcon className="h-4 w-4" />
            {requestState === "uploading" ? "Dang upload" : "Upload"}
          </Button>
          <Button
            variant="secondary"
            disabled={!uploadedDocument || requestState !== "idle"}
            loading={requestState === "previewing"}
            onClick={onRefreshPreview}
            type="button"
          >
            {requestState === "previewing" ? "Dang doc" : "Doc preview"}
          </Button>
        </div>

        {uploadedDocument ? (
          <dl className="grid gap-3 rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm dark:border-zinc-800 dark:bg-zinc-950 sm:grid-cols-2">
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">Document ID</dt>
              <dd className="mt-1 break-all font-medium">{uploadedDocument.id}</dd>
            </div>
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">Kich thuoc</dt>
              <dd className="mt-1 font-medium">
                {formatFileSize(uploadedDocument.file_size)}
              </dd>
            </div>
          </dl>
        ) : null}

        {textPreview ? (
          <div className="grid gap-3">
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-zinc-500 dark:text-zinc-400">So trang</dt>
                <dd className="mt-1 font-semibold">{textPreview.page_count}</dd>
              </div>
              <div>
                <dt className="text-zinc-500 dark:text-zinc-400">
                  So ky tu doc duoc
                </dt>
                <dd className="mt-1 font-semibold">
                  {textPreview.text_length.toLocaleString("vi-VN")}
                </dd>
              </div>
            </dl>
            <textarea
              className="min-h-64 resize-y rounded-xl border border-zinc-300 bg-zinc-50 p-3 text-sm leading-6 outline-none focus:border-zinc-400 dark:border-zinc-800 dark:bg-zinc-950 dark:focus:border-zinc-600"
              readOnly
              value={textPreview.preview}
            />
          </div>
        ) : null}
      </div>
    </Card>
  );
}
