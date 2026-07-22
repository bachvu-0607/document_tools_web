"use client";

import { useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";

import type { ZoneRect } from "@/types/omr";

export type ZoneRegion = {
  key: string;
  label: string;
  borderClass: string;
  bgClass: string;
  rect: ZoneRect | null;
};

function clamp01(value: number) {
  return Math.min(1, Math.max(0, value));
}

function rectStyle(rect: ZoneRect) {
  return {
    left: `${rect.x0 * 100}%`,
    top: `${rect.y0 * 100}%`,
    width: `${(rect.x1 - rect.x0) * 100}%`,
    height: `${(rect.y1 - rect.y0) * 100}%`,
  };
}

type OmrZoneCanvasProps = {
  imageUrl: string;
  regions: ZoneRegion[];
  activeKey: string;
  onRegionChange: (key: string, rect: ZoneRect) => void;
};

export function OmrZoneCanvas({ imageUrl, regions, activeKey, onRegionChange }: OmrZoneCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [draftRect, setDraftRect] = useState<ZoneRect | null>(null);
  const dragStartRef = useRef<{ x: number; y: number } | null>(null);

  const activeRegion = regions.find((region) => region.key === activeKey);

  function pointerToFraction(event: ReactPointerEvent<HTMLDivElement>) {
    const container = containerRef.current;
    if (!container) return { x: 0, y: 0 };
    const bounds = container.getBoundingClientRect();
    return {
      x: clamp01((event.clientX - bounds.left) / bounds.width),
      y: clamp01((event.clientY - bounds.top) / bounds.height),
    };
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    if (!activeRegion) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const point = pointerToFraction(event);
    dragStartRef.current = point;
    setDraftRect({ x0: point.x, y0: point.y, x1: point.x, y1: point.y });
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (!dragStartRef.current) return;
    const point = pointerToFraction(event);
    const start = dragStartRef.current;
    setDraftRect({
      x0: Math.min(start.x, point.x),
      y0: Math.min(start.y, point.y),
      x1: Math.max(start.x, point.x),
      y1: Math.max(start.y, point.y),
    });
  }

  function handlePointerUp() {
    if (draftRect && activeRegion && draftRect.x1 - draftRect.x0 > 0.01 && draftRect.y1 - draftRect.y0 > 0.01) {
      onRegionChange(activeRegion.key, draftRect);
    }
    dragStartRef.current = null;
    setDraftRect(null);
  }

  return (
    <div
      className="relative w-full touch-none select-none overflow-hidden rounded-xl border border-zinc-300 dark:border-zinc-700"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      ref={containerRef}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img alt="Phiếu mẫu" className="block w-full" draggable={false} src={imageUrl} />

      {regions.map((region) => {
        if (!region.rect) return null;
        return (
          <div
            className={`pointer-events-none absolute border-2 ${region.borderClass} ${region.bgClass}`}
            key={region.key}
            style={rectStyle(region.rect)}
          >
            <span
              className={`absolute -top-6 left-0 whitespace-nowrap rounded px-1.5 py-0.5 text-xs font-medium text-white ${region.borderClass.replace("border-", "bg-")}`}
            >
              {region.label}
            </span>
          </div>
        );
      })}

      {draftRect && activeRegion ? (
        <div
          className={`pointer-events-none absolute border-2 border-dashed ${activeRegion.borderClass}`}
          style={rectStyle(draftRect)}
        />
      ) : null}
    </div>
  );
}
