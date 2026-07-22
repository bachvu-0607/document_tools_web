"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { deleteOmrGradedResult, listOmrGradedResults } from "@/lib/api";
import type { OmrGradedResultResponse } from "@/types/omr";

export function OmrResultsPanel() {
  const [results, setResults] = useState<OmrGradedResultResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [listError, setListError] = useState("");
  const [search, setSearch] = useState("");
  const [deletingId, setDeletingId] = useState("");
  const [deleteError, setDeleteError] = useState("");

  async function refresh() {
    setLoading(true);
    setListError("");
    try {
      setResults(await listOmrGradedResults());
    } catch (error) {
      setListError(error instanceof Error ? error.message : "Không tải được bảng điểm");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleDelete(resultId: string) {
    const confirmed = window.confirm("Xoá kết quả này khỏi bảng điểm? Không thể hoàn tác.");
    if (!confirmed) return;

    setDeletingId(resultId);
    setDeleteError("");
    try {
      await deleteOmrGradedResult(resultId);
      await refresh();
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "Không xoá được kết quả");
    } finally {
      setDeletingId("");
    }
  }

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return results;
    return results.filter((r) =>
      [r.class_name, r.sbd, r.made, r.sheet_label, r.answer_key_name]
        .join(" ")
        .toLowerCase()
        .includes(query),
    );
  }, [results, search]);

  const averageScore =
    filtered.length > 0
      ? Math.round((filtered.reduce((sum, r) => sum + r.score_10, 0) / filtered.length) * 100) / 100
      : null;

  return (
    <Card>
      <div className="flex min-w-0 flex-col gap-1">
        <h2 className="text-xl font-semibold">Bảng điểm</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Danh sách kết quả đã được xem qua và lưu chốt ở tab "Chấm bài" — không tự động lưu, chỉ có kết quả bạn đã bấm "Lưu".
        </p>
      </div>

      <div className="mt-5 grid gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="min-h-10 flex-1 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Lọc theo lớp, SBD, mã đề, tên phiếu..."
            type="text"
            value={search}
          />
          <Button
            className="!min-h-10 !px-3 !text-xs"
            loading={loading}
            onClick={() => void refresh()}
            type="button"
            variant="secondary"
          >
            Làm mới
          </Button>
        </div>

        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          {filtered.length} kết quả{averageScore !== null ? ` — điểm trung bình ${averageScore}` : ""}
        </p>

        {listError ? <p className="text-sm text-red-600 dark:text-red-400">{listError}</p> : null}
        {deleteError ? <p className="text-sm text-red-600 dark:text-red-400">{deleteError}</p> : null}

        {filtered.length === 0 && !loading ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Chưa có kết quả nào được lưu.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-zinc-50 text-xs uppercase text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                <tr>
                  <th className="px-3 py-2 font-medium">Lớp</th>
                  <th className="px-3 py-2 font-medium">SBD</th>
                  <th className="px-3 py-2 font-medium">Mã đề</th>
                  <th className="px-3 py-2 font-medium">Phiếu</th>
                  <th className="px-3 py-2 font-medium">Điểm</th>
                  <th className="px-3 py-2 font-medium">Đúng/Sai/Trống/?</th>
                  <th className="px-3 py-2 font-medium">Lưu lúc</th>
                  <th className="px-3 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr className="border-t border-zinc-200 dark:border-zinc-800" key={r.id}>
                    <td className="px-3 py-2">{r.class_name}</td>
                    <td className="px-3 py-2">{r.sbd || "?"}</td>
                    <td className="px-3 py-2">{r.made || "?"}</td>
                    <td className="max-w-[160px] truncate px-3 py-2" title={r.sheet_label}>
                      {!r.aligned ? "⚠️ " : ""}
                      {r.sheet_label}
                    </td>
                    <td className="px-3 py-2 font-semibold">{r.score_10}</td>
                    <td className="px-3 py-2 text-xs text-zinc-500 dark:text-zinc-400">
                      {r.correct_count}/{r.wrong_count}/{r.blank_count}/{r.ambiguous_count}
                    </td>
                    <td className="px-3 py-2 text-xs text-zinc-500 dark:text-zinc-400">
                      {new Date(r.saved_at).toLocaleString("vi-VN")}
                    </td>
                    <td className="px-3 py-2">
                      <Button
                        className="!min-h-7 !border-red-300 !px-2 !text-xs !text-red-600 hover:!bg-red-50 dark:!border-red-800 dark:!text-red-400 dark:hover:!bg-red-950"
                        loading={deletingId === r.id}
                        onClick={() => void handleDelete(r.id)}
                        type="button"
                        variant="secondary"
                      >
                        Xoá
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Card>
  );
}
