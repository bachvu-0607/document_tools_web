"use client";

import { useRef } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

type OmrDigitsEditorProps = {
  digits: string;
  ambiguousPositions?: number[];
  editable?: boolean;
  onChange?: (index: number, newDigit: string) => void;
};

export function OmrDigitsEditor({
  digits,
  ambiguousPositions = [],
  editable = false,
  onChange,
}: OmrDigitsEditorProps) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  function handleInput(index: number, event: ChangeEvent<HTMLInputElement>) {
    if (!onChange) return;
    const raw = event.target.value.replace(/[^0-9]/g, "").slice(-1);
    if (raw === "") return;
    onChange(index, raw);
    inputRefs.current[index + 1]?.focus();
  }

  function handleKeyDown(index: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace") {
      inputRefs.current[index - 1]?.focus();
    }
  }

  return (
    <div className="flex flex-wrap gap-1">
      {digits.split("").map((digit, index) => (
        <input
          className={`flex h-9 w-8 items-center justify-center rounded-md border text-center text-sm font-semibold outline-none ${
            ambiguousPositions.includes(index)
              ? "border-amber-500 bg-amber-500/15 text-amber-700 dark:text-amber-300"
              : digit === "?"
                ? "border-zinc-300 bg-zinc-100 text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900"
                : "border-sky-500 bg-sky-500/10"
          } ${editable ? "" : "cursor-default"}`}
          disabled={!editable}
          key={index}
          maxLength={1}
          onChange={(event) => handleInput(index, event)}
          onKeyDown={(event) => handleKeyDown(index, event)}
          ref={(el) => {
            inputRefs.current[index] = el;
          }}
          value={digit}
        />
      ))}
    </div>
  );
}
