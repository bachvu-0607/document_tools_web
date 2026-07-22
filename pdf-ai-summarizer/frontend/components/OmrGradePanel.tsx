"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { OmrAnswerGrid } from "@/components/OmrAnswerGrid";
import { OmrDigitsEditor } from "@/components/OmrDigitsEditor";
import {
  gradeOmrSheetsBatch,
  getOmrSheetPreviewUrl,
  listOmrAnswerKeys,
  listOmrSheets,
  listOmrTemplates,
  overrideOmrDetection,
  saveOmrGradedResults,
} from "@/lib/api";
import type {
  OmrAnswerKeyResponse,
  OmrGradeSheetResult,
  OmrSheetResponse,
  OmrTemplateResponse,
} from "@/types/omr";

type OmrGradePanelProps = {
  initialSheetIds?: string[];
};

export function OmrGradePanel({ initialSheetIds }: OmrGradePanelProps) {
  const [sheets, setSheets] = useState<OmrSheetResponse[]>([]);
  const [answerKeys, setAnswerKeys] = useState<OmrAnswerKeyResponse[]>([]);
  const [templates, setTemplates] = useState<OmrTemplateResponse[]>([]);
  const [answerKeyId, setAnswerKeyId] = useState("");
  const [selectedSheetIds, setSelectedSheetIds] = useState<string[]>(initialSheetIds ?? []);

  const [grading, setGrading] = useState(false);
  const [gradeError, setGradeError] = useState("");
  const [results, setResults] = useState<OmrGradeSheetResult[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);

  const [className, setClassName] = useState("");
  const [savingResults, setSavingResults] = useState(false);
  const [saveResultsError, setSaveResultsError] = useState("");
  const [savedSheetIds, setSavedSheetIds] = useState<Set<string>>(new Set());

  const [editMode, setEditMode] = useState(false);
  const [editedSbd, setEditedSbd] = useState("");
  const [editedMade, setEditedMade] = useState("");
  const [editedAnswers, setEditedAnswers] = useState<string[]>([]);
  const [savingFix, setSavingFix] = useState(false);
  const [previewCacheBust, setPreviewCacheBust] = useState(0);

  useEffect(() => {
    void (async () => {
      try {
        const [sheetList, keyList, templateList] = await Promise.all([
          listOmrSheets(),
          listOmrAnswerKeys(),
          listOmrTemplates(),
        ]);
        setSheets(sheetList);
        setAnswerKeys(keyList);
        setTemplates(templateList);
        if (keyList.length > 0) setAnswerKeyId(keyList[0].id);
      } catch {
        // Bo qua - form se tu disable neu danh sach rong.
      }
    })();
  }, []);

  function toggleSheet(sheetId: string) {
    setSelectedSheetIds((prev) =>
      prev.includes(sheetId) ? prev.filter((id) => id !== sheetId) : [...prev, sheetId],
    );
  }

  async function handleGrade() {
    if (!answerKeyId || selectedSheetIds.length === 0) return;
    setGrading(true);
    setGradeError("");
    try {
      const response = await gradeOmrSheetsBatch(answerKeyId, selectedSheetIds);
      setResults(response.results);
      setActiveIndex(0);
      setSavedSheetIds(new Set());
      setSaveResultsError("");
    } catch (error) {
      setGradeError(error instanceof Error ? error.message : "Không chấm được");
    } finally {
      setGrading(false);
    }
  }

  async function handleSaveAllResults() {
    if (!className.trim() || results.length === 0) return;
    setSavingResults(true);
    setSaveResultsError("");
    try {
      await saveOmrGradedResults({
        class_name: className.trim(),
        answer_key_id: answerKeyId,
        sheet_ids: results.map((r) => r.sheet_id),
      });
      setSavedSheetIds(new Set(results.map((r) => r.sheet_id)));
    } catch (error) {
      setSaveResultsError(error instanceof Error ? error.message : "Không lưu được bảng điểm");
    } finally {
      setSavingResults(false);
    }
  }

  const activeResult = results[activeIndex] ?? null;
  const activeKey = answerKeys.find((k) => k.id === answerKeyId);
  const activeTemplate = templates.find((t) => t.id === activeKey?.template_id);
  const numChoices = activeTemplate?.num_choices ?? 4;

  useEffect(() => {
    if (activeResult) {
      setEditedSbd(activeResult.sbd);
      setEditedMade(activeResult.made);
      setEditedAnswers(activeResult.questions.map((q) => q.detected_answer));
      setEditMode(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex, results.length]);

  function goPrev() {
    setActiveIndex((prev) => Math.max(0, prev - 1));
  }
  function goNext() {
    setActiveIndex((prev) => Math.min(results.length - 1, prev + 1));
  }

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (results.length === 0 || editMode) return;
      if (event.key === "ArrowLeft") goPrev();
      if (event.key === "ArrowRight") goNext();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [results.length, editMode, activeIndex]);

  async function handleSaveFix() {
    if (!activeResult || !activeTemplate) return;
    setSavingFix(true);
    setGradeError("");
    try {
      await overrideOmrDetection(activeResult.sheet_id, activeTemplate.id, {
        sbd: editedSbd,
        made: editedMade,
        answers: editedAnswers,
      });
      const response = await gradeOmrSheetsBatch(answerKeyId, [activeResult.sheet_id]);
      const updated = response.results[0];
      setResults((prev) => prev.map((r, i) => (i === activeIndex ? updated : r)));
      setEditMode(false);
      setPreviewCacheBust(Date.now());
      setSavedSheetIds((prev) => {
        const next = new Set(prev);
        next.delete(activeResult.sheet_id);
        return next;
      });
    } catch (error) {
      setGradeError(error instanceof Error ? error.message : "Không lưu được chỉnh sửa");
    } finally {
      setSavingFix(false);
    }
  }

  return (
    <Card>
      <div className="flex min-w-0 flex-col gap-1">
        <h2 className="text-xl font-semibold">Chấm bài</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Chọn đáp án chuẩn + các phiếu học sinh, chấm 1 lần rồi lướt qua từng bài bằng nút hoặc phím ← →.
        </p>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Đáp án chuẩn
            <select
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setAnswerKeyId(event.target.value)}
              value={answerKeyId}
            >
              {answerKeys.length === 0 ? <option value="">Chưa có đáp án nào</option> : null}
              {answerKeys.map((key) => (
                <option key={key.id} value={key.id}>
                  {key.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Lớp (để lưu vào bảng điểm)
            <input
              className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
              onChange={(event) => setClassName(event.target.value)}
              placeholder="VD: 10A1"
              type="text"
              value={className}
            />
          </label>
        </div>

        <div className="grid gap-2">
          <p className="text-sm font-medium">Phiếu học sinh cần chấm ({selectedSheetIds.length} đã chọn)</p>
          <div className="grid max-h-52 grid-cols-2 gap-2 overflow-y-auto rounded-xl border border-zinc-200 p-2 dark:border-zinc-800 sm:grid-cols-4">
            {sheets.map((sheet) => {
              const checked = selectedSheetIds.includes(sheet.id);
              return (
                <button
                  className={`truncate rounded-lg border px-2 py-1.5 text-left text-xs transition ${
                    checked
                      ? "border-indigo-500 bg-indigo-500/10 font-medium"
                      : "border-zinc-200 text-zinc-600 dark:border-zinc-800 dark:text-zinc-400"
                  }`}
                  key={sheet.id}
                  onClick={() => toggleSheet(sheet.id)}
                  title={sheet.label}
                  type="button"
                >
                  {checked ? "✓ " : ""}
                  {sheet.label}
                </button>
              );
            })}
          </div>
        </div>

        <Button
          disabled={!answerKeyId || selectedSheetIds.length === 0}
          loading={grading}
          onClick={handleGrade}
          type="button"
        >
          {grading ? "Đang chấm" : `Chấm ${selectedSheetIds.length || ""} bài`}
        </Button>
        {gradeError ? <p className="text-sm text-red-600 dark:text-red-400">{gradeError}</p> : null}

        {results.length > 0 && activeResult ? (
          <div className="grid gap-4 border-t border-zinc-200 pt-5 dark:border-zinc-800">
            <div className="flex flex-wrap items-center gap-2">
              {results.map((result, index) => {
                const needsReview = result.wrong_count > 0 || result.ambiguous_count > 0;
                return (
                  <button
                    className={`rounded-full border px-2.5 py-1 text-xs font-medium transition ${
                      index === activeIndex
                        ? "border-indigo-600 bg-indigo-600 text-white"
                        : !result.aligned
                          ? "border-red-500 bg-red-500/15 text-red-700 dark:text-red-300"
                          : needsReview
                            ? "border-amber-500 bg-amber-500/15 text-amber-700 dark:text-amber-300"
                            : "border-emerald-500 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                    }`}
                    key={result.sheet_id}
                    onClick={() => setActiveIndex(index)}
                    type="button"
                  >
                    {!result.aligned ? "⚠️ " : ""}
                    {savedSheetIds.has(result.sheet_id) ? "✓ " : ""}
                    {result.sheet_label} ({result.score_10})
                  </button>
                );
              })}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                {savedSheetIds.size === results.length && results.length > 0
                  ? `✓ Đã lưu ${results.length} kết quả vào bảng điểm lớp "${className.trim()}"`
                  : "Xem qua từng bài, sửa nếu cần, rồi lưu chốt cả đợt vào bảng điểm."}
              </p>
              <Button
                className="!min-h-8 !px-3 !text-xs"
                disabled={!className.trim()}
                loading={savingResults}
                onClick={() => void handleSaveAllResults()}
                type="button"
              >
                💾 Lưu tất cả kết quả ({results.length})
              </Button>
            </div>
            {!className.trim() ? (
              <p className="text-xs text-amber-600 dark:text-amber-400">Cần nhập tên Lớp ở trên để lưu được vào bảng điểm.</p>
            ) : null}
            {saveResultsError ? <p className="text-sm text-red-600 dark:text-red-400">{saveResultsError}</p> : null}

            <div className="flex items-center justify-between">
              <Button onClick={goPrev} disabled={activeIndex === 0} type="button" variant="secondary">
                ← Trước
              </Button>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Bài {activeIndex + 1} / {results.length} — dùng phím ← → để lướt nhanh
              </p>
              <Button onClick={goNext} disabled={activeIndex === results.length - 1} type="button" variant="secondary">
                Sau →
              </Button>
            </div>

            {!activeResult.aligned ? (
              <p className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                ⚠️ Không tìm được đủ 4 dấu góc đen để nắn thẳng ảnh này — điểm số có thể không chính xác. Nên xem lại ảnh preview bằng mắt hoặc chụp lại.
              </p>
            ) : null}

            <div className="grid gap-2 rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950 sm:grid-cols-2">
              <div>
                <p className="text-lg font-semibold">{activeResult.sheet_label}</p>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  SBD {activeResult.sbd || "?"} — Mã đề {activeResult.made || "?"}
                </p>
              </div>
              <div className="sm:text-right">
                <p className="text-2xl font-bold">{activeResult.score_10}/10</p>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  {activeResult.correct_count} đúng — {activeResult.wrong_count} sai — {activeResult.blank_count} bỏ trống — {activeResult.ambiguous_count} không chắc
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">
                {editMode ? "Đang sửa — gõ chữ A/B/C/D trực tiếp vào ô, xong bấm Lưu" : "Xanh lá = đúng, đỏ = sai, vàng cam = không chắc"}
              </p>
              <Button
                className="!min-h-8 !px-3 !text-xs"
                onClick={() => setEditMode((prev) => !prev)}
                type="button"
                variant="secondary"
              >
                {editMode ? "Huỷ sửa" : "Sửa khoanh"}
              </Button>
            </div>

            {editMode ? (
              <div className="grid gap-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="mb-1.5 text-sm font-medium">SBD</p>
                    <OmrDigitsEditor
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
                      digits={editedMade}
                      editable
                      onChange={(index, value) =>
                        setEditedMade((prev) => prev.slice(0, index) + value + prev.slice(index + 1))
                      }
                    />
                  </div>
                </div>
                <OmrAnswerGrid
                  answers={editedAnswers}
                  editable
                  numChoices={numChoices}
                  onChange={(index, value) =>
                    setEditedAnswers((prev) => prev.map((a, i) => (i === index ? value : a)))
                  }
                />
                <Button loading={savingFix} onClick={handleSaveFix} type="button">
                  {savingFix ? "Đang lưu" : "Lưu chỉnh sửa & chấm lại"}
                </Button>
              </div>
            ) : (
              <OmrAnswerGrid
                answers={activeResult.questions.map((q) => q.detected_answer)}
                correctAnswers={activeResult.questions.map((q) => q.correct_answer)}
                numChoices={numChoices}
              />
            )}

            <div className="grid gap-2">
              <p className="text-sm font-medium">Ảnh preview</p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt="Preview cham bai"
                className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700"
                key={`${activeResult.sheet_id}-${previewCacheBust}`}
                src={`${getOmrSheetPreviewUrl(activeResult.sheet_id, activeTemplate?.id ?? "")}&t=${previewCacheBust}`}
              />
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
