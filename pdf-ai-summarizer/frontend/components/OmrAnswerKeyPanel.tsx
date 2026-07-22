"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { OmrAnswerGrid } from "@/components/OmrAnswerGrid";
import { OmrDigitsEditor } from "@/components/OmrDigitsEditor";
import {
  createOmrAnswerKey,
  deleteOmrAnswerKey,
  detectOmrSheet,
  getOmrSheetFileUrl,
  getOmrSheetPreviewUrl,
  listOmrAnswerKeys,
  listOmrSheets,
  listOmrTemplates,
} from "@/lib/api";
import type {
  OmrAnswerKeyResponse,
  OmrDetectionResponse,
  OmrSheetResponse,
  OmrTemplateResponse,
} from "@/types/omr";

type OmrAnswerKeyPanelProps = {
  initialSheetId?: string;
};

export function OmrAnswerKeyPanel({ initialSheetId }: OmrAnswerKeyPanelProps) {
  const [sheets, setSheets] = useState<OmrSheetResponse[]>([]);
  const [templates, setTemplates] = useState<OmrTemplateResponse[]>([]);
  const [sheetId, setSheetId] = useState("");
  const [templateId, setTemplateId] = useState("");

  const [detecting, setDetecting] = useState(false);
  const [detectError, setDetectError] = useState("");
  const [result, setResult] = useState<OmrDetectionResponse | null>(null);
  const [previewCacheBust, setPreviewCacheBust] = useState(0);

  const [editedSbd, setEditedSbd] = useState("");
  const [editedMade, setEditedMade] = useState("");
  const [editedAnswers, setEditedAnswers] = useState<string[]>([]);

  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const [answerKeys, setAnswerKeys] = useState<OmrAnswerKeyResponse[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [deletingKeyId, setDeletingKeyId] = useState("");
  const [deleteKeyError, setDeleteKeyError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [sheetList, templateList] = await Promise.all([listOmrSheets(), listOmrTemplates()]);
        setSheets(sheetList);
        setTemplates(templateList);
        if (initialSheetId) {
          setSheetId(initialSheetId);
        } else if (sheetList.length > 0) {
          setSheetId(sheetList[0].id);
        }
        if (templateList.length > 0) setTemplateId(templateList[0].id);
      } catch {
        // Bo qua - danh sach rong thi form se tu disable nut chay doc.
      }
    })();
  }, [initialSheetId]);

  async function refreshAnswerKeys() {
    setLoadingKeys(true);
    try {
      setAnswerKeys(await listOmrAnswerKeys());
    } catch {
      // Loi tai danh sach khong chan duoc luong chinh, bo qua im lang.
    } finally {
      setLoadingKeys(false);
    }
  }

  useEffect(() => {
    void refreshAnswerKeys();
  }, []);

  async function handleDeleteAnswerKey(answerKeyId: string) {
    const confirmed = window.confirm("Xoá đáp án này? Không thể hoàn tác.");
    if (!confirmed) return;

    setDeletingKeyId(answerKeyId);
    setDeleteKeyError("");
    try {
      await deleteOmrAnswerKey(answerKeyId);
      await refreshAnswerKeys();
    } catch (error) {
      setDeleteKeyError(error instanceof Error ? error.message : "Không xoá được đáp án");
    } finally {
      setDeletingKeyId("");
    }
  }

  async function handleDetect() {
    if (!sheetId || !templateId) return;
    setDetecting(true);
    setDetectError("");
    try {
      const detection = await detectOmrSheet(templateId, sheetId);
      setResult(detection);
      setEditedSbd(detection.sbd);
      setEditedMade(detection.made);
      setEditedAnswers(detection.answers);
      setPreviewCacheBust(Date.now());
    } catch (error) {
      setDetectError(error instanceof Error ? error.message : "Không đọc được phiếu");
    } finally {
      setDetecting(false);
    }
  }

  async function handleSave() {
    if (!result) return;
    setSaving(true);
    setSaveError("");
    try {
      await createOmrAnswerKey({
        name,
        template_id: result.template_id,
        source_sheet_id: result.sheet_id,
        sbd: editedSbd,
        made: editedMade,
        answers: editedAnswers,
      });
      setName("");
      setResult(null);
      await refreshAnswerKeys();
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Không lưu được đáp án");
    } finally {
      setSaving(false);
    }
  }

  const canDetect = Boolean(sheetId) && Boolean(templateId);
  const canSave = Boolean(result) && name.trim().length > 0;
  const selectedTemplate = templates.find((t) => t.id === templateId);
  const numChoices = selectedTemplate?.num_choices ?? 4;

  return (
    <Card>
      <div className="flex min-w-0 flex-col gap-1">
        <h2 className="text-xl font-semibold">Tạo đáp án</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Chọn phiếu đã tô đúng + mẫu tương ứng, đọc thử, sửa lại nếu máy đọc sai, rồi lưu thành đáp án chuẩn dùng để chấm bài.
        </p>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Phiếu (đã tô đúng)
            <select
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setSheetId(event.target.value)}
              value={sheetId}
            >
              {sheets.length === 0 ? <option value="">Chưa có phiếu nào</option> : null}
              {sheets.map((sheet) => (
                <option key={sheet.id} value={sheet.id}>
                  {sheet.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Mẫu phiếu
            <select
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setTemplateId(event.target.value)}
              value={templateId}
            >
              {templates.length === 0 ? <option value="">Chưa có mẫu nào</option> : null}
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <Button disabled={!canDetect} loading={detecting} onClick={handleDetect} type="button">
          {detecting ? "Đang đọc" : "Đọc phiếu"}
        </Button>
        {detectError ? <p className="text-sm text-red-600 dark:text-red-400">{detectError}</p> : null}

        {result ? (
          <div className="grid gap-4 border-t border-zinc-200 pt-5 dark:border-zinc-800">
            {!result.aligned ? (
              <p className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                ⚠️ Không tìm được đủ 4 dấu góc đen để nắn thẳng ảnh này — kết quả đọc có thể kém chính xác hơn bình thường. Nên chụp lại ảnh rõ cả 4 góc, hoặc kiểm tra kỹ và sửa tay bên dưới trước khi lưu.
              </p>
            ) : null}
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Gõ chữ cái A/B/C/D trực tiếp vào từng ô để sửa nếu máy đọc sai (Backspace để xoá, tự nhảy sang ô kế tiếp).
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <p className="mb-1.5 text-sm font-medium">SBD</p>
                <OmrDigitsEditor
                  ambiguousPositions={result.sbd_ambiguous_digits}
                  digits={editedSbd}
                  editable
                  onChange={(index, value) =>
                    setEditedSbd((prev) => prev.slice(0, index) + value + prev.slice(index + 1))
                  }
                />
              </div>
              <div>
                <p className="mb-1.5 text-sm font-medium">Mã đề</p>
                <OmrDigitsEditor
                  ambiguousPositions={result.made_ambiguous_digits}
                  digits={editedMade}
                  editable
                  onChange={(index, value) =>
                    setEditedMade((prev) => prev.slice(0, index) + value + prev.slice(index + 1))
                  }
                />
              </div>
            </div>

            <OmrAnswerGrid
              ambiguousQuestions={result.ambiguous_questions}
              answers={editedAnswers}
              editable
              numChoices={numChoices}
              onChange={(index, value) =>
                setEditedAnswers((prev) => prev.map((a, i) => (i === index ? value : a)))
              }
            />

            <label className="grid gap-2 text-sm font-medium">
              Tên đáp án
              <input
                className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
                onChange={(event) => setName(event.target.value)}
                placeholder="VD: Đáp án - Kiểm tra Toán 15p - 10A1"
                type="text"
                value={name}
              />
            </label>

            <Button disabled={!canSave} loading={saving} onClick={handleSave} type="button">
              {saving ? "Đang lưu" : "Lưu đáp án"}
            </Button>
            {saveError ? <p className="text-sm text-red-600 dark:text-red-400">{saveError}</p> : null}

            <div className="grid gap-2">
              <p className="text-sm font-medium">Ảnh preview (khoanh vị trí đã đọc)</p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt="Preview detect"
                className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700"
                key={previewCacheBust}
                src={`${getOmrSheetPreviewUrl(result.sheet_id, result.template_id)}&t=${previewCacheBust}`}
              />
            </div>
          </div>
        ) : null}

        <div className="mt-2 grid gap-3 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Đáp án đã lưu</p>
            <Button
              className="!min-h-8 !px-3 !text-xs"
              loading={loadingKeys}
              onClick={() => void refreshAnswerKeys()}
              type="button"
              variant="secondary"
            >
              Làm mới
            </Button>
          </div>
          {deleteKeyError ? <p className="text-sm text-red-600 dark:text-red-400">{deleteKeyError}</p> : null}
          {answerKeys.length === 0 && !loadingKeys ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Chưa có đáp án nào.</p>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {answerKeys.map((key) => (
                <div
                  className="grid gap-2 rounded-xl border-2 border-zinc-200 bg-zinc-50 p-2 dark:border-zinc-800 dark:bg-zinc-950"
                  key={key.id}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    alt={key.name}
                    className="aspect-[3/4] w-full rounded-lg object-cover"
                    src={getOmrSheetFileUrl(key.source_sheet_id)}
                  />
                  <p className="truncate text-xs font-medium" title={key.name}>
                    {key.name}
                  </p>
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                    {key.answers.length} câu — Mã đề {key.made || "?"}
                  </p>
                  <Button
                    className="!min-h-8 !border-red-300 !px-2 !text-xs !text-red-600 hover:!bg-red-50 dark:!border-red-800 dark:!text-red-400 dark:hover:!bg-red-950"
                    loading={deletingKeyId === key.id}
                    onClick={() => void handleDeleteAnswerKey(key.id)}
                    type="button"
                    variant="secondary"
                  >
                    Xoá
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
