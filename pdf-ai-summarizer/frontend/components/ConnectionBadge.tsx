"use client";

import type { HealthResponse } from "@/types/health";
import { Button } from "@/components/ui/Button";
import { RefreshIcon } from "@/components/ui/icons";

export type ConnectionState = "checking" | "connected" | "disconnected";

type ConnectionBadgeProps = {
  state: ConnectionState;
  health: HealthResponse | null;
  onRefresh: () => void;
};

const stateConfig: Record<ConnectionState, { label: string; dot: string }> = {
  connected: { label: "Backend san sang", dot: "bg-emerald-500" },
  checking: { label: "Dang kiem tra", dot: "bg-amber-500 animate-pulse" },
  disconnected: { label: "Mat ket noi", dot: "bg-red-500" },
};

export function ConnectionBadge({ state, health, onRefresh }: ConnectionBadgeProps) {
  const config = stateConfig[state];

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex min-h-10 items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 text-sm shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <span className={`h-2.5 w-2.5 rounded-full ${config.dot}`} />
        <span className="font-medium">{config.label}</span>
        {health ? (
          <span className="text-zinc-400 dark:text-zinc-500">· v{health.version}</span>
        ) : null}
      </div>
      <Button
        variant="secondary"
        className="rounded-full"
        disabled={state === "checking"}
        onClick={onRefresh}
        type="button"
      >
        <RefreshIcon className={state === "checking" ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
        Kiem tra lai
      </Button>
    </div>
  );
}
