"use client";

import { useState } from "react";

import { OmrAnswerKeyPanel } from "@/components/OmrAnswerKeyPanel";
import { OmrGradePanel } from "@/components/OmrGradePanel";
import { OmrResultsPanel } from "@/components/OmrResultsPanel";
import { OmrTemplatePanel } from "@/components/OmrTemplatePanel";
import { OmrUploadPanel } from "@/components/OmrUploadPanel";

type OmrSubTab = "upload" | "template" | "answerKey" | "grade" | "results";

const TAB_LABELS: Record<OmrSubTab, string> = {
  upload: "Upload bài làm",
  template: "Đọc phiếu mẫu",
  answerKey: "Tạo đáp án",
  grade: "Chấm bài",
  results: "Bảng điểm",
};

export function OmrPanel() {
  const [subTab, setSubTab] = useState<OmrSubTab>("upload");

  const [templateSheetId, setTemplateSheetId] = useState<string | undefined>(undefined);
  const [answerKeySheetId, setAnswerKeySheetId] = useState<string | undefined>(undefined);
  const [gradeSheetIds, setGradeSheetIds] = useState<string[] | undefined>(undefined);

  function goToTemplate(sheetId: string) {
    setTemplateSheetId(sheetId);
    setSubTab("template");
  }
  function goToAnswerKey(sheetId: string) {
    setAnswerKeySheetId(sheetId);
    setSubTab("answerKey");
  }
  function goToGrade(sheetIds: string[]) {
    setGradeSheetIds(sheetIds);
    setSubTab("grade");
  }

  return (
    <div className="grid gap-3">
      <div className="inline-flex w-fit flex-wrap gap-1 rounded-full border border-zinc-300/80 bg-white/90 p-1 shadow-sm dark:border-zinc-800/80 dark:bg-zinc-900/90">
        {(Object.keys(TAB_LABELS) as OmrSubTab[]).map((tab) => (
          <button
            className={`rounded-full px-3 py-1 text-sm font-medium transition ${
              subTab === tab
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-zinc-600 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-100"
            }`}
            key={tab}
            onClick={() => setSubTab(tab)}
            type="button"
          >
            {TAB_LABELS[tab]}
          </button>
        ))}
      </div>

      {subTab === "upload" ? (
        <OmrUploadPanel
          onGoToAnswerKey={goToAnswerKey}
          onGoToGrade={goToGrade}
          onGoToTemplate={goToTemplate}
        />
      ) : subTab === "template" ? (
        <OmrTemplatePanel initialReferenceSheetId={templateSheetId} />
      ) : subTab === "answerKey" ? (
        <OmrAnswerKeyPanel initialSheetId={answerKeySheetId} />
      ) : subTab === "grade" ? (
        <OmrGradePanel initialSheetIds={gradeSheetIds} />
      ) : (
        <OmrResultsPanel />
      )}
    </div>
  );
}
