"use client";

import { useRef } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

const CHOICE_LETTERS = "ABCDEFGH";
const BLANK_STYLE = "border-zinc-200 bg-zinc-100 text-zinc-400 dark:border-zinc-800 dark:bg-zinc-900";

type OmrAnswerGridProps = {
  answers: string[];
  numChoices: number;
  ambiguousQuestions?: number[];
  // Truyen vao de bat che do "cham diem" (to mau dung/sai theo dap an chuan)
  // thay vi che do "doc thu" (chi to mau co/khong co dap an).
  correctAnswers?: string[];
  editable?: boolean;
  onChange?: (index: number, newAnswer: string) => void;
};

export function OmrAnswerGrid({
  answers,
  numChoices,
  ambiguousQuestions = [],
  correctAnswers,
  editable = false,
  onChange,
}: OmrAnswerGridProps) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const validLetters = CHOICE_LETTERS.slice(0, numChoices);

  function handleInput(index: number, event: ChangeEvent<HTMLInputElement>) {
    if (!onChange) return;
    const raw = event.target.value.toUpperCase().slice(-1);
    if (raw === "") {
      onChange(index, "");
      return;
    }
    if (!validLetters.includes(raw)) return;
    onChange(index, raw);
    // Go xong 1 ky tu hop le thi tu nhay sang cau tiep theo, go lien tuc
    // khong can bam chuot/tab qua tung o.
    inputRefs.current[index + 1]?.focus();
  }

  function handleKeyDown(index: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace" && answers[index] === "") {
      inputRefs.current[index - 1]?.focus();
    }
  }

  return (
    <div className="grid grid-cols-5 gap-2 sm:grid-cols-8">
      {answers.map((answer, index) => {
        const questionNumber = index + 1;
        const isAmbiguous = ambiguousQuestions.includes(questionNumber);

        let colorClass = BLANK_STYLE;
        if (isAmbiguous) {
          colorClass = "border-amber-500 bg-amber-500/15";
        } else if (correctAnswers) {
          if (answer === "") colorClass = BLANK_STYLE;
          else if (answer === correctAnswers[index]) colorClass = "border-emerald-500 bg-emerald-500/15";
          else colorClass = "border-red-500 bg-red-500/15";
        } else if (answer !== "") {
          colorClass = "border-sky-500 bg-sky-500/10";
        }

        return (
          <div className={`rounded-lg border p-2 text-center text-xs transition ${colorClass}`} key={questionNumber}>
            <p className="font-medium">{questionNumber}</p>
            {editable ? (
              <input
                className="mt-0.5 w-full bg-transparent text-center text-sm font-semibold uppercase outline-none"
                maxLength={1}
                onChange={(event) => handleInput(index, event)}
                onKeyDown={(event) => handleKeyDown(index, event)}
                ref={(el) => {
                  inputRefs.current[index] = el;
                }}
                value={answer}
              />
            ) : (
              <p className="text-sm font-semibold">{answer || "—"}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
