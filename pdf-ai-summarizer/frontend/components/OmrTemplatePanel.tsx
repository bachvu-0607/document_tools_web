"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  createOmrTemplate,
  deleteOmrTemplate,
  getOmrSheetAlignedUrl,
  getOmrSheetFileUrl,
  listOmrSheets,
  listOmrTemplates,
} from "@/lib/api";
import { OmrZoneCanvas } from "@/components/OmrZoneCanvas";
import type { ZoneRegion } from "@/components/OmrZoneCanvas";
import type { OmrSheetResponse, OmrTemplateResponse, ZoneRect } from "@/types/omr";

const MAX_ANSWER_BLOCKS = 3;

const ANSWER_BLOCK_COLORS = [
  { borderClass: "border-violet-500", bgClass: "bg-violet-500/15" },
  { borderClass: "border-fuchsia-500", bgClass: "bg-fuchsia-500/15" },
  { borderClass: "border-rose-500", bgClass: "bg-rose-500/15" },
];

type AnswerBlockDraft = {
  rect: ZoneRect | null;
  numQuestions: number;
  numColumns: number;
};

type OmrTemplatePanelProps = {
  initialReferenceSheetId?: string;
};

export function OmrTemplatePanel({ initialReferenceSheetId }: OmrTemplatePanelProps) {
  const [sheets, setSheets] = useState<OmrSheetResponse[]>([]);
  const [referenceSheetId, setReferenceSheetId] = useState(initialReferenceSheetId ?? "");

  const [templates, setTemplates] = useState<OmrTemplateResponse[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [listError, setListError] = useState("");
  const [deletingTemplateId, setDeletingTemplateId] = useState("");
  const [deleteError, setDeleteError] = useState("");

  const [activeKey, setActiveKey] = useState("sbd");
  const [sbdRect, setSbdRect] = useState<ZoneRect | null>(null);
  const [madeRect, setMadeRect] = useState<ZoneRect | null>(null);
  const [answerBlocks, setAnswerBlocks] = useState<AnswerBlockDraft[]>([
    { rect: null, numQuestions: 10, numColumns: 1 },
  ]);

  const [name, setName] = useState("");
  const [sbdDigits, setSbdDigits] = useState(6);
  const [madeDigits, setMadeDigits] = useState(3);
  const [numChoices, setNumChoices] = useState(4);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  async function refreshSheets() {
    try {
      const result = await listOmrSheets();
      setSheets(result);
      if (!referenceSheetId && result.length > 0) {
        setReferenceSheetId(result[0].id);
      }
    } catch {
      // Loi tai danh sach phieu se hien qua o panel upload, khong lap lai o day.
    }
  }

  async function refreshTemplates() {
    setLoadingTemplates(true);
    setListError("");
    try {
      const result = await listOmrTemplates();
      setTemplates(result);
    } catch (error) {
      setListError(error instanceof Error ? error.message : "Không tải được danh sách mẫu");
    } finally {
      setLoadingTemplates(false);
    }
  }

  useEffect(() => {
    void refreshSheets();
    void refreshTemplates();
  }, []);

  async function handleDeleteTemplate(templateId: string) {
    const confirmed = window.confirm("Xoá mẫu phiếu này? Không thể hoàn tác.");
    if (!confirmed) return;

    setDeletingTemplateId(templateId);
    setDeleteError("");
    try {
      await deleteOmrTemplate(templateId);
      await refreshTemplates();
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "Không xoá được mẫu phiếu");
    } finally {
      setDeletingTemplateId("");
    }
  }

  const regions: ZoneRegion[] = [
    { key: "sbd", label: "SBD", borderClass: "border-sky-500", bgClass: "bg-sky-500/15", rect: sbdRect },
    { key: "made", label: "Mã đề", borderClass: "border-amber-500", bgClass: "bg-amber-500/15", rect: madeRect },
    ...answerBlocks.map((block, index) => ({
      key: `answer-${index}`,
      label: `Câu hỏi - Khối ${index + 1}`,
      borderClass: ANSWER_BLOCK_COLORS[index].borderClass,
      bgClass: ANSWER_BLOCK_COLORS[index].bgClass,
      rect: block.rect,
    })),
  ];

  function handleRegionChange(key: string, rect: ZoneRect) {
    if (key === "sbd") {
      setSbdRect(rect);
    } else if (key === "made") {
      setMadeRect(rect);
    } else if (key.startsWith("answer-")) {
      const index = Number(key.split("-")[1]);
      setAnswerBlocks((prev) => prev.map((block, i) => (i === index ? { ...block, rect } : block)));
    }
  }

  function handleAddAnswerBlock() {
    if (answerBlocks.length >= MAX_ANSWER_BLOCKS) return;
    setAnswerBlocks((prev) => [...prev, { rect: null, numQuestions: 10, numColumns: 1 }]);
    setActiveKey(`answer-${answerBlocks.length}`);
  }

  function handleRemoveAnswerBlock(index: number) {
    if (answerBlocks.length <= 1) return;
    setAnswerBlocks((prev) => prev.filter((_, i) => i !== index));
    setActiveKey("sbd");
  }

  function updateAnswerBlockField(index: number, field: "numQuestions" | "numColumns", value: number) {
    setAnswerBlocks((prev) => prev.map((block, i) => (i === index ? { ...block, [field]: value } : block)));
  }

  const allAnswerBlocksDrawn = answerBlocks.every((block) => block.rect !== null);
  const canSave = Boolean(referenceSheetId) && Boolean(sbdRect) && Boolean(madeRect) && allAnswerBlocksDrawn && name.trim().length > 0;

  async function handleSaveTemplate() {
    if (!canSave || !sbdRect || !madeRect) return;
    setSaving(true);
    setSaveError("");
    try {
      await createOmrTemplate({
        name,
        reference_sheet_id: referenceSheetId,
        sbd_zone: sbdRect,
        sbd_digits: sbdDigits,
        made_zone: madeRect,
        made_digits: madeDigits,
        answer_blocks: answerBlocks.map((block) => ({
          zone: block.rect as ZoneRect,
          num_questions: block.numQuestions,
          num_columns: block.numColumns,
        })),
        num_choices: numChoices,
      });
      setName("");
      setSbdRect(null);
      setMadeRect(null);
      setAnswerBlocks([{ rect: null, numQuestions: 10, numColumns: 1 }]);
      await refreshTemplates();
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Không lưu được mẫu phiếu");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <div className="flex min-w-0 flex-col gap-1">
        <h2 className="text-xl font-semibold">Mẫu phiếu</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Chọn 1 ảnh phiếu đã tải lên, khoanh vùng SBD, Mã đề và (các) khối câu hỏi — chỉ khoanh đúng lưới ô tô, không lấy phần ô viết tay. Mẫu này dùng lại được cho mọi phiếu cùng loại.
        </p>
      </div>

      <div className="mt-5 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Ảnh dùng làm mẫu
          <select
            className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
            onChange={(event) => setReferenceSheetId(event.target.value)}
            value={referenceSheetId}
          >
            {sheets.length === 0 ? <option value="">Chưa có phiếu nào, hãy tải lên trước</option> : null}
            {sheets.map((sheet) => (
              <option key={sheet.id} value={sheet.id}>
                {sheet.label}
              </option>
            ))}
          </select>
        </label>

        {referenceSheetId ? (
          <>
            <div className="flex flex-wrap items-center gap-2">
              {regions.map((region) => (
                <button
                  className={`rounded-full border-2 px-3 py-1.5 text-sm font-medium transition ${
                    activeKey === region.key
                      ? `${region.borderClass} ${region.bgClass}`
                      : "border-zinc-300 text-zinc-500 dark:border-zinc-700 dark:text-zinc-400"
                  }`}
                  key={region.key}
                  onClick={() => setActiveKey(region.key)}
                  type="button"
                >
                  {region.label} {region.rect ? "✓" : ""}
                </button>
              ))}
              <Button
                className="!min-h-8 !px-3 !text-xs"
                disabled={answerBlocks.length >= MAX_ANSWER_BLOCKS}
                onClick={handleAddAnswerBlock}
                type="button"
                variant="secondary"
              >
                + Thêm khối câu hỏi
              </Button>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Đang khoanh vùng <strong>{regions.find((r) => r.key === activeKey)?.label}</strong> — giữ chuột kéo 1 khung quanh đúng vùng đó trên ảnh bên dưới. Vùng câu hỏi bị chia làm nhiều khối tách rời (vd 2 cột không liền nhau) thì bấm "Thêm khối câu hỏi" để khoanh thêm — thứ tự khối = thứ tự câu hỏi (khối 1 là các câu đầu, khối 2 nối tiếp theo sau...).
            </p>

            <OmrZoneCanvas
              activeKey={activeKey}
              imageUrl={getOmrSheetAlignedUrl(referenceSheetId)}
              onRegionChange={handleRegionChange}
              regions={regions}
            />
          </>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Tên mẫu
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setName(event.target.value)}
              placeholder="VD: Mẫu phiếu chuẩn - Toán 10A1"
              type="text"
              value={name}
            />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Số lựa chọn / câu
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              min={2}
              onChange={(event) => setNumChoices(Number(event.target.value))}
              type="number"
              value={numChoices}
            />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Số chữ số SBD
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              min={1}
              onChange={(event) => setSbdDigits(Number(event.target.value))}
              type="number"
              value={sbdDigits}
            />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Số chữ số Mã đề
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              min={1}
              onChange={(event) => setMadeDigits(Number(event.target.value))}
              type="number"
              value={madeDigits}
            />
          </label>
        </div>

        <div className="grid gap-3">
          <p className="text-sm font-medium">Các khối câu hỏi</p>
          {answerBlocks.map((block, index) => (
            <div
              className="grid gap-3 rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950"
              key={index}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium">
                  Khối {index + 1} {block.rect ? "✓ đã khoanh" : "— chưa khoanh"}
                </p>
                <Button
                  className="!min-h-8 !px-3 !text-xs"
                  disabled={answerBlocks.length <= 1}
                  onClick={() => handleRemoveAnswerBlock(index)}
                  type="button"
                  variant="secondary"
                >
                  Xoá khối
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <label className="grid gap-1 text-xs font-medium">
                  Số câu (bước nhảy 5)
                  <input
                    className="min-h-9 w-full rounded-lg border border-zinc-300 bg-white px-2 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:focus:border-zinc-600"
                    min={1}
                    onChange={(event) => updateAnswerBlockField(index, "numQuestions", Number(event.target.value))}
                    step={5}
                    type="number"
                    value={block.numQuestions}
                  />
                </label>
                <label className="grid gap-1 text-xs font-medium">
                  Số cột
                  <input
                    className="min-h-9 w-full rounded-lg border border-zinc-300 bg-white px-2 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:focus:border-zinc-600"
                    min={1}
                    onChange={(event) => updateAnswerBlockField(index, "numColumns", Number(event.target.value))}
                    type="number"
                    value={block.numColumns}
                  />
                </label>
              </div>
            </div>
          ))}
        </div>

        <Button disabled={!canSave} loading={saving} onClick={handleSaveTemplate} type="button">
          {saving ? "Đang lưu" : "Lưu mẫu"}
        </Button>
        {!canSave ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Cần khoanh đủ vùng SBD, Mã đề, mọi khối câu hỏi và đặt tên trước khi lưu.
          </p>
        ) : null}
        {saveError ? <p className="text-sm text-red-600 dark:text-red-400">{saveError}</p> : null}

        <div className="mt-2 grid gap-3 border-t border-zinc-200 pt-5 dark:border-zinc-800">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Mẫu phiếu đã lưu</p>
            <Button
              className="!min-h-8 !px-3 !text-xs"
              loading={loadingTemplates}
              onClick={() => void refreshTemplates()}
              type="button"
              variant="secondary"
            >
              Làm mới
            </Button>
          </div>
          {listError ? <p className="text-sm text-red-600 dark:text-red-400">{listError}</p> : null}
          {deleteError ? <p className="text-sm text-red-600 dark:text-red-400">{deleteError}</p> : null}
          {templates.length === 0 && !loadingTemplates ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Chưa có mẫu nào.</p>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {templates.map((template) => {
                const totalQuestions = template.answer_blocks.reduce((sum, b) => sum + b.num_questions, 0);
                return (
                  <div
                    className="grid gap-2 rounded-xl border-2 border-zinc-200 bg-zinc-50 p-2 dark:border-zinc-800 dark:bg-zinc-950"
                    key={template.id}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      alt={template.name}
                      className="aspect-[3/4] w-full rounded-lg object-cover"
                      src={getOmrSheetFileUrl(template.reference_sheet_id)}
                    />
                    <p className="truncate text-xs font-medium" title={template.name}>
                      {template.name}
                    </p>
                    <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                      {totalQuestions} câu ({template.answer_blocks.length} khối) x {template.num_choices} lựa chọn
                    </p>
                    {template.is_owner ? (
                      <Button
                        className="!min-h-8 !border-red-300 !px-2 !text-xs !text-red-600 hover:!bg-red-50 dark:!border-red-800 dark:!text-red-400 dark:hover:!bg-red-950"
                        loading={deletingTemplateId === template.id}
                        onClick={() => void handleDeleteTemplate(template.id)}
                        type="button"
                        variant="secondary"
                      >
                        Xoá
                      </Button>
                    ) : (
                      <p className="text-[11px] italic text-zinc-400 dark:text-zinc-500">Dùng chung — không phải mẫu của bạn</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
