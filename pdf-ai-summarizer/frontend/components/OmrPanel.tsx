"use client";

import { useState } from "react";

import { OmrAnswerKeyPanel } from "@/components/OmrAnswerKeyPanel";
import { OmrGradePanel } from "@/components/OmrGradePanel";
import { OmrResultsPanel } from "@/components/OmrResultsPanel";
import { OmrTemplatePanel } from "@/components/OmrTemplatePanel";
import { OmrUploadPanel } from "@/components/OmrUploadPanel";

export type OmrSubTab = "upload" | "template" | "answerKey" | "grade" | "results";

export const OMR_TAB_ORDER: OmrSubTab[] = ["upload", "template", "answerKey", "grade", "results"];

export const OMR_TAB_LABELS: Record<OmrSubTab, string> = {
  upload: "Upload bài làm",
  template: "Đọc phiếu mẫu",
  answerKey: "Tạo đáp án",
  grade: "Chấm bài",
  results: "Bảng điểm",
};

type OmrPanelProps = {
  // Dieu huong 5 buoc nay gio do sidebar ben ngoai (app/page.tsx) dieu khien,
  // khong con thanh tab rieng ben trong component nay nua - de sidebar la
  // NOI DUY NHAT hien thi cay dieu huong, tranh 2 tang tab giong nhau gay roi.
  activeTab: OmrSubTab;
  onTabChange: (tab: OmrSubTab) => void;
};

export function OmrPanel({ activeTab, onTabChange }: OmrPanelProps) {
  const [templateSheetId, setTemplateSheetId] = useState<string | undefined>(undefined);
  const [answerKeySheetId, setAnswerKeySheetId] = useState<string | undefined>(undefined);
  const [gradeSheetIds, setGradeSheetIds] = useState<string[] | undefined>(undefined);

  function goToTemplate(sheetId: string) {
    setTemplateSheetId(sheetId);
    onTabChange("template");
  }
  function goToAnswerKey(sheetId: string) {
    setAnswerKeySheetId(sheetId);
    onTabChange("answerKey");
  }
  function goToGrade(sheetIds: string[]) {
    setGradeSheetIds(sheetIds);
    onTabChange("grade");
  }

  return (
    <div className="grid gap-3">
      {activeTab === "upload" ? (
        <OmrUploadPanel
          onGoToAnswerKey={goToAnswerKey}
          onGoToGrade={goToGrade}
          onGoToTemplate={goToTemplate}
        />
      ) : activeTab === "template" ? (
        <OmrTemplatePanel initialReferenceSheetId={templateSheetId} />
      ) : activeTab === "answerKey" ? (
        <OmrAnswerKeyPanel initialSheetId={answerKeySheetId} />
      ) : activeTab === "grade" ? (
        <OmrGradePanel initialSheetIds={gradeSheetIds} />
      ) : (
        <OmrResultsPanel />
      )}
    </div>
  );
}
